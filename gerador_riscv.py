import sys

import gerador_tac
from tokenizador import tokenize
from analisador_sintatico import analisar, ErroSintatico
from analisador_semantico import analisar_semantica
from gerador_tac import gerar_tac, formatar

# ==========================================
# GERADOR DE ASSEMBLY RISC-V DA LINGUAGEM .PAY
# ==========================================
#
# Recebe a lista de instruções TAC e traduz cada uma para instruções do
# RISC-V (RV32, com a extensão F para os números quebrados). O arquivo
# gerado roda no simulador RARS.
#
# ALOCAÇÃO INGÊNUA (a recomendada nos slides)
#
#   Todo valor mora na memória: variáveis e temporários (t1, t2...).
#   Para cada instrução TAC o gerador:
#       1. carrega os operandos da memória para registradores
#       2. faz a operação
#       3. guarda o resultado de volta na memória
#
#   Exemplo (com a, b e t1 globais):
#
#       t1 = a + b    vira    la  t6, var_a         t6 recebe o endereço de a
#                             lw  t0, 0(t6)         t0 recebe o valor de a
#                             la  t6, var_b
#                             lw  t1, 0(t6)         t1 recebe o valor de b
#                             add t0, t0, t1        t0 = a + b
#                             la  t6, var_t1
#                             sw  t0, 0(t6)         guarda na memória de t1
#
#   CUIDADO com os nomes: o t1 do TAC (um temporário, que vira o rótulo
#   var_t1 na memória) não tem nada a ver com o registrador t1 do RISC-V.
#   Os nomes são parecidos por coincidência.
#
#   É lento (muito acesso à memória), mas é simples e sempre funciona,
#   porque nenhum valor precisa sobreviver em registrador de uma instrução
#   TAC para a outra. Assim não tem como faltar registrador.
#
# ONDE CADA VALOR MORA
#
#   - Programa principal: cada nome vira um rótulo na seção .data
#     (preco vira var_preco). São as variáveis globais.
#   - Dentro de uma receita: parâmetros, variáveis e temporários ficam na
#     pilha, no quadro (frame) da receita. Assim cada chamada tem a sua
#     cópia, e a receita pode até chamar a si mesma.
#
# REGISTRADORES USADOS
#
#   t0, t1     operandos inteiros (contado, temounao e endereço de etiqueta)
#   ft0, ft1   operandos quebrados (float)
#   t5         ajuda a converter contado em quebrado
#   t6         guarda endereços de rótulos da .data
#   a0..a7     argumentos inteiros e valor de retorno inteiro
#   fa0..fa7   argumentos quebrados e valor de retorno quebrado
#   a7         número do serviço pedido ao RARS no ecall
#   sp, s0     topo da pilha e base do quadro da receita atual
#   ra         endereço de volta depois de uma chamada
#
# TIPOS
#
#   contado   -> inteiro de 32 bits (.word)
#   temounao  -> inteiro: 1 é original, 0 é oliginal
#   quebrado  -> float de 32 bits (.float), usa as instruções da extensão F
#   etiqueta  -> endereço do texto na .data
#
# O tipo de cada nome vem da tabela que o gerador de TAC preencheu
# (gerador_tac.tipos e gerador_tac.assinaturas).
#
# LIMITAÇÕES CONHECIDAS
#
#   - Comparar duas etiquetas (pareceigual entre textos) não é suportado:
#     seria preciso comparar letra por letra, e não os endereços.
#   - Se um bloco declara de novo uma variável que já existe fora dele, as
#     duas ocupam o mesmo lugar na memória (ver gera_bloco no gerador_tac).
#   - Uma receita recebe no máximo 8 argumentos inteiros e 8 quebrados
#     (a0..a7 e fa0..fa7). Mais que isso precisaria passar pela pilha.


class ErroGeracao(Exception):
    pass


# Operações com inteiros: operandos em t0 e t1, resultado em t0.
# Comparações não existem prontas no RISC-V além do "menor que" (slt), então
# as outras são montadas a partir dele:
#   a > b   é o mesmo que   b < a
#   a <= b  é o mesmo que   não (b < a)      (xori com 1 inverte 0 e 1)
#   a == b  é o mesmo que   (a - b) == 0     (seqz: 1 se for zero)
OPERACOES_INTEIRO = {
    "+": ["add t0, t0, t1"],
    "-": ["sub t0, t0, t1"],
    "*": ["mul t0, t0, t1"],
    "==": ["sub t0, t0, t1", "seqz t0, t0"],
    "!=": ["sub t0, t0, t1", "snez t0, t0"],
    "<": ["slt t0, t0, t1"],
    ">": ["slt t0, t1, t0"],
    "<=": ["slt t0, t1, t0", "xori t0, t0, 1"],
    ">=": ["slt t0, t0, t1", "xori t0, t0, 1"],
    "and": ["and t0, t0, t1"],
    "or": ["or t0, t0, t1"],
}

# Operações com quebrados: operandos em ft0 e ft1.
# As contas deixam o resultado em ft0. As comparações deixam 1 ou 0 em t0.
OPERACOES_QUEBRADO = {
    "+": ["fadd.s ft0, ft0, ft1"],
    "-": ["fsub.s ft0, ft0, ft1"],
    "*": ["fmul.s ft0, ft0, ft1"],
    "/": ["fdiv.s ft0, ft0, ft1"],
    "==": ["feq.s t0, ft0, ft1"],
    "!=": ["feq.s t0, ft0, ft1", "xori t0, t0, 1"],
    "<": ["flt.s t0, ft0, ft1"],
    ">": ["flt.s t0, ft1, ft0"],
    "<=": ["fle.s t0, ft0, ft1"],
    ">=": ["fle.s t0, ft1, ft0"],
}

# Serviços do RARS (o número vai em a7 antes do ecall)
IMPRIME_INTEIRO = 1
IMPRIME_QUEBRADO = 2
IMPRIME_TEXTO = 4
ENCERRA = 10
IMPRIME_CARACTERE = 11

# Linhas da seção .text (o código)
codigo = []

# Textos e números quebrados que aparecem no programa. Cada um ganha um
# rótulo na .data, porque não cabem direto dentro de uma instrução.
textos = {}      # '"passou liso"' -> "texto1"
quebrados = {}   # "350.5"         -> "numero1"

# Receita que está sendo traduzida agora ("principal" fora delas)
escopo_atual = "principal"

# Posição de cada valor local na pilha da receita atual, em relação ao s0
pilha = {}

# Argumentos guardados pelos "param", esperando o "call" que vem depois
argumentos_pendentes = []


# ---------- funções de apoio ----------

def escreve(instrucao):
    codigo.append("    " + instrucao)


def escreve_rotulo(nome):
    codigo.append(f"{nome}:")


def eh_texto(valor):
    return valor[0] in "\"'"


def eh_numero(valor):
    return valor[0].isdigit()


def eh_local(nome):
    """Diz se o nome mora na pilha da receita atual."""
    return nome in pilha


def tipo_de(valor):
    if eh_texto(valor):
        return "etiqueta"
    if eh_numero(valor):
        return "quebrado" if "." in valor else "contado"
    if eh_local(valor):
        return gerador_tac.tipos[escopo_atual][valor]
    return gerador_tac.tipos["principal"][valor]


def rotulo_do_texto(valor):
    if valor not in textos:
        textos[valor] = f"texto{len(textos) + 1}"
    return textos[valor]


def rotulo_do_quebrado(valor):
    if valor not in quebrados:
        quebrados[valor] = f"numero{len(quebrados) + 1}"
    return quebrados[valor]


# ---------- carregar e guardar ----------
# É aqui que mora a alocação ingênua: tudo sai da memória para um
# registrador e volta para a memória logo depois.

def carrega_inteiro(valor, registrador):
    """Coloca um contado, temounao ou etiqueta no registrador inteiro."""
    if eh_texto(valor):
        escreve(f"la {registrador}, {rotulo_do_texto(valor)}")
    elif eh_numero(valor):
        escreve(f"li {registrador}, {valor}")
    elif eh_local(valor):
        escreve(f"lw {registrador}, {pilha[valor]}(s0)")
    else:
        escreve(f"la t6, var_{valor}")
        escreve(f"lw {registrador}, 0(t6)")


def carrega_quebrado(valor, registrador):
    """Coloca um valor no registrador float, convertendo se for contado."""
    if tipo_de(valor) != "quebrado":
        # contado cabe em quebrado: carrega como inteiro e converte
        carrega_inteiro(valor, "t5")
        escreve(f"fcvt.s.w {registrador}, t5")
    elif eh_numero(valor):
        escreve(f"la t6, {rotulo_do_quebrado(valor)}")
        escreve(f"flw {registrador}, 0(t6)")
    elif eh_local(valor):
        escreve(f"flw {registrador}, {pilha[valor]}(s0)")
    else:
        escreve(f"la t6, var_{valor}")
        escreve(f"flw {registrador}, 0(t6)")


def carrega(valor, tipo_esperado, registrador_inteiro, registrador_quebrado):
    """Carrega no registrador certo para o tipo esperado e diz qual usou."""
    if tipo_esperado == "quebrado":
        carrega_quebrado(valor, registrador_quebrado)
        return registrador_quebrado
    carrega_inteiro(valor, registrador_inteiro)
    return registrador_inteiro


def guarda(nome, registrador):
    """Guarda o registrador na memória do nome (sw para inteiro, fsw para float)."""
    instrucao = "fsw" if tipo_de(nome) == "quebrado" else "sw"
    if eh_local(nome):
        escreve(f"{instrucao} {registrador}, {pilha[nome]}(s0)")
    else:
        escreve(f"la t6, var_{nome}")
        escreve(f"{instrucao} {registrador}, 0(t6)")


# ---------- tradução de cada instrução TAC ----------

def traduz_copia(instrucao):
    # x = y
    destino = instrucao["destino"]
    registrador = carrega(instrucao["arg1"], tipo_de(destino), "t0", "ft0")
    guarda(destino, registrador)


def traduz_binaria(instrucao):
    # t1 = a op b
    op, destino = instrucao["op"], instrucao["destino"]
    esquerda, direita = instrucao["arg1"], instrucao["arg2"]
    tipos_operandos = [tipo_de(esquerda), tipo_de(direita)]

    if "etiqueta" in tipos_operandos:
        raise ErroGeracao("comparar etiquetas ainda nao e suportado no RISC-V")

    # Se um dos lados é quebrado (ou é divisão, que sempre dá quebrado),
    # a conta inteira é feita com float
    if op == "/" or "quebrado" in tipos_operandos:
        carrega_quebrado(esquerda, "ft0")
        carrega_quebrado(direita, "ft1")
        linhas = OPERACOES_QUEBRADO[op]
    else:
        carrega_inteiro(esquerda, "t0")
        carrega_inteiro(direita, "t1")
        linhas = OPERACOES_INTEIRO[op]

    for linha in linhas:
        escreve(linha)

    # Contas com float deixam o resultado em ft0. O resto deixa em t0.
    guarda(destino, "ft0" if tipo_de(destino) == "quebrado" else "t0")


def traduz_not(instrucao):
    carrega_inteiro(instrucao["arg1"], "t0")
    escreve("seqz t0, t0")  # 1 vira 0 e 0 vira 1
    guarda(instrucao["destino"], "t0")


def traduz_rotulo(instrucao):
    escreve_rotulo(instrucao["destino"])


def traduz_goto(instrucao):
    escreve(f"j {instrucao['destino']}")


def traduz_if_false(instrucao):
    carrega_inteiro(instrucao["arg1"], "t0")
    escreve(f"beqz t0, {instrucao['destino']}")  # pula se a condição for 0


def traduz_param(instrucao):
    # Só guarda. Os argumentos são colocados nos registradores no "call",
    # quando já se sabe qual receita é e o tipo de cada parâmetro.
    argumentos_pendentes.append(instrucao["arg1"])


def traduz_call(instrucao):
    # Convenção do RISC-V: argumentos inteiros vão em a0, a1, a2... e os
    # quebrados em fa0, fa1, fa2... O retorno volta em a0 ou fa0.
    nome, destino = instrucao["arg1"], instrucao["destino"]
    assinatura = gerador_tac.assinaturas[nome]

    usados_inteiros = 0
    usados_quebrados = 0
    for valor, tipo in zip(argumentos_pendentes, assinatura["parametros"]):
        if tipo == "quebrado":
            carrega_quebrado(valor, f"fa{usados_quebrados}")
            usados_quebrados += 1
        else:
            carrega_inteiro(valor, f"a{usados_inteiros}")
            usados_inteiros += 1
    argumentos_pendentes.clear()

    escreve(f"jal receita_{nome}")  # pula e guarda em ra o endereço de volta

    if destino is not None:
        guarda(destino, "fa0" if assinatura["retorno"] == "quebrado" else "a0")


def traduz_receita(instrucao):
    # Início de receita: monta o quadro (frame) na pilha.
    #
    #     s0 - 4    ra (endereço de volta)
    #     s0 - 8    s0 de quem chamou
    #     s0 - 12   primeiro valor local
    #     s0 - 16   segundo valor local
    #     ...
    global escopo_atual, pilha
    nome, parametros = instrucao["destino"], instrucao["arg1"]
    escopo_atual = nome

    locais = list(gerador_tac.tipos[nome])
    pilha = {}
    for posicao, local in enumerate(locais):
        pilha[local] = -(12 + 4 * posicao)

    # A convenção do RISC-V pede que o sp seja sempre múltiplo de 16, então
    # o tamanho do quadro é arredondado para cima (ex: 20 bytes viram 32)
    tamanho = 8 + 4 * len(locais)
    tamanho = (tamanho + 15) // 16 * 16

    codigo.append("")
    escreve_rotulo(f"receita_{nome}")
    escreve(f"addi sp, sp, -{tamanho}")   # reserva o quadro
    escreve(f"sw ra, {tamanho - 4}(sp)")
    escreve(f"sw s0, {tamanho - 8}(sp)")
    escreve(f"addi s0, sp, {tamanho}")    # s0 aponta para o início do quadro

    # Os parâmetros chegam em registradores. Guarda cada um no seu lugar.
    usados_inteiros = 0
    usados_quebrados = 0
    for parametro in parametros:
        if tipo_de(parametro) == "quebrado":
            guarda(parametro, f"fa{usados_quebrados}")
            usados_quebrados += 1
        else:
            guarda(parametro, f"a{usados_inteiros}")
            usados_inteiros += 1


def traduz_return(instrucao):
    if instrucao["arg1"] is not None:
        tipo_retorno = gerador_tac.assinaturas[escopo_atual]["retorno"]
        carrega(instrucao["arg1"], tipo_retorno, "a0", "fa0")

    # Desmonta o quadro e volta para quem chamou. A ordem importa: o s0 é
    # usado para achar o ra e o s0 antigo, então ele é o último a mudar.
    escreve("lw ra, -4(s0)")    # endereço de volta
    escreve("mv sp, s0")        # sp volta para onde estava antes do quadro
    escreve("lw s0, -8(s0)")    # s0 volta a ser o de quem chamou
    escreve("ret")              # pula para o ra


def traduz_print(instrucao):
    valor = instrucao["arg1"]
    tipo = tipo_de(valor)

    if tipo == "quebrado":
        carrega_quebrado(valor, "fa0")
        servico = IMPRIME_QUEBRADO
    elif tipo == "etiqueta":
        carrega_inteiro(valor, "a0")
        servico = IMPRIME_TEXTO
    else:
        carrega_inteiro(valor, "a0")  # temounao aparece como 1 ou 0
        servico = IMPRIME_INTEIRO
    escreve(f"li a7, {servico}")
    escreve("ecall")

    # Pula uma linha depois, como o print do Python
    escreve("li a0, 10")  # 10 é o código do caractere de nova linha
    escreve(f"li a7, {IMPRIME_CARACTERE}")
    escreve("ecall")


def traduz_fim(instrucao):
    escreve(f"li a7, {ENCERRA}")
    escreve("ecall")


TRADUTORES = {
    "copia": traduz_copia,
    "not": traduz_not,
    "rotulo": traduz_rotulo,
    "goto": traduz_goto,
    "ifFalse": traduz_if_false,
    "param": traduz_param,
    "call": traduz_call,
    "receita": traduz_receita,
    "return": traduz_return,
    "print": traduz_print,
    "fim": traduz_fim,
}


# ---------- seção .data ----------

def texto_para_assembly(valor):
    """Converte um texto do .pay para o formato do .string do assembly.

    O assembly só aceita texto entre aspas duplas. Um texto .pay com aspas
    simples, como 'vai pagar "imposto"', precisa ter as aspas duplas de
    dentro escapadas: "vai pagar \\"imposto\\"".
    """
    conteudo = valor[1:-1]
    if valor[0] == "'":
        conteudo = conteudo.replace('"', '\\"')
    return f'"{conteudo}"'


def monta_dados():
    linhas = [".data"]

    # Variáveis globais e temporários do programa principal
    for nome, tipo in gerador_tac.tipos["principal"].items():
        if tipo == "quebrado":
            linhas.append(f"var_{nome}: .float 0.0")
        else:
            linhas.append(f"var_{nome}: .word 0")

    for valor, rotulo in quebrados.items():
        linhas.append(f"{rotulo}: .float {valor}")

    # Textos por último: eles têm tamanhos quebrados e iriam desalinhar
    # os .word e .float que viessem depois
    for valor, rotulo in textos.items():
        linhas.append(f"{rotulo}: .string {texto_para_assembly(valor)}")

    return linhas


# ---------- entrada e saída ----------

def gerar_riscv(instrucoes):
    """Recebe a lista do gerar_tac() e devolve o assembly como texto."""
    global codigo, textos, quebrados, escopo_atual, pilha, argumentos_pendentes
    codigo = []
    textos = {}
    quebrados = {}
    escopo_atual = "principal"
    pilha = {}
    argumentos_pendentes = []

    codigo.append(".text")
    codigo.append(".globl main")
    escreve_rotulo("main")

    for instrucao in instrucoes:
        # Cada trecho começa com a instrução TAC em comentário, para dar
        # para ver de onde saiu cada pedaço do assembly. Rótulos e receitas
        # já aparecem como rótulos. O param fica sem comentário porque o
        # código dele só é escrito no call (ver traduz_param).
        if instrucao["op"] not in ["rotulo", "receita", "param"]:
            escreve("# " + formatar(instrucao).strip())

        tradutor = TRADUTORES.get(instrucao["op"], traduz_binaria)
        tradutor(instrucao)

    # A .data vem depois porque só agora se sabe quais textos e números
    # quebrados apareceram no código
    return "\n".join(monta_dados() + [""] + codigo) + "\n"


if __name__ == "__main__":
    # python gerador_riscv.py [entrada.pay] [saida.s]
    nome_arquivo = sys.argv[1] if len(sys.argv) > 1 else "programa.pay"
    nome_saida = sys.argv[2] if len(sys.argv) > 2 else "programa.s"

    with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
        codigo_fonte = arquivo.read()

    try:
        arvore = analisar(tokenize(codigo_fonte))
    except ErroSintatico as mensagem:
        print("Erros sintaticos: 1")
        print(" ", mensagem)
        sys.exit(1)

    lista_de_erros = analisar_semantica(arvore)
    if lista_de_erros:
        print("Erros semanticos:", len(lista_de_erros))
        for mensagem in lista_de_erros:
            print(" ", mensagem)
        sys.exit(1)

    assembly = gerar_riscv(gerar_tac(arvore))
    with open(nome_saida, "w", encoding="utf-8") as arquivo:
        arquivo.write(assembly)

    print("Erros sintaticos: 0")
    print("Erros semanticos: 0")
    print(f"Assembly RISC-V gravado em {nome_saida}")

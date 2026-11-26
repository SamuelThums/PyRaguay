import sys

from tokenizador import tokenize
from analisador_sintatico import analisar, ErroSintatico
from analisador_semantico import analisar_semantica

# ==========================================
# GERADOR DE CÓDIGO INTERMEDIÁRIO (TAC) DA LINGUAGEM .PAY
# ==========================================
#
# Recebe a árvore sintática (já conferida pelo analisador semântico) e
# transforma o programa em Código de Três Endereços (TAC, Three-Address Code).
#
# No TAC cada instrução faz UMA operação só, no formato:
#
#     destino = operando1 operador operando2
#
# Exemplo:  quebrado d eisso (a maisbarato b) dobradinha c aduana
#
#     t1 = a + b
#     t2 = t1 * c
#     d = t2
#
# Os nomes t1, t2, t3... são temporários: guardam os resultados no meio do
# caminho. Ainda não são registradores de verdade. Escolher em qual
# registrador do RISC-V cada um vai ficar é trabalho da próxima etapa.
#
# A árvore é percorrida em pós-ordem: primeiro os filhos, depois o nó. Assim,
# quando chega a vez de um operador, os dois lados dele já foram calculados.
#
# Cada instrução é guardada como um dicionário com quatro campos:
#
#     {"op": "+", "destino": "t1", "arg1": "a", "arg2": "b"}
#
# Os campos que uma instrução não usa ficam como None. Guardar em dicionário,
# e não direto como texto, facilita a próxima etapa (gerar RISC-V), que
# precisa olhar cada pedaço da instrução separado.
#
# Instruções que este gerador emite:
#
#   op             exemplo impresso               significado
#   -------------  -----------------------------  --------------------------------
#   + - * /        t1 = a + b                     conta
#   == != < > ...  t1 = a < b                     comparação (dá 1 ou 0)
#   and or         t1 = a and b                   lógica (dá 1 ou 0)
#   not            t1 = not a                     negação
#   copia          x = t1                         copia um valor para a variável
#   rotulo         L1:                            marca um ponto para pular
#   goto           goto L1                        pula sempre
#   ifFalse        ifFalse t1 goto L1             pula se a condição for falsa
#   param          param a                        empilha um argumento
#   call           t1 = call soma, 2              chama a receita com 2 argumentos
#   return         return t1                      devolve o valor da receita
#   print          print t1                       tnirp
#   receita        soma(a, b):                    início de uma receita
#   fim            fim                            fim do programa principal

# Cada operador da linguagem .pay vira o símbolo de costume no TAC, que é
# mais fácil de ler (e é o que aparece nos livros e nos slides).
OPERADORES = {
    "maisbarato": "+",
    "sumiu": "-",
    "dobradinha": "*",
    "divideai": "/",
    "pareceigual": "==",
    "trocado": "!=",
    "achatou": "<",
    "estourou": ">",
    "menoroumenos": "<=",
    "maioroumais": ">=",
    "levajunto": "and",
    "ouentao": "or",
}

# temounao vira número: verdadeiro é 1 e falso é 0, como no assembly
BOOLEANOS = {"original": "1", "oliginal": "0"}

# Instruções do programa principal (o que fica fora das receitas)
principal = []

# Instruções das receitas. Ficam separadas porque o corpo de uma receita só
# roda quando ela é chamada: não pode ficar no meio do programa principal.
receitas = []

# Lista onde o emite() está escrevendo agora: principal ou receitas
lista_atual = principal

# Contadores para criar nomes novos: t1, t2, t3... e L1, L2, L3...
contador_temporarios = 0
contador_rotulos = 0


# ---------- funções de apoio ----------

def nova_temporaria():
    """Devolve um nome de temporário que ainda não foi usado: t1, t2, t3..."""
    global contador_temporarios
    contador_temporarios += 1
    return f"t{contador_temporarios}"


def novo_rotulo():
    """Devolve um nome de rótulo que ainda não foi usado: L1, L2, L3..."""
    global contador_rotulos
    contador_rotulos += 1
    return f"L{contador_rotulos}"


def emite(op, destino=None, arg1=None, arg2=None):
    """Guarda uma instrução TAC no fim da lista atual."""
    lista_atual.append({"op": op, "destino": destino, "arg1": arg1, "arg2": arg2})


# ---------- instruções ----------
# Mesmo esquema do analisador semântico: cada tipo de nó tem a sua função,
# e a função gerar escolhe qual chamar pelo nome do nó.

def gerar(no):
    # Toda instrução tem a linha como último filho. O TAC não precisa dela.
    if no[0] not in ["programa", "bloco"]:
        no = no[:-1]

    GERADORES[no[0]](no)


def gera_programa(no):
    for instrucao in no[1:]:
        gerar(instrucao)


def gera_bloco(no):
    for instrucao in no[1:]:
        gerar(instrucao)


def gera_declaracao(no):
    # contado x eisso a maisbarato b   ->   t1 = a + b
    #                                       x = t1
    _, tipo, nome, valor = no
    resultado = gerar_expressao(valor)
    emite("copia", nome, resultado)


def gera_atribuicao(no):
    _, nome, valor = no
    resultado = gerar_expressao(valor)
    emite("copia", nome, resultado)


def gera_receita(no):
    # receita contado soma (contado a etambem contado b) { galantia a maisbarato b; }
    #
    #     soma(a, b):
    #         t1 = a + b
    #         return t1
    global lista_atual
    _, tipo_retorno, nome, parametros, corpo = no
    nomes_parametros = [parametro[2] for parametro in parametros[1:]]

    # Tudo que for emitido daqui até o fim da receita vai para a lista de
    # receitas, e não para o programa principal
    lista_de_fora = lista_atual
    lista_atual = receitas

    emite("receita", nome, nomes_parametros)
    gerar(corpo)

    # Garante que a receita sempre volta para quem chamou, mesmo uma
    # semtroco que não tem galantia no final
    if not corpo[1:] or corpo[-1][0] != "galantia":
        emite("return")

    lista_atual = lista_de_fora


def gera_galantia(no):
    if len(no) > 1:
        emite("return", None, gerar_expressao(no[1]))
    else:
        emite("return")


def gera_iph(no):
    # Sem ueuce:                    Com ueuce:
    #
    #     t1 = condicao                 t1 = condicao
    #     ifFalse t1 goto L1            ifFalse t1 goto L1
    #     ...bloco do iph...            ...bloco do iph...
    # L1:                               goto L2
    #                               L1:
    #                                   ...bloco do ueuce...
    #                               L2:
    condicao = gerar_expressao(no[1])
    rotulo_falso = novo_rotulo()
    emite("ifFalse", rotulo_falso, condicao)
    gerar(no[2])

    if len(no) > 3:
        rotulo_fim = novo_rotulo()
        emite("goto", rotulo_fim)
        emite("rotulo", rotulo_falso)
        gerar(no[3][1])  # bloco do ueuce
        emite("rotulo", rotulo_fim)
    else:
        emite("rotulo", rotulo_falso)


def gera_uaile(no):
    # L1:
    #     t1 = condicao
    #     ifFalse t1 goto L2
    #     ...bloco...
    #     goto L1            volta para testar a condição de novo
    # L2:
    rotulo_inicio = novo_rotulo()
    rotulo_fim = novo_rotulo()

    emite("rotulo", rotulo_inicio)
    condicao = gerar_expressao(no[1])
    emite("ifFalse", rotulo_fim, condicao)
    gerar(no[2])
    emite("goto", rotulo_inicio)
    emite("rotulo", rotulo_fim)


def gera_tnirp(no):
    emite("print", None, gerar_expressao(no[1]))


def gera_chamada(no):
    # Chamada solta, como "anunciar(produto);". Não guarda o resultado.
    gerar_chamada(no, guardar_resultado=False)


GERADORES = {
    "programa": gera_programa,
    "bloco": gera_bloco,
    "declaracao": gera_declaracao,
    "atribuicao": gera_atribuicao,
    "receita": gera_receita,
    "galantia": gera_galantia,
    "iph": gera_iph,
    "uaile": gera_uaile,
    "tnirp": gera_tnirp,
    "chamada": gera_chamada,
}


# ---------- expressões ----------
# É o algoritmo dos slides:
#
#     função gerar_tac(no):
#         se no é folha: retorna no.valor
#         esq  = gerar_tac(no.esquerda)
#         dir  = gerar_tac(no.direita)
#         temp = nova_temporaria()
#         emite(temp = esq op dir)
#         retorna temp
#
# Cada chamada devolve o NOME onde o resultado ficou: o próprio valor (se é
# folha) ou o temporário que acabou de ser criado.

def gerar_expressao(expressao):
    # Folha: número, texto, booleano ou nome de variável. Não precisa de
    # instrução nenhuma, o valor já está pronto para ser usado.
    if isinstance(expressao, str):
        return BOOLEANOS.get(expressao, expressao)

    operador = expressao[0]

    if operador == "chamada":
        return gerar_chamada(expressao, guardar_resultado=True)

    if operador == "naotem":
        valor = gerar_expressao(expressao[1])
        temporario = nova_temporaria()
        emite("not", temporario, valor)
        return temporario

    # Operador binário: primeiro os dois filhos (pós-ordem), depois ele
    esquerda = gerar_expressao(expressao[1])
    direita = gerar_expressao(expressao[2])
    temporario = nova_temporaria()
    emite(OPERADORES[operador], temporario, esquerda, direita)
    return temporario


def gerar_chamada(no, guardar_resultado):
    # x = soma(a, b)   ->   param a
    #                       param b
    #                       t1 = call soma, 2
    #                       x = t1
    nome, argumentos = no[1], no[2:]

    # Primeiro calcula todos os argumentos, da esquerda para a direita.
    # Só depois emite os param, para os param ficarem juntos antes do call.
    valores = [gerar_expressao(argumento) for argumento in argumentos]
    for valor in valores:
        emite("param", None, valor)

    if guardar_resultado:
        temporario = nova_temporaria()
        emite("call", temporario, nome, len(valores))
        return temporario

    emite("call", None, nome, len(valores))
    return None


# ---------- entrada e saída ----------

def gerar_tac(arvore):
    """Recebe a árvore sintática e devolve a lista de instruções TAC.

    O programa principal vem primeiro e termina com "fim". Depois vêm as
    receitas, que só rodam quando alguém chama.
    """
    global principal, receitas, lista_atual
    global contador_temporarios, contador_rotulos
    principal = []
    receitas = []
    lista_atual = principal
    contador_temporarios = 0
    contador_rotulos = 0

    gerar(arvore)
    emite("fim")
    return principal + receitas


def formatar(instrucao):
    """Transforma uma instrução (dicionário) em uma linha de texto."""
    op = instrucao["op"]
    destino = instrucao["destino"]
    arg1 = instrucao["arg1"]
    arg2 = instrucao["arg2"]

    # Rótulos e inícios de receita ficam encostados na margem. O resto é
    # recuado, para ficar fácil ver onde cada trecho começa.
    if op == "rotulo":
        return f"{destino}:"
    if op == "receita":
        return f"{destino}({', '.join(arg1)}):"

    if op == "copia":
        texto = f"{destino} = {arg1}"
    elif op == "not":
        texto = f"{destino} = not {arg1}"
    elif op == "goto":
        texto = f"goto {destino}"
    elif op == "ifFalse":
        texto = f"ifFalse {arg1} goto {destino}"
    elif op == "param":
        texto = f"param {arg1}"
    elif op == "call":
        chamada = f"call {arg1}, {arg2}"
        texto = f"{destino} = {chamada}" if destino else chamada
    elif op == "return":
        texto = f"return {arg1}" if arg1 is not None else "return"
    elif op == "print":
        texto = f"print {arg1}"
    elif op == "fim":
        texto = "fim"
    else:
        # Sobrou só operador binário: + - * / == != < > <= >= and or
        texto = f"{destino} = {arg1} {op} {arg2}"

    return "    " + texto


def imprimir_tac(instrucoes):
    for instrucao in instrucoes:
        print(formatar(instrucao))


if __name__ == "__main__":
    # Dá para escolher o arquivo: python gerador_tac.py outro.pay
    nome_arquivo = sys.argv[1] if len(sys.argv) > 1 else "programa.pay"
    with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
        codigo_fonte = arquivo.read()

    try:
        arvore = analisar(tokenize(codigo_fonte))
    except ErroSintatico as mensagem:
        print("Erros sintaticos: 1")
        print(" ", mensagem)
        sys.exit(1)

    # Só gera código para programa correto. Se o semântico achou erro, o TAC
    # sairia errado, então para aqui.
    lista_de_erros = analisar_semantica(arvore)
    if lista_de_erros:
        print("Erros semanticos:", len(lista_de_erros))
        for mensagem in lista_de_erros:
            print(" ", mensagem)
        sys.exit(1)

    print("Erros sintaticos: 0")
    print("Erros semanticos: 0")
    print()
    print("Codigo de tres enderecos (TAC):")
    imprimir_tac(gerar_tac(arvore))

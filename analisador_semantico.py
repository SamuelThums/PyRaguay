import sys

from tokenizador import tokenize
from analisador_sintatico import analisar, ErroSintatico, COMPARADORES

# ==========================================
# ANALISADOR SEMÂNTICO DA LINGUAGEM .PAY
# ==========================================
#
# Recebe a árvore sintática montada pelo analisador sintático e confere se o
# programa faz sentido:
#
#   - todo identificador usado foi declarado antes
#   - nenhum nome foi declarado duas vezes no mesmo escopo
#   - os tipos combinam nas expressões aritméticas, lógicas e relacionais
#   - as chamadas de receita têm a quantidade e o tipo certo de argumentos
#   - o galantia devolve o tipo que a receita prometeu
#
# Os erros não param a análise: eles vão para a lista "erros" e a travessia
# continua, para mostrar o máximo de problemas de uma vez.
#
# Regras de tipo:
#   - contado cabe onde se espera quebrado (15 vira 15.0), o contrário não
#   - divideai sempre dá quebrado, como o / do Python
#   - o tipo "erro" é usado quando algo já deu errado. Ele combina com
#     qualquer tipo, para o mesmo problema não ser avisado várias vezes.

NUMERICOS = ["contado", "quebrado"]
ARITMETICOS = ["maisbarato", "sumiu", "dobradinha", "divideai"]
LOGICOS = ["levajunto", "ouentao"]

# Pilha de escopos: cada escopo é um dicionário (tabela hash) nome -> símbolo.
# escopos[0] é o global e escopos[-1] é o escopo atual.
escopos = [{}]

erros = []

# Linha da instrução que está sendo analisada, usada nas mensagens de erro.
linha = 0

# Receita que está sendo analisada, para o galantia saber o que devolver.
# Fica None quando estamos fora de qualquer receita.
receita_atual = None


# ---------- tabela de símbolos ----------

def abre_escopo():
    escopos.append({})


def fecha_escopo():
    escopos.pop()


def declara(nome, simbolo):
    """Coloca o símbolo no escopo atual, se o nome ainda não existir nele."""
    if nome in escopos[-1]:
        anterior = escopos[-1][nome]["linha"]
        erro(f"'{nome}' ja foi declarado neste escopo (na linha {anterior})")
        return
    escopos[-1][nome] = simbolo


def busca(nome):
    """Procura o nome do escopo mais interno até o global."""
    for escopo in reversed(escopos):
        if nome in escopo:
            return escopo[nome]
    return None


# ---------- funções de apoio ----------

def erro(mensagem):
    erros.append(f"FISCAL DA RECEITA (linha {linha}): {mensagem}")


def cabe(tipo_esperado, tipo_recebido):
    """Diz se um valor do tipo recebido pode ser usado onde se espera o outro."""
    if "erro" in [tipo_esperado, tipo_recebido]:
        return True
    if tipo_esperado == tipo_recebido:
        return True
    return tipo_esperado == "quebrado" and tipo_recebido == "contado"


def confere_condicao(condicao, comando):
    tipo = tipo_de(condicao)
    if not cabe("temounao", tipo):
        erro(f"a condicao do {comando} precisa ser temounao, mas e {tipo}")


# ---------- instruções ----------
# Visitor: cada tipo de nó tem a sua função, e a função visitar escolhe qual
# chamar pelo nome do nó (o primeiro item da lista).

def visitar(no):
    global linha

    # Toda instrução tem a linha como último filho. Ela é guardada e tirada
    # do nó, para as funções abaixo só verem os filhos de verdade.
    if no[0] not in ["programa", "bloco"]:
        linha = no[-1]
        no = no[:-1]

    VISITANTES[no[0]](no)


def visita_programa(no):
    for instrucao in no[1:]:
        visitar(instrucao)


def visita_bloco(no):
    # Cada bloco de iph, ueuce e uaile tem o seu próprio escopo
    abre_escopo()
    for instrucao in no[1:]:
        visitar(instrucao)
    fecha_escopo()


def visita_declaracao(no):
    _, tipo, nome, valor = no
    # O valor é analisado antes de declarar: "contado x eisso x" é erro
    tipo_valor = tipo_de(valor)
    if not cabe(tipo, tipo_valor):
        erro(f"'{nome}' e {tipo} mas recebeu um valor {tipo_valor}")
    declara(nome, {"categoria": "variavel", "tipo": tipo, "linha": linha})


def visita_atribuicao(no):
    _, nome, valor = no
    tipo_valor = tipo_de(valor)
    simbolo = busca(nome)
    if simbolo is None:
        erro(f"'{nome}' nao foi declarado")
    elif simbolo["categoria"] == "receita":
        erro(f"'{nome}' e uma receita e nao pode receber valor")
    elif not cabe(simbolo["tipo"], tipo_valor):
        erro(f"'{nome}' e {simbolo['tipo']} mas recebeu um valor {tipo_valor}")


def visita_receita(no):
    global receita_atual
    _, tipo_retorno, nome, parametros, corpo = no

    # A receita entra na tabela antes do corpo, para poder chamar a si mesma
    tipos_parametros = [parametro[1] for parametro in parametros[1:]]
    declara(nome, {"categoria": "receita", "tipo": tipo_retorno,
                   "parametros": tipos_parametros, "linha": linha})

    # Parâmetros e variáveis do corpo ficam no mesmo escopo, por isso as
    # instruções do corpo são visitadas aqui, sem passar por visita_bloco
    abre_escopo()
    for _, tipo, nome_parametro in parametros[1:]:
        declara(nome_parametro, {"categoria": "variavel", "tipo": tipo, "linha": linha})

    receita_de_fora = receita_atual
    receita_atual = (nome, tipo_retorno)
    for instrucao in corpo[1:]:
        visitar(instrucao)
    receita_atual = receita_de_fora

    fecha_escopo()


def visita_galantia(no):
    tipo_valor = tipo_de(no[1]) if len(no) > 1 else "semtroco"

    if receita_atual is None:
        erro("galantia so pode ser usado dentro de uma receita")
        return

    nome, tipo_retorno = receita_atual
    if tipo_retorno == "semtroco" and tipo_valor != "semtroco":
        erro(f"a receita '{nome}' e semtroco e nao devolve valor")
    elif tipo_retorno != "semtroco" and tipo_valor == "semtroco":
        erro(f"a receita '{nome}' precisa devolver um valor {tipo_retorno}")
    elif not cabe(tipo_retorno, tipo_valor):
        erro(f"a receita '{nome}' devolve {tipo_retorno} mas o galantia devolve {tipo_valor}")


def visita_iph(no):
    confere_condicao(no[1], "iph")
    visitar(no[2])
    if len(no) > 3:
        visitar(no[3][1])  # bloco do ueuce


def visita_uaile(no):
    confere_condicao(no[1], "uaile")
    visitar(no[2])


def visita_tnirp(no):
    tipo = tipo_de(no[1])
    if tipo == "semtroco":
        erro("tnirp recebeu uma receita semtroco, que nao devolve nada")


def visita_chamada(no):
    # Chamada solta, como "anunciar(produto);". O valor devolvido é ignorado.
    tipo_da_chamada(no)


VISITANTES = {
    "programa": visita_programa,
    "bloco": visita_bloco,
    "declaracao": visita_declaracao,
    "atribuicao": visita_atribuicao,
    "receita": visita_receita,
    "galantia": visita_galantia,
    "iph": visita_iph,
    "uaile": visita_uaile,
    "tnirp": visita_tnirp,
    "chamada": visita_chamada,
}


# ---------- tipos das expressões ----------
# A expressão é visitada de baixo para cima (pós-ordem): primeiro descobre o
# tipo dos filhos, depois confere se o operador aceita esses tipos.

def tipo_de(expressao):
    # Folha: um valor ou um nome, guardado como texto
    if isinstance(expressao, str):
        return tipo_da_folha(expressao)

    operador = expressao[0]

    if operador == "chamada":
        return tipo_da_chamada(expressao)

    if operador == "naotem":
        tipo = tipo_de(expressao[1])
        if not cabe("temounao", tipo):
            erro(f"naotem precisa de temounao, mas recebeu {tipo}")
        return "temounao"

    esquerda = tipo_de(expressao[1])
    direita = tipo_de(expressao[2])
    ja_deu_erro = "erro" in [esquerda, direita]

    if operador in ARITMETICOS:
        if ja_deu_erro:
            return "erro"
        if esquerda not in NUMERICOS or direita not in NUMERICOS:
            erro(f"{operador} so faz conta com numeros, mas recebeu {esquerda} e {direita}")
            return "erro"
        if operador == "divideai" or "quebrado" in [esquerda, direita]:
            return "quebrado"
        return "contado"

    if operador in LOGICOS:
        if not cabe("temounao", esquerda) or not cabe("temounao", direita):
            erro(f"{operador} precisa de temounao dos dois lados, mas recebeu {esquerda} e {direita}")
        return "temounao"

    if operador in COMPARADORES:
        if ja_deu_erro:
            return "temounao"
        if operador in ["pareceigual", "trocado"]:
            # Igualdade: os dois lados precisam ser do mesmo tipo (ou números)
            combina = cabe(esquerda, direita) or cabe(direita, esquerda)
        else:
            # achatou, estourou...: só faz sentido com números
            combina = esquerda in NUMERICOS and direita in NUMERICOS
        if not combina:
            erro(f"{operador} nao compara {esquerda} com {direita}")
        return "temounao"


def tipo_da_folha(texto):
    if texto[0] in "\"'":
        return "etiqueta"
    if texto in ["original", "oliginal"]:
        return "temounao"
    if texto[0].isdigit():
        return "quebrado" if "." in texto else "contado"

    # Se não é valor, é um nome: precisa estar na tabela de símbolos
    simbolo = busca(texto)
    if simbolo is None:
        erro(f"'{texto}' nao foi declarado")
        return "erro"
    if simbolo["categoria"] == "receita":
        erro(f"'{texto}' e uma receita, precisa ser chamada com abreportamala fechaportamala")
        return "erro"
    return simbolo["tipo"]


def tipo_da_chamada(no):
    nome, argumentos = no[1], no[2:]

    # Os argumentos são analisados sempre, mesmo se a receita não existir,
    # para achar erros dentro deles também
    tipos_argumentos = [tipo_de(argumento) for argumento in argumentos]

    simbolo = busca(nome)
    if simbolo is None:
        erro(f"a receita '{nome}' nao foi declarada")
        return "erro"
    if simbolo["categoria"] != "receita":
        erro(f"'{nome}' nao e uma receita")
        return "erro"

    esperados = simbolo["parametros"]
    if len(tipos_argumentos) != len(esperados):
        erro(f"a receita '{nome}' espera {len(esperados)} argumento(s) "
             f"mas recebeu {len(tipos_argumentos)}")
    else:
        for posicao in range(len(esperados)):
            if not cabe(esperados[posicao], tipos_argumentos[posicao]):
                erro(f"o argumento {posicao + 1} de '{nome}' devia ser "
                     f"{esperados[posicao]} mas e {tipos_argumentos[posicao]}")

    return simbolo["tipo"]


# ---------- entrada e saída ----------

def analisar_semantica(arvore):
    """Recebe a árvore sintática e devolve a lista de erros semânticos."""
    global escopos, erros, linha, receita_atual
    escopos = [{}]
    erros = []
    linha = 0
    receita_atual = None

    visitar(arvore)
    return erros


def imprimir_tabela():
    """Mostra o que ficou no escopo global depois da análise."""
    print("Tabela de simbolos (escopo global):")
    for nome, simbolo in escopos[0].items():
        if simbolo["categoria"] == "receita":
            parametros = ", ".join(simbolo["parametros"])
            print(f"  {nome}: receita {simbolo['tipo']} ({parametros})  linha {simbolo['linha']}")
        else:
            print(f"  {nome}: {simbolo['tipo']}  linha {simbolo['linha']}")


if __name__ == "__main__":
    # Dá para escolher o arquivo: python analisador_semantico.py outro.pay
    nome_arquivo = sys.argv[1] if len(sys.argv) > 1 else "programa.pay"
    with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
        codigo_fonte = arquivo.read()

    try:
        arvore = analisar(tokenize(codigo_fonte))
    except ErroSintatico as mensagem:
        print("Erros sintaticos: 1")
        print(" ", mensagem)
        sys.exit(1)

    print("Erros sintaticos: 0")
    lista_de_erros = analisar_semantica(arvore)
    print("Erros semanticos:", len(lista_de_erros))
    for mensagem in lista_de_erros:
        print(" ", mensagem)
    imprimir_tabela()

from tokenizador import tokenize

# ==========================================
# ANALISADOR SINTÁTICO DA LINGUAGEM .PAY
# ==========================================
#
# Recebe a lista de tokens do tokenizador e confere se eles estão na ordem
# que a gramática permite. Enquanto confere, monta a árvore sintática.
#
# Cada regra da gramática abaixo é uma função com o mesmo nome.
#
#   programa    -> instrucao*
#   instrucao   -> receita | declaracao | atribuicao | iph | uaile
#                | galantia | tnirp | chamada aduana
#
#   receita     -> receita TIPO IDENTIFICADOR ( parametros ) bloco
#   bloco       -> abremochila instrucao* fechamochila
#   declaracao  -> TIPO IDENTIFICADOR eisso expressao aduana
#   atribuicao  -> IDENTIFICADOR eisso expressao aduana
#   iph         -> iph ( expressao ) bloco [ ueuce bloco ]
#   uaile       -> uaile ( expressao ) bloco
#   galantia    -> galantia [ expressao ] aduana
#   tnirp       -> tnirp ( expressao ) aduana
#   chamada     -> IDENTIFICADOR ( argumentos )
#
#   expressao   -> e_logico   ( ouentao e_logico )*
#   e_logico    -> negacao    ( levajunto negacao )*
#   negacao     -> naotem negacao | comparacao
#   comparacao  -> soma       ( COMPARADOR soma )*
#   soma        -> termo      ( (maisbarato | sumiu) termo )*
#   termo       -> fator      ( (dobradinha | divideai) fator )*
#   fator       -> NUMERO | STRING | BOOLEANO | IDENTIFICADOR | chamada
#                | ( expressao )
#
# Nas regras, "(" é abreportamala e ")" é fechaportamala.
#
# As regras de expressão chamam uma à outra de cima para baixo. Quem está mais
# embaixo é resolvido primeiro: por isso dobradinha vem antes de maisbarato.
#
# Cada nó da árvore é uma lista: o primeiro item é o nome do nó e os outros
# são os filhos. Exemplo:  ["maisbarato", "preco", "frete"]

COMPARADORES = ["pareceigual", "trocado", "achatou", "estourou", "menoroumenos", "maioroumais"]

# Tokens que ainda faltam analisar. O primeiro da lista é o token atual.
tokens = []


class ErroSintatico(Exception):
    pass


# ---------- funções de apoio ----------

def tipo_atual():
    return tokens[0][0]


def lexema_atual():
    return tokens[0][1]


def lexema_seguinte():
    return tokens[1][1]


def avanca():
    """Tira o token atual da lista e devolve o texto dele."""
    token = tokens.pop(0)
    return token[1]


def erro(esperado):
    tipo, lexema, linha, coluna = tokens[0]
    raise ErroSintatico(
        f"BARRADO NA ADUANA (linha {linha}, coluna {coluna}): "
        f"esperava {esperado} mas encontrou {lexema}"
    )


def consome_palavra(palavra):
    """Exige que o token atual seja exatamente essa palavra (ex: aduana)."""
    if lexema_atual() != palavra:
        erro(palavra)
    return avanca()


def consome_categoria(categoria):
    """Exige que o token atual seja dessa categoria (ex: TIPO, IDENTIFICADOR)."""
    if tipo_atual() != categoria:
        erro(categoria)
    return avanca()


# ---------- instruções ----------

def programa():
    no = ["programa"]
    while tipo_atual() != "FIM":
        no.append(instrucao())
    return no


def instrucao():
    if lexema_atual() == "receita":
        return receita()
    if tipo_atual() == "TIPO":
        return declaracao()
    if lexema_atual() == "iph":
        return iph()
    if lexema_atual() == "uaile":
        return uaile()
    if lexema_atual() == "galantia":
        return galantia()
    if lexema_atual() == "tnirp":
        return tnirp()

    # Um identificador pode começar uma atribuição ou uma chamada.
    # Quem decide é o token que vem depois dele.
    if tipo_atual() == "IDENTIFICADOR" and lexema_seguinte() == "eisso":
        return atribuicao()
    if tipo_atual() == "IDENTIFICADOR" and lexema_seguinte() == "abreportamala":
        no = chamada()
        consome_palavra("aduana")
        return no

    erro("uma instrucao")


def receita():
    consome_palavra("receita")
    tipo_retorno = consome_categoria("TIPO")
    nome = consome_categoria("IDENTIFICADOR")

    consome_palavra("abreportamala")
    parametros = ["parametros"]
    while lexema_atual() != "fechaportamala":
        # Do segundo parâmetro em diante, precisa do etambem antes
        if len(parametros) > 1:
            consome_palavra("etambem")
        tipo = consome_categoria("TIPO")
        nome_parametro = consome_categoria("IDENTIFICADOR")
        parametros.append(["parametro", tipo, nome_parametro])
    consome_palavra("fechaportamala")

    return ["receita", tipo_retorno, nome, parametros, bloco()]


def bloco():
    consome_palavra("abremochila")
    no = ["bloco"]
    while lexema_atual() != "fechamochila":
        no.append(instrucao())
    consome_palavra("fechamochila")
    return no


def declaracao():
    tipo = consome_categoria("TIPO")
    nome = consome_categoria("IDENTIFICADOR")
    consome_palavra("eisso")
    valor = expressao()
    consome_palavra("aduana")
    return ["declaracao", tipo, nome, valor]


def atribuicao():
    nome = consome_categoria("IDENTIFICADOR")
    consome_palavra("eisso")
    valor = expressao()
    consome_palavra("aduana")
    return ["atribuicao", nome, valor]


def iph():
    consome_palavra("iph")
    consome_palavra("abreportamala")
    condicao = expressao()
    consome_palavra("fechaportamala")
    no = ["iph", condicao, bloco()]

    # O ueuce é opcional
    if lexema_atual() == "ueuce":
        avanca()
        no.append(["ueuce", bloco()])
    return no


def uaile():
    consome_palavra("uaile")
    consome_palavra("abreportamala")
    condicao = expressao()
    consome_palavra("fechaportamala")
    return ["uaile", condicao, bloco()]


def galantia():
    consome_palavra("galantia")
    no = ["galantia"]
    # O valor é opcional: receita semtroco não devolve nada
    if lexema_atual() != "aduana":
        no.append(expressao())
    consome_palavra("aduana")
    return no


def tnirp():
    consome_palavra("tnirp")
    consome_palavra("abreportamala")
    valor = expressao()
    consome_palavra("fechaportamala")
    consome_palavra("aduana")
    return ["tnirp", valor]


def chamada():
    no = ["chamada", consome_categoria("IDENTIFICADOR")]
    consome_palavra("abreportamala")
    while lexema_atual() != "fechaportamala":
        # Do segundo argumento em diante, precisa do etambem antes
        if len(no) > 2:
            consome_palavra("etambem")
        no.append(expressao())
    consome_palavra("fechaportamala")
    return no


# ---------- expressões ----------
# Todas seguem a mesma ideia: lê o lado esquerdo e, enquanto aparecer um
# operador daquele nível, lê o lado direito. O operador vira o nó e os dois
# lados viram os filhos.

def expressao():
    no = e_logico()
    while lexema_atual() == "ouentao":
        operador = avanca()
        no = [operador, no, e_logico()]
    return no


def e_logico():
    no = negacao()
    while lexema_atual() == "levajunto":
        operador = avanca()
        no = [operador, no, negacao()]
    return no


def negacao():
    if lexema_atual() == "naotem":
        avanca()
        return ["naotem", negacao()]
    return comparacao()


def comparacao():
    no = soma()
    while lexema_atual() in COMPARADORES:
        operador = avanca()
        no = [operador, no, soma()]
    return no


def soma():
    no = termo()
    while lexema_atual() in ["maisbarato", "sumiu"]:
        operador = avanca()
        no = [operador, no, termo()]
    return no


def termo():
    no = fator()
    while lexema_atual() in ["dobradinha", "divideai"]:
        operador = avanca()
        no = [operador, no, fator()]
    return no


def fator():
    if tipo_atual() in ["NUMERO", "STRING", "BOOLEANO"]:
        return avanca()

    if tipo_atual() == "IDENTIFICADOR":
        if lexema_seguinte() == "abreportamala":
            return chamada()
        return avanca()

    if lexema_atual() == "abreportamala":
        avanca()
        no = expressao()
        consome_palavra("fechaportamala")
        return no

    erro("um valor")


# ---------- entrada e saída ----------

def analisar(lista_de_tokens):
    """Recebe os tokens do tokenizador e devolve a árvore sintática."""
    global tokens

    # Os erros léxicos já foram avisados pelo tokenizador, então saem da lista.
    tokens = [token for token in lista_de_tokens if token[0] != "ERRO"]

    # O token FIM marca o final, para nunca faltar um "token atual".
    if tokens:
        ultima_linha, ultima_coluna = tokens[-1][2], tokens[-1][3]
    else:
        ultima_linha, ultima_coluna = 1, 1
    tokens.append(("FIM", "fim do arquivo", ultima_linha, ultima_coluna))

    return programa()


def imprimir_arvore(no, nivel=0):
    """Mostra a árvore: quanto mais recuado, mais fundo na árvore."""
    recuo = "    " * nivel
    if isinstance(no, list):
        print(recuo + no[0])
        for filho in no[1:]:
            imprimir_arvore(filho, nivel + 1)
    else:
        print(recuo + no)


if __name__ == "__main__":
    with open("programa.pay", "r", encoding="utf-8") as arquivo:
        codigo_fonte = arquivo.read()

    try:
        arvore = analisar(tokenize(codigo_fonte))
        print("Erros sintaticos: 0")
        imprimir_arvore(arvore)
    except ErroSintatico as mensagem:
        print("Erros sintaticos: 1")
        print(" ", mensagem)

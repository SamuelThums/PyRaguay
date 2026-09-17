import re

# ==========================================
# COMANDOS DA LINGUAGEM .PAY -> PYTHON
# ==========================================
#
# iph               -> if
# ueuce             -> else
# uaile             -> while
# galantia          -> return
# tnirp             -> print
# receita           -> def
#
# contado           -> int    (tipo: dinheiro contado, sem centavos)
# quebrado          -> float  (tipo: valor quebrado, com centavos)
# etiqueta          -> string (tipo: o texto escrito na etiqueta)
# temounao          -> bool   (tipo: "tem ou nao tem?")
# semtroco          -> void   (tipo: a receita nao devolve nada)
#
# original          -> True
# oliginal          -> False
#
# maisbarato        -> +      (operador aritmetico)
# sumiu             -> -      (operador aritmetico)
# dobradinha        -> *      (operador aritmetico)
# divideai          -> /      (operador aritmetico)
#
# eisso             -> =      (operador de atribuicao)
#
# pareceigual       -> ==     (operador condicional: "parece igual", sera que e?)
# trocado           -> !=     (operador condicional: essa mercadoria é trocada)
# achatou           -> <      (operador condicional: o preço achatou)
# estourou          -> >      (operador condicional: o preço estourou)
# menoroumenos      -> <=     (operador condicional)
# maioroumais       -> >=     (operador condicional)
#
# levajunto         -> and    (operador logico: "leva junto que sai mais barato")
# ouentao           -> or     (operador logico: "ou então leva esse aqui")
# naotem            -> not    (operador logico: "não tem", clássico do camelô)
#
# abreportamala     -> (
# fechaportamala    -> )
# abremochila       -> {
# fechamochila      -> }
# etambem           -> ,      (separa argumentos e parametros: "e tambem leva esse")
#
# aduana            -> ;      (pontuacao: termina a instrucao, passou na aduana)
#
# "texto" ou 'texto' -> string (aceita aspas simples, duplas e aspas internas)
#
# \\                -> comentário de uma linha
#
# \°                -> abre comentário de bloco
# °\                -> fecha comentário de bloco

# Especificação dos tokens, na ordem em que devem ser testados.
# A ordem importa: comentários e strings precisam ser reconhecidos antes de
# qualquer outra coisa, e as palavras-chave precisam vir antes do
# identificador genérico.
ESPECIFICACAO_TOKENS = [
    ("COMENTARIO",           r"\\°.*?°\\|\\\\[^\n]*"),
    ("STRING",                r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''),
    ("PALAVRA_CHAVE",         r"\b(?:iph|ueuce|uaile|galantia|tnirp|receita)\b"),
    ("TIPO",                  r"\b(?:contado|quebrado|etiqueta|temounao|semtroco)\b"),
    ("BOOLEANO",              r"\b(?:original|oliginal)\b"),
    ("NUMERO",                r"\d+\.\d+|\d+"),
    ("OPERADOR_ATRIBUICAO",   r"\beisso\b"),
    ("OPERADOR_LOGICO",       r"\b(?:levajunto|ouentao|naotem)\b"),
    ("OPERADOR_CONDICIONAL",  r"\b(?:pareceigual|trocado|menoroumenos|maioroumais|achatou|estourou)\b"),
    # separa os operadores por conta das ordens na eq
    #("OPERADOR_ARITMETICO",   r"\b(?:dobradinha|divideai)\b"),
    #("OPERADOR_ARITMETICO_SUB_ADD",   r"\b(?:maisbarato|sumiu)\b"),
    ("OPERADOR_ARITMETICO",   r"\b(?:maisbarato|sumiu|dobradinha|divideai)\b"),
    ("PONTUACAO",             r"\baduana\b"),
    ("SIMBOLO",               r"\b(?:abreportamala|fechaportamala|abremochila|fechamochila|etambem)\b"),
    ("IDENTIFICADOR",         r"[a-zA-Z_][a-zA-Z0-9_]*"),
    ("ESPACO",                r"[ \t]+"),
    ("QUEBRA_LINHA",          r"\r\n|\n"),
]

# Mantido como dicionário simples para quem só quer consultar os padrões.
tokens = dict(ESPECIFICACAO_TOKENS)

_PADRAO_GERAL = re.compile(
    "|".join(f"(?P<{nome}>{padrao})" for nome, padrao in ESPECIFICACAO_TOKENS),
    re.DOTALL,
)

_TIPOS_IGNORADOS = {"ESPACO", "QUEBRA_LINHA", "COMENTARIO"}


def tokenize(codigo):
    resultado = []
    erros = []
    pos = 0
    linha = 1
    coluna = 1
    tamanho = len(codigo)

    while pos < tamanho:
        casamento = _PADRAO_GERAL.match(codigo, pos)

        if casamento is None:
            caractere = codigo[pos]
            erros.append((caractere, linha, coluna))
            resultado.append(("ERRO", caractere, linha, coluna))
            if caractere == "\n":
                linha += 1
                coluna = 1
            else:
                coluna += 1
            pos += 1
            continue

        tipo = casamento.lastgroup
        lexema = casamento.group()
        linha_inicio, coluna_inicio = linha, coluna
        pos = casamento.end()

        quebras = lexema.count("\n")
        if quebras:
            linha += quebras
            coluna = len(lexema) - lexema.rfind("\n")
        else:
            coluna += len(lexema)

        if tipo in _TIPOS_IGNORADOS:
            continue

        resultado.append((tipo, lexema, linha_inicio, coluna_inicio))

    print("Tokens encontrados:", len(resultado))
    print("Erros lexicos:", len(erros))
    for caractere, linha_erro, coluna_erro in erros:
        print(
            f"  MERCADORIA NAO ENCONTRADA (linha {linha_erro}, coluna {coluna_erro}): "
            f"{caractere!r} nao faz parte do sortimento da linguagem PAY"
        )

    return resultado


# Lendo o código-fonte de um arquivo .pay
with open("programa.pay", "r", encoding="utf-8") as arquivo:
    codigo_fonte = arquivo.read()

lista = tokenize(codigo_fonte)

for tipo, lexema, linha, coluna in lista:
    print(f"{tipo} -> {lexema}  (linha {linha}, coluna {coluna})")

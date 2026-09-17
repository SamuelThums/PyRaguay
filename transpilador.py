import ast
import io
import re
import tokenize


ARQUIVO_ENTRADA = "py_to_pay.py"
ARQUIVO_SAIDA = "programa.pay"


PALAVRAS = {
    "if": "iph",
    "else": "ueuce",
    "while": "uaile",
    "return": "galantia",
    "print": "tnirp",
    "def": "receita",
    "True": "original",
    "False": "oliginal",
    "and": "levajunto",
    "or": "ouentao",
    "not": "naotem",
}

# A linguagem PAY e estaticamente tipada: a anotacao Python vira a palavra de
# tipo que aparece antes do nome da variavel, do parametro ou da receita.
TIPOS = {
    "int": "contado",
    "float": "quebrado",
    "str": "etiqueta",
    "bool": "temounao",
    "None": "semtroco",
}

OPERADORES = {
    "+": "maisbarato",
    "-": "sumiu",
    "*": "dobradinha",
    "/": "divideai",
    "=": "eisso",
    "==": "pareceigual",
    "!=": "trocado",
    "<": "achatou",
    ">": "estourou",
    "<=": "menoroumenos",
    ">=": "maioroumais",
    "(": "abreportamala",
    ")": "fechaportamala",
    ",": "etambem",
}

# Estruturas cuja condicao precisa sair entre parenteses, como pede o enunciado:
# "iph abreportamala ... fechaportamala abremochila".
CONTROLE_COM_CONDICAO = {"if", "while"}

# ":" e "->" nao entram em OPERADORES porque dependem do contexto: podem
# aparecer anotando um tipo ou abrindo um bloco, e cada caso vira um lexema
# PAY diferente.
ABRE_BLOCO = "abremochila"
FECHA_BLOCO = "fechamochila"
TERMINADOR = "aduana"


def converter_string(texto):
    valor = ast.literal_eval(texto)
    if not isinstance(valor, str):
        raise ValueError("Somente strings de texto sao suportadas")

    # A linguagem PAY aceita o literal como foi escrito (aspas simples,
    # duplas, com aspas do outro tipo por dentro), mantendo as aspas originais.
    return texto


def converter_tipo(texto):
    if texto not in TIPOS:
        raise ValueError(f"Tipo Python sem equivalente em PAY: {texto}")

    return TIPOS[texto]


def converter_atomo(tipo, texto):
    """Traduz um unico token Python que nao depende do contexto da linha."""
    if tipo == tokenize.NAME:
        return PALAVRAS.get(texto, texto)
    if tipo == tokenize.NUMBER:
        if not re.fullmatch(r"\d+(\.\d+)?", texto):
            raise ValueError(f"Numero nao suportado pela linguagem PAY: {texto}")
        return texto
    if tipo == tokenize.STRING:
        return converter_string(texto)
    if tipo == tokenize.OP:
        if texto not in OPERADORES:
            raise ValueError(f"Operador Python sem equivalente em PAY: {texto}")
        return OPERADORES[texto]

    raise ValueError(f"Elemento Python nao suportado: {texto}")


def converter_parametros(tokens):
    """De "(preco: float, frete: float)" para "( quebrado preco, quebrado frete )".

    Em PAY o tipo vem antes do nome, entao cada trio "nome : tipo" e invertido.
    Parametro sem anotacao e recusado: a tipagem explicita e obrigatoria.
    """
    saida = ["abreportamala"]
    indice = 1

    while indice < len(tokens) - 1:
        _, texto = tokens[indice]

        if texto == ",":
            saida.append(OPERADORES[","])
            indice += 1
            continue

        if tokens[indice + 1][1] != ":":
            raise ValueError(f"Parametro sem tipo explicito: {texto}")

        saida.append(converter_tipo(tokens[indice + 2][1]))
        saida.append(texto)
        indice += 3

    saida.append("fechaportamala")
    return saida


def converter_declaracao_receita(tokens):
    """De "def soma(a: int) -> float" para "receita quebrado soma ( contado a )"."""
    nome = tokens[1][1]
    posicao_seta = next(
        (indice for indice, (_, texto) in enumerate(tokens) if texto == "->"),
        None,
    )

    if posicao_seta is None:
        raise ValueError(f"Receita sem tipo de retorno explicito: {nome}")

    tipo_retorno = converter_tipo(tokens[posicao_seta + 1][1])
    parametros = converter_parametros(tokens[2:posicao_seta])

    return ["receita", tipo_retorno, nome] + parametros


def converter_comando(tokens):
    """Traduz uma instrucao comum.

    "preco: float = 350.5" vira "quebrado preco eisso 350.5": o tipo anotado
    passa para a frente do nome, como numa declaracao estilo C.
    """
    declara_variavel = (
        len(tokens) > 2
        and tokens[0][0] == tokenize.NAME
        and tokens[1][1] == ":"
    )

    if declara_variavel:
        cabecalho = [converter_tipo(tokens[2][1]), tokens[0][1]]
        return cabecalho + [converter_atomo(*token) for token in tokens[3:]]

    return [converter_atomo(*token) for token in tokens]


def converter_controle(tokens):
    """De "if x > 0" para "iph ( x estourou 0 )".

    Python dispensa os parenteses na condicao; a linguagem PAY os exige, entao
    eles sao colocados aqui em volta de tudo que vem depois do iph/uaile.
    """
    palavra = PALAVRAS[tokens[0][1]]
    condicao = [converter_atomo(*token) for token in tokens[1:]]

    return [palavra, "abreportamala"] + condicao + ["fechaportamala"]


def converter_linha(tokens):
    """Converte os tokens Python de uma linha logica em lexemas PAY."""
    abre_bloco = bool(tokens) and tokens[-1] == (tokenize.OP, ":")
    if abre_bloco:
        tokens = tokens[:-1]

    if tokens and tokens[0][1] == "def":
        saida = converter_declaracao_receita(tokens)
    elif tokens and tokens[0][1] in CONTROLE_COM_CONDICAO:
        saida = converter_controle(tokens)
    else:
        saida = converter_comando(tokens)

    # Bloco aberto dispensa terminador; toda outra instrucao fecha com "aduana".
    saida.append(ABRE_BLOCO if abre_bloco else TERMINADOR)
    return saida


def transpilar(codigo_python):
    linhas = []
    tokens_linha = []
    # Comentarios soltos e linhas em branco ficam represados ate o proximo
    # comando: assim eles caem depois do "fechamochila" do bloco que terminou,
    # e nao grudados no fim do bloco anterior.
    pendentes = []
    comentario = None
    nivel = 0

    def descarregar_pendentes():
        for item in pendentes:
            if item is None:
                linhas.append("")
            else:
                linhas.append("    " * nivel + "\\\\ " + item)
        pendentes.clear()

    def salvar_linha():
        nonlocal tokens_linha, comentario

        if tokens_linha:
            descarregar_pendentes()
            texto = "    " * nivel + " ".join(converter_linha(tokens_linha))
            if comentario:
                texto += "  \\\\ " + comentario
            linhas.append(texto)

        tokens_linha = []
        comentario = None

    tokens_python = tokenize.generate_tokens(io.StringIO(codigo_python).readline)

    for token in tokens_python:
        tipo = token.type
        texto = token.string

        if tipo in (tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        if tipo == tokenize.INDENT:
            nivel += 1
        elif tipo == tokenize.DEDENT:
            nivel -= 1
            linhas.append("    " * nivel + FECHA_BLOCO)
        elif tipo == tokenize.COMMENT:
            comentario = texto[1:].strip()
        elif tipo == tokenize.NEWLINE:
            salvar_linha()
        elif tipo == tokenize.NL:
            if tokens_linha:
                continue
            pendentes.append(comentario)
            comentario = None
        else:
            tokens_linha.append((tipo, texto))

    salvar_linha()

    # Comentarios finais entram no arquivo; linhas em branco sobrando, nao.
    while pendentes and pendentes[-1] is None:
        pendentes.pop()
    descarregar_pendentes()

    return "\n".join(linhas) + "\n"


def main():
    try:
        with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as arquivo:
            codigo_python = arquivo.read()

        codigo_pay = transpilar(codigo_python)

        with open(ARQUIVO_SAIDA, "w", encoding="utf-8", newline="\r\n") as arquivo:
            arquivo.write(codigo_pay)

        print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
    except (OSError, SyntaxError, tokenize.TokenError, ValueError) as erro:
        print(f"Erro na transpilacao: {erro}")


if __name__ == "__main__":
    main()

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
}

OPERADORES = {
    "+": "maisbarato",
    "-": "sumiu",
    "*": "dobradinha",
    "/": "divideai",
    "=": "eisso",
    "==": "pareceigual",
    "<=": "menoroumenos",
    ">=": "maioroumais",
    "(": "abreportamala",
    ")": "fechaportamala",
    ",": "aduana",
    ":": "abremochila",
}


def converter_string(texto):
    valor = ast.literal_eval(texto)
    if not isinstance(valor, str):
        raise ValueError("Somente strings de texto sao suportadas")

    palavras = valor.split()
    invalidas = [
        palavra for palavra in palavras
        if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", palavra) is None
    ]
    if invalidas:
        raise ValueError(
            "A linguagem PAY nao aceita este texto em strings: "
            + ", ".join(invalidas)
        )
    return palavras


def transpilar(codigo_python):
    linhas = []
    linha_atual = []
    comentario = None
    coluna_comentario = 0
    nivel = 0

    def salvar_linha(finalizar=True):
        nonlocal linha_atual, comentario, coluna_comentario
        if linha_atual:
            if finalizar and linha_atual[-1] != "abremochila":
                linha_atual.append("aduana")
            texto = "    " * nivel + " ".join(linha_atual)
            if comentario:
                texto += "  \\\\ " + comentario
            linhas.append(texto)
        elif comentario:
            linhas.append(" " * coluna_comentario + "\\\\ " + comentario)
        linha_atual = []
        comentario = None
        coluna_comentario = 0

    tokens_python = tokenize.generate_tokens(io.StringIO(codigo_python).readline)

    for token in tokens_python:
        tipo = token.type
        texto = token.string

        if tipo in (tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        if tipo == tokenize.INDENT:
            nivel += 1
        elif tipo == tokenize.DEDENT:
            salvar_linha()
            nivel -= 1
            linhas.append("    " * nivel + "fechamochila")
        elif tipo == tokenize.NAME:
            linha_atual.append(PALAVRAS.get(texto, texto))
        elif tipo == tokenize.NUMBER:
            if not texto.isdigit():
                raise ValueError(f"Numero nao suportado pela linguagem PAY: {texto}")
            linha_atual.append(texto)
        elif tipo == tokenize.STRING:
            linha_atual.extend(converter_string(texto))
        elif tipo == tokenize.OP:
            if texto not in OPERADORES:
                raise ValueError(f"Operador Python sem equivalente em PAY: {texto}")
            linha_atual.append(OPERADORES[texto])
        elif tipo == tokenize.COMMENT:
            comentario = texto[1:].strip()
            coluna_comentario = token.start[1]
        elif tipo == tokenize.NEWLINE:
            salvar_linha()
        elif tipo == tokenize.NL:
            if comentario and not linha_atual:
                salvar_linha()
        elif tipo not in (tokenize.INDENT, tokenize.DEDENT):
            raise ValueError(f"Elemento Python nao suportado: {texto}")

    salvar_linha()
    return "\n".join(linhas) + "\n"


def main():
    try:
        with open(ARQUIVO_ENTRADA, "r", encoding="utf-8") as arquivo:
            codigo_python = arquivo.read()

        codigo_pay = transpilar(codigo_python)

        with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as arquivo:
            arquivo.write(codigo_pay)

        print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
    except (OSError, SyntaxError, tokenize.TokenError, ValueError) as erro:
        print(f"Erro na transpilacao: {erro}")


if __name__ == "__main__":
    main()

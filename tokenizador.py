import re

tokens = {
    "PALAVRA_CHAVE": r"iph|ueuce|uaile|galantia|tnirp",
    "NUMERO": r"\d+",
    "OPERADOR": r"maisbarato|sumiu|dobradinha|divideai|eisso|pareceigual|menoroumenos|maioroumais",
    "SIMBOLO": r"abreportamala|fechaportamala|abremochila|fechamochila|aduana",
    "IDENTIFICADOR": r"[a-zA-Z][a-zA-Z0-9]*",
}


def tokenize(codigo):
    resultado = []
    erros = 0
    for palavra in codigo.split():
        tipo_encontrado = "ERRO"
        for tipo, padrao in tokens.items():
            if re.fullmatch(padrao, palavra):
                tipo_encontrado = tipo
                break
        if tipo_encontrado == "ERRO":
            erros += 1
        resultado.append((tipo_encontrado, palavra))
    print("Tokens encontrados:", len(resultado))
    print("Erros lexicos:", erros)
    return resultado


# Lendo o código-fonte de um arquivo .pay
with open("programa.pay", "r", encoding="utf-8") as arquivo:
    codigo_fonte = arquivo.read()

lista = tokenize(codigo_fonte)
for tipo, lexema in lista:
    print(tipo, "->", lexema)

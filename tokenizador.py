import re

# Complete as expressoes regulares que estao vazias.
# A ordem importa: o primeiro tipo que casar e o escolhido.
tokens = {
    "PALAVRA_CHAVE": r"iph|ueuce|uaile|galantia|tnirp",
    "NUMERO":        r"\d+",
    "IDENTIFICADOR": r"[a-zA-Z][a-zA-Z0-9]*",   # x   soma   valor1
    "OPERADOR":      r"",   # +  -  *  /  =  ==  <  >
    "SIMBOLO":       r"[();]",
}


def tokenize(codigo):
    resultado = []          # lista de tokens reconhecidos
    erros = 0

    for palavra in codigo.split():
        tipo_encontrado = "ERRO"

        for tipo, padrao in tokens.items():
            if re.fullmatch(padrao, palavra):
                tipo_encontrado = tipo
                break

        if tipo_encontrado == "ERRO":
            erros = erros + 1

        resultado.append((tipo_encontrado, palavra))

    print("Tokens encontrados:", len(resultado))
    print("Erros lexicos:", erros)
    return resultado


# Teste
lista = tokenize("if x == 10 return x + 1 ;")

for tipo, lexema in lista:
    print(tipo, "->", lexema)

import contextlib
import io

import analisador_semantico as semantico
from analisador_sintatico import analisar
from tokenizador import tokenize

# ==========================================
# TESTES DO ANALISADOR SEMÂNTICO
# ==========================================
#
# Rode com:  python testes_semantico.py
#
# Primeiro testa a tabela de símbolos sozinha. Depois roda programas .pay
# pequenos que DEVEM dar erro e confere se o erro certo apareceu.


def erros_do_codigo(codigo):
    # O tokenizador imprime um resumo; aqui ele é escondido para não poluir
    with contextlib.redirect_stdout(io.StringIO()):
        arvore = analisar(tokenize(codigo))
    return semantico.analisar_semantica(arvore)


def testa_tabela_de_simbolos():
    semantico.escopos = [{}]
    semantico.erros = []

    semantico.declara("x", {"categoria": "variavel", "tipo": "contado", "linha": 1})
    assert semantico.busca("x")["tipo"] == "contado"

    # Escopo interno enxerga o de fora e pode esconder o nome (shadowing)
    semantico.abre_escopo()
    assert semantico.busca("x")["tipo"] == "contado"
    semantico.declara("x", {"categoria": "variavel", "tipo": "etiqueta", "linha": 2})
    assert semantico.busca("x")["tipo"] == "etiqueta"
    semantico.declara("y", {"categoria": "variavel", "tipo": "temounao", "linha": 3})
    semantico.fecha_escopo()

    # Ao sair do bloco, volta o x de fora e o y some
    assert semantico.busca("x")["tipo"] == "contado"
    assert semantico.busca("y") is None

    # Duplicidade no mesmo escopo vira erro
    semantico.declara("x", {"categoria": "variavel", "tipo": "contado", "linha": 4})
    assert len(semantico.erros) == 1

    print("ok   tabela de simbolos")


# Cada caso: (descrição, código .pay, trecho que precisa aparecer no erro)
CASOS_INVALIDOS = [
    ("variavel nao declarada",
     "contado a eisso 5 aduana\n"
     "contado b eisso a maisbarato z aduana",
     "(linha 2): 'z' nao foi declarado"),

    ("receita nao declarada",
     "sumir abreportamala fechaportamala aduana",
     "a receita 'sumir' nao foi declarada"),

    ("variavel fora do seu escopo",
     "iph abreportamala original fechaportamala abremochila\n"
     "    contado y eisso 1 aduana\n"
     "fechamochila\n"
     "tnirp abreportamala y fechaportamala aduana",
     "(linha 4): 'y' nao foi declarado"),

    ("variavel duplicada no mesmo escopo",
     "contado x eisso 5 aduana\n"
     "contado x eisso 10 aduana",
     "'x' ja foi declarado neste escopo (na linha 1)"),

    ("receita duplicada",
     "receita semtroco oi abreportamala fechaportamala abremochila fechamochila\n"
     "receita semtroco oi abreportamala fechaportamala abremochila fechamochila",
     "(linha 2): 'oi' ja foi declarado"),

    ("conta com etiqueta",
     'contado x eisso 3 maisbarato "tres" aduana',
     "maisbarato so faz conta com numeros, mas recebeu contado e etiqueta"),

    ("levajunto com numero",
     "temounao t eisso original levajunto 1 aduana",
     "levajunto precisa de temounao dos dois lados"),

    ("comparacao de etiqueta com numero",
     'temounao t eisso "a" achatou 2 aduana',
     "achatou nao compara etiqueta com contado"),

    ("condicao do iph nao e temounao",
     "iph abreportamala 5 fechaportamala abremochila fechamochila",
     "a condicao do iph precisa ser temounao, mas e contado"),

    ("declaracao com tipo errado",
     'contado x eisso "dez" aduana',
     "'x' e contado mas recebeu um valor etiqueta"),

    ("quebrado nao cabe em contado",
     "contado x eisso 1.5 aduana",
     "'x' e contado mas recebeu um valor quebrado"),

    ("argumento com tipo errado",
     "receita contado dobro abreportamala contado n fechaportamala abremochila\n"
     "    galantia n dobradinha 2 aduana\n"
     "fechamochila\n"
     'contado r eisso dobro abreportamala "dois" fechaportamala aduana',
     "o argumento 1 de 'dobro' devia ser contado mas e etiqueta"),

    ("argumentos a mais",
     "receita contado dobro abreportamala contado n fechaportamala abremochila\n"
     "    galantia n dobradinha 2 aduana\n"
     "fechamochila\n"
     "contado r eisso dobro abreportamala 1 etambem 2 fechaportamala aduana",
     "a receita 'dobro' espera 1 argumento(s) mas recebeu 2"),

    ("retorno com tipo errado",
     "receita contado nome abreportamala fechaportamala abremochila\n"
     '    galantia "camelo" aduana\n'
     "fechamochila",
     "a receita 'nome' devolve contado mas o galantia devolve etiqueta"),

    ("semtroco devolvendo valor",
     "receita semtroco nada abreportamala fechaportamala abremochila\n"
     "    galantia 1 aduana\n"
     "fechamochila",
     "a receita 'nada' e semtroco e nao devolve valor"),

    ("galantia fora de receita",
     "galantia 1 aduana",
     "galantia so pode ser usado dentro de uma receita"),
]


def testa_casos_invalidos():
    falhas = 0
    for descricao, codigo, esperado in CASOS_INVALIDOS:
        erros = erros_do_codigo(codigo)
        if any(esperado in mensagem for mensagem in erros):
            print("ok  ", descricao)
        else:
            falhas += 1
            print("FALHOU", descricao)
            print("   esperava:", esperado)
            print("   recebeu: ", erros)
    return falhas


def testa_varios_erros_de_uma_vez():
    # A análise não pode parar no primeiro erro
    erros = erros_do_codigo(
        "contado a eisso b aduana\n"
        'contado c eisso "x" aduana\n'
        "contado a eisso 1 aduana"
    )
    assert len(erros) == 3, erros
    print("ok   varios erros de uma vez")


def testa_programa_valido():
    with open("programa.pay", "r", encoding="utf-8") as arquivo:
        erros = erros_do_codigo(arquivo.read())
    assert erros == [], erros
    print("ok   programa.pay sem erros")


if __name__ == "__main__":
    testa_tabela_de_simbolos()
    testa_programa_valido()
    testa_varios_erros_de_uma_vez()
    falhas = testa_casos_invalidos()
    print()
    print("Tudo certo!" if falhas == 0 else f"{falhas} teste(s) falharam")

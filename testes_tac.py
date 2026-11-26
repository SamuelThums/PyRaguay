import contextlib
import io

from analisador_semantico import analisar_semantica
from analisador_sintatico import analisar
from gerador_tac import gerar_tac, formatar
from tokenizador import tokenize

# ==========================================
# TESTES DO GERADOR DE TAC
# ==========================================
#
# Rode com:  python testes_tac.py
#
# Cada caso é um programa .pay pequeno e o TAC que ele tem que gerar,
# linha por linha. Os recuos são ignorados na comparação.


def tac_do_codigo(codigo):
    # O tokenizador imprime um resumo. Aqui ele é escondido (redirect_stdout
    # joga o que seria impresso em um texto que ninguém lê).
    with contextlib.redirect_stdout(io.StringIO()):
        arvore = analisar(tokenize(codigo))
    erros = analisar_semantica(arvore)
    assert erros == [], erros
    return [formatar(instrucao).strip() for instrucao in gerar_tac(arvore)]


# Cada caso: (descrição, código .pay, TAC esperado)
CASOS = [
    # O teste inicial pedido nos slides: d = (a + b) * c
    ("d = (a + b) * c",
     "contado a eisso 5 aduana\n"
     "contado b eisso 3 aduana\n"
     "contado c eisso 2 aduana\n"
     "contado d eisso abreportamala a maisbarato b fechaportamala dobradinha c aduana",
     ["a = 5",
      "b = 3",
      "c = 2",
      "t1 = a + b",
      "t2 = t1 * c",
      "d = t2",
      "fim"]),

    # Sem parênteses, a multiplicação é feita primeiro
    ("precedencia",
     "contado x eisso 1 maisbarato 2 dobradinha 3 aduana",
     ["t1 = 2 * 3",
      "t2 = 1 + t1",
      "x = t2",
      "fim"]),

    ("booleanos e naotem",
     "temounao a eisso original aduana\n"
     "temounao b eisso naotem a levajunto oliginal aduana",
     ["a = 1",
      "t1 = not a",
      "t2 = t1 and 0",
      "b = t2",
      "fim"]),

    ("iph sem ueuce",
     "contado x eisso 1 aduana\n"
     "iph abreportamala x estourou 0 fechaportamala abremochila\n"
     "    tnirp abreportamala x fechaportamala aduana\n"
     "fechamochila",
     ["x = 1",
      "t1 = x > 0",
      "ifFalse t1 goto L1",
      "print x",
      "L1:",
      "fim"]),

    ("iph com ueuce",
     "contado x eisso 1 aduana\n"
     "iph abreportamala x pareceigual 1 fechaportamala abremochila\n"
     '    tnirp abreportamala "um" fechaportamala aduana\n'
     "fechamochila\n"
     "ueuce abremochila\n"
     '    tnirp abreportamala "outro" fechaportamala aduana\n'
     "fechamochila",
     ["x = 1",
      "t1 = x == 1",
      "ifFalse t1 goto L1",
      'print "um"',
      "goto L2",
      "L1:",
      'print "outro"',
      "L2:",
      "fim"]),

    ("uaile",
     "contado i eisso 0 aduana\n"
     "uaile abreportamala i achatou 3 fechaportamala abremochila\n"
     "    i eisso i maisbarato 1 aduana\n"
     "fechamochila",
     ["i = 0",
      "L1:",
      "t1 = i < 3",
      "ifFalse t1 goto L2",
      "t2 = i + 1",
      "i = t2",
      "goto L1",
      "L2:",
      "fim"]),

    # O corpo da receita vai para depois do "fim" do programa principal
    ("receita e chamada",
     "receita contado soma abreportamala contado a etambem contado b fechaportamala abremochila\n"
     "    galantia a maisbarato b aduana\n"
     "fechamochila\n"
     "contado x eisso soma abreportamala 2 etambem 3 fechaportamala aduana",
     ["param 2",
      "param 3",
      "t2 = call soma, 2",
      "x = t2",
      "fim",
      "soma(a, b):",
      "t1 = a + b",
      "return t1"]),

    # Receita semtroco sem galantia ganha um return no final.
    # A chamada solta não guarda o resultado em temporário.
    ("receita semtroco",
     "receita semtroco avisa abreportamala etiqueta m fechaportamala abremochila\n"
     "    tnirp abreportamala m fechaportamala aduana\n"
     "fechamochila\n"
     'avisa abreportamala "oi" fechaportamala aduana',
     ['param "oi"',
      "call avisa, 1",
      "fim",
      "avisa(m):",
      "print m",
      "return"]),

    # Os argumentos são calculados antes dos param
    ("argumento com conta",
     "receita contado dobro abreportamala contado n fechaportamala abremochila\n"
     "    galantia n dobradinha 2 aduana\n"
     "fechamochila\n"
     "contado y eisso dobro abreportamala 1 maisbarato 2 fechaportamala aduana",
     ["t2 = 1 + 2",
      "param t2",
      "t3 = call dobro, 1",
      "y = t3",
      "fim",
      "dobro(n):",
      "t1 = n * 2",
      "return t1"]),
]


def testa_casos():
    falhas = 0
    for descricao, codigo, esperado in CASOS:
        gerado = tac_do_codigo(codigo)
        if gerado == esperado:
            print(f"ok   {descricao}")
        else:
            falhas += 1
            print(f"FALHOU {descricao}")
            print("   esperado:", esperado)
            print("   gerado:  ", gerado)
    return falhas


def testa_programa_pay():
    # Não confere linha por linha, só se o programa inteiro gera sem quebrar
    with open("programa.pay", "r", encoding="utf-8") as arquivo:
        tac = tac_do_codigo(arquivo.read())
    assert "fim" in tac
    assert "calcular_total(preco, frete):" in tac
    print("ok   programa.pay gera TAC")


if __name__ == "__main__":
    falhas = testa_casos()
    testa_programa_pay()
    print()
    print("Tudo certo!" if falhas == 0 else f"{falhas} teste(s) falharam")

import contextlib
import io
import os
import subprocess
import sys
import tempfile

from analisador_semantico import analisar_semantica
from analisador_sintatico import analisar
from gerador_riscv import gerar_riscv
from gerador_tac import gerar_tac
from tokenizador import tokenize

# ==========================================
# TESTES DO GERADOR RISC-V
# ==========================================
#
# Rode com:  python testes_riscv.py caminho/do/rars1_6.jar
#
# Cada caso é um programa .pay e o que ele tem que imprimir. O teste gera o
# assembly, roda de verdade no simulador RARS e compara a saída.
#
# Bibliotecas usadas (todas já vêm com o Python):
#   subprocess  roda o RARS (um programa Java) e captura o que ele imprime,
#               como se fosse digitado no terminal: java -jar rars.jar ...
#   tempfile    cria uma pasta temporária para o arquivo .s de cada caso,
#               que é apagada sozinha no final
#   os          monta o caminho do arquivo dentro dessa pasta
#
# O RARS baixa em https://github.com/TheThirdOne/rars/releases (precisa de Java).


def assembly_do_codigo(codigo):
    # O tokenizador imprime um resumo; aqui ele é escondido
    with contextlib.redirect_stdout(io.StringIO()):
        arvore = analisar(tokenize(codigo))
    erros = analisar_semantica(arvore)
    assert erros == [], erros
    return gerar_riscv(gerar_tac(arvore))


def roda_no_rars(caminho_rars, assembly):
    """Grava o assembly num arquivo, roda no RARS e devolve as linhas impressas."""
    with tempfile.TemporaryDirectory() as pasta:
        arquivo = os.path.join(pasta, "teste.s")
        with open(arquivo, "w", encoding="utf-8") as saida:
            saida.write(assembly)

        # nc: não mostra o aviso de copyright
        # me: mensagens de erro do RARS vão para o stderr, separadas da saída
        resultado = subprocess.run(
            ["java", "-jar", caminho_rars, "nc", "me", arquivo],
            capture_output=True, text=True, timeout=60,
        )

    linhas = resultado.stdout.splitlines()
    # O RARS termina com uma linha em branco e um aviso. Só interessa o resto.
    while linhas and (linhas[-1] == "" or "Program terminated" in linhas[-1]):
        linhas.pop()
    return linhas, resultado.stderr


# Cada caso: (descrição, código .pay, linhas que o programa precisa imprimir)
CASOS = [
    ("d = (a + b) * c",
     "contado a eisso 5 aduana\n"
     "contado b eisso 3 aduana\n"
     "contado c eisso 2 aduana\n"
     "contado d eisso abreportamala a maisbarato b fechaportamala dobradinha c aduana\n"
     "tnirp abreportamala d fechaportamala aduana",
     ["16"]),

    ("contado misturado com quebrado",
     "quebrado q eisso 10 aduana\n"
     "q eisso q sumiu 0.5 aduana\n"
     "tnirp abreportamala q fechaportamala aduana\n"
     "tnirp abreportamala 7 divideai 2 fechaportamala aduana",
     ["9.5", "3.5"]),

    ("comparacoes e logica",
     "contado x eisso 5 aduana\n"
     "tnirp abreportamala x estourou 3 levajunto x achatou 10 fechaportamala aduana\n"
     "tnirp abreportamala x pareceigual 4 ouentao x menoroumenos 4 fechaportamala aduana\n"
     "tnirp abreportamala naotem abreportamala x trocado 5 fechaportamala fechaportamala aduana\n"
     "tnirp abreportamala x maioroumais 5 fechaportamala aduana",
     ["1", "0", "1", "1"]),

    ("iph e ueuce",
     "contado x eisso 2 aduana\n"
     "iph abreportamala x pareceigual 1 fechaportamala abremochila\n"
     '    tnirp abreportamala "um" fechaportamala aduana\n'
     "fechamochila\n"
     "ueuce abremochila\n"
     '    tnirp abreportamala "outro" fechaportamala aduana\n'
     "fechamochila",
     ["outro"]),

    ("uaile",
     "contado i eisso 3 aduana\n"
     "uaile abreportamala i estourou 0 fechaportamala abremochila\n"
     "    tnirp abreportamala i fechaportamala aduana\n"
     "    i eisso i sumiu 1 aduana\n"
     "fechamochila",
     ["3", "2", "1"]),

    ("receita com argumentos de tipos diferentes",
     "receita quebrado media abreportamala quebrado a etambem contado b etambem quebrado c fechaportamala abremochila\n"
     "    galantia abreportamala a maisbarato b maisbarato c fechaportamala divideai 3 aduana\n"
     "fechamochila\n"
     "tnirp abreportamala media abreportamala 1.5 etambem 2 etambem 4.5 fechaportamala fechaportamala aduana",
     ["2.6666667"]),

    # Recursão: cada chamada tem o seu próprio n na pilha
    ("recursao (fatorial)",
     "receita contado fatorial abreportamala contado n fechaportamala abremochila\n"
     "    iph abreportamala n menoroumenos 1 fechaportamala abremochila\n"
     "        galantia 1 aduana\n"
     "    fechamochila\n"
     "    galantia n dobradinha fatorial abreportamala n sumiu 1 fechaportamala aduana\n"
     "fechamochila\n"
     "tnirp abreportamala fatorial abreportamala 5 fechaportamala fechaportamala aduana",
     ["120"]),

    ("recursao dupla (fibonacci)",
     "receita contado fib abreportamala contado n fechaportamala abremochila\n"
     "    iph abreportamala n achatou 2 fechaportamala abremochila\n"
     "        galantia n aduana\n"
     "    fechamochila\n"
     "    galantia fib abreportamala n sumiu 1 fechaportamala maisbarato "
     "fib abreportamala n sumiu 2 fechaportamala aduana\n"
     "fechamochila\n"
     "tnirp abreportamala fib abreportamala 10 fechaportamala fechaportamala aduana",
     ["55"]),

    ("receita semtroco",
     "receita semtroco avisa abreportamala etiqueta m fechaportamala abremochila\n"
     "    tnirp abreportamala m fechaportamala aduana\n"
     "fechamochila\n"
     "avisa abreportamala 'diz \"oi\"' fechaportamala aduana",
     ['diz "oi"']),
]

# O programa.pay de exemplo, do começo ao fim
SAIDA_PROGRAMA_PAY = [
    "eletronico barato",
    'vai pagar "imposto" pro fisco',
    "desconfia dessa encomenda",
    "imposto dobrado, sem nota",
    "731.0",
    "116.833336",
    "116.833336",
]


def confere(caminho_rars, descricao, codigo, esperado):
    saida, erros_rars = roda_no_rars(caminho_rars, assembly_do_codigo(codigo))
    if saida == esperado:
        print(f"ok   {descricao}")
        return 0
    print(f"FALHOU {descricao}")
    print("   esperado:", esperado)
    print("   saiu:    ", saida)
    if erros_rars:
        print("   RARS:    ", erros_rars.strip())
    return 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python testes_riscv.py caminho/do/rars1_6.jar")
        sys.exit(1)
    caminho_rars = sys.argv[1]

    falhas = 0
    for descricao, codigo, esperado in CASOS:
        falhas += confere(caminho_rars, descricao, codigo, esperado)

    with open("programa.pay", "r", encoding="utf-8") as arquivo:
        falhas += confere(caminho_rars, "programa.pay", arquivo.read(), SAIDA_PROGRAMA_PAY)

    print()
    print("Tudo certo!" if falhas == 0 else f"{falhas} teste(s) falharam")

# Exemplo simples: soma o preco com o frete e confere se passou do limite.

# Receita que recebe dois valores e devolve a soma
def somar(preco: float, frete: int) -> float:
    return preco + frete

# Variaveis com tipo: quebrado (float) e contado (int)
preco: float = 100.5
frete: int = 20
limite: int = 110

# Chama a receita e mostra o resultado
total: float = somar(preco, frete)
print(total)

# Se passou do limite paga imposto, senao passa liso
if total > limite:
    print("paga imposto")
else:
    print("passou liso")

# Conta de 1 ate 3
contador: int = 1
while contador <= 3:
    print(contador)
    contador = contador + 1

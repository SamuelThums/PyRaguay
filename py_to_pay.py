# O programa calcula o valor total da compra somando preço + frete
# e verifica se o valor ultrapassa o limite definido.

def calcular_total(preco, frete):
    # Soma o preço do produto com o frete
    total = preco + frete
    return total

# Exibe uma mensagem inicial
print("comprando eletronico barato")

# Define o preço do produto (com centavos, por isso o float)
preco = 350.5

# Define o limite usado para verificar a cobrança de imposto
limite = 300

# Define o valor do frete
frete = 15

# Calcula o valor total da compra usando a função
total = calcular_total(preco, frete)

# Guarda se a compra ultrapassou o limite
ultrapassou = total >= limite

# Se ultrapassou o limite e o frete nao ficou caro demais, cobra imposto
if ultrapassou == True and frete <= 20:
    print('vai pagar "imposto" pro fisco')
else:
    print("passou liso")

# Confere se o frete estourou o combinado ou o total ficou diferente do limite
if frete > 20 or total != limite:
    print("desconfia dessa encomenda")

# Se nao ultrapassou, e porque o preco achatou direitinho
if not ultrapassou:
    print("preco achatou direitinho")

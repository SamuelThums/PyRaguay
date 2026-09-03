# O programa calcula o valor total da compra somando preço + frete
# e verifica se o valor ultrapassa o limite definido.

# Exibe uma mensagem inicial
print("comprando eletronico barato")

# Define o preço do produto
preco = 350

# Define o limite usado para verificar a cobrança de imposto
limite = 300

# Define o valor do frete
frete = 15

# Calcula o valor total da compra: preço + frete
total = preco + frete

# Se o total for maior ou igual ao limite
if total >= limite:
    # Informa que a compra será taxada
    print("vai pagar imposto pro fisco")

# Caso contrário
else:
    # Informa que a compra passou sem imposto
    print("passou liso")

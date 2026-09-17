# O programa calcula o valor total da compra somando preço + frete
# e verifica se o valor ultrapassa o limite definido.

def calcular_total(preco: float, frete: float) -> float:
    # Soma o preço do produto com o frete
    total: float = preco + frete
    return total

# Anuncia a mercadoria em voz alta e nao devolve nada pra quem chamou
def anunciar(mensagem: str) -> None:
    print(mensagem)

# Nome que está escrito na etiqueta do produto
produto: str = "eletronico barato"

# Exibe uma mensagem inicial
anunciar(produto)

# Define o preço do produto (com centavos, por isso o float)
preco: float = 350.5

# Define o limite usado para verificar a cobrança de imposto
limite: int = 300

# Define o valor do frete
frete: int = 15

# Calcula o valor total da compra usando a função
total: float = calcular_total(preco, frete)

# Guarda se a compra ultrapassou o limite
ultrapassou: bool = total >= limite

# A mercadoria desceu a serra sem nota fiscal
tem_nota: bool = False

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

# Sem nota na mao, o fisco cobra o imposto dobrado
if tem_nota == False:
    imposto: float = total * 2
    anunciar("imposto dobrado, sem nota")
    print(imposto)

# Desconta o frete pra saber quanto custou so a mercadoria
mercadoria: float = total - frete

# Parcela o que sobrou em tres vezes, no olho
parcelas: int = 3
valor_parcela: float = mercadoria / parcelas

# Vai cantando cada parcela enquanto nao chegar na ultima
contador: int = 1
while contador < parcelas:
    print(valor_parcela)
    contador = contador + 1

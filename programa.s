.data
var_produto: .word 0
var_preco: .float 0.0
var_limite: .word 0
var_frete: .word 0
var_t2: .float 0.0
var_total: .float 0.0
var_t3: .word 0
var_ultrapassou: .word 0
var_tem_nota: .word 0
var_t4: .word 0
var_t5: .word 0
var_t6: .word 0
var_t7: .word 0
var_t8: .word 0
var_t9: .word 0
var_t10: .word 0
var_t11: .word 0
var_t12: .float 0.0
var_imposto: .float 0.0
var_t13: .float 0.0
var_mercadoria: .float 0.0
var_parcelas: .word 0
var_t14: .float 0.0
var_valor_parcela: .float 0.0
var_contador: .word 0
var_t15: .word 0
var_t16: .word 0
numero1: .float 350.5
texto1: .string "eletronico barato"
texto2: .string "vai pagar \"imposto\" pro fisco"
texto3: .string "passou liso"
texto4: .string "desconfia dessa encomenda"
texto5: .string "preco achatou direitinho"
texto6: .string "imposto dobrado, sem nota"

.text
.globl main
main:
    # produto = "eletronico barato"
    la t0, texto1
    la t6, var_produto
    sw t0, 0(t6)
    # call anunciar, 1
    la t6, var_produto
    lw a0, 0(t6)
    jal receita_anunciar
    # preco = 350.5
    la t6, numero1
    flw ft0, 0(t6)
    la t6, var_preco
    fsw ft0, 0(t6)
    # limite = 300
    li t0, 300
    la t6, var_limite
    sw t0, 0(t6)
    # frete = 15
    li t0, 15
    la t6, var_frete
    sw t0, 0(t6)
    # t2 = call calcular_total, 2
    la t6, var_preco
    flw fa0, 0(t6)
    la t6, var_frete
    lw t5, 0(t6)
    fcvt.s.w fa1, t5
    jal receita_calcular_total
    la t6, var_t2
    fsw fa0, 0(t6)
    # total = t2
    la t6, var_t2
    flw ft0, 0(t6)
    la t6, var_total
    fsw ft0, 0(t6)
    # t3 = total >= limite
    la t6, var_total
    flw ft0, 0(t6)
    la t6, var_limite
    lw t5, 0(t6)
    fcvt.s.w ft1, t5
    fle.s t0, ft1, ft0
    la t6, var_t3
    sw t0, 0(t6)
    # ultrapassou = t3
    la t6, var_t3
    lw t0, 0(t6)
    la t6, var_ultrapassou
    sw t0, 0(t6)
    # tem_nota = 0
    li t0, 0
    la t6, var_tem_nota
    sw t0, 0(t6)
    # t4 = ultrapassou == 1
    la t6, var_ultrapassou
    lw t0, 0(t6)
    li t1, 1
    sub t0, t0, t1
    seqz t0, t0
    la t6, var_t4
    sw t0, 0(t6)
    # t5 = frete <= 20
    la t6, var_frete
    lw t0, 0(t6)
    li t1, 20
    slt t0, t1, t0
    xori t0, t0, 1
    la t6, var_t5
    sw t0, 0(t6)
    # t6 = t4 and t5
    la t6, var_t4
    lw t0, 0(t6)
    la t6, var_t5
    lw t1, 0(t6)
    and t0, t0, t1
    la t6, var_t6
    sw t0, 0(t6)
    # ifFalse t6 goto L1
    la t6, var_t6
    lw t0, 0(t6)
    beqz t0, L1
    # print 'vai pagar "imposto" pro fisco'
    la a0, texto2
    li a7, 4
    ecall
    li a0, 10
    li a7, 11
    ecall
    # goto L2
    j L2
L1:
    # print "passou liso"
    la a0, texto3
    li a7, 4
    ecall
    li a0, 10
    li a7, 11
    ecall
L2:
    # t7 = frete > 20
    la t6, var_frete
    lw t0, 0(t6)
    li t1, 20
    slt t0, t1, t0
    la t6, var_t7
    sw t0, 0(t6)
    # t8 = total != limite
    la t6, var_total
    flw ft0, 0(t6)
    la t6, var_limite
    lw t5, 0(t6)
    fcvt.s.w ft1, t5
    feq.s t0, ft0, ft1
    xori t0, t0, 1
    la t6, var_t8
    sw t0, 0(t6)
    # t9 = t7 or t8
    la t6, var_t7
    lw t0, 0(t6)
    la t6, var_t8
    lw t1, 0(t6)
    or t0, t0, t1
    la t6, var_t9
    sw t0, 0(t6)
    # ifFalse t9 goto L3
    la t6, var_t9
    lw t0, 0(t6)
    beqz t0, L3
    # print "desconfia dessa encomenda"
    la a0, texto4
    li a7, 4
    ecall
    li a0, 10
    li a7, 11
    ecall
L3:
    # t10 = not ultrapassou
    la t6, var_ultrapassou
    lw t0, 0(t6)
    seqz t0, t0
    la t6, var_t10
    sw t0, 0(t6)
    # ifFalse t10 goto L4
    la t6, var_t10
    lw t0, 0(t6)
    beqz t0, L4
    # print "preco achatou direitinho"
    la a0, texto5
    li a7, 4
    ecall
    li a0, 10
    li a7, 11
    ecall
L4:
    # t11 = tem_nota == 0
    la t6, var_tem_nota
    lw t0, 0(t6)
    li t1, 0
    sub t0, t0, t1
    seqz t0, t0
    la t6, var_t11
    sw t0, 0(t6)
    # ifFalse t11 goto L5
    la t6, var_t11
    lw t0, 0(t6)
    beqz t0, L5
    # t12 = total * 2
    la t6, var_total
    flw ft0, 0(t6)
    li t5, 2
    fcvt.s.w ft1, t5
    fmul.s ft0, ft0, ft1
    la t6, var_t12
    fsw ft0, 0(t6)
    # imposto = t12
    la t6, var_t12
    flw ft0, 0(t6)
    la t6, var_imposto
    fsw ft0, 0(t6)
    # call anunciar, 1
    la a0, texto6
    jal receita_anunciar
    # print imposto
    la t6, var_imposto
    flw fa0, 0(t6)
    li a7, 2
    ecall
    li a0, 10
    li a7, 11
    ecall
L5:
    # t13 = total - frete
    la t6, var_total
    flw ft0, 0(t6)
    la t6, var_frete
    lw t5, 0(t6)
    fcvt.s.w ft1, t5
    fsub.s ft0, ft0, ft1
    la t6, var_t13
    fsw ft0, 0(t6)
    # mercadoria = t13
    la t6, var_t13
    flw ft0, 0(t6)
    la t6, var_mercadoria
    fsw ft0, 0(t6)
    # parcelas = 3
    li t0, 3
    la t6, var_parcelas
    sw t0, 0(t6)
    # t14 = mercadoria / parcelas
    la t6, var_mercadoria
    flw ft0, 0(t6)
    la t6, var_parcelas
    lw t5, 0(t6)
    fcvt.s.w ft1, t5
    fdiv.s ft0, ft0, ft1
    la t6, var_t14
    fsw ft0, 0(t6)
    # valor_parcela = t14
    la t6, var_t14
    flw ft0, 0(t6)
    la t6, var_valor_parcela
    fsw ft0, 0(t6)
    # contador = 1
    li t0, 1
    la t6, var_contador
    sw t0, 0(t6)
L6:
    # t15 = contador < parcelas
    la t6, var_contador
    lw t0, 0(t6)
    la t6, var_parcelas
    lw t1, 0(t6)
    slt t0, t0, t1
    la t6, var_t15
    sw t0, 0(t6)
    # ifFalse t15 goto L7
    la t6, var_t15
    lw t0, 0(t6)
    beqz t0, L7
    # print valor_parcela
    la t6, var_valor_parcela
    flw fa0, 0(t6)
    li a7, 2
    ecall
    li a0, 10
    li a7, 11
    ecall
    # t16 = contador + 1
    la t6, var_contador
    lw t0, 0(t6)
    li t1, 1
    add t0, t0, t1
    la t6, var_t16
    sw t0, 0(t6)
    # contador = t16
    la t6, var_t16
    lw t0, 0(t6)
    la t6, var_contador
    sw t0, 0(t6)
    # goto L6
    j L6
L7:
    # fim
    li a7, 10
    ecall

receita_calcular_total:
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    addi s0, sp, 32
    fsw fa0, -12(s0)
    fsw fa1, -16(s0)
    # t1 = preco + frete
    flw ft0, -12(s0)
    flw ft1, -16(s0)
    fadd.s ft0, ft0, ft1
    fsw ft0, -20(s0)
    # total = t1
    flw ft0, -20(s0)
    fsw ft0, -24(s0)
    # return total
    flw fa0, -24(s0)
    lw ra, -4(s0)
    mv sp, s0
    lw s0, -8(s0)
    ret

receita_anunciar:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    addi s0, sp, 16
    sw a0, -12(s0)
    # print mensagem
    lw a0, -12(s0)
    li a7, 4
    ecall
    li a0, 10
    li a7, 11
    ecall
    # return
    lw ra, -4(s0)
    mv sp, s0
    lw s0, -8(s0)
    ret

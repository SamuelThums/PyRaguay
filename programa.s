.data
var_preco: .float 0.0
var_frete: .word 0
var_limite: .word 0
var_t2: .float 0.0
var_total: .float 0.0
var_t3: .word 0
var_contador: .word 0
var_t4: .word 0
var_t5: .word 0
numero1: .float 100.5
texto1: .string "paga imposto"
texto2: .string "passou liso"

.text
.globl main
main:
    # preco = 100.5
    la t6, numero1
    flw ft0, 0(t6)
    la t6, var_preco
    fsw ft0, 0(t6)
    # frete = 20
    li t0, 20
    la t6, var_frete
    sw t0, 0(t6)
    # limite = 110
    li t0, 110
    la t6, var_limite
    sw t0, 0(t6)
    # t2 = call somar, 2
    la t6, var_preco
    flw fa0, 0(t6)
    la t6, var_frete
    lw a0, 0(t6)
    jal receita_somar
    la t6, var_t2
    fsw fa0, 0(t6)
    # total = t2
    la t6, var_t2
    flw ft0, 0(t6)
    la t6, var_total
    fsw ft0, 0(t6)
    # print total
    la t6, var_total
    flw fa0, 0(t6)
    li a7, 2
    ecall
    li a0, 10
    li a7, 11
    ecall
    # t3 = total > limite
    la t6, var_total
    flw ft0, 0(t6)
    la t6, var_limite
    lw t5, 0(t6)
    fcvt.s.w ft1, t5
    flt.s t0, ft1, ft0
    la t6, var_t3
    sw t0, 0(t6)
    # ifFalse t3 goto L1
    la t6, var_t3
    lw t0, 0(t6)
    beqz t0, L1
    # print "paga imposto"
    la a0, texto1
    li a7, 4
    ecall
    li a0, 10
    li a7, 11
    ecall
    # goto L2
    j L2
L1:
    # print "passou liso"
    la a0, texto2
    li a7, 4
    ecall
    li a0, 10
    li a7, 11
    ecall
L2:
    # contador = 1
    li t0, 1
    la t6, var_contador
    sw t0, 0(t6)
L3:
    # t4 = contador <= 3
    la t6, var_contador
    lw t0, 0(t6)
    li t1, 3
    slt t0, t1, t0
    xori t0, t0, 1
    la t6, var_t4
    sw t0, 0(t6)
    # ifFalse t4 goto L4
    la t6, var_t4
    lw t0, 0(t6)
    beqz t0, L4
    # print contador
    la t6, var_contador
    lw a0, 0(t6)
    li a7, 1
    ecall
    li a0, 10
    li a7, 11
    ecall
    # t5 = contador + 1
    la t6, var_contador
    lw t0, 0(t6)
    li t1, 1
    add t0, t0, t1
    la t6, var_t5
    sw t0, 0(t6)
    # contador = t5
    la t6, var_t5
    lw t0, 0(t6)
    la t6, var_contador
    sw t0, 0(t6)
    # goto L3
    j L3
L4:
    # fim
    li a7, 10
    ecall

receita_somar:
    addi sp, sp, -32
    sw ra, 28(sp)
    sw s0, 24(sp)
    addi s0, sp, 32
    fsw fa0, -12(s0)
    sw a0, -16(s0)
    # t1 = preco + frete
    flw ft0, -12(s0)
    lw t5, -16(s0)
    fcvt.s.w ft1, t5
    fadd.s ft0, ft0, ft1
    fsw ft0, -20(s0)
    # return t1
    flw fa0, -20(s0)
    lw ra, -4(s0)
    mv sp, s0
    lw s0, -8(s0)
    ret

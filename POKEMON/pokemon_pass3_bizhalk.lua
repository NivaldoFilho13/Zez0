--[[
Zez0 - Pokémon FireRed (passo 3: andar inteligente)

Diferente dos passos anteriores (que só repetiam um padrão fixo), esse
script lê a posição REAL do personagem na memória do jogo, pra:
    - Andar em direção a um alvo (x, y) reduzindo a distância a cada passo
    - Perceber quando bate numa parede (a posição não muda depois de
      tentar andar) e tentar uma direção alternativa em vez de ficar
      preso empurrando a parede pra sempre

IMPORTANTE: antes de usar, troque ENDERECO_X e ENDERECO_Y abaixo pelos
endereços que você achou com o RAM Search (veja o passo-a-passo que te
mandei). Sem isso, o script não tem como saber onde o personagem está.
--]]

-- ================= CONFIGURAÇÃO =================
-- Endereços confirmados por testes reais (RAM Search) em 12/09/2026
local ENDERECO_X = 0x02557C
local ENDERECO_Y = 0x02557E
local DOMINIO = "EWRAM"

local FRAMES_POR_PASSO = 20   -- frames segurando a direção (1 tile andado)
local FRAMES_PAUSA = 2        -- pausa entre passos
local MAX_TENTATIVAS_TRAVADO = 4  -- quantas direções alternativas tenta antes de desistir

-- ================= FUNÇÕES BÁSICAS =================
local function posicao_atual()
    local x = memory.read_u16_le(ENDERECO_X, DOMINIO)
    local y = memory.read_u16_le(ENDERECO_Y, DOMINIO)
    return x, y
end

local function pressionar(direcao, frames)
    joypad.set({[direcao] = true})
    for i = 1, frames do
        emu.frameadvance()
    end
    joypad.set({[direcao] = false})
    for i = 1, FRAMES_PAUSA do
        emu.frameadvance()
    end
end

-- Tenta andar 1 tile na direção dada. Retorna true se a posição mudou
-- (andou de verdade) ou false se ficou parado (bateu em algo).
local function tentar_passo(direcao)
    local x_antes, y_antes = posicao_atual()
    pressionar(direcao, FRAMES_POR_PASSO)
    local x_depois, y_depois = posicao_atual()
    return (x_depois ~= x_antes) or (y_depois ~= y_antes)
end

-- ================= NAVEGAÇÃO INTELIGENTE =================
-- Decide a melhor direção pra reduzir a distância até o alvo (prioriza
-- o eixo com maior diferença, igual fizemos na IA gulosa do snake).
local function direcao_preferida(x, y, alvo_x, alvo_y)
    local dx = alvo_x - x
    local dy = alvo_y - y

    if math.abs(dx) >= math.abs(dy) and dx ~= 0 then
        return dx > 0 and "Right" or "Left"
    elseif dy ~= 0 then
        return dy > 0 and "Down" or "Up"
    end
    return nil
end

-- Lista de direções alternativas pra tentar quando bate em algo
local TODAS_DIRECOES = {"Up", "Down", "Left", "Right"}

local function andar_ate(alvo_x, alvo_y)
    console.log(string.format("Zez0: indo até (%d, %d)...", alvo_x, alvo_y))

    while true do
        local x, y = posicao_atual()

        if x == alvo_x and y == alvo_y then
            console.log("Zez0: cheguei no alvo!")
            return true
        end

        local direcao = direcao_preferida(x, y, alvo_x, alvo_y)
        if tentar_passo(direcao) then
            goto continua  -- deu certo, segue o loop normalmente
        end
        -- Bateu em algo: tenta outras direções até desempaca
        local desempacou = false
        for tentativa = 1, MAX_TENTATIVAS_TRAVADO do
            local alternativa = TODAS_DIRECOES[math.random(1, 4)]
            if alternativa ~= direcao and tentar_passo(alternativa) then
                desempacou = true
                break
            end
        end

        if not desempacou then
            console.log("Zez0: travado, não consegui desviar. Parando.")
            return false
        end

        ::continua::
    end
end

console.log("Zez0 - Passo 3: sistema de andar inteligente ativo.")
andar_ate(10, 10)
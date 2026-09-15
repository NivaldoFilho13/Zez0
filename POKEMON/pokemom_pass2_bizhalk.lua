local FRAMES_POR_PASSO = 20  
local FRAMES_PAUSA = 2      

local function andar(direcao, quantidade_passos)
    for _ = 1, quantidade_passos do
        joypad.set({[direcao] = true})
        for i = 1, FRAMES_POR_PASSO do
            emu.frameadvance()
        end
        joypad.set({[direcao] = false})
        for i = 1, FRAMES_PAUSA do
            emu.frameadvance()
        end
    end
end

console.log("Zez0 - Passo 2: andando em círculo (testando as 4 direções)...")

while true do
    andar("Right", 3)
    andar("Down", 3)
    andar("Left", 3)
    andar("Up", 3)
end
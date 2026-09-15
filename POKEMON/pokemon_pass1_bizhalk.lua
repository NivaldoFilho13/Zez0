local FRAMES_SEGURANDO = 4  
local FRAMES_SOLTO = 10     

console.log("Zez0 - Passo 1: apertando A repetidamente para avançar diálogos...")

while true do
    joypad.set({["A"] = true})
    for i = 1, FRAMES_SEGURANDO do
        emu.frameadvance()
    end

    joypad.set({["A"] = false})
    for i = 1, FRAMES_SOLTO do
        emu.frameadvance()
    end
end
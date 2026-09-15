local ENDERECO_X = 0x02557C
local ENDERECO_Y = 0x02557E
local ENDERECO_MAPA = 0x036E0E
local ENDERECO_BATALHA = nil 
local DOMINIO = "EWRAM"

local FRAMES_POR_PASSO = 20
local FRAMES_PAUSA = 2
local LIMITE_CUTSCENE = 2  
local CICLOS_AQUECIMENTO_INICIO = 15  


local ARQUIVO_MEMORIA = "zez0_memoria.txt"


local function dividir(texto, separador)
    local partes = {}
    for parte in texto:gmatch("([^" .. separador .. "]+)") do
        table.insert(partes, parte)
    end
    return partes
end

local function registrar_no_arquivo(linha)
    local arq = io.open(ARQUIVO_MEMORIA, "a")
    if arq then
        arq:write(linha .. "\n")
        arq:close()
    end
end


local ultimo_x_valido, ultimo_y_valido, ultimo_mapa_valido = 0, 0, 0

local function posicao_atual()
    local ok_x, x = pcall(memory.read_u16_le, ENDERECO_X, DOMINIO)
    local ok_y, y = pcall(memory.read_u16_le, ENDERECO_Y, DOMINIO)

    if ok_x and x ~= nil then
        ultimo_x_valido = x
    else
        x = ultimo_x_valido
    end

    if ok_y and y ~= nil then
        ultimo_y_valido = y
    else
        y = ultimo_y_valido
    end

    return x, y
end

local function mapa_atual()
    local ok, m = pcall(memory.read_u8, ENDERECO_MAPA, DOMINIO)
    if ok and m ~= nil then
        ultimo_mapa_valido = m
    end
    return ultimo_mapa_valido
end

local function pressionar(direcao, frames)
    for i = 1, frames do
        joypad.set({[direcao] = true})
        emu.frameadvance()
    end
    for i = 1, FRAMES_PAUSA do
        joypad.set({[direcao] = false})
        emu.frameadvance()
    end
end

local function chave(x, y)
    return x .. "," .. y
end

local DIRECOES = {
    {nome = "Right", dx = 1, dy = 0},
    {nome = "Left", dx = -1, dy = 0},
    {nome = "Down", dx = 0, dy = 1},
    {nome = "Up", dx = 0, dy = -1},
}

local function embaralhar(lista)
    for i = #lista, 2, -1 do
        local j = math.random(i)
        lista[i], lista[j] = lista[j], lista[i]
    end
end


local pontuacao_total = 0
local PONTOS_POR_TILE_NOVO = 1
local PONTOS_POR_INTERACAO_NOVA = 5
local ultimo_marco_avisado = 0
local INTERVALO_MARCO = 50 

local function somar_pontos(quantidade)
    pontuacao_total = pontuacao_total + quantidade
    if pontuacao_total - ultimo_marco_avisado >= INTERVALO_MARCO then
        ultimo_marco_avisado = pontuacao_total
        console.log(string.format("Zez0: %d pontos de progresso até agora!", pontuacao_total))
    end
end
local visitados = {}   
local paredes = {}    
local mapa_carregado = nil 

local function marcar_visitado(x, y)
    local k = chave(x, y)
    if not visitados[k] then
        visitados[k] = true
        registrar_no_arquivo(string.format("VISITADO|%d|%d|%d", mapa_carregado, x, y))
        somar_pontos(PONTOS_POR_TILE_NOVO)
    end
end

local function marcar_parede(x, y, direcao)
    local k = chave(x, y) .. "|" .. direcao
    if not paredes[k] then
        paredes[k] = true
        registrar_no_arquivo(string.format("PAREDE|%d|%d|%d|%s", mapa_carregado, x, y, direcao))
    end
end


local function desmarcar_parede(x, y, direcao)
    local k = chave(x, y) .. "|" .. direcao
    if paredes[k] then
        paredes[k] = nil
        registrar_no_arquivo(string.format("PAREDE_REMOVIDA|%d|%d|%d|%s", mapa_carregado, x, y, direcao))
        console.log(string.format(
            "Zez0: corrigindo a memória — (%d,%d) [%s] não é parede de verdade, removendo.", x, y, direcao
        ))
    end
end

local function eh_parede_conhecida(x, y, direcao)
    return paredes[chave(x, y) .. "|" .. direcao] == true
end


local pontos_interacao = {}  -
local saidas = {} 
local saidas_registradas = {} 
local mapas_conhecidos = {}  
local function carregar_memoria_do_mapa(mapa_id)
    visitados = {}
    paredes = {}
    pontos_interacao = {}
    saidas = {}
    saidas_registradas = {}
    mapa_carregado = mapa_id

    local mapa_ja_registrado = false
    local arq = io.open(ARQUIVO_MEMORIA, "r")

    if arq then
        local total_visitados, total_paredes, total_interacoes, total_saidas = 0, 0, 0, 0
        for linha in arq:lines() do
            local partes = dividir(linha, "|")

            if partes[1] == "MAPA_VISITADO" and partes[2] then
                local id_lido = tonumber(partes[2])
                if id_lido then
                    mapas_conhecidos[id_lido] = true
                    if id_lido == mapa_id then
                        mapa_ja_registrado = true
                    end
                end
            elseif partes[1] == "VISITADO" and partes[2] and partes[3] and partes[4] then
                local m, vx, vy = tonumber(partes[2]), tonumber(partes[3]), tonumber(partes[4])
                if m == mapa_id and vx and vy then
                    visitados[chave(vx, vy)] = true
                    total_visitados = total_visitados + 1
                end
            elseif partes[1] == "PAREDE" and partes[2] and partes[3] and partes[4] and partes[5] then
                local m, px, py = tonumber(partes[2]), tonumber(partes[3]), tonumber(partes[4])
                if m == mapa_id and px and py then
                    paredes[chave(px, py) .. "|" .. partes[5]] = true
                    total_paredes = total_paredes + 1
                end
            elseif partes[1] == "PAREDE_REMOVIDA" and partes[2] and partes[3] and partes[4] and partes[5] then
                local m, px, py = tonumber(partes[2]), tonumber(partes[3]), tonumber(partes[4])
                if m == mapa_id and px and py then
                    paredes[chave(px, py) .. "|" .. partes[5]] = nil
                    total_paredes = total_paredes - 1
                end
            elseif partes[1] == "INTERACAO" and partes[2] and partes[3] and partes[4] and partes[5] then
                local m, ix, iy, idir = tonumber(partes[2]), tonumber(partes[3]), tonumber(partes[4]), partes[5]
                if m == mapa_id and ix and iy then
                    table.insert(pontos_interacao, {x = ix, y = iy, direcao = idir})
                    total_interacoes = total_interacoes + 1
                end
            elseif partes[1] == "SAIDA" and partes[2] and partes[3] and partes[4] and partes[5] and partes[6] then
                local m, sx, sy, sdestino = tonumber(partes[2]), tonumber(partes[3]), tonumber(partes[4]), tonumber(partes[6])
                if m == mapa_id and sx and sy and sdestino then
                    table.insert(saidas, {x = sx, y = sy, direcao = partes[5], destino = sdestino})
                    saidas_registradas[chave(sx, sy) .. "|" .. partes[5]] = true
                    total_saidas = total_saidas + 1
                end
            end
            
        end
        arq:close()

        console.log(string.format(
            "Zez0: mapa %d carregado (%d tiles, %d paredes, %d interações, %d saídas conhecidas).",
            mapa_id, total_visitados, total_paredes, total_interacoes, total_saidas
        ))
    else
        console.log(string.format("Zez0: mapa %d ainda não tem memória salva, começando do zero.", mapa_id))
    end

    if not mapa_ja_registrado then
        mapas_conhecidos[mapa_id] = true
        registrar_no_arquivo(string.format("MAPA_VISITADO|%d", mapa_id))
        console.log(string.format("Zez0: mapa %d é novo, registrando na memória de mapas.", mapa_id))
    end
end


local function registrar_saida(x, y, direcao_nome, mapa_origem)
    local destino = mapa_atual()
    local k = chave(x, y) .. "|" .. direcao_nome
    if not saidas_registradas[k] then
        saidas_registradas[k] = true
        table.insert(saidas, {x = x, y = y, direcao = direcao_nome, destino = destino})
        registrar_no_arquivo(string.format("SAIDA|%d|%d|%d|%s|%d", mapa_origem, x, y, direcao_nome, destino))
        console.log(string.format("Zez0: descobri uma saída em (%d,%d) [%s] -> mapa %d! Registrada.", x, y, direcao_nome, destino))
    end
end

local ultima_posicao = nil
local contador_sem_progresso = 0


local function tentar_mover(direcao_nome, dx, dy, x, y, eh_caminho_conhecido)
    pressionar(direcao_nome, FRAMES_POR_PASSO)
    local novo_x, novo_y = posicao_atual()

    if novo_x == x and novo_y == y then
        pressionar(direcao_nome, FRAMES_POR_PASSO)
        novo_x, novo_y = posicao_atual()
    end

    local esperado_x, esperado_y = x + dx, y + dy

    if novo_x == esperado_x and novo_y == esperado_y then
        desmarcar_parede(x, y, direcao_nome)  
        return true, novo_x, novo_y, false
    elseif novo_x == x and novo_y == y then
        
        for i = 1, 3 do
            pressionar("A", FRAMES_POR_PASSO)
        end
        pressionar(direcao_nome, FRAMES_POR_PASSO)
        novo_x, novo_y = posicao_atual()

        if novo_x == esperado_x and novo_y == esperado_y then
            desmarcar_parede(x, y, direcao_nome)
            registrar_no_arquivo(string.format("INTERACAO|%d|%d|%d|%s", mapa_carregado, x, y, direcao_nome))
            somar_pontos(PONTOS_POR_INTERACAO_NOVA)
            console.log(string.format("Zez0: tinha uma interação em (%d,%d), resolvida com A. Registrada na memória.", x, y))
            return true, novo_x, novo_y, false
        end

        if eh_caminho_conhecido then
            
            for tentativa = 1, 2 do
                for i = 1, FRAMES_POR_PASSO do
                    emu.frameadvance()
                end
                pressionar(direcao_nome, FRAMES_POR_PASSO)
                novo_x, novo_y = posicao_atual()
                if novo_x == esperado_x and novo_y == esperado_y then
                    desmarcar_parede(x, y, direcao_nome)
                    return true, novo_x, novo_y, false
                end
            end
            console.log(string.format(
                "Zez0: algo (talvez alguém em movimento) está bloqueando o caminho perto de (%d,%d).", x, y
            ))
            return false, x, y, false
        else
            marcar_parede(x, y, direcao_nome)
            return false, x, y, false
        end
    else
        registrar_saida(x, y, direcao_nome, mapa_carregado)
        return true, novo_x, novo_y, true  
    end
end


local MAX_CICLOS_CUTSCENE = 5

local function lidar_com_cutscene(x, y)
    console.log("Zez0: nada muda em nenhuma direção mesmo testando — parece cutscene de verdade. Tentando destravar...")
    registrar_no_arquivo(string.format("TRANSICAO|%d|%d|%d", mapa_carregado, x, y))

    for ciclo = 1, MAX_CICLOS_CUTSCENE do
        
        for i = 1, 10 do
            pressionar("A", FRAMES_POR_PASSO)
            local nx, ny = posicao_atual()
            if nx ~= x or ny ~= y then
                console.log("Zez0: liberado com A, voltando a explorar.")
                return
            end
        end

        
        for i = 1, 5 do
            pressionar("B", FRAMES_POR_PASSO)
            local nx, ny = posicao_atual()
            if nx ~= x or ny ~= y then
                console.log("Zez0: liberado com B, voltando a explorar.")
                return
            end
        end

        
        local qualquer = DIRECOES[math.random(1, 4)]
        pressionar(qualquer.nome, FRAMES_POR_PASSO)
        local nx, ny = posicao_atual()
        if nx ~= x or ny ~= y then
            console.log("Zez0: consegui andar de novo, voltando a explorar.")
            return
        end

        console.log(string.format("Zez0: ciclo %d/%d sem sucesso, tentando de novo...", ciclo, MAX_CICLOS_CUTSCENE))
    end

    
    console.log("Zez0: tentei bastante (A/B várias vezes) e ainda travado. Marcando esse ponto como sem saída conhecida.")
    for _, d in ipairs(DIRECOES) do
        marcar_parede(x, y, d.nome)
    end
end


local function encontrar_caminho_para_fronteira(x0, y0)
    local fila = {{x = x0, y = y0}}
    local veio_de = {}
    local visto = {[chave(x0, y0)] = true}
    local cabeca = 1

    while cabeca <= #fila do
        local atual = fila[cabeca]
        cabeca = cabeca + 1

        for _, d in ipairs(DIRECOES) do
            if not eh_parede_conhecida(atual.x, atual.y, d.nome) then
                local nx, ny = atual.x + d.dx, atual.y + d.dy

                if not visitados[chave(nx, ny)] then
                   
                    local caminho = {}
                    local passo = atual
                    while passo.x ~= x0 or passo.y ~= y0 do
                        local info = veio_de[chave(passo.x, passo.y)]
                        table.insert(caminho, 1, info.dir)
                        passo = {x = info.x, y = info.y}
                    end
                    return caminho, d.nome
                elseif not visto[chave(nx, ny)] then
                    visto[chave(nx, ny)] = true
                    veio_de[chave(nx, ny)] = {x = atual.x, y = atual.y, dir = d.nome}
                    table.insert(fila, {x = nx, y = ny})
                end
            end
        end
    end

    return nil  
end

local function direcao_por_nome(nome)
    for _, d in ipairs(DIRECOES) do
        if d.nome == nome then return d end
    end
end


local function encontrar_caminho_para_ponto(x0, y0, alvo_x, alvo_y)
    if x0 == alvo_x and y0 == alvo_y then return {} end

    local fila = {{x = x0, y = y0}}
    local veio_de = {}
    local visto = {[chave(x0, y0)] = true}
    local cabeca = 1

    while cabeca <= #fila do
        local atual = fila[cabeca]
        cabeca = cabeca + 1

        for _, d in ipairs(DIRECOES) do
            if not eh_parede_conhecida(atual.x, atual.y, d.nome) then
                local nx, ny = atual.x + d.dx, atual.y + d.dy

                if nx == alvo_x and ny == alvo_y then
                    local caminho = {d.nome}
                    local passo = atual
                    while passo.x ~= x0 or passo.y ~= y0 do
                        local info = veio_de[chave(passo.x, passo.y)]
                        table.insert(caminho, 1, info.dir)
                        passo = {x = info.x, y = info.y}
                    end
                    return caminho
                elseif visitados[chave(nx, ny)] and not visto[chave(nx, ny)] then
                    visto[chave(nx, ny)] = true
                    veio_de[chave(nx, ny)] = {x = atual.x, y = atual.y, dir = d.nome}
                    table.insert(fila, {x = nx, y = ny})
                end
            end
        end
    end

    return nil
end


local function encontrar_melhor_saida(x0, y0)
    for _, s in ipairs(saidas) do
        if not mapas_conhecidos[s.destino] then
            local caminho = encontrar_caminho_para_ponto(x0, y0, s.x, s.y)
            if caminho then
                return caminho, s.direcao, true
            end
        end
    end

    for _, s in ipairs(saidas) do
        local caminho = encontrar_caminho_para_ponto(x0, y0, s.x, s.y)
        if caminho then
            return caminho, s.direcao, false
        end
    end

    return nil
end


local function aguardar_inicio_do_jogo()
    console.log("Zez0: tentando passar da tela de título / início do jogo...")
    for ciclo = 1, CICLOS_AQUECIMENTO_INICIO do
        pressionar("A", FRAMES_POR_PASSO)
    end
    console.log("Zez0: aquecimento concluído, seguindo para exploração.")
end


console.log("Zez0 - Passo 4 v3: exploração com memória por mapa iniciada.")
aguardar_inicio_do_jogo()
carregar_memoria_do_mapa(mapa_atual())

while true do
    local mapa_id_agora = mapa_atual()
    if mapa_id_agora ~= mapa_carregado then
        console.log(string.format("Zez0: mudei do mapa %d pro mapa %d!", mapa_carregado, mapa_id_agora))
        carregar_memoria_do_mapa(mapa_id_agora)
        ultima_posicao = nil
        contador_sem_progresso = 0
    end

    local x, y = posicao_atual()
    marcar_visitado(x, y)

    if ultima_posicao and ultima_posicao.x == x and ultima_posicao.y == y then
        contador_sem_progresso = contador_sem_progresso + 1
    else
        contador_sem_progresso = 0
    end
    ultima_posicao = {x = x, y = y}

    if contador_sem_progresso >= LIMITE_CUTSCENE then
        
        local direcoes_teste = {}
        for _, d in ipairs(DIRECOES) do
            table.insert(direcoes_teste, d)
        end
        embaralhar(direcoes_teste)

        local moveu_no_teste = false
        for _, d in ipairs(direcoes_teste) do
            local sucesso = tentar_mover(d.nome, d.dx, d.dy, x, y, true)
            if sucesso then
                moveu_no_teste = true
                break
            end
        end

        if not moveu_no_teste then
            lidar_com_cutscene(x, y)
        end
        contador_sem_progresso = 0
    else
        
    local candidatos = {}
    for _, d in ipairs(DIRECOES) do
        if not eh_parede_conhecida(x, y, d.nome) then
            local nx, ny = x + d.dx, y + d.dy
            if not visitados[chave(nx, ny)] then
                table.insert(candidatos, d)
            end
        end
    end
    embaralhar(candidatos)

    local moveu = false
    for _, d in ipairs(candidatos) do
        local sucesso = tentar_mover(d.nome, d.dx, d.dy, x, y, false)
        if sucesso then
            moveu = true
            break
        end
    end

    if not moveu and math.random(1, 4) == 1 then
        local direcoes_paredes = {}
        for _, d in ipairs(DIRECOES) do
            if eh_parede_conhecida(x, y, d.nome) then
                table.insert(direcoes_paredes, d)
            end
        end
        embaralhar(direcoes_paredes)

        for _, d in ipairs(direcoes_paredes) do
            local sucesso = tentar_mover(d.nome, d.dx, d.dy, x, y, false)
            if sucesso then
                moveu = true
                break
            end
        end
    end

    if not moveu then
        local caminho, direcao_final = encontrar_caminho_para_fronteira(x, y)

        if caminho then
            console.log(string.format("Zez0: indo até uma área não explorada (%d passos)...", #caminho))
            for _, nome_dir in ipairs(caminho) do
                local px, py = posicao_atual()
                local d = direcao_por_nome(nome_dir)
                tentar_mover(d.nome, d.dx, d.dy, px, py, true)
            end
            moveu = true
        else

            local caminho_saida, direcao_saida, eh_mapa_novo = encontrar_melhor_saida(x, y)

            if caminho_saida then
                if eh_mapa_novo then
                    console.log("Zez0: mapa totalmente explorado! Indo até uma saída pra um lugar novo...")
                else
                    console.log("Zez0: mapa totalmente explorado! Indo até uma saída conhecida (todas levam a lugares já visitados).")
                end

                for _, nome_dir in ipairs(caminho_saida) do
                    local px, py = posicao_atual()
                    local d = direcao_por_nome(nome_dir)
                    tentar_mover(d.nome, d.dx, d.dy, px, py, true)
                end

                local px, py = posicao_atual()
                local d = direcao_por_nome(direcao_saida)
                tentar_mover(d.nome, d.dx, d.dy, px, py, true)
            else
                console.log("Zez0: explorei tudo que consegui alcançar e ainda não achei nenhuma saída daqui.")
            end
        end
    end
    end
end

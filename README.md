# Zez0

Zez0 é um projeto de IA criado para jogar jogos, aprendendo e explorando
sozinho a cada partida.

## Jogos em Python (pygame)

### Snake

- **`snake.py`** — IA gulosa (greedy): sempre se move em direção à
  comida, evitando parede e o próprio corpo. Não aprende, só segue regras.

```
pip install pygame
python snake.py
```

### Campo minado

- **`campo_minado.py`** — joga usando só dedução lógica 100% certa.

```
pip install pygame
python campo_minado.py
```

### Pac-Man

- **`pacman.py`** — mapa fixo com 4 power pellets. Usa BFS pra
  comer bolinhas evitando fantasmas; ao comer um power pellet, os
  fantasmas ficam assustados por 10 segundos e a IA aproveita pra
  persegui-los e ganhar pontos bônus.

```
pip install pygame
python pacman.py
```

## Automação de Pokémon Fire Red (BizHawk + Lua)

Módulo mais avançado do Zez0: em vez de rodar dentro do próprio script
Python, ele controla um jogo de verdade rodando num emulador, através
de scripts Lua.

- **`pokemon_passo1.lua`** — primeiro teste de controle:
  aperta A repetidamente pra confirmar que o script consegue mandar
  comandos pro emulador.
- **`pokemon_passo2.lua`** — testa o controle direcional,
  andando em círculo.
- **`pokemon_passo3.lua`** — lê a posição real
  do personagem (via leitura de memória do emulador) e anda até uma
  coordenada específica, desviando de obstáculos.
- **`pokemon_passo4.lua`** — versão atual e mais
  completa. Explora o mapa sozinho, sem repetir lugares, com memória
  persistente em arquivo (`zez0_memoria.txt`) separada por mapa:
  tiles visitados, paredes conhecidas (que se autocorrigem quando
  descobre um erro), pontos de interação, saídas entre mapas, e um
  sistema de pontuação. Reconhece cutscenes/diálogos forçados
  (quando X e Y não mudam de jeito nenhum) separadamente de bloqueios
  pontuais (parede, NPC, placa), e prefere sair de mapas já totalmente
  explorados por uma saída que leve a um lugar novo.

Requer um emulador de Game Boy Advance com suporte a script Lua
(veja a seção de permissões de uso abaixo) e uma ROM do Fire Red que
você já possua.

## Reinício automático

Os jogos em Python reiniciam sozinhos quando a IA perde (ou vence),
sem precisar rodar o comando de novo.

## Roadmap

- [ ] Sistema de detecção e reação a batalhas no Fire Red
- [ ] Reconhecimento de NPCs em movimento (precisa de um novo endereço
      de memória, mais avançado que os já encontrados)
- [ ] Migrar o Pac-Man pra Q-Learning também
- [ ] Melhorar a IA do campo minado com dedução por probabilidade
- [ ] Salvar/carregar o Q-table dos jogos em Python num arquivo

## Fora de escopo

O Zez0 não inclui (e não incluirá) automações que simulam atividade
humana em massa para gerar pontos artificialmente em programas como
Microsoft Rewards — isso viola os termos de serviço da Microsoft.

## Direitos autorais e permissões de uso

O Zez0 não distribui nem inclui nenhuma ROM de jogo, ficheiro de BIOS,
ou código de emulador — os scripts Lua só automatizam um emulador que
você mesmo instala e uma ROM que você mesmo possui, através de comandos
externos (apertar botões, ler memória), sem copiar ou redistribuir
nada protegido por direitos autorais.

A automação do Fire Red foi construída pensando em rodar sobre o
**BizHawk**, cujo núcleo de emulação de Game Boy Advance é baseado no
**mGBA**, projeto de código aberto mantido por Jeffrey Pfau
(Copyright © 2013–2026 Jeffrey Pfau), distribuído sob a
**Mozilla Public License 2.0 (MPL-2.0)**:

> https://github.com/mgba-emu/mgba

Ao usar o Zez0 com um emulador baseado em mGBA (diretamente ou através
do BizHawk), os termos da MPL-2.0 do mGBA se aplicam ao próprio
emulador — o Zez0 não altera, redistribui nem reivindica nenhum
direito sobre esse código; apenas interage com ele de fora, como
qualquer usuário jogando manualmente faria.

Pokémon, Fire Red e todos os nomes, personagens e marcas relacionados
são propriedade da Nintendo, Game Freak e Creatures Inc. O Zez0 é um
projeto pessoal/educacional de automação e não tem nenhuma afiliação
com essas empresas.

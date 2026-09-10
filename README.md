# Zez0

Zez0 é um projeto de IA criado para jogar jogos, aprendendo sozinho a
cada partida.

## Jogos

### Snake

- **`zez0_snake.py`** — IA gulosa (greedy): sempre se move em direção à
  comida, evitando parede e o próprio corpo. Não aprende, só segue regras.
- **`zez0_snake_qlearning.py`** — IA que aprende de verdade com Q-Learning
  tabular. Treina ~3.000 partidas rápido (sem tela) e depois mostra
  jogando, continuando a aprender ao vivo.
- **`zez0_snake_qlearning_paralelo.py`** — mesma coisa, mas o treino é
  dividido entre vários núcleos do seu processador (multiprocessing),
  pra treinar mais rápido. Mostra na tela quanto tempo cada abordagem
  levou, pra comparar.

```
pip install pygame
python zez0_snake_qlearning.py
```

### Campo minado

- **`zez0_campo_minado.py`** — joga usando só dedução lógica 100% certa
  (quando o número bate com as bandeiras/desconhecidos ao redor).
- **`zez0_campo_minado_qlearning.py`** — combina a dedução lógica com
  Q-Learning para as jogadas incertas, aprendendo um padrão reutilizável
  a partir da vizinhança de cada célula.
- **`zez0_campo_minado_qlearning_paralelo.py`** — mesma IA, mas com o
  treino distribuído entre vários processos.

```
pip install pygame
python zez0_campo_minado_qlearning.py
```

### Pac-Man

- **`zez0_pacman.py`** — mapa fixo (sempre o mesmo labirinto, validado
  como 100% conectado) com 4 power pellets. A IA usa BFS pra comer
  bolinhas evitando os fantasmas; ao comer um power pellet, os fantasmas
  ficam assustados por 10 segundos e a IA aproveita pra persegui-los e
  ganhar pontos bônus, antes de voltar a comer bolinhas normais.

```
pip install pygame
python zez0_pacman.py
```

## Reinício automático

Todos os jogos reiniciam sozinhos quando a IA perde (ou vence), sem
precisar rodar o comando de novo — é só deixar rodando.

## Estrutura do projeto

```
zez0/
├── snake_qlearning.py
├── zez0_campo_minado_qlearning.py
├── zez0_pacman.py
└── README.md
```

## Roadmap

- [ ] Migrar o Pac-Man pra Q-Learning também (fantasmas que a IA aprende
      a prever/evitar com o tempo, em vez de só BFS)
- [ ] Melhorar a IA do campo minado com dedução por probabilidade
      (quando não há jogada 100% certa)
- [ ] Expandir para outros jogos simples (2048, Flappy Bird, etc.)
- [ ] Salvar/carregar o que a IA aprendeu (Q-table) num arquivo, pra não
      perder o progresso toda vez que fechar o programa

## Fora de escopo

O Zez0 não inclui (e não incluirá) automações que simulam atividade
humana em massa para gerar pontos artificialmente em programas como
Microsoft Rewards — isso viola os termos de serviço da Microsoft. Por
esse mesmo motivo, os módulos de monitoramento de preços e de pesquisa
de tópicos foram removidos do projeto: o foco do Zez0 passou a ser
exclusivamente IA jogando jogos.

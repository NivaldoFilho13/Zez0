# Zez0

Zez0 é um projeto de IA criado para jogar jogos, aprendendo sozinho a
cada partida.

## Jogos

### Snake

- **`snake_qlearning.py`** — IA que aprende de verdade com Q-Learning
  tabular. Treina ~3.000 partidas rápido (sem tela) e depois mostra
  jogando, continuando a aprender ao vivo.

```
pip install pygame
python snake_qlearning.py
```

### Campo minado

- **`campo_minado_qlearning.py`** — combina a dedução lógica com
  Q-Learning para as jogadas incertas, aprendendo um padrão reutilizável
  a partir da vizinhança de cada célula.

```
pip install pygame
python campo_minado_qlearning.py
```

### Pac-Man

- **`pacman.py`** — mapa fixo (sempre o mesmo labirinto, validado
  como 100% conectado) com 4 power pellets. A IA usa BFS pra comer
  bolinhas evitando os fantasmas; ao comer um power pellet, os fantasmas
  ficam assustados por 10 segundos e a IA aproveita pra persegui-los e
  ganhar pontos bônus, antes de voltar a comer bolinhas normais.

```
pip install pygame
python pacman.py
```

## Reinício automático

Todos os jogos reiniciam sozinhos quando a IA perde (ou vence), sem
precisar rodar o comando de novo — é só deixar rodando.

## Estrutura do projeto

```
zez0/
├── snake_qlearning.py
├── campo_minado_qlearning.py
├── pacman.py
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

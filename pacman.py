import math
import pygame
import random
import sys
from collections import deque

MAZE = [
    "#########################",
    "#     #         #       #",
    "##### ##### ### ####### #",
    "#   #       #           #",
    "# # # # ##### ######### #",
    "# # #             #     #",
    "# # # ### # ##### # #####",
    "# #     #   #     #   # #",
    "# ####### # ##### ### # #",
    "# #   #     #       # # #",
    "# ### # ### # # ##### # #",
    "# #   # # # # #       # #",
    "# # # # # # # # ####### #",
    "# # #   #   #     #     #",
    "# # # # ######### # ### #",
    "# # # # #       #     # #",
    "# # # # # ##### ##### # #",
    "#   #   # #         #   #",
    "### ### # # ##### ##### #",
    "#     #   #             #",
    "#########################",
]

PELLETS_INICIAIS = [(19, 5), (9, 3), (9, 19), (1, 17)]
PACMAN_INICIO = (1, 1)
CASA_FANTASMAS = [(19, 12), (19, 13), (19, 14)]
TIPOS_FANTASMAS = ["vermelho", "rosa", "azul"]

LINHAS = len(MAZE)
COLUNAS = len(MAZE[0])

TAMANHO_BLOCO = 28
BARRA_STATUS = 44
LARGURA = COLUNAS * TAMANHO_BLOCO
ALTURA = LINHAS * TAMANHO_BLOCO + BARRA_STATUS

CHANCE_FANTASMA_ASSUSTADO_PULAR = 0.20
DURACAO_MODO_PODER_MS = 10_000
INTERVALO_PASSO_MS = 200
RENDER_FPS = 60
PISCAR_ULTIMOS_MS = 3_000
DISTANCIA_INTERCEPTACAO = 4

PRETO = (10, 10, 30)
AZUL_PAREDE = (30, 30, 140)
AMARELO = (240, 220, 0)
BRANCO = (255, 255, 255)
AZUL_ASSUSTADO = (40, 60, 220)
CINZA_CASA = (60, 60, 80)
CORES_TIPOS = {
    "vermelho": (220, 0, 0),
    "rosa": (255, 120, 200),
    "azul": (0, 220, 220),
}

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Zez0 - Pac-Man automatizado")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont("arial", 22)


def carregar_grade():
    return [list(linha) for linha in MAZE]


def vizinhos_livres(grade, pos):
    r, c = pos
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < LINHAS and 0 <= nc < COLUNAS and grade[nr][nc] != "#":
            yield (nr, nc)


def bfs_caminho(grade, origem, destino, celulas_proibidas=frozenset()):
    if origem == destino:
        return [origem]
    fila = deque([origem])
    veio_de = {origem: None}
    while fila:
        atual = fila.popleft()
        for viz in vizinhos_livres(grade, atual):
            if viz in veio_de or (viz in celulas_proibidas and viz != destino):
                continue
            veio_de[viz] = atual
            if viz == destino:
                caminho = [viz]
                while veio_de[caminho[-1]] is not None:
                    caminho.append(veio_de[caminho[-1]])
                caminho.reverse()
                return caminho
            fila.append(viz)
    return None


def bfs_distancia(grade, origem, destino):
    caminho = bfs_caminho(grade, origem, destino)
    return len(caminho) - 1 if caminho else float("inf")


def interpolar_posicao(anterior, atual, t):
    ar, ac = anterior
    br, bc = atual
    return (ar + (br - ar) * t, ac + (bc - ac) * t)


def mover_para_alvo(grade, origem, alvo):
    caminho = bfs_caminho(grade, origem, alvo)
    if caminho and len(caminho) > 1:
        return caminho[1]
    opcoes = list(vizinhos_livres(grade, origem))
    return random.choice(opcoes) if opcoes else origem


def prever_alvo_interceptacao(jogo):
    dr = jogo.pacman[0] - jogo.pacman_anterior[0]
    dc = jogo.pacman[1] - jogo.pacman_anterior[1]
    r = jogo.pacman[0] + dr * DISTANCIA_INTERCEPTACAO
    c = jogo.pacman[1] + dc * DISTANCIA_INTERCEPTACAO
    if 0 <= r < LINHAS and 0 <= c < COLUNAS and jogo.grade[r][c] != "#":
        return (r, c)
    return jogo.pacman


class JogoPacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grade = carregar_grade()
        abertas = [
            (r, c) for r in range(LINHAS) for c in range(COLUNAS)
            if self.grade[r][c] != "#"
        ]

        self.pacman = PACMAN_INICIO
        self.pacman_anterior = PACMAN_INICIO
        self.pellets = set(PELLETS_INICIAIS)
        self.dots = set(abertas) - {self.pacman} - set(CASA_FANTASMAS) - self.pellets

        self.fantasmas = [
            {"pos": pos, "pos_anterior": pos, "assustado": False, "tipo": tipo}
            for pos, tipo in zip(CASA_FANTASMAS, TIPOS_FANTASMAS)
        ]

        self.pontuacao = 0
        self.game_over = False
        self.power_fim_ms = 0
        self.tempo_ultimo_passo_ms = pygame.time.get_ticks()

    def em_modo_poder(self):
        return pygame.time.get_ticks() < self.power_fim_ms

    def atualizar_modo_poder(self):
        if not self.em_modo_poder():
            for f in self.fantasmas:
                f["assustado"] = False

    def escolher_alvo_pacman(self):
        if self.em_modo_poder():
            assustados = [f["pos"] for f in self.fantasmas if f["assustado"]]
            assustados.sort(key=lambda p: bfs_distancia(self.grade, self.pacman, p))
            for alvo in assustados[:3]:
                caminho = bfs_caminho(self.grade, self.pacman, alvo)
                if caminho:
                    return caminho

        proibidas = set()
        for f in self.fantasmas:
            if not f["assustado"]:
                proibidas.add(f["pos"])
                for viz in vizinhos_livres(self.grade, f["pos"]):
                    proibidas.add(viz)

        itens = self.dots | self.pellets
        candidatos = sorted(itens, key=lambda d: bfs_distancia(self.grade, self.pacman, d))

        for item in candidatos[:15]:
            caminho = bfs_caminho(self.grade, self.pacman, item, celulas_proibidas=proibidas)
            if caminho:
                return caminho

        for item in candidatos[:5]:
            caminho = bfs_caminho(self.grade, self.pacman, item)
            if caminho:
                return caminho

        return None

    def passo_pacman(self):
        self.pacman_anterior = self.pacman

        caminho = self.escolher_alvo_pacman()
        if caminho and len(caminho) > 1:
            self.pacman = caminho[1]

        if self.pacman in self.dots:
            self.dots.remove(self.pacman)
            self.pontuacao += 1

        if self.pacman in self.pellets:
            self.pellets.remove(self.pacman)
            self.pontuacao += 5
            self.power_fim_ms = pygame.time.get_ticks() + DURACAO_MODO_PODER_MS
            for f in self.fantasmas:
                f["assustado"] = True

    def passo_fantasmas(self):
        self.atualizar_modo_poder()

        for f in self.fantasmas:
            f["pos_anterior"] = f["pos"]

            if f["assustado"]:
                if random.random() < CHANCE_FANTASMA_ASSUSTADO_PULAR:
                    continue
                opcoes = list(vizinhos_livres(self.grade, f["pos"]))
                if opcoes:
                    f["pos"] = max(
                        opcoes,
                        key=lambda p: abs(p[0] - self.pacman[0]) + abs(p[1] - self.pacman[1]),
                    )
                continue

            if f["tipo"] == "vermelho":
                alvo = prever_alvo_interceptacao(self)
                f["pos"] = mover_para_alvo(self.grade, f["pos"], alvo)
            elif f["tipo"] == "rosa":
                opcoes = list(vizinhos_livres(self.grade, f["pos"]))
                f["pos"] = random.choice(opcoes) if opcoes else f["pos"]
            elif f["tipo"] == "azul":
                f["pos"] = mover_para_alvo(self.grade, f["pos"], self.pacman)

    def verificar_colisao(self):
        for i, f in enumerate(self.fantasmas):
            if f["pos"] == self.pacman:
                if f["assustado"]:
                    self.pontuacao += 50
                    f["pos"] = CASA_FANTASMAS[i]
                    f["pos_anterior"] = CASA_FANTASMAS[i]
                    f["assustado"] = False
                else:
                    self.game_over = True


def desenhar(jogo, partidas, melhor_pontuacao, t):
    agora = pygame.time.get_ticks()
    tela.fill(PRETO)

    for r in range(LINHAS):
        for c in range(COLUNAS):
            x, y = c * TAMANHO_BLOCO, r * TAMANHO_BLOCO + BARRA_STATUS
            if jogo.grade[r][c] == "#":
                pygame.draw.rect(tela, AZUL_PAREDE, (x, y, TAMANHO_BLOCO, TAMANHO_BLOCO))

    cr, cc = CASA_FANTASMAS[0]
    x, y = cc * TAMANHO_BLOCO, cr * TAMANHO_BLOCO + BARRA_STATUS
    pygame.draw.rect(tela, CINZA_CASA, (x, y, TAMANHO_BLOCO * 3, TAMANHO_BLOCO))

    for (r, c) in jogo.dots:
        x, y = c * TAMANHO_BLOCO, r * TAMANHO_BLOCO + BARRA_STATUS
        centro = (x + TAMANHO_BLOCO // 2, y + TAMANHO_BLOCO // 2)
        pygame.draw.circle(tela, BRANCO, centro, 3)

    pulso = 2 * math.sin(agora / 150.0)
    for (r, c) in jogo.pellets:
        x, y = c * TAMANHO_BLOCO, r * TAMANHO_BLOCO + BARRA_STATUS
        centro = (x + TAMANHO_BLOCO // 2, y + TAMANHO_BLOCO // 2)
        pygame.draw.circle(tela, BRANCO, centro, 8 + pulso)

    pr, pc = interpolar_posicao(jogo.pacman_anterior, jogo.pacman, t)
    x, y = pc * TAMANHO_BLOCO, pr * TAMANHO_BLOCO + BARRA_STATUS
    centro = (x + TAMANHO_BLOCO // 2, y + TAMANHO_BLOCO // 2)
    pygame.draw.circle(tela, AMARELO, centro, TAMANHO_BLOCO // 2 - 3)

    for f in jogo.fantasmas:
        fr, fc = interpolar_posicao(f["pos_anterior"], f["pos"], t)
        x, y = fc * TAMANHO_BLOCO, fr * TAMANHO_BLOCO + BARRA_STATUS
        centro = (x + TAMANHO_BLOCO // 2, y + TAMANHO_BLOCO // 2)

        if f["assustado"]:
            tempo_restante = jogo.power_fim_ms - agora
            if tempo_restante < PISCAR_ULTIMOS_MS and (agora // 200) % 2 == 0:
                cor = BRANCO
            else:
                cor = AZUL_ASSUSTADO
        else:
            cor = CORES_TIPOS[f["tipo"]]

        pygame.draw.circle(tela, cor, centro, TAMANHO_BLOCO // 2 - 3)

    segundos_poder = max(0, (jogo.power_fim_ms - agora) // 1000 + 1)
    extra = f" | MODO PODER: {segundos_poder}s" if jogo.em_modo_poder() else ""
    status = f"Zez0 | Partidas: {partidas} | Pontuação: {jogo.pontuacao} | Melhor: {melhor_pontuacao}{extra}"
    tela.blit(fonte.render(status, True, BRANCO), (10, 8))


def main():
    jogo = JogoPacman()
    partidas = 0
    melhor_pontuacao = 0

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

        agora = pygame.time.get_ticks()

        if jogo.game_over or (not jogo.dots and not jogo.pellets):
            partidas += 1
            melhor_pontuacao = max(melhor_pontuacao, jogo.pontuacao)
            desenhar(jogo, partidas, melhor_pontuacao, 1.0)
            pygame.display.flip()
            pygame.time.delay(900)
            jogo = JogoPacman()
            continue

        if agora - jogo.tempo_ultimo_passo_ms >= INTERVALO_PASSO_MS:
            jogo.passo_pacman()
            jogo.verificar_colisao()
            if not jogo.game_over:
                jogo.passo_fantasmas()
                jogo.verificar_colisao()
            jogo.tempo_ultimo_passo_ms = agora

        t = min(1.0, (agora - jogo.tempo_ultimo_passo_ms) / INTERVALO_PASSO_MS)
        desenhar(jogo, partidas, melhor_pontuacao, t)
        pygame.display.flip()
        relogio.tick(RENDER_FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

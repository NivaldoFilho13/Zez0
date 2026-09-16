import pygame
import random
import sys
import time
import multiprocessing
from collections import defaultdict


LINHAS, COLUNAS = 10, 10
TOTAL_MINAS = 15
TAMANHO_CELULA = 40
LARGURA, ALTURA = COLUNAS * TAMANHO_CELULA, LINHAS * TAMANHO_CELULA + 40
FPS_IA = 4

PARTIDAS_TREINO_TOTAL = 800
NUM_PROCESSOS = max(1, multiprocessing.cpu_count() - 1) or 1

ALPHA = 0.15
EPSILON_INICIAL = 0.3
EPSILON_MIN = 0.02
EPSILON_DECAIMENTO = 0.995

CINZA_CLARO = (200, 200, 200)
CINZA_ESCURO = (120, 120, 120)
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
VERMELHO = (200, 0, 0)
AMARELO = (200, 180, 0)

CORES_NUMEROS = {
    1: (0, 0, 200),
    2: (0, 120, 0),
    3: (200, 0, 0),
    4: (0, 0, 120),
    5: (120, 0, 0),
    6: (0, 130, 130),
    7: (0, 0, 0),
    8: (100, 100, 100),
}


class CampoMinado:
    def __init__(self, linhas, colunas, minas):
        self.linhas = linhas
        self.colunas = colunas
        self.total_minas = minas
        self.reset()

    def reset(self):
        self.minas = set()
        self.numeros = {}
        self.revelado = set()
        self.bandeira = set()
        self.primeiro_clique = True
        self.game_over = False
        self.vitoria = False

    def vizinhos(self, pos):
        r, c = pos
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.linhas and 0 <= nc < self.colunas:
                    yield (nr, nc)

    def gerar_minas(self, celula_segura):
        proibidas = {celula_segura} | set(self.vizinhos(celula_segura))
        todas = [
            (r, c)
            for r in range(self.linhas)
            for c in range(self.colunas)
            if (r, c) not in proibidas
        ]
        self.minas = set(random.sample(todas, self.total_minas))
        for r in range(self.linhas):
            for c in range(self.colunas):
                if (r, c) not in self.minas:
                    self.numeros[(r, c)] = sum(
                        1 for v in self.vizinhos((r, c)) if v in self.minas
                    )

    def revelar(self, pos):
        if self.primeiro_clique:
            self.gerar_minas(pos)
            self.primeiro_clique = False

        if pos in self.revelado or pos in self.bandeira:
            return "nada"

        if pos in self.minas:
            self.revelado.add(pos)
            self.game_over = True
            return "mina"

        pilha = [pos]
        while pilha:
            atual = pilha.pop()
            if atual in self.revelado:
                continue
            self.revelado.add(atual)
            if self.numeros.get(atual, 0) == 0:
                for v in self.vizinhos(atual):
                    if v not in self.revelado and v not in self.bandeira:
                        pilha.append(v)

        if len(self.revelado) == self.linhas * self.colunas - self.total_minas:
            self.vitoria = True

        return "seguro"

    def alternar_bandeira(self, pos):
        if pos in self.revelado:
            return
        if pos in self.bandeira:
            self.bandeira.remove(pos)
        else:
            self.bandeira.add(pos)

    def celulas_desconhecidas(self):
        todas = {(r, c) for r in range(self.linhas) for c in range(self.colunas)}
        return todas - self.revelado - self.bandeira


def deducao_logica(campo):
    revelar_seguras = set()
    marcar_minas = set()
    for pos in campo.revelado:
        numero = campo.numeros.get(pos, 0)
        if numero == 0:
            continue
        vizinhos = list(campo.vizinhos(pos))
        desconhecidos = [
            v for v in vizinhos if v not in campo.revelado and v not in campo.bandeira
        ]
        bandeiras = [v for v in vizinhos if v in campo.bandeira]
        if not desconhecidos:
            continue
        if len(bandeiras) == numero:
            revelar_seguras.update(desconhecidos)
        elif len(desconhecidos) + len(bandeiras) == numero:
            marcar_minas.update(desconhecidos)
    return revelar_seguras, marcar_minas


def estado_da_celula(campo, celula):
    restricoes = []
    for viz in campo.vizinhos(celula):
        if viz in campo.revelado:
            numero = campo.numeros.get(viz, 0)
            vizinhos_do_numero = list(campo.vizinhos(viz))
            desconhecidos = [
                v
                for v in vizinhos_do_numero
                if v not in campo.revelado and v not in campo.bandeira
            ]
            bandeiras = [v for v in vizinhos_do_numero if v in campo.bandeira]
            faltam = numero - len(bandeiras)
            restricoes.append((faltam, len(desconhecidos)))
    return tuple(sorted(restricoes))


class AgenteQLearning:
    def __init__(self):
        self.q = defaultdict(float)
        self.epsilon = EPSILON_INICIAL

    def escolher_celula(self, campo, candidatas):
        if random.random() < self.epsilon:
            return random.choice(candidatas)
        return max(candidatas, key=lambda c: self.q[estado_da_celula(campo, c)])

    def aprender(self, estado, resultado):
        recompensa = 1.0 if resultado == "seguro" else -1.0
        atual = self.q[estado]
        self.q[estado] = atual + ALPHA * (recompensa - atual)

    def decair_epsilon(self):
        self.epsilon = max(EPSILON_MIN, self.epsilon * EPSILON_DECAIMENTO)


def jogar_uma_partida(campo, agente, aprendendo=True):
    campo.revelar((campo.linhas // 2, campo.colunas // 2))
    while not campo.game_over and not campo.vitoria:
        seguras, minas = deducao_logica(campo)
        if minas:
            for c in minas:
                campo.alternar_bandeira(c)
        if seguras:
            for c in seguras:
                if not campo.game_over:
                    campo.revelar(c)
            continue
        candidatas = list(campo.celulas_desconhecidas())
        if not candidatas:
            break
        fronteira = [
            c for c in candidatas if any(v in campo.revelado for v in campo.vizinhos(c))
        ]
        alvo_lista = fronteira if fronteira else candidatas
        celula = agente.escolher_celula(campo, alvo_lista)
        estado = estado_da_celula(campo, celula)
        resultado = campo.revelar(celula)
        if aprendendo and estado:
            agente.aprender(estado, resultado)


def treinar_sequencial(partidas):
    agente = AgenteQLearning()
    for _ in range(partidas):
        campo = CampoMinado(LINHAS, COLUNAS, TOTAL_MINAS)
        jogar_uma_partida(campo, agente, aprendendo=True)
        agente.decair_epsilon()
    return agente


def treinar_worker(args):

    partidas, semente = args
    random.seed(semente)
    agente = AgenteQLearning()
    for _ in range(partidas):
        campo = CampoMinado(LINHAS, COLUNAS, TOTAL_MINAS)
        jogar_uma_partida(campo, agente, aprendendo=True)
        agente.decair_epsilon()
    return dict(agente.q)


def combinar_q_tables(lista_de_qs):

    somas = defaultdict(float)
    contagens = defaultdict(int)

    for q_processo in lista_de_qs:
        for estado, valor in q_processo.items():
            somas[estado] += valor
            contagens[estado] += 1

    combinado = defaultdict(float)
    for estado, soma in somas.items():
        combinado[estado] = soma / contagens[estado]

    return combinado


def treinar_paralelo(partidas_total, num_processos):
    partidas_por_processo = max(1, partidas_total // num_processos)
    tarefas = [
        (partidas_por_processo, random.randint(0, 999999)) for _ in range(num_processos)
    ]

    with multiprocessing.Pool(processes=num_processos) as pool:
        resultados = pool.map(treinar_worker, tarefas)

    q_combinado = combinar_q_tables(resultados)

    agente = AgenteQLearning()
    agente.q = q_combinado
    agente.epsilon = EPSILON_MIN
    return agente


def desenhar(tela, fonte, fonte_status, campo, partidas, vitorias):
    tela.fill(BRANCO)
    for r in range(campo.linhas):
        for c in range(campo.colunas):
            x, y = c * TAMANHO_CELULA, r * TAMANHO_CELULA + 40
            retangulo = pygame.Rect(x, y, TAMANHO_CELULA, TAMANHO_CELULA)
            pos = (r, c)
            if pos in campo.revelado:
                if pos in campo.minas:
                    pygame.draw.rect(tela, VERMELHO, retangulo)
                else:
                    pygame.draw.rect(tela, CINZA_CLARO, retangulo)
                    numero = campo.numeros.get(pos, 0)
                    if numero > 0:
                        cor = CORES_NUMEROS.get(numero, PRETO)
                        texto = fonte.render(str(numero), True, cor)
                        tela.blit(texto, texto.get_rect(center=retangulo.center))
            elif pos in campo.bandeira:
                pygame.draw.rect(tela, CINZA_ESCURO, retangulo)
                texto = fonte.render("F", True, AMARELO)
                tela.blit(texto, texto.get_rect(center=retangulo.center))
            else:
                pygame.draw.rect(tela, CINZA_ESCURO, retangulo)
            pygame.draw.rect(tela, PRETO, retangulo, 1)

    status = f"Partidas: {partidas} | Vitórias: {vitorias}"
    texto_status = fonte_status.render(status, True, PRETO)
    tela.blit(texto_status, (10, 8))


def jogar_com_tela(agente):
    pygame.init()
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Zez0 - Campo Minado Q-Learning (treino paralelo)")
    relogio = pygame.time.Clock()
    fonte = pygame.font.SysFont("arial", 20, bold=True)
    fonte_status = pygame.font.SysFont("arial", 22)

    partidas = 0
    vitorias = 0
    campo = CampoMinado(LINHAS, COLUNAS, TOTAL_MINAS)
    campo.revelar((LINHAS // 2, COLUNAS // 2))

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

        if campo.game_over or campo.vitoria:
            partidas += 1
            if campo.vitoria:
                vitorias += 1
            agente.decair_epsilon()
            desenhar(tela, fonte, fonte_status, campo, partidas, vitorias)
            pygame.display.flip()
            pygame.time.delay(700)
            campo = CampoMinado(LINHAS, COLUNAS, TOTAL_MINAS)
            campo.revelar((LINHAS // 2, COLUNAS // 2))
            continue

        seguras, minas = deducao_logica(campo)
        if minas:
            for c in minas:
                campo.alternar_bandeira(c)
        if seguras:
            for c in seguras:
                if not campo.game_over:
                    campo.revelar(c)
        else:
            candidatas = list(campo.celulas_desconhecidas())
            if candidatas:
                fronteira = [
                    c
                    for c in candidatas
                    if any(v in campo.revelado for v in campo.vizinhos(c))
                ]
                alvo_lista = fronteira if fronteira else candidatas
                celula = agente.escolher_celula(campo, alvo_lista)
                estado = estado_da_celula(campo, celula)
                resultado = campo.revelar(celula)
                if estado:
                    agente.aprender(estado, resultado)

        desenhar(tela, fonte, fonte_status, campo, partidas, vitorias)
        pygame.display.flip()
        relogio.tick(FPS_IA)

    pygame.quit()
    sys.exit()


def main():
    print(f"Núcleos que serão usados no treino paralelo: {NUM_PROCESSOS}\n")

    print(f"[1/2] Treino SEQUENCIAL ({PARTIDAS_TREINO_TOTAL} partidas, 1 processo)...")
    inicio = time.perf_counter()
    treinar_sequencial(PARTIDAS_TREINO_TOTAL)
    tempo_sequencial = time.perf_counter() - inicio
    print(f"      Tempo: {tempo_sequencial:.2f} segundos\n")

    print(
        f"[2/2] Treino PARALELO ({PARTIDAS_TREINO_TOTAL} partidas divididas entre {NUM_PROCESSOS} processos)..."
    )
    inicio = time.perf_counter()
    agente = treinar_paralelo(PARTIDAS_TREINO_TOTAL, NUM_PROCESSOS)
    tempo_paralelo = time.perf_counter() - inicio
    print(f"      Tempo: {tempo_paralelo:.2f} segundos\n")

    if tempo_paralelo < tempo_sequencial:
        ganho = tempo_sequencial / tempo_paralelo
        print(
            f"Resultado: o treino paralelo foi {ganho:.2f}x mais rápido nesta máquina.\n"
        )
    else:
        print(
            "Resultado: nesta máquina/carga de trabalho, o custo de abrir processos "
            "foi maior que o ganho. Tente aumentar PARTIDAS_TREINO_TOTAL.\n"
        )

    print("Abrindo janela para ver a IA (treinada em paralelo) jogando...")
    jogar_com_tela(agente)


if __name__ == "__main__":
    main()

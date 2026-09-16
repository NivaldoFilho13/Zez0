import pygame
import random
import pickle
import os

pygame.init()

LARGURA = 600
ALTURA = 400
TAMANHO = 20
VELOCIDADE = 20

TELA = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Snake - Q-Learning")

RELOGIO = pygame.time.Clock()

# Cores
PRETO = (15, 15, 15)
VERDE = (0, 200, 0)
VERDE_CLARO = (100, 255, 100)
VERMELHO = (255, 50, 50)
BRANCO = (255, 255, 255)
CINZA = (50, 50, 50)


ALPHA = 0.1     
GAMMA = 0.9     
EPSILON = 1.0    
EPSILON_MIN = 0.01
EPSILON_DECAY = 0.995

ARQUIVO_QTABLE = "qtable.pkl"


if os.path.exists(ARQUIVO_QTABLE):
    with open(ARQUIVO_QTABLE, "rb") as arquivo:
        Q = pickle.load(arquivo)
else:
    Q = {}


def obter_q(estado):
    """
    Retorna os valores Q para as três ações:
    0 = seguir reto
    1 = virar para esquerda
    2 = virar para direita
    """

    if estado not in Q:
        Q[estado] = [0.0, 0.0, 0.0]

    return Q[estado]


DIRECOES = [
    (0, -TAMANHO),   # cima
    (TAMANHO, 0),    # direita
    (0, TAMANHO),    # baixo
    (-TAMANHO, 0)    # esquerda
]


class Snake:

    def __init__(self):
        self.reset()

    def reset(self):

        self.cobra = [
            (300, 200),
            (280, 200),
            (260, 200)
        ]

        self.direcao = 1  

        self.comida = self.nova_comida()

        self.pontos = 0
        self.passos = 0
        self.max_passos = 200

    def nova_comida(self):

        while True:

            comida = (
                random.randrange(0, LARGURA, TAMANHO),
                random.randrange(0, ALTURA, TAMANHO)
            )

            if comida not in self.cobra:
                return comida

    def perigo(self, direcao):

        cabeca = self.cobra[0]

        novo_x = cabeca[0] + DIRECOES[direcao][0]
        novo_y = cabeca[1] + DIRECOES[direcao][1]

        nova_posicao = (novo_x, novo_y)

        if novo_x < 0 or novo_x >= LARGURA:
            return 1

        if novo_y < 0 or novo_y >= ALTURA:
            return 1

        if nova_posicao in self.cobra:
            return 1

        return 0

    def estado(self):

        cabeca_x, cabeca_y = self.cobra[0]
        comida_x, comida_y = self.comida

        # Direção atual
        cima = int(self.direcao == 0)
        direita = int(self.direcao == 1)
        baixo = int(self.direcao == 2)
        esquerda = int(self.direcao == 3)

        # Perigos
        esquerda_perigo = self.perigo((self.direcao - 1) % 4)
        frente_perigo = self.perigo(self.direcao)
        direita_perigo = self.perigo((self.direcao + 1) % 4)

        # Localização da comida
        comida_esquerda = int(comida_x < cabeca_x)
        comida_direita = int(comida_x > cabeca_x)

        comida_cima = int(comida_y < cabeca_y)
        comida_baixo = int(comida_y > cabeca_y)

        return (
            esquerda_perigo,
            frente_perigo,
            direita_perigo,

            cima,
            direita,
            baixo,
            esquerda,

            comida_esquerda,
            comida_direita,
            comida_cima,
            comida_baixo
        )

    
    def passo(self, acao):

        self.passos += 1



        if acao == 1:
            self.direcao = (self.direcao - 1) % 4

        elif acao == 2:
            self.direcao = (self.direcao + 1) % 4

        # Nova cabeça
        cabeca = self.cobra[0]

        nova_cabeca = (
            cabeca[0] + DIRECOES[self.direcao][0],
            cabeca[1] + DIRECOES[self.direcao][1]
        )

        if (
            nova_cabeca[0] < 0 or
            nova_cabeca[0] >= LARGURA or
            nova_cabeca[1] < 0 or
            nova_cabeca[1] >= ALTURA or
            nova_cabeca in self.cobra
        ):
            return -10, True

        # Distância antes de andar
        distancia_anterior = abs(
            cabeca[0] - self.comida[0]
        ) + abs(
            cabeca[1] - self.comida[1]
        )

        self.cobra.insert(0, nova_cabeca)

        if nova_cabeca == self.comida:

            self.pontos += 1
            self.comida = self.nova_comida()

            recompensa = 10

        else:

            self.cobra.pop()

            distancia_nova = abs(
                nova_cabeca[0] - self.comida[0]
            ) + abs(
                nova_cabeca[1] - self.comida[1]
            )

            # Recompensa por aproximar-se da comida
            if distancia_nova < distancia_anterior:
                recompensa = 1
            else:
                recompensa = -1

        # Evita ficar andando indefinidamente
        if self.passos > self.max_passos + len(self.cobra) * 10:
            return -10, True

        return recompensa, False


def escolher_acao(estado):

    global EPSILON

    valores = obter_q(estado)

    # Exploração
    if random.random() < EPSILON:
        return random.randint(0, 2)

    # Exploração da melhor ação
    maior = max(valores)

    melhores = [
        i for i, valor in enumerate(valores)
        if valor == maior
    ]

    return random.choice(melhores)


def treinar(episodios=10000):

    global EPSILON

    cobra = Snake()

    melhor_pontuacao = 0

    for episodio in range(1, episodios + 1):

        cobra.reset()

        estado = cobra.estado()

        while True:

            acao = escolher_acao(estado)

            recompensa, morreu = cobra.passo(acao)

            novo_estado = cobra.estado()

            q_atual = obter_q(estado)
            q_futuro = obter_q(novo_estado)

            # Fórmula do Q-Learning
            q_atual[acao] += ALPHA * (
                recompensa +
                GAMMA * max(q_futuro) -
                q_atual[acao]
            )

            estado = novo_estado

            if morreu:
                break

        # Reduz exploração
        if EPSILON > EPSILON_MIN:
            EPSILON *= EPSILON_DECAY

        if cobra.pontos > melhor_pontuacao:
            melhor_pontuacao = cobra.pontos

        if episodio % 100 == 0:

            print(
                f"Episódio: {episodio:5d} | "
                f"Pontos: {cobra.pontos:3d} | "
                f"Recorde: {melhor_pontuacao:3d} | "
                f"Epsilon: {EPSILON:.3f}"
            )

        # Salva a inteligência
        if episodio % 500 == 0:

            with open(ARQUIVO_QTABLE, "wb") as arquivo:
                pickle.dump(Q, arquivo)

    with open(ARQUIVO_QTABLE, "wb") as arquivo:
        pickle.dump(Q, arquivo)

    print("\nTreinamento concluído!")


def jogar():

    cobra = Snake()

    fonte = pygame.font.Font(None, 30)

    rodando = True

    while rodando:

        for evento in pygame.event.get():

            if evento.type == pygame.QUIT:
                pygame.quit()
                return

        estado = cobra.estado()

        valores = obter_q(estado)

        # Durante o jogo a IA não precisa explorar
        acao = valores.index(max(valores))

        recompensa, morreu = cobra.passo(acao)

        TELA.fill(PRETO)

        # Grade
        for x in range(0, LARGURA, TAMANHO):
            pygame.draw.line(
                TELA,
                CINZA,
                (x, 0),
                (x, ALTURA)
            )

        for y in range(0, ALTURA, TAMANHO):
            pygame.draw.line(
                TELA,
                CINZA,
                (0, y),
                (LARGURA, y)
            )

        # Cobra
        for i, parte in enumerate(cobra.cobra):

            cor = (
                VERDE_CLARO
                if i == 0
                else VERDE
            )

            pygame.draw.rect(
                TELA,
                cor,
                (
                    parte[0],
                    parte[1],
                    TAMANHO,
                    TAMANHO
                )
            )

        # Comida
        pygame.draw.rect(
            TELA,
            VERMELHO,
            (
                cobra.comida[0],
                cobra.comida[1],
                TAMANHO,
                TAMANHO
            )
        )

        # Pontuação
        texto = fonte.render(
            f"Pontos: {cobra.pontos}",
            True,
            BRANCO
        )

        TELA.blit(texto, (10, 10))

        pygame.display.flip()

        RELOGIO.tick(VELOCIDADE)

        if morreu:

            pygame.time.delay(1000)

            cobra.reset()


def menu():

    fonte = pygame.font.Font(None, 40)

    print("====================================")
    print("       SNAKE COM Q-LEARNING")
    print("====================================")
    print()
    print("1 - Treinar a IA")
    print("2 - Jogar com a IA")
    print("3 - Treinar e depois jogar")
    print()

    opcao = input("Escolha: ")

    if opcao == "1":

        quantidade = input(
            "Quantidade de episódios [10000]: "
        )

        quantidade = int(quantidade or 10000)

        treinar(quantidade)

    elif opcao == "2":

        if not Q:
            print("A IA ainda não foi treinada.")
            print("Execute a opção 1 primeiro.")
            return

        jogar()

    elif opcao == "3":

        treinar(10000)
        jogar()


if __name__ == "__main__":
    menu()

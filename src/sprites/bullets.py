##########################################################
#  Projéteis — Arquitetura escalável por tipo de arma.
#
#  Cada subclasse define apenas o que muda:
#  tamanho, cor, velocidade, dano e vida útil.
##########################################################

import pygame
from src.config import *


class Bala(pygame.sprite.Sprite):
    """Bala genérica. Todos os projéteis herdam daqui."""

    def __init__(self, pos_mundo, direcao, cor, eh_inimiga=False,
                 velocidade=15, tamanho=(8, 8), dano=10, vida=100):
        super().__init__()
        self.image = pygame.Surface(tamanho, pygame.SRCALPHA)
        # Círculo em vez de quadrado → mais bonito
        raio = min(tamanho) // 2
        pygame.draw.circle(self.image, cor, (tamanho[0]//2, tamanho[1]//2), raio)

        self.pos        = pygame.math.Vector2(pos_mundo)
        self.rect       = self.image.get_rect(center=self.pos)
        self.dir        = pygame.math.Vector2(direcao)
        self.velocidade = velocidade
        self.eh_inimiga = eh_inimiga
        self.dano       = dano
        self.cor        = cor
        self.tempo_vida = vida

    def update(self, particulas=None):
        self.pos        += self.dir * self.velocidade
        self.rect.center = self.pos
        self.tempo_vida -= 1

        # Gera rastro de partículas se um gerenciador for fornecido
        if particulas and self.tempo_vida % 2 == 0:
            particulas.rastro_bala(self.pos, self.dir, self.cor)

        if self.tempo_vida <= 0:
            self.kill()


# ── Variações de projétil ──────────────────────────────────────────────

class BalaMetralhadora(Bala):
    """Rápida, pequena — cadência alta compensa o dano base baixo."""
    def __init__(self, pos, direcao, eh_inimiga=False, dano=7, tamanho=(6, 6)):
        super().__init__(pos, direcao, AMARELO, eh_inimiga,
                         velocidade=18, tamanho=tamanho, dano=dano, vida=80)


class BalaShotgun(Bala):
    """Lenta, grande — dano alto por pellet, dispara em trio."""
    def __init__(self, pos, direcao, eh_inimiga=False, dano=15, tamanho=(10, 10)):
        super().__init__(pos, direcao, ROXO, eh_inimiga,
                         velocidade=12, tamanho=tamanho, dano=dano, vida=60)


class BalaInimiga(Bala):
    """Projétil de cor laranja para inimigos atiradores."""
    def __init__(self, pos, direcao):
        super().__init__(pos, direcao, LARANJA, eh_inimiga=True,
                         velocidade=9, tamanho=(9, 9), dano=12, vida=120)


class BalaBoss(Bala):
    """Projétil grande e lento do Boss — bullet hell."""
    def __init__(self, pos, direcao, cor=VERMELHO):
        super().__init__(pos, direcao, cor, eh_inimiga=True,
                         velocidade=5, tamanho=(14, 14), dano=20, vida=200)

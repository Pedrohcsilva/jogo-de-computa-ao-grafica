##########################################################
#  Projéteis — Cápsulas elongadas + rastro de luz
#
#  Toda bala é uma cápsula orientada na direção de voo.
#  BalaBase: lógica comum (move, rastro, kill).
#  Subclasses definem cor, tamanho, velocidade e dano.
##########################################################

import pygame
import math
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import *


def _capsula(cor, brilho, cap_w, cap_h, angulo_graus):
    """Retorna Surface de cápsula rotacionada."""
    base = pygame.Surface((cap_w, cap_h), pygame.SRCALPHA)
    r = cap_h // 2
    cx_b, cy_b = cap_w // 2, cap_h // 2
    pygame.draw.rect(base, cor, (r, 0, cap_w - 2*r, cap_h))
    pygame.draw.circle(base, cor, (r, cy_b), r)
    pygame.draw.circle(base, cor, (cap_w - r, cy_b), r)
    # Linha de brilho
    pygame.draw.line(base, brilho, (r, max(1, cy_b - r//2 + 1)),
                     (cap_w - r, max(1, cy_b - r//2 + 1)), 1)
    return pygame.transform.rotate(base, angulo_graus)


class BalaBase(pygame.sprite.Sprite):
    def __init__(self, pos_mundo, direcao, cor, brilho,
                 velocidade, cap_w, cap_h, dano, vida, eh_inimiga=False):
        super().__init__()
        self.cor        = cor
        self.dir        = pygame.math.Vector2(direcao).normalize()
        self.velocidade = velocidade
        self.eh_inimiga = eh_inimiga
        self.dano       = dano
        self.tempo_vida = vida
        self.pos        = pygame.math.Vector2(pos_mundo)

        angulo     = -math.degrees(math.atan2(self.dir.y, self.dir.x))
        self.image = _capsula(cor, brilho, cap_w, cap_h, angulo)
        self.rect  = self.image.get_rect(center=self.pos)

    def update(self, particulas=None):
        self.pos        += self.dir * self.velocidade
        self.rect.center = self.pos
        self.tempo_vida -= 1
        if particulas and self.tempo_vida % 2 == 0:
            particulas.rastro_bala(self.pos, self.dir, self.cor)
        if self.tempo_vida <= 0:
            self.kill()

    def aplicar_perfurante(self):
        """Chamado quando acerta inimigo com upgrade perfurante.
        Decrementa contador de penetrações; mata a bala quando esgota."""
        if not hasattr(self, '_penetracoes_restantes'):
            return False  # não tem upgrade
        self._penetracoes_restantes -= 1
        if self._penetracoes_restantes <= 0:
            self.kill()
        return True  # bala continua viva por enquanto

    def tentar_ricochet(self, inimigos, inimigo_acertado):
        """Redireciona para o inimigo mais próximo (exceto o acertado).
        Retorna True se ricocheteou, False se não havia alvo."""
        if not getattr(self, '_tem_ricochet', False) or getattr(self, '_ricocheteou', False):
            return False
        alvos = [i for i in inimigos if i is not inimigo_acertado and i.alive()]
        if not alvos:
            return False
        mais_proximo = min(alvos, key=lambda i: (i.pos - self.pos).length())
        nova_dir = mais_proximo.pos - self.pos
        if nova_dir.length() > 0:
            self.dir = nova_dir.normalize()
            self._ricocheteou = True
            self.tempo_vida = max(self.tempo_vida, 60)  # garante alcance para ricochet
            return True
        return False


# ── Pistola (default) ─────────────────────────────────────────────────
class Bala(BalaBase):
    def __init__(self, pos_mundo, direcao, cor=AZUL_TIRO, eh_inimiga=False,
                 velocidade=15, tamanho=(8, 8), dano=10, vida=100):
        brilho = tuple(min(255, c + 100) for c in (cor or AZUL_TIRO))
        super().__init__(pos_mundo, direcao, cor or AZUL_TIRO, brilho,
                         velocidade=velocidade,
                         cap_w=16, cap_h=6,
                         dano=dano, vida=vida, eh_inimiga=eh_inimiga)


# ── Metralhadora ──────────────────────────────────────────────────────
class BalaMetralhadora(BalaBase):
    def __init__(self, pos, direcao, eh_inimiga=False, dano=7, tamanho=None):
        cap_w = (tamanho[0] * 2) if tamanho else 20
        cap_h = tamanho[1] if tamanho else 4
        super().__init__(pos, direcao, AMARELO, (255, 255, 160),
                         velocidade=20, cap_w=cap_w, cap_h=cap_h,
                         dano=dano, vida=80, eh_inimiga=eh_inimiga)


# ── Shotgun ───────────────────────────────────────────────────────────
class BalaShotgun(BalaBase):
    def __init__(self, pos, direcao, eh_inimiga=False, dano=15, tamanho=None):
        cap_w = (tamanho[0] * 2) if tamanho else 14
        cap_h = tamanho[1] if tamanho else 9
        super().__init__(pos, direcao, ROXO, (220, 160, 255),
                         velocidade=12, cap_w=cap_w, cap_h=cap_h,
                         dano=dano, vida=60, eh_inimiga=eh_inimiga)


# ── Inimigo atirador ──────────────────────────────────────────────────
class BalaInimiga(BalaBase):
    def __init__(self, pos, direcao):
        super().__init__(pos, direcao, LARANJA, (255, 200, 100),
                         velocidade=9, cap_w=12, cap_h=9,
                         dano=12, vida=120, eh_inimiga=True)


# ── Boss ──────────────────────────────────────────────────────────────
class BalaBoss(BalaBase):
    def __init__(self, pos, direcao, cor=VERMELHO):
        brilho = tuple(min(255, c + 120) for c in cor)
        super().__init__(pos, direcao, cor, brilho,
                         velocidade=5, cap_w=18, cap_h=14,
                         dano=20, vida=200, eh_inimiga=True)

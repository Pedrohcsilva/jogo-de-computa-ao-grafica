##########################################################
#  Números de Dano Flutuantes (Floating Damage Numbers)
#
#  COMPORTAMENTO:
#   - Surgem na posição do inimigo atingido
#   - Sobem suavemente com easing (desaceleram no topo)
#   - Fade-out na segunda metade da vida
#   - Cores distintas por tipo: dano normal, crítico, boss
#
#  MATEMÁTICA DO MOVIMENTO:
#   vel.y *= 0.92 por frame → sobe mais rápido no início
#   e desacelera exponencialmente (easing out)
##########################################################

import pygame
import random
from src.config import *


# Fonte compartilhada — criada uma vez, reutilizada
_fonte_dano: pygame.font.Font | None = None
_fonte_critico: pygame.font.Font | None = None

def _get_fontes():
    global _fonte_dano, _fonte_critico
    if _fonte_dano is None:
        _fonte_dano   = pygame.font.SysFont("Arial", 20, bold=True)
        _fonte_critico = pygame.font.SysFont("Arial", 28, bold=True)
    return _fonte_dano, _fonte_critico


class NumeroDano:
    """
    Um único número flutuante.
    Não é Sprite — gerenciado diretamente pelo GerenciadorNumeroDano.
    """
    __slots__ = ("pos", "vel", "texto_surf", "vida", "vida_max", "critico")

    VIDA_PADRAO = 55   # frames (~0.9 segundos)

    def __init__(self, pos_mundo, valor, critico=False, eh_jogador=False):
        self.pos     = pygame.math.Vector2(pos_mundo)
        self.critico = critico

        # Velocidade inicial: sobe rápido, deriva levemente pra um lado
        self.vel = pygame.math.Vector2(
            random.uniform(-0.6, 0.6),   # deriva horizontal leve
            -4.5 if critico else -3.0    # críticos sobem mais alto
        )

        self.vida     = self.VIDA_PADRAO
        self.vida_max = self.VIDA_PADRAO

        # Pré-renderiza o texto com a cor correta
        fonte_d, fonte_c = _get_fontes()
        fonte  = fonte_c if critico else fonte_d

        if eh_jogador:
            cor = VERMELHO          # dano recebido pelo jogador
        elif critico:
            cor = AMARELO           # crítico do jogador
        else:
            cor = (255, 255, 255)   # dano normal do jogador

        texto = f"-{valor}!" if eh_jogador else (f"{valor}!" if critico else str(valor))
        self.texto_surf = fonte.render(texto, True, cor)

    def update(self):
        # Easing out: desacelera conforme sobe
        self.vel.y *= 0.92
        self.vel.x *= 0.95
        self.pos   += self.vel
        self.vida  -= 1

    @property
    def vivo(self):
        return self.vida > 0

    def desenhar(self, superficie, offset):
        # Fade-out na segunda metade da vida
        progresso = self.vida / self.vida_max
        if progresso < 0.5:
            alpha = int(255 * (progresso / 0.5))
            surf  = self.texto_surf.copy()
            surf.set_alpha(alpha)
        else:
            surf = self.texto_surf

        pos_tela = self.pos + offset
        # Centraliza o texto na posição
        superficie.blit(surf, (
            int(pos_tela.x) - surf.get_width()  // 2,
            int(pos_tela.y) - surf.get_height() // 2,
        ))


class GerenciadorNumeroDano:
    """Pool de números flutuantes. Mesma estratégia do GerenciadorParticulas."""

    MAX = 60   # raramente precisamos de mais que isso

    def __init__(self):
        self.numeros: list[NumeroDano] = []

    def adicionar(self, pos_mundo, valor, critico=False, eh_jogador=False):
        if len(self.numeros) < self.MAX:
            self.numeros.append(NumeroDano(pos_mundo, valor, critico, eh_jogador))

    def update(self):
        for n in self.numeros:
            n.update()
        self.numeros = [n for n in self.numeros if n.vivo]

    def desenhar(self, superficie, offset):
        for n in self.numeros:
            n.desenhar(superficie, offset)

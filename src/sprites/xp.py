import pygame
import math
from src.config import *

class XpGem(pygame.sprite.Sprite):
    def __init__(self, pos_mundo, valor):
        super().__init__()
        self.valor = valor
        # Tamanho varia com valor do XP
        tamanho = min(16, 8 + valor // 10)
        self._construir_imagem(tamanho)
        self.pos = pygame.math.Vector2(pos_mundo)
        self.rect = self.image.get_rect(center=self.pos)
        self.vel = pygame.math.Vector2(0, 0)
        self.velocidade_max = 12
        self.raio_magnetismo = 200
        self._bob_timer = 0   # animação de bobbing

    def _construir_imagem(self, s):
        """Losango ciano brilhante — comunica 'coletável de XP' visualmente."""
        self.image = pygame.Surface((s, s), pygame.SRCALPHA)
        cx, cy = s // 2, s // 2
        # Losango externo (sombra)
        pontos_ext = [(cx, 0), (s-1, cy), (cx, s-1), (0, cy)]
        pygame.draw.polygon(self.image, (0, 120, 140), pontos_ext)
        # Losango interno (cor principal)
        m = max(2, s // 5)
        pontos_int = [(cx, m), (s-1-m, cy), (cx, s-1-m), (m, cy)]
        pygame.draw.polygon(self.image, XP_COLOR, pontos_int)
        # Brilho pequeno no canto superior
        pygame.draw.circle(self.image, (200, 255, 255), (cx - s//6, cy - s//6), max(1, s//6))

    def update(self, pos_jogador):
        self._bob_timer += 1
        direcao = pos_jogador - self.pos
        distancia = direcao.length()

        if distancia < self.raio_magnetismo:
            if distancia > 0:
                desejo = direcao.normalize() * self.velocidade_max
                steer  = desejo - self.vel
                self.vel += steer * 0.1
                self.pos += self.vel

        self.rect.center = self.pos
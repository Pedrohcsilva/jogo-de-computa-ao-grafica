#####################################################
#  Classe Itens. Define o comportamento dos itens.
#####################################################

import pygame
import math
from src.config import *

class ItemArma(pygame.sprite.Sprite):
    def __init__(self, pos_mundo, tipo):
        super().__init__()
        self.tipo = tipo
        self.cor = AMARELO if tipo == "Metralhadora" else ROXO
        self._construir_imagem()
        
        self.pos = pygame.math.Vector2(pos_mundo)
        self.rect = self.image.get_rect(center=self.pos)
        
        self.tempo_vida = ITEM_VIDA
        self._bob = 0

    def _construir_imagem(self):
        """Estrela de 5 pontas colorida por tipo de arma."""
        s = 24
        self.image = pygame.Surface((s, s), pygame.SRCALPHA)
        cx, cy = s // 2, s // 2
        pontos = []
        for i in range(10):
            ang = math.radians(i * 36 - 90)
            r   = (s // 2 - 2) if i % 2 == 0 else (s // 4)
            pontos.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        cor_escura = tuple(max(0, c - 80) for c in self.cor)
        pygame.draw.polygon(self.image, cor_escura, pontos)
        pontos2 = []
        for i in range(10):
            ang = math.radians(i * 36 - 90)
            r   = ((s // 2 - 5) if i % 2 == 0 else (s // 4 - 2))
            pontos2.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        pygame.draw.polygon(self.image, self.cor, pontos2)
        # Brilho central
        pygame.draw.circle(self.image, (255, 255, 220), (cx, cy), 3)
        self._img_base = self.image.copy()

    def update(self):
        self._bob += 0.1
        self.rect.center = self.pos
        self.tempo_vida -= 1

        # Feedback visual: pisca quando resta 30% do tempo
        if self.tempo_vida < ITEM_VIDA * 0.3:
            if (self.tempo_vida // 10) % 2 == 0:
                self.image.set_alpha(0)
            else:
                self.image.set_alpha(255)
        
        if self.tempo_vida <= 0:
            self.kill()
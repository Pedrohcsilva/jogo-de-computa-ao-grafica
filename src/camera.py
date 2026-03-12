##########################################################
#  Câmera com Screen Shake.
#
#  MATEMÁTICA DO SCREEN SHAKE:
#   - Mantemos um "trauma" (0.0 → 1.0) que decai por frame.
#   - O offset real = random(-1,1) * MAX_OFFSET * trauma²
#   - Usar trauma² em vez de trauma deixa o início violento
#     e o fim suave — curva de easing quadrática.
##########################################################

import pygame
import random


class Camera:
    MAX_OFFSET = 20      # pixels máximos de deslocamento
    DECAIMENTO = 0.05    # quanto o trauma cai por frame

    def __init__(self):
        self.trauma = 0.0                       # 0 = parado, 1 = máximo shake
        self.offset = pygame.math.Vector2(0, 0) # offset base (centro da tela)

    # ── API pública ────────────────────────────────────────────────────

    def adicionar_shake(self, intensidade: float):
        """Soma trauma (clampado em 1.0). Chame ao causar/receber dano."""
        self.trauma = min(1.0, self.trauma + intensidade)

    def update(self, pos_jogador, largura, altura):
        """
        Calcula o offset de translação para renderizar o mundo.
        O shake é sobreposto ao offset de câmera normal.
        """
        # Offset de câmera: mantém o jogador no centro
        centro = pygame.math.Vector2(largura // 2, altura // 2)
        base   = centro - pos_jogador

        # Screen shake: deslocamento aleatório escalado por trauma²
        shake_x = random.uniform(-1, 1) * self.MAX_OFFSET * (self.trauma ** 2)
        shake_y = random.uniform(-1, 1) * self.MAX_OFFSET * (self.trauma ** 2)

        # Decai o trauma suavemente
        self.trauma = max(0.0, self.trauma - self.DECAIMENTO)

        self.offset = base + pygame.math.Vector2(shake_x, shake_y)
        return self.offset

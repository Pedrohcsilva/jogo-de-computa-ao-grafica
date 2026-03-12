##########################################################
#  Cinematica de Entrada do Boss.
#
#  MÁQUINA DE ESTADOS da intro:
#   IDLE      → aguarda ser ativada
#   ESCURECE  → overlay vai de 0 a 180 alpha (30 frames)
#   AVISO     → texto "⚠ BOSS INCOMING" pisca (60 frames)
#   SHAKE     → screen shake crescente sem texto (20 frames)
#   SPAWN     → sinaliza ao main.py para spawnar o boss
#   COMPLETO  → cinematica encerrada, jogo volta ao normal
#
#  O main.py consulta `intro.pronto_para_spawnar()` e
#  `intro.completo` para saber quando agir.
##########################################################

import pygame
from src.config import *


class BossIntro:
    IDLE      = "idle"
    ESCURECE  = "escurece"
    AVISO     = "aviso"
    SHAKE     = "shake"
    SPAWN     = "spawn"
    COMPLETO  = "completo"

    def __init__(self, largura, altura, camera):
        self.largura = largura
        self.altura  = altura
        self.camera  = camera

        self.estado  = self.IDLE
        self.timer   = 0

        # Overlay de escurecimento
        self.overlay_alpha = 0
        self._overlay_surf = pygame.Surface((largura, altura), pygame.SRCALPHA)

        # Fontes
        self._fonte_aviso = pygame.font.SysFont("Arial", 64, bold=True)
        self._fonte_sub   = pygame.font.SysFont("Arial", 28, bold=True)

        self._spawnou = False  # flag consumível para o main.py

    # ── API pública ───────────────────────────────────────────────

    def iniciar(self):
        """Chame quando a fase do boss for atingida."""
        if self.estado == self.IDLE:
            self.estado = self.ESCURECE
            self.timer  = 0

    @property
    def ativo(self):
        """True enquanto a cinematica não terminou."""
        return self.estado not in (self.IDLE, self.COMPLETO)

    @property
    def completo(self):
        return self.estado == self.COMPLETO

    def pronto_para_spawnar(self):
        """
        Consumível: retorna True UMA VEZ quando é hora de criar o boss.
        O main.py deve chamar isso a cada frame durante a cinematica.
        """
        if self.estado == self.SPAWN and not self._spawnou:
            self._spawnou = True
            return True
        return False

    def resetar(self):
        self.estado        = self.IDLE
        self.timer         = 0
        self.overlay_alpha = 0
        self._spawnou      = False

    # ── Update ────────────────────────────────────────────────────

    def update(self):
        if not self.ativo:
            return

        self.timer += 1

        if self.estado == self.ESCURECE:
            # Alpha sobe de 0 a 160 em 30 frames
            self.overlay_alpha = min(160, int(160 * self.timer / 30))
            if self.timer >= 30:
                self.estado = self.AVISO
                self.timer  = 0

        elif self.estado == self.AVISO:
            # Pisca por 60 frames
            if self.timer >= 60:
                self.estado = self.SHAKE
                self.timer  = 0

        elif self.estado == self.SHAKE:
            # Shake crescente por 20 frames
            intensidade = 0.3 + (self.timer / 20) * 0.7
            self.camera.adicionar_shake(intensidade * 0.15)
            if self.timer >= 20:
                self.estado = self.SPAWN
                self.timer  = 0

        elif self.estado == self.SPAWN:
            # Aguarda 5 frames após spawnar para o boss aparecer visualmente
            if self.timer >= 5:
                self.estado        = self.COMPLETO
                self.overlay_alpha = 0

    # ── Desenho ───────────────────────────────────────────────────

    def desenhar(self, superficie):
        if not self.ativo:
            return

        # Overlay escuro
        if self.overlay_alpha > 0:
            self._overlay_surf.fill((0, 0, 0, self.overlay_alpha))
            superficie.blit(self._overlay_surf, (0, 0))

        cx = self.largura  // 2
        cy = self.altura // 2

        if self.estado == self.AVISO:
            # Pisca a cada 8 frames
            if (self.timer // 8) % 2 == 0:
                # Sombra do texto
                sombra = self._fonte_aviso.render("⚠  BOSS INCOMING  ⚠", True, PRETO)
                superficie.blit(sombra, sombra.get_rect(center=(cx + 3, cy - 37)))
                # Texto principal vermelho
                texto = self._fonte_aviso.render("⚠  BOSS INCOMING  ⚠", True, VERMELHO)
                superficie.blit(texto, texto.get_rect(center=(cx, cy - 40)))

            # Subtítulo fixo
            sub = self._fonte_sub.render("Prepare-se...", True, (180, 180, 180))
            superficie.blit(sub, sub.get_rect(center=(cx, cy + 30)))

        elif self.estado == self.SHAKE:
            # Texto some gradualmente durante o shake
            alpha = max(0, int(255 * (1 - self.timer / 20)))
            texto = self._fonte_aviso.render("⚠  BOSS INCOMING  ⚠", True, VERMELHO)
            texto.set_alpha(alpha)
            superficie.blit(texto, texto.get_rect(center=(cx, cy - 40)))

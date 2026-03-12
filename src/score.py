##########################################################
#  Sistema de Score com Multiplicador de Combo
#
#  MECÂNICA:
#   Matar inimigos consecutivos sem tomar dano acumula combo.
#   Cada kill vale: xp_valor * multiplicador_atual.
#
#  MULTIPLICADOR:
#   combo 1–4   → 1x   (azul)
#   combo 5–9   → 2x   (verde)
#   combo 10–19 → 3x   (amarelo)
#   combo 20+   → 5x   (vermelho pulsante)
#
#  RESET:
#   Tomar qualquer dano → combo volta a 0, multiplicador a 1x.
#
#  HIGHSCORE:
#   Salvo em JSON no diretório do jogo.
#   Carregado na inicialização e comparado ao sair.
##########################################################

import json
import os
import pygame
from src.config import *

HIGHSCORE_FILE = "highscore.json"


def _carregar_highscore() -> int:
    try:
        with open(HIGHSCORE_FILE) as f:
            return int(json.load(f).get("highscore", 0))
    except (FileNotFoundError, ValueError, KeyError):
        return 0


def _salvar_highscore(valor: int):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump({"highscore": valor}, f)


class GerenciadorScore:
    """Acumula pontos, gerencia combo e persiste highscore."""

    # Thresholds de combo → (multiplicador, cor_display)
    _NIVEIS_COMBO = [
        (20, 5, (255,  60,  60)),   # ≥20 kills → 5x  vermelho
        (10, 3, (255, 215,   0)),   # ≥10 kills → 3x  amarelo
        ( 5, 2, ( 80, 255, 120)),   # ≥ 5 kills → 2x  verde
        ( 0, 1, (150, 150, 200)),   # padrão    → 1x  azul-cinza
    ]

    def __init__(self):
        self.score     = 0
        self.combo     = 0          # kills consecutivos sem tomar dano
        self.highscore = _carregar_highscore()

        # Display transitório do multiplicador (pisca ao mudar)
        self._mult_anterior   = 1
        self._flash_mult_timer = 0

        # Fonte — criada uma vez
        self._fonte_score = pygame.font.SysFont("Arial", 22, bold=True)
        self._fonte_combo  = pygame.font.SysFont("Arial", 18, bold=True)
        self._fonte_mult   = pygame.font.SysFont("Arial", 32, bold=True)

    # ── Propriedades calculadas ───────────────────────────────────────

    @property
    def multiplicador(self) -> int:
        for threshold, mult, _ in self._NIVEIS_COMBO:
            if self.combo >= threshold:
                return mult
        return 1

    @property
    def _cor_mult(self) -> tuple:
        for threshold, mult, cor in self._NIVEIS_COMBO:
            if self.combo >= threshold:
                return cor
        return (150, 150, 200)

    # ── API pública ───────────────────────────────────────────────────

    def registrar_kill(self, xp_valor: int):
        """
        Chame ao matar qualquer inimigo (ou boss).
        Incrementa combo e adiciona pontos com multiplicador.
        """
        self.combo += 1
        pontos      = xp_valor * self.multiplicador
        self.score += pontos

        # Flash se o multiplicador mudou
        novo_mult = self.multiplicador
        if novo_mult != self._mult_anterior:
            self._flash_mult_timer = 45   # frames de destaque
            self._mult_anterior    = novo_mult

        if self.score > self.highscore:
            self.highscore = self.score

    def registrar_dano(self):
        """Chame quando o jogador sofrer dano efetivo (não bloqueado por i-frames)."""
        self.combo = 0
        self._mult_anterior = 1

    def reset(self):
        """Reset completo ao recomeçar (salva highscore antes)."""
        _salvar_highscore(self.highscore)
        self.score = 0
        self.combo = 0
        self._mult_anterior    = 1
        self._flash_mult_timer = 0

    def salvar(self):
        _salvar_highscore(self.highscore)

    def update(self):
        if self._flash_mult_timer > 0:
            self._flash_mult_timer -= 1

    # ── HUD draw ──────────────────────────────────────────────────────

    def desenhar_hud(self, superficie, x, y):
        """
        Renderiza o bloco de score no canto da tela.
        Canto superior direito recomendado.
        """
        # Score atual
        s_score = self._fonte_score.render(
            f"SCORE  {self.score:>8}", True, BRANCO)
        superficie.blit(s_score, (x - s_score.get_width(), y))

        # Highscore
        s_hi = self._fonte_combo.render(
            f"BEST   {self.highscore:>8}", True, (140, 140, 160))
        superficie.blit(s_hi, (x - s_hi.get_width(), y + 26))

        # Multiplicador (só mostra se > 1x ou em flash)
        mult = self.multiplicador
        if mult > 1 or self._flash_mult_timer > 0:
            # Pulsa em tamanho quando acaba de mudar
            escala = 1.0 + 0.3 * (self._flash_mult_timer / 45) if self._flash_mult_timer > 0 else 1.0
            cor    = self._cor_mult

            txt = self._fonte_mult.render(f"×{mult}", True, cor)

            if escala != 1.0:
                w = int(txt.get_width() * escala)
                h = int(txt.get_height() * escala)
                txt = pygame.transform.scale(txt, (w, h))

            superficie.blit(txt, (x - txt.get_width(), y + 48))

        # Combo counter (kills sem tomar dano)
        if self.combo > 0:
            s_combo = self._fonte_combo.render(
                f"COMBO  {self.combo}", True, self._cor_mult)
            superficie.blit(s_combo, (x - s_combo.get_width(), y + 82))

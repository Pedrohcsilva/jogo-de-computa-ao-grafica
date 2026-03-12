##########################################################
#  Menu Principal — Tela de título do Bullet Haven.
#
#  ESTADOS:
#   "titulo"   → tela inicial (ENTER para jogar, Q para sair)
#   "controles" → exibe os controles do jogo
#   "creditos"  → créditos básicos
#
#  VISUAL:
#   Fundo animado com partículas flutuantes (mesmo estilo
#   biomecânico do jogo).
#   Título com brilho pulsante e scanlines estilizadas.
##########################################################

import pygame
import math
import random
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *
from src.persistence import SistemaPeristencia


class MenuPrincipal:
    """Tela de título exibida antes do jogo começar."""

    def __init__(self, largura: int, altura: int):
        self.largura  = largura
        self.altura   = altura
        self.ativo    = True          # False quando jogador confirma start
        self._estado  = "titulo"      # "titulo" | "controles"
        self._tick    = 0

        # Fontes
        self._fonte_titulo  = pygame.font.SysFont("Arial", 88, bold=True)
        self._fonte_sub     = pygame.font.SysFont("Arial", 28, bold=True)
        self._fonte_md      = pygame.font.SysFont("Arial", 22, bold=True)
        self._fonte_sm      = pygame.font.SysFont("Arial", 18)

        # Partículas decorativas do fundo
        self._particulas = [
            {
                "x": random.uniform(0, largura),
                "y": random.uniform(0, altura),
                "vx": random.uniform(-0.4, 0.4),
                "vy": random.uniform(-0.6, -0.1),
                "r":  random.randint(1, 3),
                "cor": random.choice([
                    (0, 200, 100), (0, 100, 255), (180, 50, 255),
                    (0, 255, 180), (255, 200, 0),
                ]),
                "alpha": random.randint(80, 200),
            }
            for _ in range(120)
        ]

        # Itens do menu
        self._itens = [
            {"label": "▶  JOGAR",      "acao": "jogar"},
        ]
        
        # Adiciona "Continuar" se houver save
        if SistemaPeristencia.existe_save():
            self._itens.insert(0, {"label": "↻  CONTINUAR", "acao": "continuar"})
        
        self._itens.extend([
            {"label": "⌨  CONTROLES",  "acao": "controles"},
            {"label": "✕  SAIR",        "acao": "sair"},
        ])
        self._selecionado = 0

    # ── API pública ───────────────────────────────────────────────────

    def processar_evento(self, evento) -> str | None:
        """
        Retorna:
          'jogar'  — inicia o jogo
          'sair'   — encerra
          None     — nada aconteceu
        """
        if not self.ativo:
            return None

        if self._estado == "controles":
            if evento.type == pygame.KEYDOWN:
                self._estado = "titulo"
            return None

        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self._selecionado = (self._selecionado - 1) % len(self._itens)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self._selecionado = (self._selecionado + 1) % len(self._itens)
            elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._confirmar()
            elif evento.key == pygame.K_ESCAPE:
                return "sair"

        if evento.type == pygame.MOUSEMOTION:
            # Hover com mouse
            for i, item in enumerate(self._itens):
                r = self._rect_item(i)
                if r.collidepoint(evento.pos):
                    self._selecionado = i

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, item in enumerate(self._itens):
                r = self._rect_item(i)
                if r.collidepoint(evento.pos):
                    self._selecionado = i
                    return self._confirmar()

        return None

    def _confirmar(self) -> str | None:
        acao = self._itens[self._selecionado]["acao"]
        if acao == "jogar":
            self.ativo = False
            return "jogar"
        elif acao == "continuar":
            self.ativo = False
            return "continuar"
        elif acao == "controles":
            self._estado = "controles"
            return None
        elif acao == "sair":
            return "sair"
        return None

    def _rect_item(self, idx: int) -> pygame.Rect:
        """Retorna o rect aproximado de cada item do menu para hover/click."""
        cy = self.altura // 2 + 30 + idx * 60
        return pygame.Rect(self.largura // 2 - 150, cy - 20, 300, 44)

    def update(self):
        self._tick += 1

        # Atualiza partículas de fundo
        for p in self._particulas:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            # Rebobina quando sai da tela
            if p["y"] < -10:
                p["y"] = self.altura + 5
                p["x"] = random.uniform(0, self.largura)

    def desenhar(self, superficie: pygame.Surface):
        if not self.ativo:
            return

        # Fundo escuro
        superficie.fill((6, 8, 14))

        # Partículas flutuantes
        for p in self._particulas:
            s = pygame.Surface((p["r"] * 2, p["r"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p["cor"], p["alpha"]), (p["r"], p["r"]), p["r"])
            superficie.blit(s, (int(p["x"]) - p["r"], int(p["y"]) - p["r"]))

        if self._estado == "controles":
            self._desenhar_controles(superficie)
        else:
            self._desenhar_titulo(superficie)

    def _desenhar_titulo(self, superficie: pygame.Surface):
        t   = self._tick
        W, H = self.largura, self.altura

        # ── Grade de fundo sutil ─────────────────────────────────────
        for x in range(0, W, 80):
            pygame.draw.line(superficie, (15, 25, 18), (x, 0), (x, H))
        for y in range(0, H, 80):
            pygame.draw.line(superficie, (15, 25, 18), (0, y), (W, y))

        # ── Título principal — glow pulsante ─────────────────────────
        pulso   = math.sin(t * 0.04)
        r_base  = int(0 + 40 * (0.5 + 0.5 * pulso))
        g_base  = int(200 + 55 * (0.5 + 0.5 * pulso))
        b_base  = int(80 + 60 * (0.5 + 0.5 * pulso))
        cor_titulo = (r_base, g_base, b_base)

        # Sombra
        sombra = self._fonte_titulo.render("BULLET HAVEN", True, (0, 0, 0))
        superficie.blit(sombra, sombra.get_rect(center=(W // 2 + 4, H // 2 - 190 + 4)))

        # Glow (versão borrada simulada com offset)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            glow = self._fonte_titulo.render("BULLET HAVEN", True,
                                             (r_base // 3, g_base // 3, b_base // 3))
            superficie.blit(glow, glow.get_rect(center=(W // 2 + dx, H // 2 - 190 + dy)))

        titulo = self._fonte_titulo.render("BULLET HAVEN", True, cor_titulo)
        superficie.blit(titulo, titulo.get_rect(center=(W // 2, H // 2 - 190)))

        # ── Subtítulo ────────────────────────────────────────────────
        sub = self._fonte_sub.render("15 FASES  •  3 BOSSES  •  ROGUELITE", True, (80, 120, 100))
        superficie.blit(sub, sub.get_rect(center=(W // 2, H // 2 - 110)))

        # Linha decorativa
        larg_linha = 400
        pygame.draw.line(superficie, (0, 120, 60),
                         (W // 2 - larg_linha // 2, H // 2 - 85),
                         (W // 2 + larg_linha // 2, H // 2 - 85), 1)

        # ── Itens do menu ────────────────────────────────────────────
        for i, item in enumerate(self._itens):
            cy       = H // 2 + 30 + i * 60
            selecion = (i == self._selecionado)

            # Fundo do item selecionado
            if selecion:
                pulso_item = 0.5 + 0.5 * math.sin(t * 0.12)
                alpha_bg   = int(40 + 30 * pulso_item)
                bg = pygame.Surface((320, 44), pygame.SRCALPHA)
                bg.fill((0, 200, 100, alpha_bg))
                pygame.draw.rect(bg, (0, 255, 120, 120), (0, 0, 320, 44), width=1, border_radius=6)
                superficie.blit(bg, bg.get_rect(center=(W // 2, cy)))

            cor = (0, 255, 130) if selecion else (140, 170, 150)
            txt = self._fonte_sub.render(item["label"], True, cor)
            superficie.blit(txt, txt.get_rect(center=(W // 2, cy)))

        # ── Dica de navegação ────────────────────────────────────────
        pisca = (t // 35) % 2 == 0
        if pisca:
            dica = self._fonte_sm.render("↑↓ navegar   ENTER confirmar   Q sair", True, (50, 80, 60))
            superficie.blit(dica, dica.get_rect(center=(W // 2, H - 50)))

        # ── Versão ───────────────────────────────────────────────────
        ver = self._fonte_sm.render("v3.0", True, (30, 50, 35))
        superficie.blit(ver, (W - 60, H - 30))

    def _desenhar_controles(self, superficie: pygame.Surface):
        W, H = self.largura, self.altura

        # Overlay semitransparente
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 210))
        superficie.blit(ov, (0, 0))

        titulo = self._fonte_sub.render("⌨  CONTROLES", True, (0, 255, 130))
        superficie.blit(titulo, titulo.get_rect(center=(W // 2, H // 2 - 200)))

        linhas = [
            ("WASD",         "Mover o personagem"),
            ("Mouse",        "Mirar"),
            ("Clique esq.",  "Atirar"),
            ("ESPAÇO",       "Usar poder especial"),
            ("ESC",          "Pausar / Continuar"),
            ("1 / 2 / 3",   "Escolher upgrade no level-up"),
            ("R",            "Reiniciar após Game Over"),
            ("Q",            "Sair do jogo"),
        ]

        for i, (tecla, desc) in enumerate(linhas):
            y = H // 2 - 140 + i * 46
            t_tecla = self._fonte_md.render(tecla, True, (0, 220, 110))
            t_desc  = self._fonte_md.render(desc,  True, (180, 200, 185))
            superficie.blit(t_tecla, t_tecla.get_rect(right=W // 2 - 20, centery=y))
            superficie.blit(t_desc,  t_desc.get_rect(left=W // 2 + 20,  centery=y))

            # Linha separadora
            if i < len(linhas) - 1:
                pygame.draw.line(superficie, (20, 40, 25),
                                 (W // 2 - 280, y + 22), (W // 2 + 280, y + 22))

        volta = self._fonte_sm.render("Pressione qualquer tecla para voltar", True, (60, 100, 70))
        superficie.blit(volta, volta.get_rect(center=(W // 2, H // 2 + 240)))

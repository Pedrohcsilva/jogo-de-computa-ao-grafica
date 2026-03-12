##########################################################
#  CartaFase — Menu de recompensa entre fases.
#
#  Aparece toda vez que o jogador completa uma fase normal
#  ou derrota um boss. Oferece 3 cartas especiais temáticas,
#  visualmente distintas do menu de level-up (que é
#  triggered por XP).
#
#  CATEGORIAS de carta:
#   🩸 SANGUE   — ofensivo (dano, cadência, perfuração)
#   🛡 FERRO    — defensivo (HP, escudo, regeneração)
#   ⚡ ÉTER     — utility (velocidade, XP, poder especial)
#   ☠ MALDIÇÃO — efeito poderoso com custo (trade-offs)
#
#  Visual: cards grandes em retrato (portrait), fundo
#  escuro com moldura colorida por categoria, animação
#  de entrada deslizando de baixo para cima.
##########################################################

import pygame
import math
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *


# ── Pool de cartas especiais ───────────────────────────────────────────
# Cada carta: id, nome, desc, categoria, cor, icone, efeito(fn), unica
CARTAS = [
    # ── 🩸 SANGUE (ofensivo) ─────────────────────────────────────────
    {
        "id": "carta_frenesi",
        "nome": "Frenesi de Combate",
        "desc": "Dano +25%\nCadência +20%",
        "cat": "SANGUE", "cor": (220, 40, 40), "icone": "🩸",
        "unica": False,
        "efeito": lambda p: (
            setattr(p, "dano_bala",   int(getattr(p, "dano_bala",   10) * 1.25)),
            setattr(p, "cadencia",    int(getattr(p, "cadencia",    500) * 0.80)),
        ),
    },
    {
        "id": "carta_perfurar",
        "nome": "Lança Sombria",
        "desc": "Balas atravessam\naté 5 inimigos",
        "cat": "SANGUE", "cor": (180, 20, 60), "icone": "🩸",
        "unica": True,
        "efeito": lambda p: setattr(p, "bala_perfurante", True) or
                             setattr(p, "_penetracoes_restantes_base", 5),
    },
    {
        "id": "carta_executar",
        "nome": "Execução",
        "desc": "Inimigos com\n< 20% HP explodem",
        "cat": "SANGUE", "cor": (200, 0, 0), "icone": "🩸",
        "unica": True,
        "efeito": lambda p: setattr(p, "carta_execucao", True),
    },
    {
        "id": "carta_sangue_frio",
        "nome": "Sangue Frio",
        "desc": "+30% dano quando\nHP < 40%",
        "cat": "SANGUE", "cor": (160, 0, 80), "icone": "🩸",
        "unica": True,
        "efeito": lambda p: setattr(p, "carta_sangue_frio", True),
    },
    {
        "id": "carta_metralhadora_plus",
        "nome": "Cano Quente",
        "desc": "Metralhadora:\n+3 projéteis em cone",
        "cat": "SANGUE", "cor": (210, 80, 20), "icone": "🩸",
        "unica": True,
        "efeito": lambda p: setattr(p, "carta_cano_quente", True),
    },

    # ── 🛡 FERRO (defensivo) ─────────────────────────────────────────
    {
        "id": "carta_fortaleza",
        "nome": "Fortaleza",
        "desc": "HP máx +50\nHP atual +30",
        "cat": "FERRO", "cor": (40, 120, 220), "icone": "🛡",
        "unica": False,
        "efeito": lambda p: (
            setattr(p, "hp_max", p.hp_max + 50),
            setattr(p, "hp",     min(p.hp + 30, p.hp_max + 50)),
        ),
    },
    {
        "id": "carta_regenerar",
        "nome": "Pulso Vital",
        "desc": "Regenera 3 HP/s\nautonamente",
        "cat": "FERRO", "cor": (20, 160, 100), "icone": "🛡",
        "unica": True,
        "efeito": lambda p: setattr(p, "regen_hp", getattr(p, "regen_hp", 0) + 3),
    },
    {
        "id": "carta_escudo_duplo",
        "nome": "Escudo Duplo",
        "desc": "Escudo passivo\nrecarga 50% mais\nrápido",
        "cat": "FERRO", "cor": (60, 140, 255), "icone": "🛡",
        "unica": True,
        "efeito": lambda p: setattr(p, "escudo_passivo", True) or
                             setattr(p, "carta_escudo_rapido", True),
    },
    {
        "id": "carta_cura_kill",
        "nome": "Sede de Sangue",
        "desc": "Cura 5 HP por\ninimigo morto",
        "cat": "FERRO", "cor": (80, 200, 120), "icone": "🛡",
        "unica": True,
        "efeito": lambda p: (
            setattr(p, "vampirismo", True),
            setattr(p, "_vampirismo_valor", 5),
        ),
    },
    {
        "id": "carta_invulneravel",
        "nome": "Pele de Pedra",
        "desc": "+60% duração\nde invencibilidade",
        "cat": "FERRO", "cor": (100, 100, 200), "icone": "🛡",
        "unica": True,
        "efeito": lambda p: setattr(p, "iframe_longo", True),
    },

    # ── ⚡ ÉTER (utility) ─────────────────────────────────────────────
    {
        "id": "carta_vento",
        "nome": "Vento Cortante",
        "desc": "Velocidade +3\nDash mais rápido",
        "cat": "ÉTER", "cor": (180, 220, 40), "icone": "⚡",
        "unica": False,
        "efeito": lambda p: setattr(p, "velocidade", p.velocidade + 3),
    },
    {
        "id": "carta_magnetismo_plus",
        "nome": "Núcleo Magnético",
        "desc": "Raio de coleta\nde XP triplicado",
        "cat": "ÉTER", "cor": (220, 200, 0), "icone": "⚡",
        "unica": True,
        "efeito": lambda p: setattr(p, "magnetismo", True) or
                             setattr(p, "carta_magnetismo_plus", True),
    },
    {
        "id": "carta_xp_surge",
        "nome": "Surge de Conhecimento",
        "desc": "XP ganho +50%\npor 3 fases",
        "cat": "ÉTER", "cor": (160, 240, 80), "icone": "⚡",
        "unica": False,
        "efeito": lambda p: setattr(p, "xp_bonus",
                                     getattr(p, "xp_bonus", 1.0) + 0.5),
    },
    {
        "id": "carta_poder_cd",
        "nome": "Sobrecarga Etérea",
        "desc": "Cooldown do poder\nespecial -40%",
        "cat": "ÉTER", "cor": (140, 80, 255), "icone": "⚡",
        "unica": True,
        "efeito": lambda p: setattr(p, "cooldown_poder_mult",
                                     getattr(p, "cooldown_poder_mult", 1.0) * 0.60),
    },
    {
        "id": "carta_ricochet_plus",
        "nome": "Bala Espiral",
        "desc": "Balas ricocheteiam\nem cadeia (2×)",
        "cat": "ÉTER", "cor": (200, 160, 255), "icone": "⚡",
        "unica": True,
        "efeito": lambda p: setattr(p, "bala_ricochet", True),
    },

    # ── ☠ MALDIÇÃO (trade-off poderoso) ─────────────────────────────
    {
        "id": "carta_pacto_sangue",
        "nome": "Pacto de Sangue",
        "desc": "Dano ×2\nHP máx -40",
        "cat": "MALDIÇÃO", "cor": (160, 0, 160), "icone": "☠",
        "unica": True,
        "efeito": lambda p: (
            setattr(p, "dano_bala", int(getattr(p, "dano_bala", 10) * 2)),
            setattr(p, "hp_max",    max(20, p.hp_max - 40)),
            setattr(p, "hp",        min(p.hp, p.hp_max - 40)),
        ),
    },
    {
        "id": "carta_fantasma",
        "nome": "Forma Fantasma",
        "desc": "Velocidade ×2\nHP permanece\nem 1 HP",
        "cat": "MALDIÇÃO", "cor": (120, 0, 200), "icone": "☠",
        "unica": True,
        "efeito": lambda p: (
            setattr(p, "velocidade", p.velocidade * 2),
            setattr(p, "hp",        1),
            setattr(p, "hp_max",    1),
        ),
    },
    {
        "id": "carta_berserk",
        "nome": "Êxtase Berserk",
        "desc": "Cadência ×3\nBala dano -30%",
        "cat": "MALDIÇÃO", "cor": (200, 40, 120), "icone": "☠",
        "unica": True,
        "efeito": lambda p: (
            setattr(p, "cadencia",  int(getattr(p, "cadencia", 500) // 3)),
            setattr(p, "dano_bala", max(1, int(getattr(p, "dano_bala", 10) * 0.70))),
        ),
    },
    {
        "id": "carta_necronomico",
        "nome": "Necronomicon",
        "desc": "Inimigos mortos\nvoltam como aliados\n(1 a cada 10 kills)",
        "cat": "MALDIÇÃO", "cor": (80, 0, 80), "icone": "☠",
        "unica": True,
        "efeito": lambda p: setattr(p, "carta_necronomico", True),
    },
]

# Mapeamento categoria → cor de fundo escuro
_COR_FUNDO = {
    "SANGUE":   (35, 8,  8),
    "FERRO":    (8,  18, 38),
    "ÉTER":     (18, 30, 8),
    "MALDIÇÃO": (25, 5,  28),
}


class CartaFaseMenu:
    """Menu de escolha de carta especial entre fases."""

    CARD_W = 240
    CARD_H = 310

    def __init__(self, largura: int, altura: int):
        self.largura  = largura
        self.altura   = altura
        self.ativo    = False
        self.opcoes: list[dict] = []
        self._adquiridas: set[str] = set()

        self._selecionado = -1
        self._card_rects: list[pygame.Rect] = []

        # Animação de entrada (slide de baixo)
        self._anim_y   = 0.0   # 0.0 = fora da tela, 1.0 = posição final
        self._fase_num = 1

        # Fontes
        self._fonte_tit  = pygame.font.SysFont("Arial", 46, bold=True)
        self._fonte_sub  = pygame.font.SysFont("Arial", 19)
        self._fonte_cat  = pygame.font.SysFont("Arial", 14, bold=True)
        self._fonte_nome = pygame.font.SysFont("Arial", 22, bold=True)
        self._fonte_desc = pygame.font.SysFont("Arial", 17)
        self._fonte_ico  = pygame.font.SysFont("Segoe UI Emoji", 36)

    # ── API pública ───────────────────────────────────────────────────

    def sortear(self, fase: int):
        """Sorteia 3 cartas e ativa o menu."""
        self._fase_num = fase
        pool = [c for c in CARTAS
                if not (c["unica"] and c["id"] in self._adquiridas)]
        # Tenta garantir 1 carta de cada tipo diferente
        cats = {}
        for c in pool:
            cats.setdefault(c["cat"], []).append(c)

        escolhidas = []
        # 1 carta de categoria aleatória diferente
        for cat in random.sample(list(cats.keys()), min(3, len(cats))):
            if len(escolhidas) < 3:
                escolhidas.append(random.choice(cats[cat]))

        # Completa com aleatório se precisar
        while len(escolhidas) < 3 and pool:
            c = random.choice(pool)
            if c not in escolhidas:
                escolhidas.append(c)

        self.opcoes       = escolhidas[:3]
        self._selecionado = -1
        self._card_rects  = []
        self._anim_y      = 0.0
        self.ativo        = True

    def processar_evento(self, evento, jogador) -> bool:
        """Retorna True quando o jogador escolheu uma carta."""
        if not self.ativo:
            return False

        mapa = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
        if evento.type == pygame.KEYDOWN and evento.key in mapa:
            idx = mapa[evento.key]
            if idx < len(self.opcoes):
                return self._escolher(idx, jogador)

        if evento.type == pygame.MOUSEMOTION:
            self._selecionado = -1
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(evento.pos):
                    self._selecionado = i

        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, r in enumerate(self._card_rects):
                if r.collidepoint(evento.pos):
                    return self._escolher(i, jogador)

        return False

    def atualizar(self):
        """Avança animação de entrada."""
        if self.ativo and self._anim_y < 1.0:
            self._anim_y = min(1.0, self._anim_y + 0.07)

    def desenhar(self, superficie: pygame.Surface):
        if not self.ativo:
            return

        # Easing suave (ease-out cubic)
        t   = self._anim_y
        eas = 1 - (1 - t) ** 3

        # Overlay escuro
        ov = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        alpha_ov = int(200 * eas)
        ov.fill((0, 0, 0, alpha_ov))
        superficie.blit(ov, (0, 0))

        if eas < 0.05:
            return

        cx = self.largura  // 2
        cy = self.altura   // 2

        # ── Título ────────────────────────────────────────────────────
        titulo_y = int(cy - 210 + (1 - eas) * 80)
        tit = self._fonte_tit.render(f"✦  FASE {self._fase_num} CONCLUÍDA  ✦", True, (255, 220, 60))
        sombra = self._fonte_tit.render(f"✦  FASE {self._fase_num} CONCLUÍDA  ✦", True, (120, 80, 0))
        superficie.blit(sombra, sombra.get_rect(center=(cx + 3, titulo_y + 3)))
        superficie.blit(tit,    tit.get_rect(center=(cx, titulo_y)))

        sub = self._fonte_sub.render("Escolha sua recompensa de fase  —  teclas 1 / 2 / 3  ou  clique", True, (160, 160, 160))
        superficie.blit(sub, sub.get_rect(center=(cx, titulo_y + 52)))

        # ── Cards ─────────────────────────────────────────────────────
        gap      = 34
        total_w  = len(self.opcoes) * self.CARD_W + (len(self.opcoes) - 1) * gap
        start_x  = cx - total_w // 2
        card_y   = int(cy - self.CARD_H // 2 + 30 + (1 - eas) * 120)

        self._card_rects = []
        tick = pygame.time.get_ticks()

        for i, carta in enumerate(self.opcoes):
            cx_card = start_x + i * (self.CARD_W + gap)
            rect    = pygame.Rect(cx_card, card_y, self.CARD_W, self.CARD_H)
            self._card_rects.append(rect)

            hover   = (i == self._selecionado)
            cor     = carta["cor"]
            cor_fundo = _COR_FUNDO.get(carta["cat"], (15, 15, 20))

            # Offset hover (levanta o card)
            offset_y = -10 if hover else 0
            rect_draw = rect.move(0, offset_y)

            # Sombra
            pygame.draw.rect(superficie, (5, 5, 8),
                             rect_draw.move(6, 8), border_radius=16)

            # Fundo do card
            pygame.draw.rect(superficie, cor_fundo,
                             rect_draw, border_radius=16)

            # Glow externo no hover
            if hover:
                glow_r = rect_draw.inflate(12, 12)
                glow_s = pygame.Surface((glow_r.w, glow_r.h), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (*cor, 70),
                                 (0, 0, glow_r.w, glow_r.h), border_radius=20)
                superficie.blit(glow_s, glow_r.topleft)

            # Borda pulsante
            pulso = 0.5 + 0.5 * math.sin(tick / 400 + i)
            borda_alpha = int(180 + 75 * pulso) if hover else int(100 + 80 * pulso)
            borda_cor = tuple(min(255, int(c * borda_alpha / 255)) for c in cor)
            pygame.draw.rect(superficie, borda_cor, rect_draw,
                             width=(3 if hover else 2), border_radius=16)

            # Faixa de categoria (topo do card)
            faixa = pygame.Rect(rect_draw.x, rect_draw.y, self.CARD_W, 32)
            pygame.draw.rect(superficie, cor, faixa,
                             border_radius=16)
            pygame.draw.rect(superficie, cor,
                             (faixa.x, faixa.y + 16, faixa.w, 16))

            cat_txt = self._fonte_cat.render(carta["cat"], True, (255, 255, 255))
            superficie.blit(cat_txt, cat_txt.get_rect(center=faixa.center))

            # Ícone grande
            ico = self._fonte_ico.render(carta["icone"], True, cor)
            superficie.blit(ico, ico.get_rect(center=(rect_draw.centerx, rect_draw.y + 74)))

            # Número da tecla
            num = self._fonte_desc.render(f"[{i + 1}]", True, (120, 120, 140))
            superficie.blit(num, (rect_draw.x + 8, rect_draw.y + 38))

            # Nome
            nome = self._fonte_nome.render(carta["nome"], True, (255, 255, 255))
            superficie.blit(nome, nome.get_rect(center=(rect_draw.centerx, rect_draw.y + 122)))

            # Linha separadora
            pygame.draw.line(superficie, tuple(c // 2 for c in cor),
                             (rect_draw.x + 20, rect_draw.y + 142),
                             (rect_draw.right - 20, rect_draw.y + 142), 1)

            # Descrição (multi-linha)
            for j, linha in enumerate(carta["desc"].split("\n")):
                cor_desc = (200, 200, 200) if j == 0 else (150, 150, 170)
                txt = self._fonte_desc.render(linha, True, cor_desc)
                superficie.blit(txt, txt.get_rect(center=(rect_draw.centerx,
                                                            rect_draw.y + 165 + j * 26)))

            # Badge "ÚNICO" se aplicável
            if carta.get("unica"):
                badge = self._fonte_cat.render("◆ ÚNICA", True, (255, 200, 80))
                superficie.blit(badge, badge.get_rect(center=(rect_draw.centerx,
                                                               rect_draw.bottom - 30)))

            # Indicador de clique no hover
            if hover:
                pulso2 = abs((tick % 600) - 300) / 300
                alpha2 = int(140 + 115 * pulso2)
                clique = self._fonte_desc.render("▶  ESCOLHER  ◀", True, cor)
                clique.set_alpha(alpha2)
                superficie.blit(clique, clique.get_rect(
                    center=(rect_draw.centerx, rect_draw.bottom + 22)))

    # ── Internos ──────────────────────────────────────────────────────

    def _escolher(self, idx: int, jogador) -> bool:
        if idx >= len(self.opcoes):
            return False
        carta = self.opcoes[idx]
        try:
            carta["efeito"](jogador)
        except Exception as e:
            print(f"[CartaFase] Erro ao aplicar {carta['id']}: {e}")
        if carta["unica"]:
            self._adquiridas.add(carta["id"])
        self.ativo        = False
        self._selecionado = -1
        return True

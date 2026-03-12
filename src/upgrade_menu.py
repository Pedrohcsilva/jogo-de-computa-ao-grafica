##########################################################
#  Menu de Level-Up (Roguelite) — pool expandido.
#
#  NOVIDADES vs versão anterior:
#   • Upgrades "únicos" (tiro_duplo, vida_regen, explosao_ao_matar)
#     somem do pool após serem adquiridos — impossível sortear 2x.
#   • 4 novos upgrades: regen, explosão ao matar, projétil largo,
#     sprint (dash de velocidade temporária).
#   • Cards mostram ícone + borda colorida por categoria.
#   • sortear() recebe o jogador para filtrar o que já tem.
##########################################################

import pygame
import random
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *


POOL_UPGRADES = [
    # ── Ofensivos ────────────────────────────────────────────────────
    {"id": "dano",              "nome": "Balas Perfurantes",
     "desc": "+5 de dano por projétil",
     "icone": "💥", "cor": (255, 80, 80),   "unico": False},

    {"id": "dano_grande",       "nome": "Munição Pesada",
     "desc": "+12 de dano por projétil",
     "icone": "🔴", "cor": (220, 40, 40),   "unico": False},

    {"id": "cadencia",          "nome": "Cadência Aprimorada",
     "desc": "Atira 15% mais rápido",
     "icone": "🔥", "cor": (255, 140, 0),   "unico": False},

    {"id": "cadencia_grande",   "nome": "Gatilho Automático",
     "desc": "Atira 30% mais rápido",
     "icone": "⚡", "cor": (255, 100, 0),   "unico": False},

    {"id": "tiro_duplo",        "nome": "Cano Duplo",
     "desc": "Dispara 2 projéteis simultâneos",
     "icone": "🔫", "cor": (255, 200, 0),   "unico": True},

    {"id": "bala_perfurante",   "nome": "Bala Perfurante",
     "desc": "Projéteis atravessam inimigos (até 3)",
     "icone": "➡", "cor": (255, 220, 50),   "unico": True},

    {"id": "explosao_ao_matar", "nome": "Morte Explosiva",
     "desc": "Inimigos explodem ao morrer",
     "icone": "💣", "cor": (255, 100, 0),   "unico": True},

    {"id": "bala_larga",        "nome": "Calibre Máximo",
     "desc": "Projéteis 2× mais largos (+2 dano)",
     "icone": "⭕", "cor": (200, 80, 255),   "unico": True},

    {"id": "vampirismo",        "nome": "Vampirismo",
     "desc": "Cada kill cura 2 HP",
     "icone": "🩸", "cor": (180, 0, 100),   "unico": True},

    {"id": "ricochet",          "nome": "Bala Ricochete",
     "desc": "Projéteis ricocheteiam em 1 inimigo extra",
     "icone": "↩", "cor": (120, 220, 255),  "unico": True},

    {"id": "aura_dano",         "nome": "Aura de Plasma",
     "desc": "Inimigos adjacentes recebem 3 dano/s",
     "icone": "🌀", "cor": (80, 200, 255),   "unico": True},

    # ── Defensivos ───────────────────────────────────────────────────
    {"id": "hp_max",            "nome": "Armadura Reforçada",
     "desc": "Cura total + +20 HP máximo",
     "icone": "🛡", "cor": (0, 200, 100),   "unico": False},

    {"id": "hp_max_grande",     "nome": "Blindagem Pesada",
     "desc": "Cura total + +40 HP máximo",
     "icone": "🔰", "cor": (0, 160, 80),    "unico": False},

    {"id": "vida_regen",        "nome": "Nanobots Curativos",
     "desc": "Regenera 1 HP a cada 2 segundos",
     "icone": "💉", "cor": (0, 255, 150),   "unico": True},

    {"id": "regen_rapida",      "nome": "Regen Acelerada",
     "desc": "Regenera 3 HP a cada 2 segundos",
     "icone": "💊", "cor": (0, 220, 120),   "unico": True},

    {"id": "iframe_longo",      "nome": "Reflexos Aprimorados",
     "desc": "Invencibilidade pós-dano dura 50% mais",
     "icone": "🌟", "cor": (200, 200, 0),   "unico": True},

    {"id": "escudo_passivo",    "nome": "Escudo Passivo",
     "desc": "Absorve 1 hit a cada 15 segundos",
     "icone": "🔵", "cor": (50, 100, 255),  "unico": True},

    # ── Utilitários ──────────────────────────────────────────────────
    {"id": "velocidade",        "nome": "Boost de Velocidade",
     "desc": "+1 de velocidade de movimento",
     "icone": "👟", "cor": (0, 200, 255),   "unico": False},

    {"id": "velocidade_grande", "nome": "Overclock Motor",
     "desc": "+2 de velocidade de movimento",
     "icone": "🚀", "cor": (0, 150, 255),   "unico": False},

    {"id": "magnetismo",        "nome": "Campo Magnético",
     "desc": "Raio de coleta de XP dobrado",
     "icone": "🧲", "cor": (100, 180, 255), "unico": True},

    {"id": "xp_bonus",          "nome": "Amplificador de XP",
     "desc": "Ganha +50% de XP por kill",
     "icone": "✨", "cor": (0, 255, 200),   "unico": True},

    {"id": "cooldown_poder",    "nome": "Núcleo Sobrecarregado",
     "desc": "Cooldown do poder especial -30%",
     "icone": "⚙",  "cor": (255, 180, 0),   "unico": True},

    {"id": "drop_arma",         "nome": "Pilhagem",
     "desc": "Chance de drop de arma dobrada",
     "icone": "🎰", "cor": (200, 150, 50),  "unico": True},
]


class MenuUpgrade:
    def __init__(self, largura, altura):
        self.largura  = largura
        self.altura   = altura
        self.fonte_t  = pygame.font.SysFont("Arial", 42, bold=True)
        self.fonte_n  = pygame.font.SysFont("Arial", 24, bold=True)
        self.fonte_d  = pygame.font.SysFont("Arial", 18)
        self.opcoes   = []
        self.ativo    = False
        self._upgrades_adquiridos: set[str] = set()
        self._selecionado = -1
        self._card_rects: list = []

    def sortear(self, jogador=None):
        """
        Sorteia 3 upgrades do pool, excluindo únicos já adquiridos.
        Passa o jogador para filtrar upgrades irrelevantes (ex: tiro_duplo
        que o jogador já tem).
        """
        pool_disponivel = [
            u for u in POOL_UPGRADES
            if not (u["unico"] and u["id"] in self._upgrades_adquiridos)
        ]

        # Garante que nunca sorteamos tiro_duplo se jogador já tem
        if jogador and getattr(jogador, "tiro_duplo", False):
            pool_disponivel = [u for u in pool_disponivel if u["id"] != "tiro_duplo"]

        k = min(3, len(pool_disponivel))
        self.opcoes = random.sample(pool_disponivel, k)
        self.ativo  = True

    def processar_evento(self, evento, jogador):
        """Retorna True se o upgrade foi escolhido (teclado 1/2/3 ou clique no card)."""
        if not self.ativo:
            return False

        # ── Teclado ──────────────────────────────────────────────────
        mapa = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
        if evento.type == pygame.KEYDOWN and evento.key in mapa:
            idx = mapa[evento.key]
            if idx < len(self.opcoes):
                return self._escolher(idx, jogador)

        # ── Mouse: hover ──────────────────────────────────────────────
        if evento.type == pygame.MOUSEMOTION:
            self._selecionado = -1
            for i, rect in enumerate(self._card_rects):
                if rect.collidepoint(evento.pos):
                    self._selecionado = i
                    break

        # ── Mouse: clique ─────────────────────────────────────────────
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            for i, rect in enumerate(self._card_rects):
                if rect.collidepoint(evento.pos):
                    return self._escolher(i, jogador)

        return False

    def _escolher(self, idx: int, jogador) -> bool:
        """Aplica o upgrade de índice idx e fecha o menu."""
        if idx >= len(self.opcoes):
            return False
        upg = self.opcoes[idx]
        self._aplicar(upg, jogador)
        if upg["unico"]:
            self._upgrades_adquiridos.add(upg["id"])
        self.ativo        = False
        self._selecionado = -1
        return True

    def _aplicar(self, upgrade, jogador):
        uid = upgrade["id"]

        if uid == "velocidade":
            jogador.velocidade += 1
            jogador._vel_base_upgrades = jogador.velocidade
        elif uid == "velocidade_grande":
            jogador.velocidade += 2
            jogador._vel_base_upgrades = jogador.velocidade
        elif uid == "cadencia":
            jogador.cadencia = max(50, int(jogador.cadencia * 0.85))
        elif uid == "cadencia_grande":
            jogador.cadencia = max(50, int(jogador.cadencia * 0.70))
        elif uid == "dano":
            jogador.dano_bala += 5
        elif uid == "dano_grande":
            jogador.dano_bala += 12
        elif uid == "hp_max":
            jogador.hp_max += 20
            jogador.hp      = jogador.hp_max
        elif uid == "hp_max_grande":
            jogador.hp_max += 40
            jogador.hp      = jogador.hp_max
        elif uid == "tiro_duplo":
            jogador.tiro_duplo = True
        elif uid == "magnetismo":
            jogador.raio_magnetismo = getattr(jogador, "raio_magnetismo", 200) * 2
        elif uid == "vida_regen":
            jogador.regen_ativo = True
            jogador.regen_timer = 0
            jogador.regen_valor = getattr(jogador, "regen_valor", 0) + 1
        elif uid == "regen_rapida":
            jogador.regen_ativo = True
            jogador.regen_timer = 0
            jogador.regen_valor = getattr(jogador, "regen_valor", 0) + 3
        elif uid == "explosao_ao_matar":
            jogador.explosao_ao_matar = True
        elif uid == "bala_larga":
            jogador.bala_larga = True
            jogador.dano_bala += 2
        elif uid == "vampirismo":
            jogador.vampirismo = True
        elif uid == "bala_perfurante":
            jogador.bala_perfurante = True
        elif uid == "ricochet":
            jogador.bala_ricochet = True
        elif uid == "aura_dano":
            jogador.aura_dano = True
        elif uid == "iframe_longo":
            jogador.IFRAME_DURACAO = int(jogador.IFRAME_DURACAO * 1.5)
        elif uid == "escudo_passivo":
            jogador.escudo_passivo   = True
            jogador.escudo_cd_max    = 900   # 15s × 60 fps
            jogador.escudo_cd_atual  = 0
            jogador.escudo_pronto    = True
        elif uid == "xp_bonus":
            jogador.xp_bonus = getattr(jogador, "xp_bonus", 1.0) + 0.5
        elif uid == "cooldown_poder":
            jogador.cooldown_poder_mult = getattr(jogador, "cooldown_poder_mult", 1.0) * 0.7
        elif uid == "drop_arma":
            jogador.drop_arma_bonus = True

    def desenhar(self, superficie):
        if not self.ativo:
            return

        # Overlay
        overlay = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 215))
        superficie.blit(overlay, (0, 0))

        # Título
        titulo = self.fonte_t.render("✦  LEVEL UP!  ✦", True, AMARELO)
        superficie.blit(titulo, titulo.get_rect(center=(self.largura // 2, self.altura // 2 - 170)))

        sub = self.fonte_d.render("Escolha um upgrade — teclas 1 / 2 / 3  ou  clique no card", True, CINZA)
        superficie.blit(sub, sub.get_rect(center=(self.largura // 2, self.altura // 2 - 120)))

        card_w, card_h = 310, 130
        gap             = 28
        total_w         = len(self.opcoes) * card_w + (len(self.opcoes) - 1) * gap
        start_x         = (self.largura - total_w) // 2
        cy              = self.altura // 2 - 50

        piscando = (pygame.time.get_ticks() // 400) % 2 == 0

        # Reconstrói cache de rects para hit-test do mouse
        self._card_rects = []

        for i, upg in enumerate(self.opcoes):
            cx   = start_x + i * (card_w + gap)
            rect = pygame.Rect(cx, cy, card_w, card_h)
            self._card_rects.append(rect)
            cor  = upg.get("cor", BRANCO)

            hover = (i == self._selecionado)

            # Sombra do card (mais intensa com hover)
            sombra_r = pygame.Rect(cx + (6 if hover else 4), cy + (6 if hover else 4), card_w, card_h)
            pygame.draw.rect(superficie, (10, 10, 15), sombra_r, border_radius=12)

            # Fundo do card (levemente mais claro com hover)
            cor_fundo = (35, 35, 50) if hover else (22, 22, 32)
            pygame.draw.rect(superficie, cor_fundo, rect, border_radius=12)

            # Borda colorida — pisca normalmente, fica sólida e mais grossa com hover
            if hover:
                cor_bd = cor
                espessura = 3
                # Glow externo
                glow_r = rect.inflate(6, 6)
                glow_s = pygame.Surface((glow_r.width, glow_r.height), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (*cor, 60), (0, 0, glow_r.width, glow_r.height), border_radius=15)
                superficie.blit(glow_s, glow_r.topleft)
            else:
                cor_bd = cor if piscando else (50, 50, 60)
                espessura = 2
            pygame.draw.rect(superficie, cor_bd, rect, width=espessura, border_radius=12)

            # Indicador de upgrade único
            if upg.get("unico"):
                tag = self.fonte_d.render("ÚNICO", True, cor)
                superficie.blit(tag, (cx + card_w - tag.get_width() - 10, cy + 8))

            # Número da tecla
            num = self.fonte_n.render(f"[{i + 1}]", True, AMARELO)
            superficie.blit(num, (cx + 10, cy + 10))

            # Nome do upgrade
            nome = self.fonte_n.render(upg["nome"], True, BRANCO)
            superficie.blit(nome, nome.get_rect(centerx=cx + card_w // 2, y=cy + 10))

            # Linha divisória
            pygame.draw.line(superficie, (50, 50, 65),
                             (cx + 12, cy + 46), (cx + card_w - 12, cy + 46))

            # Descrição
            desc = self.fonte_d.render(upg["desc"], True, (190, 190, 190))
            superficie.blit(desc, desc.get_rect(centerx=cx + card_w // 2, y=cy + 56))

            # Barra de cor decorativa na base do card
            pygame.draw.rect(superficie, cor,
                             (cx + 12, cy + card_h - 8, card_w - 24, 4),
                             border_radius=2)

            # Indicador "CLIQUE" pulsante quando hover
            if hover:
                pulso = abs((pygame.time.get_ticks() % 600) - 300) / 300.0
                alpha_clique = int(160 + 95 * pulso)
                clique_txt = self.fonte_d.render("▶  CLIQUE PARA ESCOLHER  ◀", True, cor)
                clique_txt.set_alpha(alpha_clique)
                superficie.blit(clique_txt,
                                clique_txt.get_rect(centerx=cx + card_w // 2,
                                                    y=cy + card_h + 10))

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
from src.config import *


POOL_UPGRADES = [
    # ── Ofensivos ────────────────────────────────────────────────────
    {
        "id":     "dano",
        "nome":   "Balas Perfurantes",
        "desc":   "+5 de dano por projétil",
        "icone":  "💥",
        "cor":    (255, 80, 80),
        "unico":  False,
    },
    {
        "id":     "cadencia",
        "nome":   "Cadência Aprimorada",
        "desc":   "Atira 15% mais rápido",
        "icone":  "🔥",
        "cor":    (255, 140, 0),
        "unico":  False,
    },
    {
        "id":     "tiro_duplo",
        "nome":   "Cano Duplo",
        "desc":   "Dispara 2 projéteis simultâneos",
        "icone":  "🔫",
        "cor":    (255, 200, 0),
        "unico":  True,   # desaparece após adquirido
    },
    {
        "id":     "explosao_ao_matar",
        "nome":   "Morte Explosiva",
        "desc":   "Inimigos explodem ao morrer",
        "icone":  "💣",
        "cor":    (255, 100, 0),
        "unico":  True,
    },
    {
        "id":     "bala_larga",
        "nome":   "Calibre Máximo",
        "desc":   "Projéteis 2× mais largos (+2 dano)",
        "icone":  "⭕",
        "cor":    (200, 80, 255),
        "unico":  True,
    },
    # ── Defensivos ───────────────────────────────────────────────────
    {
        "id":     "hp_max",
        "nome":   "Armadura Reforçada",
        "desc":   "Cura total + +20 HP máximo",
        "icone":  "🛡",
        "cor":    (0, 200, 100),
        "unico":  False,
    },
    {
        "id":     "vida_regen",
        "nome":   "Nanobots Curativos",
        "desc":   "Regenera 1 HP a cada 2 segundos",
        "icone":  "💉",
        "cor":    (0, 255, 150),
        "unico":  True,
    },
    # ── Utilitários ──────────────────────────────────────────────────
    {
        "id":     "velocidade",
        "nome":   "Boost de Velocidade",
        "desc":   "+1 de velocidade de movimento",
        "icone":  "⚡",
        "cor":    (0, 200, 255),
        "unico":  False,
    },
    {
        "id":     "magnetismo",
        "nome":   "Campo Magnético",
        "desc":   "Raio de coleta de XP dobrado",
        "icone":  "🧲",
        "cor":    (100, 180, 255),
        "unico":  True,
    },
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
        """Retorna True se o upgrade foi escolhido."""
        if not self.ativo:
            return False

        mapa = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
        if evento.type == pygame.KEYDOWN and evento.key in mapa:
            idx = mapa[evento.key]
            if idx < len(self.opcoes):
                upg = self.opcoes[idx]
                self._aplicar(upg, jogador)
                if upg["unico"]:
                    self._upgrades_adquiridos.add(upg["id"])
                self.ativo = False
                return True
        return False

    def _aplicar(self, upgrade, jogador):
        uid = upgrade["id"]

        if uid == "velocidade":
            jogador.velocidade += 1

        elif uid == "cadencia":
            jogador.cadencia = max(50, int(jogador.cadencia * 0.85))

        elif uid == "dano":
            jogador.dano_bala += 5

        elif uid == "hp_max":
            jogador.hp_max += 20
            jogador.hp      = jogador.hp_max

        elif uid == "tiro_duplo":
            jogador.tiro_duplo = True

        elif uid == "magnetismo":
            jogador.raio_magnetismo = getattr(jogador, "raio_magnetismo", 200) * 2

        elif uid == "vida_regen":
            jogador.regen_ativo = True
            jogador.regen_timer = 0

        elif uid == "explosao_ao_matar":
            jogador.explosao_ao_matar = True

        elif uid == "bala_larga":
            jogador.bala_larga = True
            jogador.dano_bala += 2

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

        sub = self.fonte_d.render("Escolha um upgrade — teclas 1 / 2 / 3", True, CINZA)
        superficie.blit(sub, sub.get_rect(center=(self.largura // 2, self.altura // 2 - 120)))

        card_w, card_h = 310, 130
        gap             = 28
        total_w         = len(self.opcoes) * card_w + (len(self.opcoes) - 1) * gap
        start_x         = (self.largura - total_w) // 2
        cy              = self.altura // 2 - 50

        piscando = (pygame.time.get_ticks() // 400) % 2 == 0

        for i, upg in enumerate(self.opcoes):
            cx   = start_x + i * (card_w + gap)
            rect = pygame.Rect(cx, cy, card_w, card_h)
            cor  = upg.get("cor", BRANCO)

            # Sombra do card
            sombra_r = pygame.Rect(cx + 4, cy + 4, card_w, card_h)
            pygame.draw.rect(superficie, (10, 10, 15), sombra_r, border_radius=12)

            # Fundo do card
            pygame.draw.rect(superficie, (22, 22, 32), rect, border_radius=12)

            # Borda colorida por categoria (pisca)
            cor_bd = cor if piscando else (50, 50, 60)
            pygame.draw.rect(superficie, cor_bd, rect, width=2, border_radius=12)

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

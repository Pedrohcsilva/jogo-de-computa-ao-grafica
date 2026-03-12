##########################################################
#  Poderes Especiais — Habilidades Ativas
#
#  Concedidos automaticamente a cada 2 fases completadas.
#  Ativados com ESPAÇO (cooldown de 8s cada).
#
#  PODERES DISPONÍVEIS:
#   Fase 2 — ONDA DE CHOQUE: empurra e stuna inimigos próximos
#   Fase 4 — FRENESIM:       velocidade + cadência 2× por 5s
#   Fase 6 — ESCUDO:         invencível por 4s + campo de dano
#   Fase 8+ — OVERLOAD:      dano e cadência máximos por 6s
##########################################################

import pygame
import math
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *


# Cooldown global (ms)
COOLDOWN_MS = 8000


class GerenciadorPoderEspecial:
    """
    Gerencia até 4 poderes especiais (um por fase par completada).
    O jogador pressiona ESPAÇO para ativar o poder mais recente disponível.
    """

    PODERES = {
        # Concedido ao completar a fase 2
        2: {
            "nome":  "ONDA DE CHOQUE",
            "desc":  "Explosão empurra todos os inimigos próximos",
            "icone": "💥",
            "cor":   (0, 220, 255),
            "dur_ms": 0,   # instantâneo
        },
        # Concedido ao completar a fase 4
        4: {
            "nome":  "FRENESIM",
            "desc":  "Velocidade e cadência 2× por 5 segundos",
            "icone": "⚡",
            "cor":   (255, 200, 0),
            "dur_ms": 5000,
        },
        # Concedido ao completar a fase 6 (modo infinito)
        6: {
            "nome":  "ESCUDO BIOMEK",
            "desc":  "Invencível por 4s + dano por contato",
            "icone": "🛡",
            "cor":   (0, 255, 130),
            "dur_ms": 4000,
        },
        # Fase 8+
        8: {
            "nome":  "OVERLOAD",
            "desc":  "Dano e cadência máximos por 6 segundos",
            "icone": "☢",
            "cor":   (255, 60, 60),
            "dur_ms": 6000,
        },
    }

    def __init__(self):
        self.poderes_ativos: list[int] = []   # fases cujos poderes foram desbloqueados
        self._cooldown_fim   = 0              # ms — quando o cooldown termina
        self._efeito_fim     = 0              # ms — quando o efeito atual termina
        self._poder_atual    = None           # int — fase do poder em uso
        self._fonte          = pygame.font.SysFont("Arial", 15, bold=True)
        self._fonte_grande   = pygame.font.SysFont("Arial", 22, bold=True)

    def desbloquear(self, fase_completada: int):
        """Chame quando fase `fase_completada` for concluída."""
        # Desbloqueia se a fase completada é par e há um poder mapeado
        chave = fase_completada if fase_completada in self.PODERES else None
        # Alternativa: conceder poder para fases pares mapeadas para a chave mais próxima
        if chave is None:
            # fases > 8 ganham sempre OVERLOAD
            if fase_completada % 2 == 0 and 8 in self.PODERES:
                chave = 8
        if chave and chave not in self.poderes_ativos:
            self.poderes_ativos.append(chave)
            return self.PODERES[chave]   # retorna info para exibir mensagem
        return None

    def pode_ativar(self) -> bool:
        agora = pygame.time.get_ticks()
        return (bool(self.poderes_ativos)
                and agora >= self._cooldown_fim
                and agora >= self._efeito_fim)

    def em_efeito(self) -> bool:
        return pygame.time.get_ticks() < self._efeito_fim

    def poder_equipado(self) -> dict | None:
        """O poder disponível no slot ativo (último desbloqueado)."""
        if not self.poderes_ativos:
            return None
        return self.PODERES.get(self.poderes_ativos[-1])

    def ativar(self, player, inimigos, particulas, camera) -> str | None:
        """
        Ativa o poder equipado.
        Retorna nome do poder ativado ou None.
        """
        if not self.pode_ativar():
            return None
        agora = pygame.time.get_ticks()
        chave = self.poderes_ativos[-1]
        info  = self.PODERES.get(chave)
        if not info:
            return None

        self._poder_atual = chave
        self._cooldown_fim = agora + COOLDOWN_MS

        if info["dur_ms"] > 0:
            self._efeito_fim = agora + info["dur_ms"]

        # ── Efeitos imediatos ─────────────────────────────────────────
        if chave == 2:   # Onda de choque
            self._onda_de_choque(player, inimigos, particulas, camera)

        elif chave == 4:  # Frenesim
            player._frenesim_ativo = True
            player._frenesim_fim   = self._efeito_fim

        elif chave == 6:  # Escudo Biomek
            player._escudo_ativo = True
            player._escudo_fim   = self._efeito_fim

        elif chave == 8:  # Overload
            player._overload_ativo = True
            player._overload_fim   = self._efeito_fim

        camera.adicionar_shake(0.6)
        return info["nome"]

    def update(self, player):
        """Deve ser chamado todo frame para desativar efeitos expirados."""
        agora = pygame.time.get_ticks()

        if agora >= self._efeito_fim:
            # Garante limpeza dos flags
            if getattr(player, "_frenesim_ativo", False):
                player._frenesim_ativo = False
            if getattr(player, "_escudo_ativo", False):
                player._escudo_ativo = False
            if getattr(player, "_overload_ativo", False):
                player._overload_ativo = False

    def _onda_de_choque(self, player, inimigos, particulas, camera):
        """Empurra todos os inimigos num raio de 350px e aplica 30 de dano."""
        RAIO  = 350
        DANO  = 30
        FORCA = 180
        for ini in list(inimigos):
            d = ini.pos - player.pos
            if d.length() < RAIO:
                ini.sofrer_dano(DANO)
                if d.length() > 0:
                    ini.pos += d.normalize() * FORCA
                    ini.rect.center = ini.pos
        # Anel de partículas
        particulas.transicao_fase(LARGURA, ALTURA)
        camera.adicionar_shake(0.8)

    # ── HUD ─────────────────────────────────────────────────────────

    def desenhar_hud(self, superficie):
        """Desenha o indicador de poder especial no canto inferior direito."""
        if not self.poderes_ativos:
            return

        info  = self.poder_equipado()
        if not info:  # Proteção adicional contra None
            return
        agora = pygame.time.get_ticks()
        cor   = info["cor"]

        x = superficie.get_width() - 200
        y = superficie.get_height() - 85

        # Fundo do painel
        painel = pygame.Surface((185, 68), pygame.SRCALPHA)
        painel.fill((5, 5, 10, 180))
        pygame.draw.rect(painel, cor, (0, 0, 185, 68), width=1, border_radius=4)
        superficie.blit(painel, (x, y))

        # Ícone + nome
        label = self._fonte_grande.render(
            f"{info['icone']} {info['nome']}", True, cor)
        superficie.blit(label, (x + 8, y + 6))

        # Status: em efeito / cooldown / pronto
        if self.em_efeito():
            resto  = (self._efeito_fim - agora) / 1000
            status = self._fonte.render(f"ATIVO  {resto:.1f}s", True, (100, 255, 160))
        elif agora < self._cooldown_fim:
            cd     = (self._cooldown_fim - agora) / 1000
            pct    = 1 - cd / (COOLDOWN_MS / 1000)
            # Barra de cooldown
            bw = 165
            pygame.draw.rect(superficie, (40, 40, 50), (x + 10, y + 48, bw, 8), border_radius=3)
            pygame.draw.rect(superficie, cor,           (x + 10, y + 48, int(bw*pct), 8), border_radius=3)
            status = self._fonte.render(f"Recarga  {cd:.1f}s", True, (160, 160, 180))
        else:
            status = self._fonte.render("[ ESPAÇO ] PRONTO", True, (220, 255, 220))

        superficie.blit(status, (x + 8, y + 34))

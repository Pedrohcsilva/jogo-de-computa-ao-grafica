##########################################################
#  Boss — Máquina de Estados (State Machine).
#
#  ESTADOS:
#   FASE1 (HP > 50%): patrulha + rajadas de 8 balas
#   FASE2 (HP < 50%): Bullet Hell — espirais + dash
#   MORTO: dispara burst final e remove
#
#  MATEMÁTICA DO BULLET HELL:
#   Espiral = atirar em ângulos incrementais a cada frame.
#   angulo_espiral += velocidade_rotacao → padrão giratório.
##########################################################

import pygame
import random
import math
from src.config import *
from src.sprites.bullets import BalaBoss


class Boss(pygame.sprite.Sprite):
    FASE1 = "fase1"
    FASE2 = "fase2"

    # Cores por fase
    COR_FASE1 = (200, 0,   50)
    COR_FASE2 = (255, 80, 200)  # Magenta agressivo na fase 2

    def __init__(self, pos_jogador):
        super().__init__()

        self.hp     = BOSS_HP
        self.hp_max = BOSS_HP
        self.estado = self.FASE1
        self.xp_valor = 200
        self.nome = "KRONOS"   # #16 — nome do boss

        # Sprite
        self._construir_imagem(self.COR_FASE1)

        angulo = random.uniform(0, math.tau)
        self.pos = pos_jogador + pygame.math.Vector2(
            math.cos(angulo), math.sin(angulo)) * 800

        self.rect       = self.image.get_rect(center=self.pos)
        self.velocidade = 1.8

        # Timers de ataque
        self.ultimo_tiro_rajada  = 0
        self.cadencia_rajada     = 1500   # ms
        self.angulo_espiral      = 0.0    # graus, incrementa a cada frame
        self.vel_espiral         = 4      # graus por frame
        self.ultimo_tiro_espiral = 0
        self.cadencia_espiral    = 120    # ms

        # Dash (fase 2)
        self.vel_dash     = 0.0
        self.dir_dash     = pygame.math.Vector2(0, 0)
        self.dash_duracao = 0

        # Hit flash
        self._flash_timer  = 0
        self._img_original = self.image.copy()
        self._img_flash    = self._criar_flash()

        # #15 FIX: fonte criada UMA VEZ no __init__ — não mais a cada frame
        self._fonte_barra  = pygame.font.SysFont("Arial", 16, bold=True)
        self._fonte_nome   = pygame.font.SysFont("Arial", 20, bold=True)

    def _construir_imagem(self, cor):
        w, h = BOSS_TAMANHO
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        # Corpo octogonal estilizado
        pontos = []
        for i in range(8):
            ang = math.radians(i * 45 - 22.5)
            px  = w // 2 + int(math.cos(ang) * (w // 2 - 3))
            py  = h // 2 + int(math.sin(ang) * (h // 2 - 3))
            pontos.append((px, py))
        pygame.draw.polygon(self.image, cor, pontos)
        pygame.draw.polygon(self.image, BRANCO, pontos, width=2)

    def _criar_flash(self):
        w, h = BOSS_TAMANHO
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((255, 255, 255, 240))
        return surf

    def sofrer_dano(self, valor):
        self.hp           -= valor
        self._flash_timer  = 6

        # Transição de fase
        if self.hp <= self.hp_max // 2 and self.estado == self.FASE1:
            self.estado = self.FASE2
            self._construir_imagem(self.COR_FASE2)
            self._img_original = self.image.copy()
            self._img_flash    = self._criar_flash()

    def update(self, pos_jogador, lista_disparos):
        agora = pygame.time.get_ticks()

        if self.estado == self.FASE1:
            self._update_fase1(pos_jogador, lista_disparos, agora)
        else:
            self._update_fase2(pos_jogador, lista_disparos, agora)

        # Hit flash
        if self._flash_timer > 0:
            self.image        = self._img_flash
            self._flash_timer -= 1
        else:
            self.image        = self._img_original

    # ── Fase 1: rajada de 8 balas em estrela ──────────────────────────

    def _update_fase1(self, pos_jogador, lista_disparos, agora):
        # Move lentamente em direção ao jogador
        dir_ao_jogador = pos_jogador - self.pos
        if dir_ao_jogador.length() > 0:
            self.pos += dir_ao_jogador.normalize() * self.velocidade
        self.rect.center = self.pos

        if agora - self.ultimo_tiro_rajada > self.cadencia_rajada:
            self.ultimo_tiro_rajada = agora
            self._disparar_estrela(lista_disparos, n_balas=8, cor=VERMELHO)

    # ── Fase 2: espiral + dash agressivo ─────────────────────────────

    def _update_fase2(self, pos_jogador, lista_disparos, agora):
        # Dash: acumula velocidade e depois freia
        if self.dash_duracao > 0:
            self.pos         += self.dir_dash * self.vel_dash
            self.vel_dash    *= 0.92
            self.dash_duracao -= 1
        else:
            # Move normalmente mas mais rápido
            dir_ao_jogador = pos_jogador - self.pos
            if dir_ao_jogador.length() > 0:
                self.pos += dir_ao_jogador.normalize() * self.velocidade * 1.6

            # Inicia novo dash aleatoriamente
            if random.random() < 0.003:
                self._iniciar_dash(pos_jogador)

        self.rect.center = self.pos

        # Espiral contínua
        if agora - self.ultimo_tiro_espiral > self.cadencia_espiral:
            self.ultimo_tiro_espiral = agora
            self._disparar_espiral(lista_disparos)

        # Rajada ocasional + mais densa
        if agora - self.ultimo_tiro_rajada > self.cadencia_rajada * 0.7:
            self.ultimo_tiro_rajada = agora
            self._disparar_estrela(lista_disparos, n_balas=12, cor=ROSA)

    def _disparar_estrela(self, lista_disparos, n_balas=8, cor=VERMELHO):
        """Dispara N balas igualmente espaçadas em 360°."""
        for i in range(n_balas):
            ang = math.radians(i * (360 / n_balas))
            direcao = pygame.math.Vector2(math.cos(ang), math.sin(ang))
            lista_disparos.append({
                "pos":  pygame.math.Vector2(self.pos),
                "dir":  direcao,
                "tipo": "boss",
                "cor":  cor,
            })

    def _disparar_espiral(self, lista_disparos):
        """
        Bullet Hell: dispara 3 balas com ângulos incrementais.
        O ângulo global aumenta a cada chamada → padrão espiral.
        """
        for offset in [0, 120, 240]:  # 3 braços da espiral
            ang = math.radians(self.angulo_espiral + offset)
            direcao = pygame.math.Vector2(math.cos(ang), math.sin(ang))
            lista_disparos.append({
                "pos":  pygame.math.Vector2(self.pos),
                "dir":  direcao,
                "tipo": "boss",
                "cor":  LARANJA,
            })
        self.angulo_espiral = (self.angulo_espiral + self.vel_espiral) % 360

    def _iniciar_dash(self, pos_jogador):
        dir_ao_jogador = pos_jogador - self.pos
        if dir_ao_jogador.length() > 0:
            self.dir_dash     = dir_ao_jogador.normalize()
            self.vel_dash     = 14
            self.dash_duracao = 20

    # ── Barra de vida do Boss (renderização) ─────────────────────────

    def desenhar_barra_vida(self, superficie):
        barra_w  = 400
        barra_h  = 20
        x        = (superficie.get_width()  - barra_w) // 2
        y        = superficie.get_height() - 50
        progresso = max(0, self.hp / self.hp_max)

        # Fundo
        pygame.draw.rect(superficie, CINZA,   (x, y, barra_w, barra_h), border_radius=4)
        # Vida
        cor_vida = self.COR_FASE2 if self.estado == self.FASE2 else self.COR_FASE1
        pygame.draw.rect(superficie, cor_vida, (x, y, int(barra_w * progresso), barra_h), border_radius=4)
        # Borda
        pygame.draw.rect(superficie, BRANCO,  (x, y, barra_w, barra_h), width=2, border_radius=4)

        # Nome do boss (#16) — usa fonte criada no __init__ (#15 FIX)
        fase_str = "— FASE 2 —" if self.estado == self.FASE2 else ""
        label = self._fonte_nome.render(f"⚠ {self.nome} {fase_str}", True, cor_vida)
        superficie.blit(label, (x + barra_w // 2 - label.get_width() // 2, y - 28))

        # HP numérico
        hp_txt = self._fonte_barra.render(f"{max(0,self.hp)} / {self.hp_max}", True, BRANCO)
        superficie.blit(hp_txt, hp_txt.get_rect(center=(x + barra_w // 2, y + barra_h // 2)))

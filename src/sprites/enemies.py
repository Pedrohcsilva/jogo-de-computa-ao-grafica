##########################################################
#  Inimigos — Herança simples + comunicação via lista.
#
#  PADRÃO DE DISPARO CORRIGIDO:
#   Inimigos NÃO retornam True. Eles depositam um dict
#   numa lista_disparos. O main.py processa a lista após
#   todos os updates — evita o bug do Group.update().
#
#  HIT FLASH: mesmo mecanismo do jogador.
##########################################################

import pygame
import random
import math
from src.config import *


class InimigoBase(pygame.sprite.Sprite):
    def __init__(self, pos_jogador, vel_base, hp=20,
                 cor=VERMELHO, tamanho=(30, 30), xp_valor=10):
        super().__init__()

        self.cor      = cor
        self.xp_valor = xp_valor
        self._construir_imagem(tamanho)

        # Spawn em anel ao redor do jogador
        angulo   = random.uniform(0, math.tau)
        dist     = 700
        self.pos = pos_jogador + pygame.math.Vector2(
            math.cos(angulo), math.sin(angulo)) * dist

        self.rect       = self.image.get_rect(center=self.pos)
        self.velocidade = vel_base
        self.hp         = hp
        self.hp_max     = hp

        # Hit flash
        self._flash_timer  = 0
        self._img_original = self.image.copy()
        self._img_flash    = self._criar_flash(tamanho)

    def _construir_imagem(self, tamanho):
        """
        Sprite vetorial por tipo de inimigo.
        InimigoBase: triângulo agressivo com olho central
        Subclasses sobrescrevem via _forma_sprite()
        """
        w, h = tamanho
        self.image = pygame.Surface(tamanho, pygame.SRCALPHA)
        self._desenhar_forma(w, h)

    def _desenhar_forma(self, w, h):
        """
        Inimigo base — criatura biomecânica:
        Célula parasita com membrana pulsante e núcleo tóxico.
        Cor vermelha sanguínea, aspecto orgânico-metálico.
        """
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 1

        # Membrana externa irregular (polígono orgânico)
        pts_ext = []
        n = 10
        for i in range(n):
            a = math.radians(i * (360 / n))
            jitter = 0.82 + 0.18 * math.sin(a * 3.7)
            pts_ext.append((cx + math.cos(a) * r * jitter,
                             cy + math.sin(a) * r * jitter))
        escuro = tuple(max(0, c - 70) for c in self.cor)
        pygame.draw.polygon(self.image, escuro, pts_ext)
        pygame.draw.polygon(self.image, self.cor, pts_ext)
        pygame.draw.polygon(self.image, (255, 120, 120, 160), pts_ext, width=1)

        # Camada interna translúcida
        pts_int = []
        for i in range(n):
            a = math.radians(i * (360 / n) + 18)
            jitter = 0.5 + 0.1 * math.sin(a * 2.3)
            pts_int.append((cx + math.cos(a) * r * jitter,
                             cy + math.sin(a) * r * jitter))
        medio = tuple(min(255, c + 30) for c in self.cor)
        pygame.draw.polygon(self.image, medio, pts_int)

        # Núcleo central brilhante
        pygame.draw.circle(self.image, (255, 255, 180), (cx, cy), max(2, r // 3))
        pygame.draw.circle(self.image, (30, 0, 0), (cx, cy), max(1, r // 5))
        # Reflexo
        pygame.draw.circle(self.image, (255, 255, 255),
                           (cx - r//5, cy - r//5), max(1, r // 6))

    def _criar_flash(self, tamanho):
        surf = pygame.Surface(tamanho, pygame.SRCALPHA)
        surf.fill((255, 255, 255, 230))
        return surf

    def sofrer_dano(self, valor):
        self.hp           -= valor
        self._flash_timer  = 6

    def _mover_para(self, pos_jogador):
        direcao = pos_jogador - self.pos
        if direcao.length() > 0:
            self.pos += direcao.normalize() * self.velocidade
        self.rect.center = self.pos

    def update(self, pos_jogador, lista_disparos):
        self._mover_para(pos_jogador)

        # Gerencia hit flash
        if self._flash_timer > 0:
            self.image        = self._img_flash
            self._flash_timer -= 1
        else:
            self.image        = self._img_original


# ── Variações ─────────────────────────────────────────────────────────

class InimigoRapido(InimigoBase):
    """Amarelo ácido: rápido, insectóide biomecânico — lâminas quitinosas."""
    def __init__(self, pos_jogador, vel_base):
        super().__init__(pos_jogador, vel_base * 1.8,
                         hp=10, cor=(200, 200, 0), tamanho=(22, 22), xp_valor=8)

    def _desenhar_forma(self, w, h):
        """Inseto predador — corpo fusiforme com mandíbulas laterais."""
        cx, cy = w // 2, h // 2

        # Corpo central — elipse estreita (horizontal = direção de ataque)
        pygame.draw.ellipse(self.image, (80, 70, 0),
                            (cx - 9, cy - 4, 18, 8))
        pygame.draw.ellipse(self.image, self.cor,
                            (cx - 8, cy - 3, 16, 6))

        # Mandíbulas frontais (apontam para a direita)
        for dy in (-5, 5):
            pts = [(cx + 4, cy + dy // 2),
                   (cx + 9, cy + dy),
                   (cx + 7, cy + dy // 3)]
            pygame.draw.polygon(self.image, (160, 160, 0), pts)

        # Asas translúcidas
        for dy, alpha in [(-6, 130), (6, 130)]:
            pts_asa = [(cx - 2, cy), (cx - 8, cy + dy), (cx + 2, cy + dy // 2)]
            pygame.draw.polygon(self.image, (220, 220, 80), pts_asa)

        # Olho composto (par)
        for dx in (-3, 3):
            pygame.draw.circle(self.image, (255, 50, 0), (cx + dx, cy), 2)
            pygame.draw.circle(self.image, (0, 0, 0), (cx + dx, cy), 1)


class InimigoTank(InimigoBase):
    """Vermelho escuro: golem biomecânico blindado — placas de quitina metálica."""
    def __init__(self, pos_jogador, vel_base):
        super().__init__(pos_jogador, vel_base * 0.6,
                         hp=50, cor=(160, 10, 10), tamanho=(48, 48), xp_valor=30)

    def _desenhar_forma(self, w, h):
        """Golem blindado — múltiplas camadas de armadura orgânico-metálica."""
        cx, cy = w // 2, h // 2

        # Corpo base maciço
        pygame.draw.circle(self.image, (50, 0, 0), (cx, cy), 21)
        pygame.draw.circle(self.image, (100, 5, 5), (cx, cy), 19)

        # Placas de armadura segmentadas (6 segmentos)
        for i in range(6):
            a0 = math.radians(i * 60 - 20)
            a1 = math.radians(i * 60 + 20)
            pts = [(cx, cy)]
            for t in range(6):
                a = a0 + (a1 - a0) * t / 5
                pts.append((cx + math.cos(a) * 19, cy + math.sin(a) * 19))
            brilho = (180, 20, 20) if i % 2 == 0 else (130, 10, 10)
            pygame.draw.polygon(self.image, brilho, pts)
            pygame.draw.line(self.image, (60, 0, 0), (cx, cy),
                             (int(cx + math.cos(math.radians(i*60))*20),
                              int(cy + math.sin(math.radians(i*60))*20)), 1)

        # Anel externo de energia
        pygame.draw.circle(self.image, (220, 40, 40), (cx, cy), 21, width=2)

        # Núcleo pulsante
        pygame.draw.circle(self.image, (10, 0, 0), (cx, cy), 8)
        pygame.draw.circle(self.image, (255, 60, 60), (cx, cy), 6)
        pygame.draw.circle(self.image, (255, 200, 200), (cx, cy), 3)

        # Espinhos defensivos
        for ang_deg in [45, 135, 225, 315]:
            a = math.radians(ang_deg)
            x0, y0 = cx + math.cos(a)*19, cy + math.sin(a)*19
            x1, y1 = cx + math.cos(a)*24, cy + math.sin(a)*24
            pygame.draw.line(self.image, (220, 60, 60),
                             (int(x0), int(y0)), (int(x1), int(y1)), 2)


class InimigoAtirador(InimigoBase):
    """Roxo: criatura biomecânica flutuante — olho central com tentáculos de energia."""
    def __init__(self, pos_jogador, vel_base):
        super().__init__(pos_jogador, vel_base * 0.7,
                         hp=30, cor=(170, 40, 255), tamanho=(34, 34), xp_valor=20)
        self.ultimo_tiro = pygame.time.get_ticks()
        self.cadencia    = 2000

    def _desenhar_forma(self, w, h):
        """Olho flutuante com tentáculos — criatura biomecânica de ataque à distância."""
        cx, cy = w // 2, h // 2

        # Aura externa (halo de energia)
        for r_off, alpha_cor in [(13, (60, 10, 100)), (11, (100, 20, 160))]:
            pts = []
            n = 12
            for i in range(n):
                a = math.radians(i * (360/n))
                jitter = 0.88 + 0.12 * math.sin(a * 4)
                pts.append((cx + math.cos(a) * r_off * jitter,
                             cy + math.sin(a) * r_off * jitter))
            pygame.draw.polygon(self.image, alpha_cor, pts)

        # Corpo principal — esfera roxo-escuro
        pygame.draw.circle(self.image, (70, 0, 110), (cx, cy), 10)
        pygame.draw.circle(self.image, (130, 20, 200), (cx, cy), 8)

        # Tentáculos de energia (6 ao redor)
        for i in range(6):
            a = math.radians(i * 60)
            x0 = cx + math.cos(a) * 8
            y0 = cy + math.sin(a) * 8
            x1 = cx + math.cos(a) * 13
            y1 = cy + math.sin(a) * 13
            cor_t = (200, 80, 255) if i % 2 == 0 else (140, 40, 200)
            pygame.draw.line(self.image, cor_t, (int(x0), int(y0)),
                             (int(x1), int(y1)), 2)
            pygame.draw.circle(self.image, (220, 120, 255),
                               (int(x1), int(y1)), 2)

        # Íris e pupila do olho central
        pygame.draw.circle(self.image, (220, 160, 255), (cx, cy), 5)
        pygame.draw.circle(self.image, (30, 0, 60), (cx, cy), 3)
        # Reflexo
        pygame.draw.circle(self.image, (255, 240, 255), (cx-1, cy-1), 1)

    def update(self, pos_jogador, lista_disparos):
        distancia_vetor = pos_jogador - self.pos
        distancia       = distancia_vetor.length()

        # Kiting: se longe, aproxima; se perto, recua levemente
        if distancia > 400:
            if distancia > 0:
                self.pos += distancia_vetor.normalize() * self.velocidade
        elif distancia < 200:
            if distancia > 0:
                self.pos -= distancia_vetor.normalize() * self.velocidade

        self.rect.center = self.pos

        # Timer de disparo
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro > self.cadencia:
            self.ultimo_tiro = agora
            if distancia > 0:
                # ─── CORRETO: deposita na lista em vez de retornar True ───
                lista_disparos.append({
                    "pos": pygame.math.Vector2(self.pos),
                    "dir": distancia_vetor.normalize(),
                    "tipo": "inimigo",
                })

        # Hit flash
        if self._flash_timer > 0:
            self.image        = self._img_flash
            self._flash_timer -= 1
        else:
            self.image        = self._img_original

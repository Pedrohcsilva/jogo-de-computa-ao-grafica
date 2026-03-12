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
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

    def _angulo_para(self, pos_jogador) -> float:
        """Ângulo em graus apontando para o jogador."""
        d = pos_jogador - self.pos
        if d.length() > 0:
            return -math.degrees(math.atan2(d.y, d.x))
        return 0.0

    def update(self, pos_jogador, lista_disparos):
        self._mover_para(pos_jogador)
        self._tick = getattr(self, "_tick", 0) + 1

        if self._flash_timer > 0:
            self.image        = self._img_flash
            self._flash_timer -= 1
        else:
            # Rotação suave em direção ao jogador
            angulo = self._angulo_para(pos_jogador)
            self.image = pygame.transform.rotate(self._img_original, angulo)
        self.rect = self.image.get_rect(center=self.pos)


# ── Variações ─────────────────────────────────────────────────────────

class InimigoRapido(InimigoBase):
    """Amarelo ácido: rápido, insectóide biomecânico — lâminas quitinosas."""
    def __init__(self, pos_jogador, vel_base, hp=None):
        if hp is None:
            hp = 10
        super().__init__(pos_jogador, vel_base * 1.8,
                         hp=hp, cor=(200, 200, 0), tamanho=(22, 22), xp_valor=8)

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
    def __init__(self, pos_jogador, vel_base, hp=None):
        if hp is None:
            hp = 50
        super().__init__(pos_jogador, vel_base * 0.6,
                         hp=hp, cor=(160, 10, 10), tamanho=(48, 48), xp_valor=30)

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
    def __init__(self, pos_jogador, vel_base, hp=None, cadencia_ms=2000, dano_tiro=12):
        if hp is None:
            hp = 30
        super().__init__(pos_jogador, vel_base * 0.7,
                         hp=hp, cor=(170, 40, 255), tamanho=(34, 34), xp_valor=20)
        self.ultimo_tiro  = pygame.time.get_ticks()
        self.cadencia     = cadencia_ms   # recebe da dificuldade
        self.dano_tiro    = dano_tiro     # recebe da dificuldade

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
                lista_disparos.append({
                    "pos":  pygame.math.Vector2(self.pos),
                    "dir":  distancia_vetor.normalize(),
                    "tipo": "inimigo",
                    "dano": self.dano_tiro,   # dano escalado pela dificuldade
                })

        # Hit flash + rotação em direção ao jogador
        if self._flash_timer > 0:
            self.image        = self._img_flash
            self._flash_timer -= 1
        else:
            angulo     = self._angulo_para(pos_jogador)
            self.image = pygame.transform.rotate(self._img_original, angulo)
        self.rect = self.image.get_rect(center=self.pos)


# ══════════════════════════════════════════════════════════════════════
#  NOVOS INIMIGOS — Fase 6+
# ══════════════════════════════════════════════════════════════════════

class InimigoViral(InimigoBase):
    """
    Ciano bioluminescente: ao morrer se DIVIDE em 2 fragmentos menores.
    Fragmentos têm metade do HP e não se dividem novamente.
    Usa flag `eh_fragmento` para evitar divisão recursiva.
    """
    def __init__(self, pos_jogador, vel_base, eh_fragmento: bool = False, hp=None):
        tamanho = (20, 20) if eh_fragmento else (32, 32)
        if hp is None:
            hp = 8 if eh_fragmento else 22
        xp      = 6 if eh_fragmento else 18
        # FIX: define eh_fragmento ANTES do super().__init__ porque
        # _desenhar_forma() é chamada dentro de __init__ e usa esse atributo
        self.eh_fragmento = eh_fragmento
        super().__init__(pos_jogador, vel_base * 1.1,
                         hp=hp, cor=(0, 230, 200), tamanho=tamanho, xp_valor=xp)

    def _desenhar_forma(self, w, h):
        """Célula mitótica — bolha ciano com divisão visível no centro."""
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 1

        # Membrana externa bioluminescente
        pts = []
        n = 14
        for i in range(n):
            a = math.radians(i * (360 / n))
            jitter = 0.80 + 0.20 * math.sin(a * 5)
            pts.append((cx + math.cos(a) * r * jitter,
                        cy + math.sin(a) * r * jitter))
        pygame.draw.polygon(self.image, (0, 60, 55), pts)
        pygame.draw.polygon(self.image, (0, 180, 160), pts)
        pygame.draw.polygon(self.image, (80, 255, 240), pts, width=1)

        if not self.eh_fragmento:
            # Linha de fissão no meio (indica que vai se dividir)
            pygame.draw.line(self.image, (0, 255, 220),
                             (cx, cy - r + 3), (cx, cy + r - 3), 1)

        # Núcleo interno
        pygame.draw.circle(self.image, (0, 100, 90), (cx, cy), max(2, r // 3))
        pygame.draw.circle(self.image, (0, 255, 200), (cx, cy), max(1, r // 5))
        # Reflexo
        pygame.draw.circle(self.image, (200, 255, 250), (cx - r//4, cy - r//4), 1)

    def gerar_fragmentos(self) -> list:
        """Retorna lista com 2 fragmentos centrados na posição atual."""
        if self.eh_fragmento:
            return []
        frags = []
        hp_frag = max(4, self.hp // 2)  # Metade do HP escalado da mãe
        for offset_x in (-15, 15):
            frag = InimigoViral.__new__(InimigoViral)
            # Inicializa como fragmento com posição ligeiramente deslocada
            frag.cor      = (0, 230, 200)
            frag.xp_valor = 6
            frag.eh_fragmento = True
            frag._construir_imagem((20, 20))
            frag.pos      = pygame.math.Vector2(self.pos.x + offset_x, self.pos.y)
            frag.rect     = frag.image.get_rect(center=frag.pos)
            frag.velocidade = self.velocidade * 1.3
            frag.hp       = hp_frag
            frag.hp_max   = hp_frag
            frag._flash_timer  = 0
            frag._img_original = frag.image.copy()
            frag._img_flash    = frag._criar_flash((20, 20))
            pygame.sprite.Sprite.__init__(frag)
            frag.image = frag._img_original.copy()
            frags.append(frag)
        return frags


class InimigoNecromante(InimigoBase):
    """
    Roxo escuro: a cada 4 segundos cura os inimigos mais próximos em 8 HP.
    Pulsação verde ao curar — alerta visual.
    Mantém distância do jogador (kiting).
    """
    def __init__(self, pos_jogador, vel_base, hp=None):
        if hp is None:
            hp = 35
        super().__init__(pos_jogador, vel_base * 0.65,
                         hp=hp, cor=(120, 0, 200), tamanho=(36, 36), xp_valor=35)
        self._cura_timer    = pygame.time.get_ticks()
        self._cura_cd_ms    = 4000
        self._cura_pulsando = 0   # frames de flash verde ao curar
        self._pedido_cura   = False  # FIX: inicializa flag para evitar AttributeError

    def _desenhar_forma(self, w, h):
        """Feiticeiro fantasma — capuz cônico com orbes flutuantes."""
        cx, cy = w // 2, h // 2

        # Manto base — triângulo arredondado (capuz)
        pts_manto = [
            (cx, cy - 15),
            (cx - 13, cy + 14),
            (cx + 13, cy + 14),
        ]
        pygame.draw.polygon(self.image, (40, 0, 70), pts_manto)
        pygame.draw.polygon(self.image, (90, 0, 150), pts_manto)
        pygame.draw.polygon(self.image, (160, 40, 255), pts_manto, width=1)

        # Símbolo de cura no centro (cruz estilizada)
        pygame.draw.line(self.image, (180, 80, 255), (cx - 5, cy), (cx + 5, cy), 2)
        pygame.draw.line(self.image, (180, 80, 255), (cx, cy - 5), (cx, cy + 5), 2)

        # Orbes flutuantes ao redor (4 esferas pequenas)
        for i in range(4):
            a = math.radians(i * 90 + 45)
            ox = cx + int(math.cos(a) * 12)
            oy = cy + int(math.sin(a) * 12)
            pygame.draw.circle(self.image, (60, 0, 100), (ox, oy), 3)
            pygame.draw.circle(self.image, (200, 100, 255), (ox, oy), 2)

        # Olho brilhante no centro do capuz
        pygame.draw.circle(self.image, (255, 180, 255), (cx, cy - 3), 4)
        pygame.draw.circle(self.image, (80, 0, 120), (cx, cy - 3), 2)

    def update(self, pos_jogador, lista_disparos):
        # Kiting — mantém distância de segurança
        d = pos_jogador - self.pos
        dist = d.length()
        if dist > 350:
            self.pos += d.normalize() * self.velocidade
        elif dist < 200:
            self.pos -= d.normalize() * self.velocidade
        self.rect.center = self.pos

        self._tick = getattr(self, "_tick", 0) + 1

        # Pulso visual de cura
        if self._cura_pulsando > 0:
            self._cura_pulsando -= 1

        # Timer de cura — guarda referência para main.py via atributo
        agora = pygame.time.get_ticks()
        if agora - self._cura_timer > self._cura_cd_ms:
            self._cura_timer    = agora
            self._cura_pulsando = 20
            self._pedido_cura   = True   # main.py lê e reseta
        
        # Hit flash
        if self._flash_timer > 0:
            if self._cura_pulsando > 0:
                # Flash verde durante cura
                flash_verde = pygame.Surface(self._img_original.get_size(), pygame.SRCALPHA)
                flash_verde.fill((0, 255, 100, 180))
                self.image        = flash_verde
            else:
                self.image        = self._img_flash
            self._flash_timer -= 1
        elif self._cura_pulsando > 0:
            # Glow verde pulsante (sem hit flash)
            overlay = self._img_original.copy()
            alpha   = int(120 * (self._cura_pulsando / 20))
            glow    = pygame.Surface(overlay.get_size(), pygame.SRCALPHA)
            glow.fill((0, 255, 100, alpha))
            overlay.blit(glow, (0, 0))
            angulo = self._angulo_para(pos_jogador)
            self.image = pygame.transform.rotate(overlay, angulo)
        else:
            angulo = self._angulo_para(pos_jogador)
            self.image = pygame.transform.rotate(self._img_original, angulo)
        self.rect = self.image.get_rect(center=self.pos)


class InimigoExplosivo(InimigoBase):
    """
    Laranja: rush direto no jogador e EXPLODE ao chegar perto.
    Ao morrer (HP ≤ 0) ou ao colidir, emite uma explosão em área.
    Pulsa em vermelho conforme se aproxima — alerta visual.
    """
    RAIO_EXPLOSAO = 90
    DANO_EXPLOSAO = 30

    def __init__(self, pos_jogador, vel_base, hp=None):
        if hp is None:
            hp = 18
        super().__init__(pos_jogador, vel_base * 1.25,
                         hp=hp, cor=(255, 130, 0), tamanho=(28, 28), xp_valor=22)
        self._explodiu        = False
        self._pedido_explosao = False  # FIX: inicializa flag para evitar AttributeError

    def _desenhar_forma(self, w, h):
        """Bomba orgânica — esfera de combustão com veias de plasma."""
        cx, cy = w // 2, h // 2
        r = min(w, h) // 2 - 1

        # Corpo esférico com veias de plasma
        pygame.draw.circle(self.image, (80, 30, 0), (cx, cy), r)
        pygame.draw.circle(self.image, (200, 80, 0), (cx, cy), r - 2)

        # Veias de plasma (raios irregulares)
        for i in range(6):
            a = math.radians(i * 60 + 15)
            x0 = cx + int(math.cos(a) * 3)
            y0 = cy + int(math.sin(a) * 3)
            x1 = cx + int(math.cos(a) * (r - 2))
            y1 = cy + int(math.sin(a) * (r - 2))
            pygame.draw.line(self.image, (255, 200, 50), (x0, y0), (x1, y1), 1)

        # Borda de combustão
        pygame.draw.circle(self.image, (255, 160, 0), (cx, cy), r, width=2)

        # Núcleo brilhante
        pygame.draw.circle(self.image, (255, 60, 0), (cx, cy), max(2, r // 3))
        pygame.draw.circle(self.image, (255, 220, 100), (cx, cy), max(1, r // 6))

    def update(self, pos_jogador, lista_disparos):
        # Rush direto
        self._mover_para(pos_jogador)
        self._tick = getattr(self, "_tick", 0) + 1

        # Verificar detonação por proximidade
        dist = (pos_jogador - self.pos).length()
        if dist < self.RAIO_EXPLOSAO and not self._explodiu:
            self._explodiu      = True
            self._pedido_explosao = True   # main.py lê e processa

        # Pulsa vermelho quanto mais perto do jogador
        if self._flash_timer > 0:
            self.image        = self._img_flash
            self._flash_timer -= 1
        else:
            # Intensidade do pulso baseada na proximidade
            pulso_int = max(0.0, 1.0 - dist / 400)
            if pulso_int > 0.2:
                overlay = self._img_original.copy()
                alpha   = int(180 * pulso_int)
                glow    = pygame.Surface(overlay.get_size(), pygame.SRCALPHA)
                glow.fill((255, 50, 0, alpha))
                overlay.blit(glow, (0, 0))
                self.image = overlay
            else:
                self.image = self._img_original.copy()
        self.rect = self.image.get_rect(center=self.pos)

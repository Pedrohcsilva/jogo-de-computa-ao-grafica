##########################################################
#  Jogador — Movimento, tiro, hit flash e estado.
#
#  HIT FLASH: guardamos a imagem original e trocamos
#  temporariamente por uma versão branca ao tomar dano.
##########################################################

import pygame
import math
from src.config import *


class Jogador(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # Sprite base (quadrado verde)
        self._construir_imagem()

        self.pos  = pygame.math.Vector2(0, 0)
        self.rect = self.image.get_rect(center=(LARGURA // 2, ALTURA // 2))

        # Atributos de combate
        self.hp          = HP_MAX
        self.hp_max      = HP_MAX   # atributo próprio — upgrades alteram este, não a constante global
        self.tipo_arma   = "Pistola"
        self.cadencia    = CADENCIA_PISTOLA
        self.ultimo_tiro = 0
        self.dano_bala   = 10       # pode receber upgrade

        # XP / Level
        self.nivel            = 1
        self.xp               = 0
        self.xp_proximo_nivel = XP_BASE_LEVEL
        self.velocidade       = PLAYER_VEL

        # Aceleração suave: vel_atual interpola em direção à vel_alvo.
        # Dá "peso" ao movimento sem sacrificar responsividade.
        # LERP: vel = vel + (alvo - vel) * fator  → fator 0.18 = snappy mas suave
        self._vel_atual = pygame.math.Vector2(0, 0)
        self._ACEL      = 0.18   # fator de interpolação (0=lento, 1=instantâneo)

        # Hit Flash
        self._flash_timer    = 0
        self._img_flash      = self._criar_flash()
        # Nota: _img_base é a referência canônica pós-construção;
        # _img_original mantido por compatibilidade mas não é mais usado no update.

        # I-frames: invencibilidade temporária após tomar dano.
        # Impede que um grupo de inimigos drene todo HP em milissegundos.
        # 60 frames = 1 segundo a 60 FPS — padrão de jogos de ação.
        self._iframe_timer   = 0
        self.IFRAME_DURACAO  = 60

        # Tiro duplo (upgrade)
        self.tiro_duplo = False

        # HP Delayed (barra amarela atrás da barra de HP — Dark Souls style)
        self._hp_delayed  = float(self.hp)
        self._DELAYED_VEL = 0.5   # pixels de HP que a barra amarela perde por frame

    # ── Construção de sprite ──────────────────────────────────────────

    def _construir_imagem(self):
        """
        Sprite de robô/mech humanóide top-down — estética biomecânica.

        Anatomia (vista de cima, canhão apontando para a direita):
          • Ombros largos curvos — silhueta de combate
          • Tórax central com núcleo de energia pulsante
          • Braço de canhão estendido à direita
          • Detalhe de tubulação nos ombros
          • Borda de energia colorida por arma
        """
        S = PLAYER_SIZE           # 50 px
        self.image = pygame.Surface((S + 10, S + 10), pygame.SRCALPHA)
        W = S + 10
        cx, cy = W // 2, W // 2

        arma = getattr(self, "tipo_arma", "Pistola")
        if arma == "Metralhadora":
            cor_energia = (255, 210, 0)
            cor_nucleo  = (255, 240, 80)
        elif arma == "Shotgun":
            cor_energia = (190, 60, 255)
            cor_nucleo  = (220, 130, 255)
        else:
            cor_energia = (0, 230, 140)
            cor_nucleo  = (80, 255, 180)

        # ── Sombra base (dá profundidade) ─────────────────────────────
        pygame.draw.ellipse(self.image, (0, 0, 0, 60),
                            (cx - 20, cy - 12, 40, 24))

        # ── Ombros — elipses largas com acabamento blindado ───────────
        # Ombro esquerdo
        pts_ombro_esq = []
        for i in range(12):
            a = math.radians(i * 30 + 90)
            rx, ry = 14, 9
            pts_ombro_esq.append((cx - 10 + math.cos(a) * rx,
                                   cy      + math.sin(a) * ry))
        pygame.draw.polygon(self.image, (20, 35, 25), pts_ombro_esq)
        pygame.draw.polygon(self.image, (30, 80, 50), pts_ombro_esq)
        pygame.draw.polygon(self.image, cor_energia, pts_ombro_esq, width=1)

        # Ombro direito
        pts_ombro_dir = []
        for i in range(12):
            a = math.radians(i * 30 - 90)
            rx, ry = 14, 9
            pts_ombro_dir.append((cx + 10 + math.cos(a) * rx,
                                   cy      + math.sin(a) * ry))
        pygame.draw.polygon(self.image, (20, 35, 25), pts_ombro_dir)
        pygame.draw.polygon(self.image, (30, 80, 50), pts_ombro_dir)
        pygame.draw.polygon(self.image, cor_energia, pts_ombro_dir, width=1)

        # ── Tórax central hexagonal ────────────────────────────────────
        torax_pts = []
        for i in range(6):
            a = math.radians(i * 60)
            torax_pts.append((cx + math.cos(a) * 13,
                               cy + math.sin(a) * 13))
        pygame.draw.polygon(self.image, (10, 30, 18), torax_pts)
        pygame.draw.polygon(self.image, (25, 70, 45), torax_pts)
        pygame.draw.polygon(self.image, cor_energia, torax_pts, width=2)

        # Placa de armadura interna (hexágono menor)
        torax_inner = []
        for i in range(6):
            a = math.radians(i * 60 + 30)
            torax_inner.append((cx + math.cos(a) * 7,
                                 cy + math.sin(a) * 7))
        pygame.draw.polygon(self.image, (15, 50, 35), torax_inner)

        # ── Núcleo de energia central ──────────────────────────────────
        # Anel externo
        pygame.draw.circle(self.image, (0, 0, 0, 180), (cx, cy), 5)
        pygame.draw.circle(self.image, cor_energia, (cx, cy), 5, width=1)
        # Núcleo brilhante
        pygame.draw.circle(self.image, cor_nucleo, (cx, cy), 3)
        # Reflexo
        pygame.draw.circle(self.image, (255, 255, 255, 200), (cx - 1, cy - 1), 1)

        # ── Braço canhão (apontado para direita) ───────────────────────
        # Ombro do canhão
        pygame.draw.rect(self.image, (20, 55, 35),
                         (cx + 8, cy - 5, 8, 10), border_radius=2)
        # Cano principal
        pygame.draw.rect(self.image, (10, 25, 18),
                         (cx + 14, cy - 3, 14, 6), border_radius=1)
        pygame.draw.rect(self.image, cor_energia,
                         (cx + 14, cy - 3, 14, 6), width=1, border_radius=1)
        # Boca do cano (mais larga)
        pygame.draw.rect(self.image, cor_nucleo,
                         (cx + 26, cy - 4, 4, 8), border_radius=1)

        # ── Tubulação / detalhes orgânico-mech ────────────────────────
        # Tubo esquerdo (costas)
        pygame.draw.line(self.image, cor_energia,
                         (cx - 18, cy - 4), (cx - 8, cy - 6), 1)
        pygame.draw.line(self.image, cor_energia,
                         (cx - 18, cy + 4), (cx - 8, cy + 6), 1)
        # Pontos de junção (rebites)
        for dx, dy in [(-14, -7), (-14, 7), (cx//4, -8), (cx//4, 8)]:
            pygame.draw.circle(self.image, cor_nucleo, (cx + dx, cy + dy), 1)

        # ── Linha central de energia (spine) ──────────────────────────
        pygame.draw.line(self.image, cor_energia,
                         (cx - 10, cy), (cx + 8, cy), 1)

        self._img_base = self.image.copy()
        # Ajusta referência de tamanho para o novo canvas W×W
        self._W = W

    def _criar_flash(self):
        """Flash branco — mesmo tamanho do canvas do mech (S+10)."""
        W = PLAYER_SIZE + 10
        surf = pygame.Surface((W, W), pygame.SRCALPHA)
        surf.fill((255, 255, 255, 200))
        return surf

    def _reconstruir_se_arma_mudou(self):
        """Reconstrói o sprite quando a arma muda (borda muda de cor)."""
        arma_atual = getattr(self, "tipo_arma", "Pistola")
        if arma_atual != getattr(self, "_arma_anterior", None):
            self._arma_anterior = arma_atual
            self._construir_imagem()
            self._img_flash = self._criar_flash()

    # ── API pública ───────────────────────────────────────────────────

    def esta_invencivel(self):
        """Retorna True enquanto os i-frames estiverem ativos."""
        return self._iframe_timer > 0

    def sofrer_dano(self, valor):
        """
        Aplica dano SOMENTE se não estiver invencível.
        Ativa hit flash e inicia os i-frames simultaneamente.
        """
        if self.esta_invencivel():
            return  # descarta o dano — i-frames ativos

        self.hp             -= valor
        self._flash_timer    = 8
        self._iframe_timer   = self.IFRAME_DURACAO

    def update(self):
        # Reconstrói imagem se a arma mudou (borda colorida)
        self._reconstruir_se_arma_mudou()

        teclas  = pygame.key.get_pressed()
        direcao = pygame.math.Vector2(0, 0)

        if teclas[pygame.K_w]: direcao.y -= 1
        if teclas[pygame.K_s]: direcao.y += 1
        if teclas[pygame.K_a]: direcao.x -= 1
        if teclas[pygame.K_d]: direcao.x += 1

        # Calcula velocidade alvo: normalizada * velocidade_max (ou zero se parado)
        vel_alvo = direcao.normalize() * self.velocidade if direcao.length() > 0 \
                   else pygame.math.Vector2(0, 0)

        # LERP: interpola vel_atual em direção a vel_alvo.
        self._vel_atual += (vel_alvo - self._vel_atual) * self._ACEL
        self.pos        += self._vel_atual

        self.rect.center = self.pos

        # Decrementa i-frames
        if self._iframe_timer > 0:
            self._iframe_timer -= 1

        # Atualiza HP delayed: decai em direção ao HP real
        if self._hp_delayed > self.hp:
            self._hp_delayed = max(self.hp, self._hp_delayed - self._DELAYED_VEL)

        # ── Rotação do sprite para o mouse ──────────────────────────────
        mouse_pos   = pygame.math.Vector2(pygame.mouse.get_pos())
        centro_tela = pygame.math.Vector2(LARGURA // 2, ALTURA // 2)
        delta       = mouse_pos - centro_tela
        if delta.length() > 1:
            # atan2 retorna ângulo em relação ao eixo X; pygame.transform.rotate
            # gira no sentido anti-horário, mas atan2 usa coordenadas de tela (y invertido)
            angulo = -math.degrees(math.atan2(delta.y, delta.x))
            img_base = self._img_base
        else:
            angulo   = 0
            img_base = self._img_base

        # Visual: hit flash → pisca (i-frames) → rotação normal
        if self._flash_timer > 0:
            self.image        = pygame.transform.rotate(self._img_flash, angulo)
            self._flash_timer -= 1
        elif self._iframe_timer > 0 and (self._iframe_timer // 6) % 2 == 0:
            img_pisca = img_base.copy()
            img_pisca.set_alpha(120)
            self.image = pygame.transform.rotate(img_pisca, angulo)
        else:
            self.image = pygame.transform.rotate(img_base, angulo)

        # Atualiza rect para o novo tamanho após rotação
        self.rect = self.image.get_rect(center=self.pos)

    def atirar(self):
        """
        Retorna lista de (direcao, tipo_bala).
        Suporta tiro duplo como upgrade.
        """
        mouse_pos   = pygame.math.Vector2(pygame.mouse.get_pos())
        centro_tela = pygame.math.Vector2(LARGURA // 2, ALTURA // 2)
        dir_base    = mouse_pos - centro_tela

        if dir_base.length() == 0:
            return []

        dir_base = dir_base.normalize()
        disparos = []

        if self.tipo_arma == "Shotgun":
            angulos = [-15, 0, 15]
            for ang in angulos:
                disparos.append((dir_base.rotate(ang), "shotgun", pygame.math.Vector2(self.pos)))

        elif self.tipo_arma == "Metralhadora":
            disparos.append((dir_base, "metralhadora", pygame.math.Vector2(self.pos)))
            if self.tiro_duplo:
                # Segundo cano com offset perpendicular real de 8px
                perp   = pygame.math.Vector2(-dir_base.y, dir_base.x) * 8
                origem = pygame.math.Vector2(self.pos) + perp
                disparos.append((dir_base, "metralhadora", origem))

        else:  # Pistola
            disparos.append((dir_base, "pistola", pygame.math.Vector2(self.pos)))
            if self.tiro_duplo:
                disparos.append((dir_base.rotate(5),  "pistola", pygame.math.Vector2(self.pos)))
                disparos.append((dir_base.rotate(-5), "pistola", pygame.math.Vector2(self.pos)))

        return disparos

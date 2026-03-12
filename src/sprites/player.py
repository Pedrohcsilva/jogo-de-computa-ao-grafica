##########################################################
#  Jogador — Movimento, tiro, hit flash e estado.
#
#  HIT FLASH: guardamos a imagem original e trocamos
#  temporariamente por uma versão branca ao tomar dano.
##########################################################

import pygame
import math
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import *


class Jogador(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # ── Tamanho responsivo ───────────────────────────────────────────
        # O boneco cresce a cada fase concluída e encolhe ao tomar dano.
        # _tamanho_base  = tamanho alvo determinado pela fase
        # _tamanho_atual = valor suavizado (interpola em direção ao base)
        # Fórmula: base = PLAYER_SIZE + (fase - 1) * PLAYER_CRESCIMENTO_FASE
        # Dano:    base sofre penalidade proporcional ao HP perdido
        self.fase_atual           = 1
        self._tamanho_base        = float(PLAYER_SIZE)
        self._tamanho_atual       = float(PLAYER_SIZE)
        self._LERP_TAMANHO        = 0.08   # suavidade da transição (0=lento, 1=instantâneo)

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

        # Muzzle flash — pisca na boca do canhão ao disparar
        self._muzzle_timer = 0   # frames restantes de flash (3 frames)
        self._muzzle_pos   = pygame.math.Vector2(0, 0)   # posição no mundo

        # HP Delayed (barra amarela atrás da barra de HP — Dark Souls style)
        self._hp_delayed  = float(self.hp)
        self._DELAYED_VEL = 0.5   # pixels de HP que a barra amarela perde por frame

    # ── Construção de sprite ──────────────────────────────────────────

    def _calcular_tamanho_alvo(self) -> float:
        """
        Tamanho alvo = crescimento por fase + penalidade de HP.

        Crescimento: +PLAYER_CRESCIMENTO_FASE px por fase concluída.
        Penalidade : quando HP cai, o tamanho encolhe proporcionalmente.
                     Com HP cheio → tamanho máximo da fase.
                     Com HP zerado → teria tamanho mínimo (PLAYER_SIZE_MIN).
        """
        fase    = getattr(self, "fase_atual", 1)
        hp      = getattr(self, "hp", HP_MAX)
        hp_max  = getattr(self, "hp_max", HP_MAX)

        # Tamanho base da fase (cresce com as fases)
        tam_fase = PLAYER_SIZE + (fase - 1) * PLAYER_CRESCIMENTO_FASE

        # Razão de HP: 1.0 = cheio, 0.0 = morto
        ratio_hp = max(0.0, hp / hp_max) if hp_max > 0 else 1.0

        # Encolhe linearmente conforme perde HP
        # Com HP cheio → tam_fase; Com HP = 0 → PLAYER_SIZE_MIN
        tam_alvo = PLAYER_SIZE_MIN + (tam_fase - PLAYER_SIZE_MIN) * ratio_hp

        return max(float(PLAYER_SIZE_MIN), tam_alvo)

    def atualizar_fase(self, nova_fase: int):
        """Chamado por main.py ao avançar de fase — redefine o tamanho alvo."""
        self.fase_atual = nova_fase

    def _construir_imagem(self, tamanho_override: float = None):
        """
        Sprite de robô/mech humanóide top-down — estética biomecânica.

        Anatomia (vista de cima, canhão apontando para a direita):
          • Ombros largos curvos — silhueta de combate
          • Tórax central com núcleo de energia pulsante
          • Braço de canhão estendido à direita
          • Detalhe de tubulação nos ombros
          • Borda de energia colorida por arma
        """
        S = int(tamanho_override) if tamanho_override else PLAYER_SIZE  # tamanho dinâmico
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

    def _criar_flash(self, tamanho_override: float = None):
        """Flash branco — mesmo tamanho do canvas atual do mech."""
        S = int(tamanho_override) if tamanho_override else PLAYER_SIZE
        W = S + 10
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
        Ativa hit flash, i-frames e atualiza tamanho responsivo.
        """
        if self.esta_invencivel():
            return  # descarta o dano — i-frames ativos

        self.hp             -= valor
        self._flash_timer    = 8
        self._iframe_timer   = self.IFRAME_DURACAO
        # Atualiza alvo de tamanho imediatamente ao tomar dano
        self._tamanho_base   = self._calcular_tamanho_alvo()

    def update(self):
        # Reconstrói imagem se a arma mudou (borda colorida)
        self._reconstruir_se_arma_mudou()

        # ── Tamanho responsivo: interpolação suave ao alvo ───────────────
        # _tamanho_base é atualizado ao tomar dano e ao avançar de fase.
        # _tamanho_atual interpola suavemente — transição visual fluida.
        self._tamanho_base  = self._calcular_tamanho_alvo()
        tam_anterior        = self._tamanho_atual
        self._tamanho_atual += (self._tamanho_base - self._tamanho_atual) * self._LERP_TAMANHO

        # Reconstrói o sprite quando o tamanho mudou de forma perceptível
        if abs(self._tamanho_atual - tam_anterior) > 0.5:
            self._construir_imagem(self._tamanho_atual)
            self._img_flash = self._criar_flash(self._tamanho_atual)

        # Tick de animação para pulso do núcleo
        self._tick = getattr(self, "_tick", 0) + 1

        # Entrada de movimento: pode vir de controline.atualizar() ou teclado
        # Se o atributo _entrada_movimento foi setado, usa dele; senão, processa teclado
        if hasattr(self, '_entrada_movimento') and self._entrada_movimento:
            direcao = self._entrada_movimento
        else:
            # Fallback para teclado (retrocompatibilidade)
            teclas  = pygame.key.get_pressed()
            direcao = pygame.math.Vector2(0, 0)

            if teclas[pygame.K_w]: direcao.y -= 1
            if teclas[pygame.K_s]: direcao.y += 1
            if teclas[pygame.K_a]: direcao.x -= 1
            if teclas[pygame.K_d]: direcao.x += 1

        vel_alvo = direcao.normalize() * self.velocidade if direcao.length() > 0 \
                   else pygame.math.Vector2(0, 0)
        self._vel_atual += (vel_alvo - self._vel_atual) * self._ACEL
        self.pos        += self._vel_atual

        # ── Limites do mundo: mantém o jogador dentro de um mapa de 4000x4000 ──
        LIMITE = 2000
        if self.pos.x < -LIMITE:
            self.pos.x = -LIMITE
            self._vel_atual.x = 0
        elif self.pos.x > LIMITE:
            self.pos.x = LIMITE
            self._vel_atual.x = 0
        if self.pos.y < -LIMITE:
            self.pos.y = -LIMITE
            self._vel_atual.y = 0
        elif self.pos.y > LIMITE:
            self.pos.y = LIMITE
            self._vel_atual.y = 0

        self.rect.center = self.pos

        if self._iframe_timer > 0:
            self._iframe_timer -= 1

        if self._hp_delayed > self.hp:
            self._hp_delayed = max(self.hp, self._hp_delayed - self._DELAYED_VEL)

        # ── Rotação do sprite para o mouse ──────────────────────────────
        mouse_pos   = pygame.math.Vector2(pygame.mouse.get_pos())
        centro_tela = pygame.math.Vector2(LARGURA // 2, ALTURA // 2)
        delta       = mouse_pos - centro_tela
        angulo      = -math.degrees(math.atan2(delta.y, delta.x)) if delta.length() > 1 else 0
        img_base    = self._img_base

        # ── Pulso do núcleo: overlay animado sobre img_base ─────────────
        # Um círculo semitransparente que pulsa no centro
        pulso_sin  = math.sin(self._tick * 0.14)   # -1 → 1 em ~45 frames
        pulso_r    = int(4 + 2 * pulso_sin)
        pulso_alp  = int(100 + 80 * pulso_sin)

        # Cor do pulso varia com o poder ativo
        if getattr(self, "_frenesim_ativo", False):
            pulso_cor = (255, 200, 0, pulso_alp)
        elif getattr(self, "_escudo_ativo", False):
            pulso_cor = (0, 255, 150, pulso_alp)
        elif getattr(self, "_overload_ativo", False):
            pulso_cor = (255, 60, 60, pulso_alp)
        else:
            # Cor normal da arma
            arma = getattr(self, "tipo_arma", "Pistola")
            if arma == "Metralhadora":
                pulso_cor = (255, 210, 0, pulso_alp)
            elif arma == "Shotgun":
                pulso_cor = (190, 60, 255, pulso_alp)
            else:
                pulso_cor = (80, 255, 180, pulso_alp)

        W        = img_base.get_width()
        cx = cy  = W // 2
        img_anim = img_base.copy()
        ovl      = pygame.Surface((W, W), pygame.SRCALPHA)
        pygame.draw.circle(ovl, pulso_cor, (cx, cy), pulso_r)
        img_anim.blit(ovl, (0, 0))

        # ── Anel de escudo visível ao redor do mech ──────────────────────
        if getattr(self, "_escudo_ativo", False):
            r_escudo = W // 2 + 3
            pygame.draw.circle(img_anim, (0, 255, 160, 180), (cx, cy), r_escudo, width=2)

        # Visual: hit flash → pisca (i-frames) → animado normal
        if self._flash_timer > 0:
            self.image        = pygame.transform.rotate(self._img_flash, angulo)
            self._flash_timer -= 1
        elif self._iframe_timer > 0 and (self._iframe_timer // 6) % 2 == 0:
            img_pisca = img_anim.copy()
            img_pisca.set_alpha(120)
            self.image = pygame.transform.rotate(img_pisca, angulo)
        else:
            self.image = pygame.transform.rotate(img_anim, angulo)

        self.rect = self.image.get_rect(center=self.pos)

    def distancia_borda(self) -> float:
        """Retorna fração 0–1 da proximidade à borda do mundo (1=na borda)."""
        LIMITE = 2000
        dist_x = min(abs(self.pos.x + LIMITE), abs(self.pos.x - LIMITE))
        dist_y = min(abs(self.pos.y + LIMITE), abs(self.pos.y - LIMITE))
        dist_min = min(dist_x, dist_y)
        return max(0.0, 1.0 - dist_min / 300.0)  # aviso nos últimos 300px

    def atirar(self):
        """
        Retorna lista de (direcao, tipo_bala, origem).
        Suporta tiro duplo como upgrade.
        Ativa muzzle flash na boca do canhão.
        """
        mouse_pos   = pygame.math.Vector2(pygame.mouse.get_pos())
        centro_tela = pygame.math.Vector2(LARGURA // 2, ALTURA // 2)
        dir_base    = mouse_pos - centro_tela

        if dir_base.length() == 0:
            return []

        dir_base = dir_base.normalize()
        disparos = []

        # Posição da boca do canhão (aprox. 28px à frente do centro)
        self._muzzle_pos   = pygame.math.Vector2(self.pos) + dir_base * 28
        self._muzzle_timer = 4   # frames de brilho

        if self.tipo_arma == "Shotgun":
            angulos = [-15, 0, 15]
            for ang in angulos:
                disparos.append((dir_base.rotate(ang), "shotgun", pygame.math.Vector2(self.pos)))

        elif self.tipo_arma == "Metralhadora":
            disparos.append((dir_base, "metralhadora", pygame.math.Vector2(self.pos)))
            if self.tiro_duplo:
                perp   = pygame.math.Vector2(-dir_base.y, dir_base.x) * 8
                origem = pygame.math.Vector2(self.pos) + perp
                disparos.append((dir_base, "metralhadora", origem))
            # carta_cano_quente: +4 projéteis em cone mais aberto
            if getattr(self, "carta_cano_quente", False):
                for ang in (-14, -7, 7, 14):
                    disparos.append((dir_base.rotate(ang), "metralhadora",
                                     pygame.math.Vector2(self.pos)))

        else:  # Pistola
            disparos.append((dir_base, "pistola", pygame.math.Vector2(self.pos)))
            if self.tiro_duplo:
                disparos.append((dir_base.rotate(5),  "pistola", pygame.math.Vector2(self.pos)))
                disparos.append((dir_base.rotate(-5), "pistola", pygame.math.Vector2(self.pos)))

        return disparos

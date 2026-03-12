###################################################################
#  Bullet Haven — Ponto de entrada principal.
#
#  ARQUITETURA:
#   - Game.estados: "jogando" | "pausado" | "game_over" | "boss"
#   - Camera: desacopla posição do mundo da posição de tela
#   - GerenciadorParticulas: pool flat para máxima performance
#   - MenuUpgrade: roguelite com pool de upgrades
#   - Boss: State Machine com 2 fases + bullet hell
###################################################################

import pygame
import sys
import random
import math

from src.config import *
from src.camera        import Camera
from src.particles     import GerenciadorParticulas
from src.upgrade_menu  import MenuUpgrade
from src.damage_numbers import GerenciadorNumeroDano
from src.boss_intro    import BossIntro
from src.waves         import GerenciadorOndas
from src.score         import GerenciadorScore

from src.sprites.player  import Jogador
from src.sprites.enemies import InimigoBase, InimigoRapido, InimigoTank, InimigoAtirador
from src.sprites.boss    import Boss
from src.sprites.bullets import Bala, BalaMetralhadora, BalaShotgun, BalaInimiga, BalaBoss
from src.sprites.items   import ItemArma
from src.sprites.xp      import XpGem


class Game:
    def __init__(self):
        pygame.init()
        self.tela    = pygame.display.set_mode((LARGURA, ALTURA), pygame.FULLSCREEN)
        pygame.display.set_caption("Bullet Haven")
        self.relogio = pygame.time.Clock()

        # Fontes
        self.fonte    = pygame.font.SysFont("Arial", 24, bold=True)
        self.fonte_lg = pygame.font.SysFont("Arial", 72, bold=True)
        self.fonte_md = pygame.font.SysFont("Arial", 36, bold=True)

        # Sub-sistemas
        self.camera     = Camera()
        self.particulas = GerenciadorParticulas()
        self.menu_up    = MenuUpgrade(LARGURA, ALTURA)
        self.nums_dano  = GerenciadorNumeroDano()
        self.boss_intro = BossIntro(LARGURA, ALTURA, self.camera)
        self.ondas      = GerenciadorOndas()
        self.score      = GerenciadorScore()

        self.rodando    = True
        self._morte_timer = 0
        self.reset_total()

    # ═══════════════════════════════════════════════════════════════
    #  RESET
    # ═══════════════════════════════════════════════════════════════

    def reset_fase(self):
        self.todos_sprites  = pygame.sprite.Group()
        self.inimigos       = pygame.sprite.Group()
        self.balas_player   = pygame.sprite.Group()
        self.balas_inimigos = pygame.sprite.Group()
        self.itens_chao     = pygame.sprite.Group()
        self.xp_gems        = pygame.sprite.Group()
        self.grupo_boss     = pygame.sprite.Group()

        self.player = Jogador()
        self.todos_sprites.add(self.player)

        self.inimigos_derrotados = 0
        self.player.hp           = self.player.hp_max  # respeita upgrades de HP
        self.boss_ativo          = False
        self.boss_ref            = None

        # BUG 5 FIX: garante que o menu de upgrade nunca fique preso
        # ao morrer durante a tela de level-up
        self.menu_up.ativo = False

        self.SPAWN_EVENTO = pygame.USEREVENT + 1
        pygame.time.set_timer(self.SPAWN_EVENTO, 800)

    def reset_total(self):
        self.vidas              = 3
        self.fase               = 1
        self.meta_fase          = 10
        self.vel_inimigos       = 2.5
        self.estado             = "jogando"
        self.aviso_fase_timer   = 0
        self.particulas         = GerenciadorParticulas()
        self.nums_dano          = GerenciadorNumeroDano()
        self.score.reset()
        self.ondas              = GerenciadorOndas()
        # ── Background biomecânico: elementos gerados uma vez ────────────
        import random as _r
        # Camada 0: esporos/células flutuantes distantes (movimento lentíssimo)
        self._bio_longe = [
            (_r.uniform(0, LARGURA), _r.uniform(0, ALTURA),
             _r.randint(1, 3), _r.choice([(0,180,80,60),(100,0,180,50),(0,140,100,40)]))
            for _ in range(70)
        ]
        # Camada 1: filamentos/nervos médios
        self._bio_medio = [
            (_r.uniform(0, LARGURA), _r.uniform(0, ALTURA),
             _r.uniform(0, math.tau),          # ângulo do filamento
             _r.randint(15, 40),               # comprimento
             _r.choice([(0,120,60),(80,0,140),(0,160,80),(60,0,120)]))
            for _ in range(50)
        ]
        # Camada 2: nódulos/glândulas próximos (com o mundo)
        self._bio_perto = [
            (_r.uniform(0, LARGURA * 3) - LARGURA, _r.uniform(0, ALTURA * 3) - ALTURA,
             _r.randint(4, 10),
             _r.choice([(0,200,100),(120,0,200),(0,180,120),(100,0,180)]))
            for _ in range(60)
        ]
        # Veias do grid: linhas orgânicas cruzando o mapa
        self._veias = []
        for _ in range(20):
            x0 = _r.uniform(-200, LARGURA + 200)
            y0 = _r.uniform(-200, ALTURA + 200)
            ang = _r.uniform(0, math.tau)
            comp = _r.randint(80, 250)
            cor = _r.choice([(0,80,40),(60,0,100),(0,100,60),(40,0,80)])
            self._veias.append((x0, y0, ang, comp, cor))
        self.boss_intro.resetar()
        # BUG 5 FIX: reseta o menu junto com tudo mais
        self.menu_up.ativo      = False
        self.reset_fase()
        self.ondas.iniciar_fase(self.fase)

    # ═══════════════════════════════════════════════════════════════
    #  EVENTOS
    # ═══════════════════════════════════════════════════════════════

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.rodando = False

            if evento.type == pygame.KEYDOWN:
                # ESC: pausa/retoma — mas NÃO fecha o menu de level-up
                # BUG 4 FIX: quando menu_up está ativo, ESC é ignorado;
                # o jogador DEVE escolher um upgrade (1/2/3).
                if evento.key == pygame.K_ESCAPE and not self.menu_up.ativo:
                    if self.estado == "jogando":
                        self.estado = "pausado"
                    elif self.estado == "pausado":
                        self.estado = "jogando"
                    # "morrendo" ignora ESC — animação de morte não pode ser pausada

                # R: reinicia após game over
                if self.estado == "game_over" and evento.key == pygame.K_r:
                    self.estado = "jogando"
                    self.reset_total()

                # Q: sair a qualquer momento
                if evento.key == pygame.K_q:
                    self.rodando = False

            # Menu de upgrade captura seus próprios eventos
            if self.menu_up.ativo:
                fechou = self.menu_up.processar_evento(evento, self.player)
                if fechou:
                    self.estado = "jogando"
                    self.particulas.nivel_up_burst(self.player.pos)
                    self.camera.adicionar_shake(SHAKE_LEVEL_UP)

            # Spawn legado removido — o GerenciadorOndas controla os spawns agora

    # ═══════════════════════════════════════════════════════════════
    #  UPDATE
    # ═══════════════════════════════════════════════════════════════

    def update(self):
        # ── Cinematica do Boss (roda mesmo quando estado != "jogando") ──
        if self.boss_intro.ativo:
            self.boss_intro.update()
            # Momento exato de spawnar: cria o boss quando a intro sinaliza
            if self.boss_intro.pronto_para_spawnar():
                self._spawnar_boss()
            self.camera.update(self.player.pos, LARGURA, ALTURA)
            return  # congela toda a física durante a cinematica

        if self.estado not in ("jogando", "morrendo"):
            return

        # Estado "morrendo": câmera lenta, partículas ainda atualizam, depois game_over
        if self.estado == "morrendo":
            self._morte_timer -= 1
            self.particulas.update()
            self.camera.update(self.player.pos, LARGURA, ALTURA)
            if self._morte_timer <= 0:
                self.estado = "game_over"
            return

        # ── 1. Jogador ──────────────────────────────────────────────
        self.player.update()

        # ── 1b. Regen de vida (upgrade Nanobots) ────────────────────
        if getattr(self.player, "regen_ativo", False):
            self.player.regen_timer = getattr(self.player, "regen_timer", 0) + 1
            if self.player.regen_timer >= 120:   # a cada 2s (120 frames)
                self.player.regen_timer = 0
                self.player.hp = min(self.player.hp_max, self.player.hp + 1)

        # ── 1c. Score update ─────────────────────────────────────────
        self.score.update()

        # ── 1d. Ondas: verifica se deve spawnar próximo inimigo ──────
        self.ondas.update(len(self.inimigos))
        tipo_spawn = self.ondas.inimigo_a_spawnar()
        if tipo_spawn:
            self._spawnar_inimigo_tipo(tipo_spawn)

        # Avança fase quando onda completa
        if self.ondas.completa:
            if self.fase < BOSS_FASE_INICIO:
                # Fases 1-4: avança normalmente
                self.fase            += 1
                self.vel_inimigos    += 0.4
                self.aviso_fase_timer = 120
                self.camera.adicionar_shake(SHAKE_LEVEL_UP * 0.5)
                self.particulas.transicao_fase(LARGURA, ALTURA)
                self.ondas.iniciar_fase(self.fase)
            elif self.fase == BOSS_FASE_INICIO and not self.boss_ativo and not self.boss_intro.ativo:
                # Fase 5: inicia a cinematica do boss
                self.boss_intro.iniciar()

        # ── 2. Tiro do Jogador ──────────────────────────────────────
        if pygame.mouse.get_pressed()[0]:
            agora = pygame.time.get_ticks()
            if agora - self.player.ultimo_tiro > self.player.cadencia:
                self.player.ultimo_tiro = agora
                disparos = self.player.atirar()
                for direcao, tipo, origem in disparos:
                    bala = self._criar_bala_player(tipo, direcao, origem)
                    self.balas_player.add(bala)
                    self.todos_sprites.add(bala)

        # ── 3. Inimigos e Boss (via lista de disparos) ──────────────
        lista_disparos = []

        for inimigo in self.inimigos:
            inimigo.update(self.player.pos, lista_disparos)

        if self.boss_ativo and self.boss_ref:
            self.boss_ref.update(self.player.pos, lista_disparos)

        for pedido in lista_disparos:
            self._processar_disparo_inimigo(pedido)

        # ── 4. Gemas de XP ──────────────────────────────────────────
        raio_mag = getattr(self.player, "raio_magnetismo", 200)
        for gema in self.xp_gems:
            gema.raio_magnetismo = raio_mag
            gema.update(self.player.pos)

        # ── 5. Projéteis ─────────────────────────────────────────────
        for bala in self.balas_player:
            bala.update(self.particulas)
        for bala in self.balas_inimigos:
            bala.update(self.particulas)

        # ── 6. Itens e timers ────────────────────────────────────────
        self.itens_chao.update()
        if self.aviso_fase_timer > 0:
            self.aviso_fase_timer -= 1

        # ── 7. Partículas + Números de Dano ───────────────────────────
        self.particulas.update()
        self.nums_dano.update()

        # ── 8. Câmera ─────────────────────────────────────────────────
        self.camera.update(self.player.pos, LARGURA, ALTURA)

        # ── 9. Colisões ───────────────────────────────────────────────
        self.checar_colisoes()

    # ── Helpers de criação de balas ───────────────────────────────────

    def _criar_bala_player(self, tipo, direcao, origem=None):
        """
        Cria projétil do jogador respeitando dano_bala em TODAS as armas.
        Aplica upgrade bala_larga (projétil 2× maior) quando ativo.
        """
        pos   = origem if origem is not None else self.player.pos
        larga = getattr(self.player, "bala_larga", False)

        if tipo == "metralhadora":
            tam = (12, 12) if larga else (6, 6)
            return BalaMetralhadora(pos, direcao, dano=self.player.dano_bala, tamanho=tam)
        if tipo == "shotgun":
            tam = (18, 18) if larga else (10, 10)
            return BalaShotgun(pos, direcao, dano=self.player.dano_bala, tamanho=tam)
        # Pistola padrão
        tam = (16, 16) if larga else (8, 8)
        return Bala(pos, direcao, AZUL_TIRO, dano=self.player.dano_bala, tamanho=tam)

    def _processar_disparo_inimigo(self, pedido):
        pos  = pedido["pos"]
        dir_ = pedido["dir"]
        tipo = pedido.get("tipo", "inimigo")
        cor  = pedido.get("cor", LARANJA)

        if tipo == "boss":
            bala = BalaBoss(pos, dir_, cor=cor)
        else:
            bala = BalaInimiga(pos, dir_)

        self.balas_inimigos.add(bala)
        self.todos_sprites.add(bala)

    # ═══════════════════════════════════════════════════════════════
    #  SPAWN
    # ═══════════════════════════════════════════════════════════════

    def spawn_inimigo(self):
        """Mantido para compatibilidade; lógica principal agora em GerenciadorOndas."""
        pass

    def _spawnar_inimigo_tipo(self, tipo: str):
        """Cria um inimigo do tipo dado e adiciona aos grupos."""
        if self.boss_ativo or self.boss_intro.ativo:
            return
        mapa = {
            "normal":   InimigoBase,
            "rapido":   InimigoRapido,
            "tank":     InimigoTank,
            "atirador": InimigoAtirador,
        }
        cls  = mapa.get(tipo, InimigoBase)
        novo = cls(self.player.pos, self.vel_inimigos)
        self.inimigos.add(novo)
        self.todos_sprites.add(novo)

    def _spawnar_boss(self):
        """Chamado pela BossIntro no momento certo da cinematica."""
        boss         = Boss(self.player.pos)
        self.boss_ref   = boss
        self.boss_ativo = True
        self.grupo_boss.add(boss)
        self.todos_sprites.add(boss)

    # ═══════════════════════════════════════════════════════════════
    #  COLISÕES
    # ═══════════════════════════════════════════════════════════════

    def checar_colisoes(self):
        # ── 1. Balas do player → inimigos ───────────────────────────
        hits = pygame.sprite.groupcollide(self.inimigos, self.balas_player, False, True)
        for inimigo, balas_acertadas in hits.items():
            dano_total = 0
            for bala in balas_acertadas:
                inimigo.sofrer_dano(bala.dano)
                dano_total += bala.dano
                self.particulas.hit_sparks(inimigo.pos)
                self.particulas.sangue(inimigo.pos, quantidade=6)

            # Número de dano flutuante sobre o inimigo
            critico = dano_total >= 20   # dano alto = cor dourada
            self.nums_dano.adicionar(inimigo.pos, dano_total, critico=critico)

            if inimigo.hp <= 0:
                self._matar_inimigo(inimigo)

        # ── 2. Balas do player → Boss ────────────────────────────────
        if self.boss_ativo and self.boss_ref:
            for bala in list(self.balas_player):
                if self.boss_ref.rect.colliderect(bala.rect):
                    self.boss_ref.sofrer_dano(bala.dano)
                    bala.kill()
                    self.particulas.hit_sparks(self.boss_ref.pos)
                    self.camera.adicionar_shake(SHAKE_ACERTA_BOSS)
                    # Número de dano no boss — sempre crítico visualmente
                    self.nums_dano.adicionar(self.boss_ref.pos, bala.dano, critico=True)

                    if self.boss_ref.hp <= 0:
                        self._matar_boss()
                        break

        # ── 3. Inimigos → Jogador (contato) ─────────────────────────
        if pygame.sprite.spritecollide(self.player, self.inimigos, True):
            dano = 20
            self.player.sofrer_dano(dano)
            if not self.player.esta_invencivel():  # só mostra se dano foi aplicado
                self.nums_dano.adicionar(self.player.pos, dano, eh_jogador=True)
                self.score.registrar_dano()   # quebra o combo
            self.camera.adicionar_shake(SHAKE_CONTATO_INIMIGO)
            self._verificar_morte_jogador()

        # ── 4. Balas inimigas → Jogador ──────────────────────────────
        for bala in list(self.balas_inimigos):
            if self.player.rect.colliderect(bala.rect):
                dano = bala.dano
                self.player.sofrer_dano(dano)
                if not self.player.esta_invencivel():
                    self.nums_dano.adicionar(self.player.pos, dano, eh_jogador=True)
                    self.score.registrar_dano()   # quebra o combo
                self.camera.adicionar_shake(SHAKE_TIRO_INIMIGO)
                bala.kill()
                self._verificar_morte_jogador()

        # ── 5. Coleta de itens ───────────────────────────────────────
        item = pygame.sprite.spritecollideany(self.player, self.itens_chao)
        if item:
            self.player.tipo_arma = item.tipo
            self.player.cadencia  = (CADENCIA_METRALHADORA
                                     if item.tipo == "Metralhadora"
                                     else CADENCIA_SHOTGUN)
            item.kill()

        # ── 6. Coleta de XP ──────────────────────────────────────────
        for gema in pygame.sprite.spritecollide(self.player, self.xp_gems, True):
            self.player.xp += gema.valor
            if self.player.xp >= self.player.xp_proximo_nivel:
                self._level_up()

    def _matar_inimigo(self, inimigo):
        self.particulas.explosao(inimigo.pos, inimigo.cor, quantidade=20)

        # Shake diferenciado: Tank tem mais impacto visual que inimigo normal
        from src.sprites.enemies import InimigoTank
        if isinstance(inimigo, InimigoTank):
            self.camera.adicionar_shake(SHAKE_MATA_TANK)
        else:
            self.camera.adicionar_shake(SHAKE_MATA_NORMAL)

        self.inimigos_derrotados += 1

        # Registra kill no score com multiplicador de combo
        valor_xp = getattr(inimigo, "xp_valor", 10)
        self.score.registrar_kill(valor_xp)

        # Upgrade: Morte Explosiva — partículas extras ao matar
        if getattr(self.player, "explosao_ao_matar", False):
            self.particulas.explosao(inimigo.pos, inimigo.cor, quantidade=35, raio_max=7)
            self.camera.adicionar_shake(SHAKE_MATA_NORMAL * 1.5)

        # Drop de XP
        gema = XpGem(inimigo.pos, valor_xp)
        self.xp_gems.add(gema)
        self.todos_sprites.add(gema)

        # Drop de arma (15% de chance)
        if random.random() < 0.15:
            tipo = random.choice(["Metralhadora", "Shotgun"])
            item = ItemArma(inimigo.pos, tipo)
            self.itens_chao.add(item)
            self.todos_sprites.add(item)

        inimigo.kill()

        # A progressão de fase agora é 100% controlada pelo GerenciadorOndas
        # (ver update → ondas.completa). Removido o sistema legado de meta_fase.

    def _matar_boss(self):
        self.score.registrar_kill(self.boss_ref.xp_valor)
        self.particulas.explosao(self.boss_ref.pos, (255, 80, 200), quantidade=60, raio_max=10)
        self.camera.adicionar_shake(SHAKE_BOSS_MORTE)
        gema = XpGem(self.boss_ref.pos, self.boss_ref.xp_valor)
        self.xp_gems.add(gema)
        self.todos_sprites.add(gema)
        self.boss_ref.kill()
        self.boss_ativo = False
        self.boss_ref   = None
        self.fase       += 1
        self.aviso_fase_timer = 180

    def _verificar_morte_jogador(self):
        if self.player.hp <= 0:
            # Efeito de morte: explosão de partículas + shake máximo
            self.particulas.explosao(self.player.pos, VERDE, quantidade=50, raio_max=8)
            self.particulas.nivel_up_burst(self.player.pos)   # burst dourado extra
            self.camera.adicionar_shake(1.0)
            self._morte_timer = 40   # frames de câmera lenta antes do game over

            self.vidas -= 1
            if self.vidas > 0:
                self.reset_fase()
            else:
                self.estado = "morrendo"   # novo estado intermediário

    def _level_up(self):
        self.player.nivel            += 1
        self.player.xp                = 0
        self.player.xp_proximo_nivel  = int(self.player.xp_proximo_nivel * XP_INCREMENTO)
        self.menu_up.sortear(self.player)
        self.estado = "pausado"

    # ═══════════════════════════════════════════════════════════════
    #  DESENHO
    # ═══════════════════════════════════════════════════════════════

    def desenhar(self):
        # Cor de fundo varia por fase — paleta BIOMECÂNICA
        # verde tóxico profundo → roxo sombrio → preto orgânico
        _CORES_FUNDO = [
            (5,  15,  8),    # fase 1 — verde floresta profundo
            (6,  12,  14),   # fase 2 — verde-azulado orgânico
            (10, 6,   16),   # fase 3 — transição para roxo
            (14, 4,   18),   # fase 4 — roxo escuro ameaçador
            (18, 3,   12),   # fase 5 — roxo-sangue boss
        ]
        idx_cor = min(self.fase - 1, len(_CORES_FUNDO) - 1)
        self.tela.fill(_CORES_FUNDO[idx_cor])
        offset = self.camera.offset

        # ── Grid ─────────────────────────────────────────────────────
        self._desenhar_grid(offset)

        # ── Sprites do mundo (exceto player) ─────────────────────────
        for sprite in self.todos_sprites:
            if sprite == self.player:
                continue
            rect_pos = sprite.image.get_rect(center=sprite.pos + offset)
            self.tela.blit(sprite.image, rect_pos)

        # ── Partículas (mundo) ────────────────────────────────────────
        self.particulas.desenhar(self.tela, offset)

        # ── Números de dano flutuantes ────────────────────────────────
        self.nums_dano.desenhar(self.tela, offset)

        # ── Player (sempre no centro) ─────────────────────────────────
        centro = (LARGURA // 2, ALTURA // 2)
        self.tela.blit(self.player.image, self.player.image.get_rect(center=centro))

        # ── Barra de vida do Boss ─────────────────────────────────────
        if self.boss_ativo and self.boss_ref:
            self.boss_ref.desenhar_barra_vida(self.tela)

        # ── HUD ───────────────────────────────────────────────────────
        self._desenhar_hud()

        # ── Cinematica do Boss (sobrepõe tudo exceto o cursor) ────────
        self.boss_intro.desenhar(self.tela)

        # ── Overlays de estado ────────────────────────────────────────
        if self.estado == "game_over":
            self._desenhar_game_over()
        elif self.estado == "morrendo":
            # Flash branco crescente durante a morte
            alpha = int(180 * (1 - self._morte_timer / 40))
            flash = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            self.tela.blit(flash, (0, 0))
        elif self.estado == "pausado":
            if self.menu_up.ativo:
                self.menu_up.desenhar(self.tela)
            else:
                self._desenhar_pause()

        pygame.display.flip()

    def _desenhar_grid(self, offset):
        """
        Fundo BIOMECÂNICO com 4 camadas de parallax:
          Camada 0 (esporos distantes):  move 0.05x — quase parados
          Camada 1 (filamentos/nervos):  move 0.15x — deriva orgânica
          Camada 2 (veias do grid):      move 0.40x — estrutura do mundo
          Camada 3 (nódulos próximos):   move 1.00x — segue o mundo

        Paleta: verde tóxico + roxo profundo + preto orgânico.
        A cor de fundo base já varia por fase (definida no início de desenhar()).
        """
        ox, oy = offset.x, offset.y

        # ── Camada 0: esporos/células distantes ─────────────────────────
        for (sx, sy, sr, cor) in self._bio_longe:
            px = int(sx + ox * 0.05) % LARGURA
            py = int(sy + oy * 0.05) % ALTURA
            # Círculo com halo tênue
            if sr > 1:
                pygame.draw.circle(self.tela, (cor[0]//4, cor[1]//4, cor[2]//4),
                                   (px, py), sr + 2)
            pygame.draw.circle(self.tela, (cor[0], cor[1], cor[2]), (px, py), sr)

        # ── Camada 1: filamentos orgânicos (nervos/micelas) ──────────────
        for (sx, sy, ang, comp, cor) in self._bio_medio:
            px = (sx + ox * 0.15) % LARGURA
            py = (sy + oy * 0.15) % ALTURA
            # Segmento sinuoso: 3 pontos com curvatura
            x0, y0 = int(px), int(py)
            # Ponto médio desviado perpendicularmente
            mid_x = int(px + math.cos(ang) * comp * 0.5 + math.sin(ang) * 8)
            mid_y = int(py + math.sin(ang) * comp * 0.5 - math.cos(ang) * 8)
            x1    = int(px + math.cos(ang) * comp)
            y1    = int(py + math.sin(ang) * comp)
            # Linha principal (mais escura)
            cor_e = (cor[0]//3, cor[1]//3, cor[2]//3)
            pygame.draw.line(self.tela, cor_e, (x0, y0), (mid_x, mid_y), 1)
            pygame.draw.line(self.tela, cor_e, (mid_x, mid_y), (x1, y1), 1)
            # Ponto de junção como nódulo
            pygame.draw.circle(self.tela, cor, (mid_x, mid_y), 2)

        # ── Camada 2: veias estruturais (grid orgânico) ──────────────────
        for (vx, vy, vang, vcomp, vcor) in self._veias:
            px = (vx + ox * 0.4) % (LARGURA + 400) - 200
            py = (vy + oy * 0.4) % (ALTURA + 400) - 200
            # Veia principal
            ex = px + math.cos(vang) * vcomp
            ey = py + math.sin(vang) * vcomp
            pygame.draw.line(self.tela, vcor,
                             (int(px), int(py)), (int(ex), int(ey)), 1)
            # Ramificações menores (2 galhos)
            for side in (-1, 1):
                branch_ang = vang + side * 0.6
                bx = px + math.cos(vang) * vcomp * 0.6
                by = py + math.sin(vang) * vcomp * 0.6
                bex = bx + math.cos(branch_ang) * vcomp * 0.3
                bey = by + math.sin(branch_ang) * vcomp * 0.3
                pygame.draw.line(self.tela, vcor,
                                 (int(bx), int(by)), (int(bex), int(bey)), 1)

        # ── Camada 3: nódulos próximos (escala 1:1 com o mundo) ──────────
        for (nx, ny, nr, ncor) in self._bio_perto:
            px = int(nx + ox) % (LARGURA + 200) - 100
            py = int(ny + oy) % (ALTURA + 200) - 100
            # Só desenha se estiver visível
            if -nr <= px <= LARGURA + nr and -nr <= py <= ALTURA + nr:
                # Halo externo tênue
                cor_halo = (ncor[0]//5, ncor[1]//5, ncor[2]//5)
                pygame.draw.circle(self.tela, cor_halo, (px, py), nr + 3)
                # Corpo do nódulo
                pygame.draw.circle(self.tela, (ncor[0]//2, ncor[1]//2, ncor[2]//2),
                                   (px, py), nr)
                # Brilho central
                pygame.draw.circle(self.tela, ncor, (px, py), max(1, nr - 3))
                # Ponto de reflexo
                if nr >= 6:
                    pygame.draw.circle(self.tela, (200, 255, 220),
                                       (px - nr//3, py - nr//3), max(1, nr//4))

    def _desenhar_hud(self):
        BAR_W, BAR_H = 260, 20
        x, y = 30, 28

        # ── Barra de HP com camada delayed (Dragon Ball / Dark Souls) ──────
        # 1. Fundo cinza
        pygame.draw.rect(self.tela, (40, 40, 50), (x, y, BAR_W, BAR_H), border_radius=5)

        # 2. Camada amarela (HP delayed) — decai mais devagar que o HP real
        larg_delayed = max(0, (self.player._hp_delayed / self.player.hp_max) * BAR_W)
        pygame.draw.rect(self.tela, (200, 160, 0),
                         (x, y, int(larg_delayed), BAR_H), border_radius=5)

        # 3. HP real por cima
        cor_hp  = VERDE if self.player.hp > self.player.hp_max * 0.3 else VERMELHO
        larg_hp = max(0, (self.player.hp / self.player.hp_max) * BAR_W)
        pygame.draw.rect(self.tela, cor_hp,
                         (x, y, int(larg_hp), BAR_H), border_radius=5)

        # 4. Borda
        pygame.draw.rect(self.tela, BRANCO, (x, y, BAR_W, BAR_H), width=1, border_radius=5)

        # 5. Texto HP dentro da barra
        txt_hp = self.fonte.render(f"{self.player.hp} / {self.player.hp_max}", True, BRANCO)
        self.tela.blit(txt_hp, txt_hp.get_rect(midleft=(x + 6, y + BAR_H // 2)))

        # ── Barra de XP ───────────────────────────────────────────────────
        xp_pct = self.player.xp / self.player.xp_proximo_nivel
        pygame.draw.rect(self.tela, (30, 30, 40),     (x, y + BAR_H + 4, BAR_W, 8), border_radius=3)
        pygame.draw.rect(self.tela, XP_COLOR,          (x, y + BAR_H + 4, int(BAR_W * xp_pct), 8), border_radius=3)

        # ── Informações de status ─────────────────────────────────────────
        info = (f"VIDAS: {self.vidas}  |  FASE: {self.fase}  |  "
                f"NÍV: {self.player.nivel}  |  ARMA: {self.player.tipo_arma}")
        self.tela.blit(self.fonte.render(info, True, BRANCO), (x, y + BAR_H + 17))

        # ── Score / Combo (canto superior direito) ──────────────────────────
        self.score.desenhar_hud(self.tela, LARGURA - 20, 20)

        # ── Respiro entre ondas ───────────────────────────────────────────────
        if self.ondas.em_respiro:
            ms = self.ondas.tempo_respiro_restante_ms()
            seg = (ms // 1000) + 1
            txt = self.fonte_md.render(f"Próxima onda em {seg}...", True, (180, 180, 255))
            self.tela.blit(txt, txt.get_rect(center=(LARGURA // 2, ALTURA - 60)))

        # ── Teclas de ajuda ───────────────────────────────────────────────
        ajuda = self.fonte.render("ESC = Pausar  |  Q = Sair", True, CINZA)
        self.tela.blit(ajuda, (LARGURA - ajuda.get_width() - 20, ALTURA - 30))

        # ── Aviso de fase ─────────────────────────────────────────────────
        if self.aviso_fase_timer > 0:
            alpha  = min(255, self.aviso_fase_timer * 4)
            # Flash branco rápido no início da transição (#12)
            if self.aviso_fase_timer > 100:
                flash_alpha = int(180 * (self.aviso_fase_timer - 100) / 20)
                flash_surf = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                flash_surf.fill((255, 255, 255, min(180, flash_alpha)))
                self.tela.blit(flash_surf, (0, 0))
            sombra = self.fonte_lg.render(f"FASE {self.fase}", True, PRETO)
            texto  = self.fonte_lg.render(f"FASE {self.fase}", True, BRANCO)
            texto.set_alpha(alpha)
            sombra.set_alpha(alpha)
            rect = texto.get_rect(center=(LARGURA // 2, ALTURA // 2 + 120))
            self.tela.blit(sombra, (rect.x + 4, rect.y + 4))
            self.tela.blit(texto,  rect)

    def _desenhar_pause(self):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.tela.blit(overlay, (0, 0))
        t = self.fonte_lg.render("PAUSADO", True, BRANCO)
        self.tela.blit(t, t.get_rect(center=(LARGURA // 2, ALTURA // 2 - 40)))
        s = self.fonte_md.render("ESC para continuar", True, CINZA)
        self.tela.blit(s, s.get_rect(center=(LARGURA // 2, ALTURA // 2 + 40)))

    def _desenhar_game_over(self):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.tela.blit(overlay, (0, 0))
        go = self.fonte_lg.render("GAME OVER", True, VERMELHO)
        self.tela.blit(go, go.get_rect(center=(LARGURA // 2, ALTURA // 2 - 60)))
        info = self.fonte_md.render(
            f"Fase {self.fase} | Nível {self.player.nivel} | Score: {self.score.score}",
            True, BRANCO)
        hi   = self.fonte_md.render(f"HIGHSCORE: {self.score.highscore}", True, AMARELO)
        self.tela.blit(info, info.get_rect(center=(LARGURA // 2, ALTURA // 2 + 10)))
        self.tela.blit(hi,   hi.get_rect(center=(LARGURA // 2, ALTURA // 2 + 50)))
        restart = self.fonte.render("R = Recomeçar   |   Q = Sair", True, CINZA)
        self.tela.blit(restart, restart.get_rect(center=(LARGURA // 2, ALTURA // 2 + 70)))

    # ═══════════════════════════════════════════════════════════════
    #  LOOP PRINCIPAL
    # ═══════════════════════════════════════════════════════════════

    def executar(self):
        while self.rodando:
            self.relogio.tick(FPS)
            self.eventos()
            self.update()
            self.desenhar()
        self.score.salvar()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.executar()

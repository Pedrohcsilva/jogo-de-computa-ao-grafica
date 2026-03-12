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
from src.poder_especial import GerenciadorPoderEspecial
from src.sound         import GerenciadorSom
from src.menu_principal import MenuPrincipal
from src.persistence   import SistemaPeristencia
from src.controls      import ControladorEntrada
from src.pause_menu    import MenuPausa
from src.ui_components import BarraHP, BarraProgressao, ContadorTexto, PainelInfo
from src.difficulty    import BalanceadorDificuldade

from src.sprites.player  import Jogador
from src.colisao_manager import ColisaoManager
from src.carta_fase     import CartaFaseMenu
from src.spawn_manager   import SpawnManager
from src.sprites.enemies import (InimigoBase, InimigoRapido, InimigoTank,
                                  InimigoAtirador, InimigoViral,
                                  InimigoNecromante, InimigoExplosivo)
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
        self.camera        = Camera()
        self.particulas    = GerenciadorParticulas()
        self.menu_up       = MenuUpgrade(LARGURA, ALTURA)
        self.nums_dano     = GerenciadorNumeroDano()
        self.boss_intro    = BossIntro(LARGURA, ALTURA, self.camera)
        self.ondas         = GerenciadorOndas()
        self.score         = GerenciadorScore()
        self.poder_esp     = GerenciadorPoderEspecial()
        self.som           = GerenciadorSom()
        self.menu          = MenuPrincipal(LARGURA, ALTURA)   # ← tela de título
        self.menu_pausa    = MenuPausa(LARGURA, ALTURA)       # ← menu de pausa
        self.controles     = ControladorEntrada()  # ← controle (teclado + gamepad)
        
        # Componentes de UI
        self.barra_hp      = BarraHP(30, 28)
        self.barra_xp      = BarraProgressao(30, 28 + 20 + 4, 260, 8, (30, 30, 40), XP_COLOR)
        self.contador_combo = ContadorTexto(LARGURA - 100, 60, 28)
        
        # Sistema de dificuldade
        self.dificuldade   = BalanceadorDificuldade()
        
        self._poder_aviso_timer = 0
        self._poder_aviso_nome  = ""

        # Managers de colisão e spawn (instanciados após reset_total)
        self.rodando      = True
        self._morte_timer = 0
        self.reset_total()
        self._colisao     = ColisaoManager(self)
        self._spawn       = SpawnManager(self)
        self.carta_fase   = CartaFaseMenu(LARGURA, ALTURA)

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

    # ── Paletas biomecânicas por fase ────────────────────────────────
    _BIO_PALETAS = [
        # Fase 1 — Floresta orgânica viva: verde bioluminescente
        {
            "fundo":  (5, 15, 8),
            "longe":  [(0,200,90),(0,160,70),(20,180,60)],
            "medio":  [(0,140,60),(0,180,80),(20,160,50)],
            "perto":  [(0,220,100),(0,180,80),(30,200,70)],
            "veias":  [(0,90,45),(0,70,35),(10,100,40)],
            "n_nod":  55, "n_fil": 45, "n_veia": 18,
        },
        # Fase 2 — Tecido nervoso: verde-ciano elétrico
        {
            "fundo":  (5, 14, 16),
            "longe":  [(0,180,160),(0,140,180),(20,160,140)],
            "medio":  [(0,140,140),(0,160,180),(10,120,160)],
            "perto":  [(0,200,180),(0,160,200),(20,180,160)],
            "veias":  [(0,80,80),(0,60,100),(10,90,70)],
            "n_nod":  60, "n_fil": 50, "n_veia": 20,
        },
        # Fase 3 — Infecção: roxo-verde ácido
        {
            "fundo":  (10, 6, 18),
            "longe":  [(120,0,180),(80,0,160),(100,20,140)],
            "medio":  [(100,0,160),(80,20,180),(60,0,140)],
            "perto":  [(160,0,220),(120,0,200),(100,20,180)],
            "veias":  [(60,0,100),(50,0,80),(70,10,90)],
            "n_nod":  65, "n_fil": 55, "n_veia": 22,
        },
        # Fase 4 — Necrose profunda: roxo sombrio denso
        {
            "fundo":  (14, 4, 20),
            "longe":  [(160,0,200),(140,0,180),(120,20,160)],
            "medio":  [(140,0,180),(120,0,200),(100,0,160)],
            "perto":  [(200,0,240),(160,0,220),(140,20,200)],
            "veias":  [(80,0,120),(70,0,100),(90,10,110)],
            "n_nod":  70, "n_fil": 60, "n_veia": 25,
        },
        # Fase 5 (boss) — Entropia biomecânica: vermelho-magenta apocalíptico
        {
            "fundo":  (20, 3, 14),
            "longe":  [(200,0,80),(180,0,60),(160,20,50)],
            "medio":  [(180,0,60),(160,0,80),(140,0,50)],
            "perto":  [(240,0,100),(200,0,80),(180,20,70)],
            "veias":  [(120,0,50),(100,0,40),(110,10,45)],
            "n_nod":  80, "n_fil": 70, "n_veia": 30,
        },
    ]

    def _gerar_bio_fase(self, fase: int):
        """Regenera elementos do background com paleta e densidade da fase."""
        import random as _r
        idx = min(fase - 1, len(self._BIO_PALETAS) - 1)
        p   = self._BIO_PALETAS[idx]

        self._bio_longe = [
            (_r.uniform(0, LARGURA), _r.uniform(0, ALTURA),
             _r.randint(1, 3), _r.choice(p["longe"]))
            for _ in range(p["n_nod"])
        ]
        self._bio_medio = [
            (_r.uniform(0, LARGURA), _r.uniform(0, ALTURA),
             _r.uniform(0, math.tau), _r.randint(15, 45),
             _r.choice(p["medio"]))
            for _ in range(p["n_fil"])
        ]
        self._bio_perto = [
            (_r.uniform(0, LARGURA * 3) - LARGURA,
             _r.uniform(0, ALTURA * 3) - ALTURA,
             _r.randint(4, 11), _r.choice(p["perto"]))
            for _ in range(60)
        ]
        self._veias = [
            (_r.uniform(-200, LARGURA + 200),
             _r.uniform(-200, ALTURA + 200),
             _r.uniform(0, math.tau),
             _r.randint(80, 260),
             _r.choice(p["veias"]))
            for _ in range(p["n_veia"])
        ]
        self._bio_fundo = p["fundo"]

    def reset_total(self):
        self.vidas              = 3
        self.fase               = 1
        self.vel_inimigos       = PLAYER_VEL * 0.4  # será atualizado pelo dificuldade system
        self.estado             = "jogando"
        self.aviso_fase_timer   = 0
        self.particulas         = GerenciadorParticulas()
        self.nums_dano          = GerenciadorNumeroDano()
        self.score.reset()
        self.ondas              = GerenciadorOndas()
        self._gerar_bio_fase(1)
        self.poder_esp          = GerenciadorPoderEspecial()
        self._poder_aviso_timer = 0
        self._poder_aviso_nome  = ""
        self.boss_intro.resetar()
        self.menu_up.ativo      = False
        self.dificuldade.atualizar_fase(1)
        self.reset_fase()
        self.ondas.iniciar_fase(self.fase)
        # Reinicia música do início (fase 1)
        if hasattr(self, 'som'):
            self.som.atualizar_musica_fase(1)
            self.som.retomar_musica()
        # Cronômetro da run — ms acumulados somente quando jogando
        self._tempo_jogando_ms  = 0
        self._ultimo_tick_ms    = pygame.time.get_ticks()

    def _salvar_jogo(self):
        """Salva o estado atual do jogo."""
        dados_jogo = {
            "fase": self.fase,
            "hp_jogador": self.player.hp,
            "hp_max": self.player.hp_max,
            "arma_equipada": self.player.tipo_arma if hasattr(self.player, 'tipo_arma') else "pistola",
            "upgrades": list(self.menu_up._upgrades_adquiridos),
            "score": self.score.score,
            "combo": self.score.combo,
            "xp_atual": self.player.xp if hasattr(self.player, 'xp') else 0,
            "timestamp": pygame.time.get_ticks(),
        }
        SistemaPeristencia.salvar_jogo(dados_jogo)
    
    def _carregar_jogo(self):
        """Carrega um save do jogo."""
        dados = SistemaPeristencia.carregar_jogo()
        if not dados:
            print("Erro ao carregar save, iniciando novo jogo...")
            return
        
        # Restaurar estado
        self.reset_total()
        self.fase = dados.get("fase", 1)
        self.ondas.iniciar_fase(self.fase)
        self._gerar_bio_fase(self.fase)
        self.player.hp = dados.get("hp_jogador", self.player.hp_max)
        self.player.hp_max = dados.get("hp_max", HP_MAX)
        self.menu_up._upgrades_adquiridos = set(dados.get("upgrades", []))
        self.score.score = dados.get("score", 0)
        self.score.combo = dados.get("combo", 0)
        
        # Upgrades são reaplicados quando o jogador pegar level-up normalmente
        # (não é possível restaurar efeitos de upgrades de estado, apenas metadados)
        
        print(f"✓ Jogo restaurado da Fase {self.fase}")

    # ═══════════════════════════════════════════════════════════════
    #  EVENTOS
    # ═══════════════════════════════════════════════════════════════

    def eventos(self):
        # Coletar eventos para o frame
        lista_eventos = list(pygame.event.get())
        
        for evento in lista_eventos:
            if evento.type == pygame.QUIT:
                self.rodando = False

            # ── Menu principal intercepta tudo enquanto ativo ────────
            if self.menu.ativo:
                acao = self.menu.processar_evento(evento)
                if acao == "sair":
                    self.rodando = False
                elif acao == "jogar":
                    pass   # menu.ativo já foi setado False dentro do menu
                elif acao == "continuar":
                    self._carregar_jogo()
                    # menu.ativo já foi setado False dentro do menu
                continue    # bloqueia o resto do loop de eventos

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE and not self.menu_up.ativo and not self.menu_pausa.visivel:
                    if self.estado == "jogando":
                        self.estado = "pausado"
                        self.menu_pausa.mostrar()
                        self.som.pausar_musica()
                    elif self.estado == "pausado":
                        self.estado = "jogando"
                        self.menu_pausa.esconder()

                # R: reinicia após game over ou vitória
                if self.estado in ("game_over", "vitoria") and evento.key == pygame.K_r:
                    self.estado = "jogando"
                    self.reset_total()

                # ESPAÇO: ativa poder especial (somente quando jogando e sem menus abertos)
                if evento.key == pygame.K_SPACE and self.estado == "jogando" and not self.menu_up.ativo and not self.menu_pausa.visivel:
                    nome = self.poder_esp.ativar(
                        self.player, self.inimigos,
                        self.particulas, self.camera)
                    if nome:
                        self._poder_aviso_nome  = f"⚡ {nome} ATIVADO!"
                        self._poder_aviso_timer = 120

                # Q: sair a qualquer momento
                if evento.key == pygame.K_q:
                    self.rodando = False

            # Carta de fase (recompensa entre fases)
            if self.carta_fase.ativo:
                if self.carta_fase.processar_evento(evento, self.player):
                    # Carta escolhida: agora inicia as ondas da nova fase
                    self.ondas.iniciar_fase(self.fase)
                    self.particulas.nivel_up_burst(self.player.pos)
                    self.camera.adicionar_shake(SHAKE_LEVEL_UP)

            # Menu de upgrade captura seus próprios eventos
            if self.menu_up.ativo:
                fechou = self.menu_up.processar_evento(evento, self.player)
                if fechou:
                    self.estado = "jogando"
                    self.particulas.nivel_up_burst(self.player.pos)
                    self.camera.adicionar_shake(SHAKE_LEVEL_UP)
            
            # Menu de pausa captura seus próprios eventos
            if self.menu_pausa.visivel:
                acao = self.menu_pausa.processar_evento(evento)
                if acao == "continuar":
                    self.estado = "jogando"
                    self.menu_pausa.esconder()
                    self.som.retomar_musica()
                elif acao == "reiniciar":
                    self.estado = "jogando"
                    self.menu_pausa.esconder()
                    self.reset_total()
                elif acao == "menu":
                    self._salvar_jogo()
                    self.estado = "jogando"
                    self.menu_pausa.esconder()
                    self.reset_total()
                    self.menu.ativo = True
                elif acao == "sair":
                    self.rodando = False
                elif acao == "volume_changed":
                    # Aplica volume imediatamente ao GerenciadorSom
                    self.som.set_volume_sfx(self.menu_pausa.volume_sfx)
                    self.som.set_volume_musica(self.menu_pausa.volume_musica)

            # Spawn legado removido — o GerenciadorOndas controla os spawns agora

        # ── Processar entrada consolidada (teclado + gamepad) ──
        entrada = self.controles.atualizar(lista_eventos)
        
        # Passar movimento ao player
        if entrada["movimento"].length() > 0:
            self.player._entrada_movimento = entrada["movimento"]
        else:
            self.player._entrada_movimento = pygame.math.Vector2(0, 0)
        
        # Processar pausa pelo controlador
        if entrada["pausa"] and not self.menu_up.ativo and not self.menu_pausa.visivel:
            if self.estado == "jogando":
                self.estado = "pausado"
                self.menu_pausa.mostrar()
            elif self.estado == "pausado":
                self.estado = "jogando"
                self.menu_pausa.esconder()
        
        # Processar poder pelo controlador
        if entrada["poder"] and self.estado == "jogando":
            nome = self.poder_esp.ativar(
                self.player, self.inimigos,
                self.particulas, self.camera)
            if nome:
                self._poder_aviso_nome  = f"⚡ {nome} ATIVADO!"
                self._poder_aviso_timer = 120

    # ═══════════════════════════════════════════════════════════════
    #  UPDATE
    # ═══════════════════════════════════════════════════════════════

    def update(self):
        # ── Menu principal — atualiza animações antes de qualquer coisa ──
        if self.menu.ativo:
            self.menu.update()
            return

        # ── Cronômetro: acumula somente quando jogando ────────────────
        agora_ms = pygame.time.get_ticks()
        if self.estado == "jogando":
            self._tempo_jogando_ms = getattr(self, "_tempo_jogando_ms", 0) + \
                                     (agora_ms - getattr(self, "_ultimo_tick_ms", agora_ms))
        self._ultimo_tick_ms = agora_ms

        # ── Cinematica do Boss (roda mesmo quando estado != "jogando") ──
        if self.boss_intro.ativo:
            self.boss_intro.update()
            # Momento exato de spawnar: cria o boss quando a intro sinaliza
            if self.boss_intro.pronto_para_spawnar():
                self._spawn.spawnar_boss()
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

        # ── Carta de Fase (pausa o jogo enquanto ativa) ─────────────
        if self.carta_fase.ativo:
            self.carta_fase.atualizar()
            self.camera.update(self.player.pos, LARGURA, ALTURA)
            return

        # ── 1. Jogador ──────────────────────────────────────────────
        self.player.update()
        self.poder_esp.update(self.player)

        # ── Efeitos dos poderes especiais ativos ─────────────────────
        if getattr(self.player, "_frenesim_ativo", False):
            self.player.velocidade = PLAYER_VEL * 1.8
        elif getattr(self.player, "_overload_ativo", False):
            self.player.velocidade = PLAYER_VEL * 1.5
        else:
            self.player.velocidade = PLAYER_VEL

        # I-frames garantidos enquanto escudo ativo
        if getattr(self.player, "_escudo_ativo", False):
            self.player._iframe_timer = 10

        # Aviso de poder na tela
        if self._poder_aviso_timer > 0:
            self._poder_aviso_timer -= 1

        # ── 1b. Efeitos passivos de upgrades ────────────────────────
        # Regen de vida
        if getattr(self.player, "regen_ativo", False):
            self.player.regen_timer = getattr(self.player, "regen_timer", 0) + 1
            if self.player.regen_timer >= 120:
                self.player.regen_timer = 0
                val = getattr(self.player, "regen_valor", 1)
                self.player.hp = min(self.player.hp_max, self.player.hp + val)

        # Aura de dano — 3 dano/s (1 a cada 20 frames) em inimigos adjacentes
        if getattr(self.player, "aura_dano", False):
            self._aura_tick = getattr(self, "_aura_tick", 0) + 1
            if self._aura_tick >= 20:
                self._aura_tick = 0
                for ini in list(self.inimigos):
                    if (ini.pos - self.player.pos).length() < 120:
                        ini.sofrer_dano(3)
                        if ini.hp <= 0:
                            self._matar_inimigo(ini)

        # Escudo passivo — recarga
        if getattr(self.player, "escudo_passivo", False):
            if not getattr(self.player, "escudo_pronto", True):
                self.player.escudo_cd_atual = getattr(self.player, "escudo_cd_atual", 0) + 1
                if self.player.escudo_cd_atual >= self.player.escudo_cd_max:
                    self.player.escudo_pronto = True
                    self.player.escudo_cd_atual = 0

        # ── 1c. Score update ─────────────────────────────────────────
        self.score.update()

        # ── 1d. Ondas: verifica se deve spawnar próximo inimigo ──────
        self.ondas.update(len(self.inimigos))
        tipo_spawn = self.ondas.inimigo_a_spawnar()
        if tipo_spawn:
            self._spawn.spawnar_inimigo(tipo_spawn)

        # Avança fase quando onda completa
        if self.ondas.completa:
            e_fase_boss = (self.fase % BOSS_INTERVALO == 0)   # fases 5, 10, 15

            if e_fase_boss and not self.boss_ativo and not self.boss_intro.ativo:
                # É uma fase de boss — inicia a cinemática com o número do boss
                nivel_boss = self.fase // BOSS_INTERVALO
                self.boss_intro.iniciar(nivel_boss)

            elif not e_fase_boss:
                # Fase normal: avança
                if self.fase < META_FASES:
                    self.som.play_fase_completa()
                    self.fase            += 1
                    self.vel_inimigos    = self.dificuldade.get_velocidade_inimigos()
                    self.dificuldade.atualizar_fase(self.fase)
                    self.som.atualizar_musica_fase(self.fase)
                    self.aviso_fase_timer = 120
                    self.camera.adicionar_shake(SHAKE_LEVEL_UP * 0.5)
                    self.particulas.transicao_fase(LARGURA, ALTURA)
                    self._gerar_bio_fase(self.fase)
                    self.player.atualizar_fase(self.fase)
                    if (self.fase - 1) % 2 == 0:
                        info = self.poder_esp.desbloquear(self.fase - 1)
                        if info:
                            self._poder_aviso_nome  = f"PODER DESBLOQUEADO: {info['icone']} {info['nome']}"
                            self._poder_aviso_timer = 240
                            self.som.play_power_up()
                    # Carta de fase — jogador escolhe recompensa antes das ondas iniciarem
                    self.carta_fase.sortear(self.fase - 1)
                    # ondas.iniciar_fase chamado após carta ser escolhida (_apos_carta_fase)

        # ── 2. Tiro do Jogador ──────────────────────────────────────
        if pygame.mouse.get_pressed()[0]:
            agora = pygame.time.get_ticks()
            mult_cad = 0.5 if (getattr(self.player, "_frenesim_ativo", False)
                               or getattr(self.player, "_overload_ativo", False)) else 1.0
            cadencia_ef = int(self.player.cadencia * mult_cad)
            if agora - self.player.ultimo_tiro > cadencia_ef:
                self.player.ultimo_tiro = agora
                disparos = self.player.atirar()
                for direcao, tipo, origem in disparos:
                    bala = self._criar_bala_player(tipo, direcao, origem)
                    self.balas_player.add(bala)
                    self.todos_sprites.add(bala)
                if disparos:
                    self.som.play_tiro(self.player.tipo_arma.lower()
                                       if self.player.tipo_arma != "Metralhadora"
                                       else "metralhadora")

        # ── 3. Inimigos e Boss (via lista de disparos) ──────────────
        lista_disparos = []

        for inimigo in list(self.inimigos):
            inimigo.update(self.player.pos, lista_disparos)

            # Explosivo: detonou por proximidade
            if getattr(inimigo, "_pedido_explosao", False):
                inimigo._pedido_explosao = False
                self.particulas.explosao(inimigo.pos, (255, 130, 0), quantidade=40, raio_max=9)
                self.camera.adicionar_shake(0.6)
                # Dano em área no jogador
                dist_exp = (self.player.pos - inimigo.pos).length()
                if dist_exp < inimigo.RAIO_EXPLOSAO:
                    self.player.sofrer_dano(inimigo.DANO_EXPLOSAO)
                    if not self.player.esta_invencivel():
                        self.nums_dano.adicionar(self.player.pos,
                                                 inimigo.DANO_EXPLOSAO, eh_jogador=True)
                        self.score.registrar_dano()
                        self.som.play_dano_jogador()
                    self._verificar_morte_jogador()
                self._matar_inimigo(inimigo)

            # Necromante: cura os 3 inimigos mais próximos
            elif getattr(inimigo, "_pedido_cura", False):
                inimigo._pedido_cura = False
                vizinhos = sorted(
                    [i for i in self.inimigos if i is not inimigo],
                    key=lambda i: (i.pos - inimigo.pos).length()
                )[:3]
                for v in vizinhos:
                    v.hp = min(v.hp_max, v.hp + 8)
                    self.particulas.hit_sparks(v.pos)   # visual de cura

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

        # ── 7b. Atualizar menus (animações) ──────────────────────────
        if self.menu_pausa.visivel:
            self.menu_pausa.atualizar()

        # ── 8. Câmera ─────────────────────────────────────────────────
        self.camera.update(self.player.pos, LARGURA, ALTURA)

        # ── 9. Colisões ───────────────────────────────────────────────
        self._colisao.checar()

    # ── Helpers de criação de balas ───────────────────────────────────

    def _criar_bala_player(self, tipo, direcao, origem=None):
        """
        Cria projétil do jogador respeitando dano_bala em TODAS as armas.
        Aplica upgrade bala_larga (projétil 2× maior) quando ativo.
        Overload: dano dobrado enquanto ativo.
        Aplica bala_perfurante (penetra até 3 inimigos) e ricochet.
        """
        pos   = origem if origem is not None else self.player.pos
        larga = getattr(self.player, "bala_larga", False)
        dano  = self.player.dano_bala
        if getattr(self.player, "_overload_ativo", False):
            dano = int(dano * 2)
        # Sangue Frio: +30% dano quando HP < 40%
        if getattr(self.player, "carta_sangue_frio", False):
            if self.player.hp < self.player.hp_max * 0.40:
                dano = int(dano * 1.30)

        if tipo == "metralhadora":
            tam = (12, 12) if larga else (6, 6)
            bala = BalaMetralhadora(pos, direcao, dano=dano, tamanho=tam)
        elif tipo == "shotgun":
            tam = (18, 18) if larga else (10, 10)
            bala = BalaShotgun(pos, direcao, dano=dano, tamanho=tam)
        else:
            # Pistola padrão
            tam = (16, 16) if larga else (8, 8)
            bala = Bala(pos, direcao, AZUL_TIRO, dano=dano, tamanho=tam)

        # Aplicar upgrades de comportamento de bala
        if getattr(self.player, "bala_perfurante", False):
            bala._penetracoes_restantes = 3
        if getattr(self.player, "bala_ricochet", False):
            bala._tem_ricochet  = True
            bala._ricocheteou   = False

        return bala

    def _processar_disparo_inimigo(self, pedido):
        pos  = pedido["pos"]
        dir_ = pedido["dir"]
        tipo = pedido.get("tipo", "inimigo")
        cor  = pedido.get("cor", LARANJA)

        if tipo == "boss":
            bala = BalaBoss(pos, dir_, cor=cor)
        else:
            bala = BalaInimiga(pos, dir_)
            # Aplica dano customizado se a dificuldade escalou
            if "dano" in pedido:
                bala.dano = pedido["dano"]

        self.balas_inimigos.add(bala)
        self.todos_sprites.add(bala)

    # ═══════════════════════════════════════════════════════════════
    #  SPAWN
    # ═══════════════════════════════════════════════════════════════

    def spawn_inimigo(self):
        """Mantido para compatibilidade; lógica principal agora em GerenciadorOndas."""
        pass



    # ═══════════════════════════════════════════════════════════════
    #  COLISÕES
    # ═══════════════════════════════════════════════════════════════


    def _matar_inimigo(self, inimigo):
        self.particulas.explosao(inimigo.pos, inimigo.cor, quantidade=20)

        # Shake diferenciado
        if isinstance(inimigo, InimigoTank):
            self.camera.adicionar_shake(SHAKE_MATA_TANK)
        else:
            self.camera.adicionar_shake(SHAKE_MATA_NORMAL)

        self.inimigos_derrotados += 1

        valor_xp = getattr(inimigo, "xp_valor", 10)
        self.score.registrar_kill(valor_xp)

        # Upgrade: Morte Explosiva
        if getattr(self.player, "explosao_ao_matar", False):
            self.particulas.explosao(inimigo.pos, inimigo.cor, quantidade=35, raio_max=7)
            self.camera.adicionar_shake(SHAKE_MATA_NORMAL * 1.5)

        # Viral: divide em fragmentos ao morrer
        if isinstance(inimigo, InimigoViral) and not inimigo.eh_fragmento:
            for frag in inimigo.gerar_fragmentos():
                self.inimigos.add(frag)
                self.todos_sprites.add(frag)

        # Drop de XP
        gema = XpGem(inimigo.pos, valor_xp)
        self.xp_gems.add(gema)
        self.todos_sprites.add(gema)

        # Drop de arma (15% base, 40% com upgrade drop_arma)
        chance_drop = 0.40 if getattr(self.player, "drop_arma_bonus", False) else 0.15
        if random.random() < chance_drop:
            tipo = random.choice(["Metralhadora", "Shotgun"])
            item = ItemArma(inimigo.pos, tipo)
            self.itens_chao.add(item)
            self.todos_sprites.add(item)

        # Necronomicon: a cada 10 kills emite rajada de projéteis fantasma
        if getattr(self.player, "carta_necronomico", False):
            self._necro_contador = getattr(self, "_necro_contador", 0) + 1
            if self._necro_contador >= 10:
                self._necro_contador = 0
                for ang in range(0, 360, 30):
                    dir_n = pygame.math.Vector2(
                        math.cos(math.radians(ang)),
                        math.sin(math.radians(ang))
                    )
                    b = Bala(inimigo.pos, dir_n, cor=(160, 0, 200), dano=25, vida=90)
                    self.balas_player.add(b)
                    self.todos_sprites.add(b)
                self.particulas.explosao(inimigo.pos, (160, 0, 200), quantidade=20, raio_max=5)
                self.som.play_power_up()

        inimigo.kill()

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
        self.player.atualizar_fase(self.fase)
        self.aviso_fase_timer = 180

        # Vitória ao matar o boss final (fase 15)
        if self.fase > META_FASES:
            self.estado = "vitoria"
            self.som.play_fase_completa()
        else:
            # Continua o jogo: carta especial de fase (boss concluído)
            self._gerar_bio_fase(min(self.fase, len(self._BIO_PALETAS)))
            self.dificuldade.atualizar_fase(self.fase)
            self.som.atualizar_musica_fase(self.fase)
            self.carta_fase.sortear(self.fase - 1)
            # ondas.iniciar_fase chamado após carta ser escolhida

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
                self.estado = "morrendo"
                self.som.pausar_musica()   # para a música na morte

    def _level_up(self):
        self.player.nivel            += 1
        self.player.xp                = 0
        self.player.xp_proximo_nivel  = int(self.player.xp_proximo_nivel * XP_INCREMENTO)
        self.menu_up.sortear(self.player)
        self.estado = "pausado"
        self.som.play_level_up()

    # ═══════════════════════════════════════════════════════════════
    #  DESENHO
    # ═══════════════════════════════════════════════════════════════

    def desenhar(self):
        # ── Menu principal sobrepõe tudo quando ativo ─────────────────
        if self.menu.ativo:
            self.menu.desenhar(self.tela)
            pygame.display.flip()
            return

        # Cor de fundo vem da paleta da fase atual (gerada em _gerar_bio_fase)
        self.tela.fill(getattr(self, "_bio_fundo", (5, 15, 8)))
        offset = self.camera.offset

        # ── Grid ─────────────────────────────────────────────────────
        self._desenhar_grid(offset)

        # ── Sprites do mundo (exceto player) ─────────────────────────
        for sprite in self.todos_sprites:
            if sprite == self.player:
                continue
            rect_pos = sprite.image.get_rect(center=sprite.pos + offset)
            self.tela.blit(sprite.image, rect_pos)

        # ── Timer visual dos itens de arma ────────────────────────────
        for item in self.itens_chao:
            item.desenhar_timer(self.tela, offset)

        # ── Partículas (mundo) ────────────────────────────────────────
        self.particulas.desenhar(self.tela, offset)

        # ── Números de dano flutuantes ────────────────────────────────
        self.nums_dano.desenhar(self.tela, offset)

        # ── Player (sempre no centro) ─────────────────────────────────
        centro = (LARGURA // 2, ALTURA // 2)
        self.tela.blit(self.player.image, self.player.image.get_rect(center=centro))

        # ── Muzzle flash (boca do canhão) ────────────────────────────
        if self.player._muzzle_timer > 0:
            self.player._muzzle_timer -= 1
            t   = self.player._muzzle_timer
            r   = 6 + t * 3              # raio decrescente
            alp = t * 60                 # fade out
            pos_tela = self.player._muzzle_pos + offset
            mf = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            # Anel externo
            pygame.draw.circle(mf, (*AMARELO, alp), (r+1, r+1), r)
            # Núcleo branco
            pygame.draw.circle(mf, (255, 255, 255, min(255, alp + 80)),
                               (r+1, r+1), max(1, r // 2))
            self.tela.blit(mf, mf.get_rect(center=(int(pos_tela.x),
                                                     int(pos_tela.y))))

        # ── Barra de vida do Boss ─────────────────────────────────────
        if self.boss_ativo and self.boss_ref:
            self.boss_ref.desenhar_barra_vida(self.tela)

        # ── HUD ───────────────────────────────────────────────────────
        self._desenhar_hud()

        # ── Borda do mundo (aviso visual de limite) ──────────────────
        self._desenhar_borda_mundo(offset)

        # ── HUD do poder especial ─────────────────────────────────────
        self.poder_esp.desenhar_hud(self.tela)

        # ── Aviso de poder desbloqueado/ativado ───────────────────────
        if self._poder_aviso_timer > 0:
            alpha = min(255, self._poder_aviso_timer * 8)
            txt   = self.fonte_md.render(self._poder_aviso_nome, True, (100, 255, 200))
            txt.set_alpha(alpha)
            rx = LARGURA // 2 - txt.get_width() // 2
            ry = ALTURA // 2 + 80
            self.tela.blit(txt, (rx, ry))

        # ── Cinematica do Boss (sobrepõe tudo exceto o cursor) ────────
        self.boss_intro.desenhar(self.tela)

        # ── Overlays de estado ────────────────────────────────────────
        if self.estado == "game_over":
            self._desenhar_game_over()
        elif self.estado == "vitoria":
            self._desenhar_vitoria()
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
                self.menu_pausa.desenhar(self.tela)

        # Carta de fase sobreposta (aparece sobre o jogo pausado)
        if self.carta_fase.ativo:
            self.carta_fase.desenhar(self.tela)

        pygame.display.flip()

    def _desenhar_borda_mundo(self, offset):
        """Desenha borda vermelha pulsante quando o jogador se aproxima do limite do mundo."""
        dist = self.player.distancia_borda()
        if dist <= 0:
            return
        alpha = int(dist * 180)
        pulse = abs(pygame.time.get_ticks() % 600 - 300) / 300.0  # 0→1→0
        alpha = int(alpha * (0.6 + 0.4 * pulse))
        borda = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        espessura = int(20 + dist * 30)
        # Bordas nos 4 lados
        pygame.draw.rect(borda, (255, 50, 50, alpha), (0, 0, LARGURA, espessura))
        pygame.draw.rect(borda, (255, 50, 50, alpha), (0, ALTURA - espessura, LARGURA, espessura))
        pygame.draw.rect(borda, (255, 50, 50, alpha), (0, 0, espessura, ALTURA))
        pygame.draw.rect(borda, (255, 50, 50, alpha), (LARGURA - espessura, 0, espessura, ALTURA))
        self.tela.blit(borda, (0, 0))
        # Texto de aviso
        if dist > 0.5:
            txt = self.fonte.render("⚠ BORDA DO MUNDO", True, (255, 100, 100))
            txt.set_alpha(alpha)
            self.tela.blit(txt, txt.get_rect(center=(LARGURA // 2, 80)))

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

    def _desenhar_mini_mapa(self):
        """Mini-mapa no canto inferior esquerdo mostrando posição do jogador no mundo."""
        LIMITE = 2000
        mm_w, mm_h = 120, 120
        mm_x = 20
        mm_y = ALTURA - mm_h - 20

        # Fundo semi-transparente
        surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 120))
        pygame.draw.rect(surf, (60, 80, 60, 200), (0, 0, mm_w, mm_h), width=1, border_radius=4)

        # Inimigos no mini-mapa
        for ini in self.inimigos:
            rx = int((ini.pos.x + LIMITE) / (LIMITE * 2) * mm_w)
            ry = int((ini.pos.y + LIMITE) / (LIMITE * 2) * mm_h)
            rx = max(2, min(mm_w - 3, rx))
            ry = max(2, min(mm_h - 3, ry))
            pygame.draw.circle(surf, (255, 60, 60), (rx, ry), 2)

        # Boss no mini-mapa
        if self.boss_ativo and self.boss_ref:
            bx = int((self.boss_ref.pos.x + LIMITE) / (LIMITE * 2) * mm_w)
            by = int((self.boss_ref.pos.y + LIMITE) / (LIMITE * 2) * mm_h)
            bx = max(3, min(mm_w - 4, bx))
            by = max(3, min(mm_h - 4, by))
            pygame.draw.circle(surf, (255, 50, 255), (bx, by), 5)
            pygame.draw.circle(surf, (255, 200, 255), (bx, by), 3)

        # Jogador (sempre no centro do mini-mapa)
        px = int((self.player.pos.x + LIMITE) / (LIMITE * 2) * mm_w)
        py = int((self.player.pos.y + LIMITE) / (LIMITE * 2) * mm_h)
        px = max(4, min(mm_w - 5, px))
        py = max(4, min(mm_h - 5, py))
        pygame.draw.circle(surf, (0, 255, 120), (px, py), 4)
        pygame.draw.circle(surf, (255, 255, 255), (px, py), 2)

        self.tela.blit(surf, (mm_x, mm_y))

        # Label
        lbl = self.fonte.render("MAPA", True, (100, 140, 100))
        self.tela.blit(lbl, (mm_x + mm_w // 2 - lbl.get_width() // 2, mm_y - 18))

    def _desenhar_hud(self):
        # ── Atualizar componentes de UI ───────────────────────────────
        self.barra_hp.atualizar(self.player.hp, self.player.hp_max)
        xp_pct = self.player.xp / self.player.xp_proximo_nivel if self.player.xp_proximo_nivel > 0 else 0
        self.barra_xp.atualizar(xp_pct)
        self.contador_combo.atualizar(self.score.combo)
        
        # ── Desenhar barra de HP ──────────────────────────────────────
        self.barra_hp.desenhar(self.tela)
        
        # ── Desenhar barra de XP ──────────────────────────────────────
        self.barra_xp.desenhar(self.tela)

        # ── Barra de Progresso de Fases ──────────────────────────────────
        prog_w = 300
        prog_h = 10
        prog_x = LARGURA // 2 - prog_w // 2
        prog_y = ALTURA - 22
        prog_pct = (self.fase - 1) / max(1, META_FASES)
        pygame.draw.rect(self.tela, (20, 30, 20), (prog_x, prog_y, prog_w, prog_h), border_radius=4)
        cor_prog = (255, 200, 0) if self.fase % BOSS_INTERVALO == 0 else (0, 200, 100)
        pygame.draw.rect(self.tela, cor_prog, (prog_x, prog_y, int(prog_w * prog_pct), prog_h), border_radius=4)
        pygame.draw.rect(self.tela, (60, 80, 60), (prog_x, prog_y, prog_w, prog_h), width=1, border_radius=4)
        # Marcadores de boss nas fases 5, 10, 15
        for fase_boss in range(BOSS_INTERVALO, META_FASES + 1, BOSS_INTERVALO):
            bx = prog_x + int(prog_w * (fase_boss - 1) / META_FASES)
            pygame.draw.line(self.tela, (255, 60, 60), (bx, prog_y - 2), (bx, prog_y + prog_h + 2), 2)
        txt_prog = self.fonte.render(f"FASE {self.fase} / {META_FASES}", True, (120, 160, 120))
        self.tela.blit(txt_prog, txt_prog.get_rect(center=(LARGURA // 2, prog_y - 12)))

        # ── Informações de status ─────────────────────────────────────────
        info = (f"❤ VIDAS: {self.vidas}  |  "
                f"⬆ NÍV: {self.player.nivel}  |  ✧ ARMA: {self.player.tipo_arma}")
        self.tela.blit(self.fonte.render(info, True, BRANCO), (30, 28 + 20 + 4 + 8 + 8))

        # ── Score / Combo (desenhar contador animado) ──────────────────────
        txt_score = self.fonte_md.render(f"SCORE: {self.score.score:,}", True, (200, 200, 0))
        self.tela.blit(txt_score, (LARGURA - txt_score.get_width() - 20, 20))
        
        # ── Combo com cor dinâmica ────────────────────────────────────────
        if self.score.combo > 0:
            if self.score.combo <= 4:
                cor_combo = AZUL_TIRO
            elif self.score.combo <= 9:
                cor_combo = VERDE
            elif self.score.combo <= 19:
                cor_combo = AMARELO
            else:
                cor_combo = VERMELHO
            
            txt_combo = self.fonte_md.render(f"☠ COMBO x{self.score.combo}", True, cor_combo)
            self.tela.blit(txt_combo, (LARGURA - txt_combo.get_width() - 20, 60))

        # ── Respiro entre ondas ───────────────────────────────────────────
        if self.ondas.em_respiro:
            ms = self.ondas.tempo_respiro_restante_ms()
            seg = (ms // 1000) + 1
            txt = self.fonte_md.render(f"Próxima onda em {seg}...", True, (180, 180, 255))
            self.tela.blit(txt, txt.get_rect(center=(LARGURA // 2, ALTURA - 60)))

        # ── Tutorial — dicas na fase 1 ───────────────────────────────────
        if self.fase == 1:
            self._desenhar_tutorial()

        # ── Mini-mapa de posição no mundo ────────────────────────────────
        self._desenhar_mini_mapa()

        # ── Teclas de ajuda ───────────────────────────────────────────────
        help_text = "🎮 ESC=Pausa | ESPAÇO=Poder Especial"
        ajuda = self.fonte.render(help_text, True, CINZA)
        self.tela.blit(ajuda, (LARGURA - ajuda.get_width() - 20, ALTURA - 50))

        # ── Aviso de fase ─────────────────────────────────────────────────
        if self.aviso_fase_timer > 0:
            alpha  = min(255, self.aviso_fase_timer * 4)
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

    def _desenhar_tutorial(self):
        """Dicas contextuais exibidas apenas na fase 1 para novos jogadores."""
        dicas = [
            ("WASD",        "Mover"),
            ("Mouse",       "Mirar"),
            ("Clique",      "Atirar"),
            ("ESPAÇO",      "Poder Especial"),
        ]
        t = pygame.time.get_ticks()
        # Exibe dicas em cards flutuantes no lado direito
        base_x = LARGURA - 220
        base_y = ALTURA // 2 - 100
        for i, (tecla, desc) in enumerate(dicas):
            y = base_y + i * 52
            alpha = int(160 + 40 * math.sin(t * 0.003 + i))
            card = pygame.Surface((190, 42), pygame.SRCALPHA)
            card.fill((0, 30, 20, alpha))
            pygame.draw.rect(card, (0, 150, 80, 160), (0, 0, 190, 42), width=1, border_radius=6)
            txt_tecla = self.fonte.render(tecla, True, (0, 220, 110))
            txt_desc  = self.fonte.render(desc,  True, (180, 210, 190))
            card.blit(txt_tecla, (10, 5))
            card.blit(txt_desc,  (10, 22))
            self.tela.blit(card, (base_x, y))


    def _desenhar_game_over(self):
        import math as _math
        t = pygame.time.get_ticks()
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.tela.blit(overlay, (0, 0))

        # Título pulsante
        pulso = 0.5 + 0.5 * _math.sin(t * 0.003)
        cor_go = (int(200 + 55 * pulso), int(30 + 20 * pulso), int(30 + 20 * pulso))
        go_sombra = self.fonte_lg.render("GAME OVER", True, (80, 0, 0))
        go = self.fonte_lg.render("GAME OVER", True, cor_go)
        rect_go = go.get_rect(center=(LARGURA // 2, ALTURA // 2 - 120))
        self.tela.blit(go_sombra, (rect_go.x + 5, rect_go.y + 5))
        self.tela.blit(go, rect_go)

        # Novo recorde badge
        e_novo_recorde = self.score.score > 0 and self.score.score >= self.score.highscore
        if e_novo_recorde:
            nr = self.fonte_md.render("✦ NOVO RECORDE! ✦", True, AMARELO)
            self.tela.blit(nr, nr.get_rect(center=(LARGURA // 2, ALTURA // 2 - 55)))

        # Linha divisória
        pygame.draw.line(self.tela, (100, 30, 30),
                         (LARGURA // 2 - 280, ALTURA // 2 - 30),
                         (LARGURA // 2 + 280, ALTURA // 2 - 30), 1)

        # Stats em 2 colunas
        stats = [
            ("Fase alcançada",     f"{self.fase} / {META_FASES}"),
            ("Nível do jogador",   str(self.player.nivel)),
            ("Inimigos mortos",    str(getattr(self, 'inimigos_derrotados', 0))),
            ("Score final",        f"{self.score.score:,}"),
            ("Highscore",          f"{self.score.highscore:,}"),
        ]
        for i, (lbl, val) in enumerate(stats):
            y = ALTURA // 2 + i * 36
            cor_val = AMARELO if (i == 4 and e_novo_recorde) else BRANCO
            t_lbl = self.fonte.render(lbl + ":", True, (160, 100, 100))
            t_val = self.fonte_md.render(val, True, cor_val)
            self.tela.blit(t_lbl, t_lbl.get_rect(right=LARGURA // 2 - 10, centery=y))
            self.tela.blit(t_val, t_val.get_rect(left=LARGURA // 2 + 10, centery=y))

        pygame.draw.line(self.tela, (100, 30, 30),
                         (LARGURA // 2 - 280, ALTURA // 2 + 192),
                         (LARGURA // 2 + 280, ALTURA // 2 + 192), 1)

        restart = self.fonte_md.render("[ R ]  Jogar Novamente      [ Q ]  Sair", True, (200, 180, 180))
        self.tela.blit(restart, restart.get_rect(center=(LARGURA // 2, ALTURA // 2 + 215)))

    def _desenhar_vitoria(self):
        """Tela de vitória épica com estatísticas completas da run."""
        t = pygame.time.get_ticks()

        # Overlay escuro
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.tela.blit(overlay, (0, 0))

        # Partículas douradas de celebração (estáticas simuladas)
        import random as _rnd
        _rnd.seed(42)
        for _ in range(60):
            px = _rnd.randint(0, LARGURA)
            py = _rnd.randint(0, ALTURA // 3)
            r  = _rnd.randint(2, 5)
            a  = int(80 + 120 * abs(math.sin(t * 0.002 + _rnd.random() * 6)))
            s  = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 220, 0, a), (r, r), r)
            self.tela.blit(s, (px, py))

        # Título pulsante
        pulso     = abs(math.sin(t * 0.0025))
        cor_titulo = (int(200 + 55 * pulso), int(170 + 85 * pulso), 0)
        titulo = self.fonte_lg.render("✦  VITÓRIA  ✦", True, cor_titulo)
        self.tela.blit(titulo, titulo.get_rect(center=(LARGURA // 2, ALTURA // 2 - 200)))

        sub = self.fonte_md.render("Todos os 3 bosses derrotados — 15 fases concluídas!", True, (180, 210, 180))
        self.tela.blit(sub, sub.get_rect(center=(LARGURA // 2, ALTURA // 2 - 140)))

        # Nota de desempenho
        score = self.score.score
        nota, cor_nota = ("S", (255, 220, 0)) if score > 15000 else \
                         ("A", (0, 255, 150)) if score > 8000  else \
                         ("B", (0, 180, 255)) if score > 3000  else \
                         ("C", (180, 180, 180))
        nt = self.fonte_lg.render(nota, True, cor_nota)
        self.tela.blit(nt, nt.get_rect(center=(LARGURA // 2, ALTURA // 2 - 60)))
        nt_label = self.fonte_md.render("NOTA", True, (120, 120, 120))
        self.tela.blit(nt_label, nt_label.get_rect(center=(LARGURA // 2, ALTURA // 2 - 15)))

        # Formatar tempo de jogo  mm:ss
        ms_total = getattr(self, "_tempo_jogando_ms", 0)
        segundos = ms_total // 1000
        tempo_str = f"{segundos // 60:02d}:{segundos % 60:02d}"

        # Estatísticas em 2 colunas
        col_labels = ["Nível alcançado", "Inimigos derrotados", "Score final",   "Tempo de jogo"]
        col_values = [str(self.player.nivel),
                      str(getattr(self, "inimigos_derrotados", 0)),
                      f"{self.score.score:,}",
                      tempo_str]
        col2_labels = ["Highscore",              "Fase final",          "Combo máximo", "Arma final"]
        col2_values = [f"{self.score.highscore:,}", f"{META_FASES}/{META_FASES}",
                       str(getattr(self.score, "combo", 0)),
                       getattr(self.player, "tipo_arma", "Pistola")]

        for i in range(4):
            y = ALTURA // 2 + 10 + i * 38
            # Coluna 1
            lbl = self.fonte.render(col_labels[i] + ":", True, (140, 160, 140))
            val = self.fonte_md.render(col_values[i], True, BRANCO)
            self.tela.blit(lbl, lbl.get_rect(right=LARGURA // 2 - 20, centery=y))
            self.tela.blit(val, val.get_rect(left=LARGURA // 2 - 10, centery=y))
            # Coluna 2
            lbl2 = self.fonte.render(col2_labels[i] + ":", True, (140, 160, 140))
            val2 = self.fonte_md.render(col2_values[i], True, AMARELO if i == 0 else BRANCO)
            self.tela.blit(lbl2, lbl2.get_rect(right=LARGURA // 2 + 260, centery=y))
            self.tela.blit(val2, val2.get_rect(left=LARGURA // 2 + 270, centery=y))

        restart = self.fonte.render("R = Jogar Novamente   |   Q = Sair", True, CINZA)
        self.tela.blit(restart, restart.get_rect(center=(LARGURA // 2, ALTURA // 2 + 170)))

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

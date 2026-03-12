##########################################################
#  ColisaoManager — Gerencia todas as colisões do jogo.
#
#  Extraído de main.py para reduzir tamanho do arquivo.
#  Recebe referências aos grupos e sistemas de efeitos.
##########################################################

import pygame
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *
from src.sprites.items import ItemArma
from src.sprites.xp import XpGem
import random


class ColisaoManager:
    """Gerencia todas as colisões entre sprites do jogo."""

    def __init__(self, game):
        # Referência ao objeto Game principal (acesso a grupos e sistemas)
        self._g = game

    def checar(self):
        g = self._g
        player        = g.player
        particulas    = g.particulas
        camera        = g.camera
        nums_dano     = g.nums_dano
        som           = g.som
        score         = g.score

        # ── 1. Balas do player → inimigos ────────────────────────────
        hits = pygame.sprite.groupcollide(g.inimigos, g.balas_player, False, False)
        for inimigo, balas_acertadas in hits.items():
            dano_total = 0
            for bala in balas_acertadas:
                tem_perfurante = hasattr(bala, '_penetracoes_restantes')
                if tem_perfurante:
                    ja_acertou = getattr(bala, '_alvos_acertados', set())
                    if id(inimigo) in ja_acertou:
                        continue
                    if not hasattr(bala, '_alvos_acertados'):
                        bala._alvos_acertados = set()
                    bala._alvos_acertados.add(id(inimigo))
                    bala.aplicar_perfurante()
                else:
                    bala.tentar_ricochet(g.inimigos, inimigo)
                    bala.kill()

                inimigo.sofrer_dano(bala.dano)
                dano_total += bala.dano
                particulas.hit_sparks(inimigo.pos)
                particulas.sangue(inimigo.pos, quantidade=6)

            if dano_total > 0:
                critico = dano_total >= 20
                nums_dano.adicionar(inimigo.pos, dano_total, critico=critico)
                som.play_hit_inimigo()

            # Execução: inimigos com < 20% HP explodem ao ser acertados
            if getattr(player, "carta_execucao", False):
                if inimigo.hp > 0 and inimigo.hp < inimigo.hp_max * 0.20:
                    particulas.explosao(inimigo.pos, (255, 80, 0), quantidade=20, raio_max=5)
                    camera.adicionar_shake(0.2)
                    inimigo.hp = 0

            if inimigo.hp <= 0:
                som.play_morte_inimigo()
                g._matar_inimigo(inimigo)
                vampirismo_val = getattr(player, "_vampirismo_valor", 2) if getattr(player, "vampirismo", False) else 0
                if vampirismo_val:
                    player.hp = min(player.hp_max, player.hp + vampirismo_val)

        # ── 2. Balas do player → Boss ─────────────────────────────────
        if g.boss_ativo and g.boss_ref:
            for bala in list(g.balas_player):
                if g.boss_ref.rect.colliderect(bala.rect):
                    g.boss_ref.sofrer_dano(bala.dano)
                    bala.kill()
                    particulas.hit_sparks(g.boss_ref.pos)
                    camera.adicionar_shake(SHAKE_ACERTA_BOSS)
                    nums_dano.adicionar(g.boss_ref.pos, bala.dano, critico=True)
                    som.play_boss_hit()
                    if g.boss_ref.hp <= 0:
                        som.play_boss_morte()
                        g._matar_boss()
                        break

        # ── 2b. Boss → Jogador (contato corporal) ────────────────────
        # Dano de contato escalonado por nível do boss (30/45/60)
        if g.boss_ativo and g.boss_ref and not player.esta_invencivel():
            if g.boss_ref.rect.colliderect(player.rect):
                nivel = getattr(g.boss_ref, "nivel_boss", 1)
                dano_contato = 20 + (nivel - 1) * 15   # 20 / 35 / 50
                if getattr(player, "escudo_passivo", False) and getattr(player, "escudo_pronto", False):
                    player.escudo_pronto   = False
                    player.escudo_cd_atual = 0
                    particulas.hit_sparks(player.pos)
                    camera.adicionar_shake(0.5)
                elif getattr(player, "_escudo_ativo", False):
                    # Escudo ativo reflete dano ao boss
                    g.boss_ref.sofrer_dano(dano_contato)
                    camera.adicionar_shake(0.6)
                    particulas.hit_sparks(g.boss_ref.pos)
                else:
                    player.sofrer_dano(dano_contato)
                    nums_dano.adicionar(player.pos, dano_contato, eh_jogador=True)
                    score.registrar_dano()
                    som.play_dano_jogador()
                    camera.adicionar_shake(SHAKE_CONTATO_INIMIGO * 1.5)
                    particulas.sangue(player.pos, quantidade=12)
                    g._verificar_morte_jogador()

        # ── 3. Inimigos → Jogador (contato) ──────────────────────────
        inimigos_tocando = pygame.sprite.spritecollide(player, g.inimigos, False)
        for ini in inimigos_tocando:
            if getattr(player, "_escudo_ativo", False):
                ini.sofrer_dano(40)
                if ini.hp <= 0:
                    g._matar_inimigo(ini)
                camera.adicionar_shake(0.3)
            elif getattr(player, "escudo_passivo", False) and getattr(player, "escudo_pronto", False):
                player.escudo_pronto   = False
                player.escudo_cd_atual = 0
                ini.kill()
                particulas.hit_sparks(player.pos)
                camera.adicionar_shake(0.3)
            else:
                ini.kill()
                dano = 20
                player.sofrer_dano(dano)
                if not player.esta_invencivel():
                    nums_dano.adicionar(player.pos, dano, eh_jogador=True)
                    score.registrar_dano()
                    som.play_dano_jogador()
                camera.adicionar_shake(SHAKE_CONTATO_INIMIGO)
                g._verificar_morte_jogador()

        # ── 4. Balas inimigas → Jogador ───────────────────────────────
        for bala in list(g.balas_inimigos):
            if player.rect.colliderect(bala.rect):
                dano = bala.dano
                if getattr(player, "escudo_passivo", False) and getattr(player, "escudo_pronto", False):
                    player.escudo_pronto   = False
                    player.escudo_cd_atual = 0
                    particulas.hit_sparks(player.pos)
                    bala.kill()
                    continue
                player.sofrer_dano(dano)
                if not player.esta_invencivel():
                    nums_dano.adicionar(player.pos, dano, eh_jogador=True)
                    score.registrar_dano()
                camera.adicionar_shake(SHAKE_TIRO_INIMIGO)
                bala.kill()
                g._verificar_morte_jogador()

        # ── 5. Coleta de itens ────────────────────────────────────────
        item = pygame.sprite.spritecollideany(player, g.itens_chao)
        if item:
            player.tipo_arma = item.tipo
            player.cadencia  = (CADENCIA_METRALHADORA
                                if item.tipo == "Metralhadora"
                                else CADENCIA_SHOTGUN)
            item.kill()
            som.play_power_up()
            particulas.nivel_up_burst(player.pos)

        # ── 6. Coleta de XP ───────────────────────────────────────────
        gemas_coletadas = pygame.sprite.spritecollide(player, g.xp_gems, True)
        if gemas_coletadas:
            som.play_coleta_xp()
        for gema in gemas_coletadas:
            mult_xp = getattr(player, "xp_bonus", 1.0)
            player.xp += int(gema.valor * mult_xp)
            if player.xp >= player.xp_proximo_nivel:
                g._level_up()

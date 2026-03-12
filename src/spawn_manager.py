##########################################################
#  SpawnManager — Gerencia o spawn de inimigos e boss.
#
#  Extraído de main.py para reduzir tamanho do arquivo.
##########################################################

import pygame
import math
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *
from src.sprites.enemies import (InimigoBase, InimigoRapido, InimigoTank,
                                   InimigoAtirador, InimigoViral,
                                   InimigoNecromante, InimigoExplosivo)
from src.sprites.boss import Boss


class SpawnManager:
    """Gerencia spawn de inimigos e boss."""

    # Mapa tipo → classe
    _MAPA = {
        "normal":     InimigoBase,
        "rapido":     InimigoRapido,
        "tank":       InimigoTank,
        "atirador":   InimigoAtirador,
        "viral":      InimigoViral,
        "necromante": InimigoNecromante,
        "explosivo":  InimigoExplosivo,
    }

    def __init__(self, game):
        self._g = game

    def spawnar_inimigo(self, tipo: str):
        """Cria e adiciona um inimigo do tipo dado."""
        g = self._g
        if g.boss_ativo or g.boss_intro.ativo:
            return

        cls        = self._MAPA.get(tipo, InimigoBase)
        hp_escalado = round(g.dificuldade.get_hp_inimigos(tipo))

        if tipo == "viral":
            novo = cls(g.player.pos, g.vel_inimigos, eh_fragmento=False, hp=hp_escalado)
        elif tipo == "atirador":
            novo = cls(g.player.pos, g.vel_inimigos,
                       hp=hp_escalado,
                       cadencia_ms=g.dificuldade.get_cadencia_disparo(),
                       dano_tiro=g.dificuldade.get_dano_inimigos())
        else:
            novo = cls(g.player.pos, g.vel_inimigos, hp=hp_escalado)

        g.inimigos.add(novo)
        g.todos_sprites.add(novo)

    def spawnar_boss(self):
        """Chamado pela BossIntro quando a cinemática sinaliza spawn."""
        g = self._g
        nivel_boss  = g.fase // BOSS_INTERVALO
        boss        = Boss(g.player.pos, nivel_boss=nivel_boss)
        g.boss_ref  = boss
        g.boss_ativo = True
        g.grupo_boss.add(boss)
        g.todos_sprites.add(boss)

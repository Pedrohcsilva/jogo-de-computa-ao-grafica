##########################################################################
#  Constantes globais (Cores, Largura/Altura, FPS, Equilíbrio de jogo).
##########################################################################

import pygame

pygame.init()
info = pygame.display.Info()

# ── Tela ────────────────────────────────────────────────────────────────
LARGURA, ALTURA = info.current_w, info.current_h
FPS = 60

# ── Cores ────────────────────────────────────────────────────────────────
BRANCO      = (255, 255, 255)
PRETO       = (10,  10,  15)
VERDE       = (0,   255, 100)
VERMELHO    = (255, 50,  50)
AMARELO     = (255, 215, 0)
AZUL_TIRO   = (0,   200, 255)
ROXO        = (180, 50,  255)
CINZA       = (60,  60,  70)
LARANJA     = (255, 140, 0)
ROSA        = (255, 80,  180)

# ── Jogador ──────────────────────────────────────────────────────────────
PLAYER_VEL  = 6
PLAYER_SIZE = 50
HP_MAX      = 100

# ── Armas (cadência em ms) ───────────────────────────────────────────────
CADENCIA_PISTOLA      = 300
CADENCIA_METRALHADORA = 130
CADENCIA_SHOTGUN      = 650

# ── Itens ────────────────────────────────────────────────────────────────
ITEM_VIDA = 600   # ~10 segundos a 60 FPS

# ── XP / Level-Up ───────────────────────────────────────────────────────
XP_COLOR          = (0, 255, 255)
XP_SIZE           = 10
XP_BASE_LEVEL     = 100
XP_INCREMENTO     = 1.2

# ── Screen Shake ────────────────────────────────────────────────────────
# Escala 0.0–1.0. Com MAX_OFFSET=20 e trauma²:
# 0.4→3px | 0.6→7px | 0.8→13px | 1.0→20px
SHAKE_TIRO_INIMIGO    = 0.35   # bala inimiga acerta o jogador
SHAKE_CONTATO_INIMIGO = 0.45   # inimigo encosta no jogador
SHAKE_MATA_NORMAL     = 0.25   # mata inimigo normal
SHAKE_MATA_TANK       = 0.55   # mata Tank
SHAKE_ACERTA_BOSS     = 0.30   # bala acerta o boss
SHAKE_BOSS_MORTE      = 1.00   # boss morre — maximo absoluto
SHAKE_LEVEL_UP        = 0.40   # sobe de nivel

# ── Boss ────────────────────────────────────────────────────────────────
BOSS_FASE_INICIO  = 5    # boss aparece a partir da fase 5
BOSS_HP           = 500
BOSS_TAMANHO      = (70, 70)

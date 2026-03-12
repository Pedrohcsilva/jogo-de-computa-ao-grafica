##########################################################
#  GerenciadorSom — Síntese procedural de áudio.
#
#  Gera todos os sons em tempo real via numpy/pygame.sndarray
#  sem depender de arquivos externos.
#
#  SONS GERADOS:
#   tiro_pistola   — clique seco + transiente
#   tiro_metra     — burst curto e grave
#   tiro_shotgun   — explosão difusa
#   hit_inimigo    — estalo de impacto
#   morte_inimigo  — queda orgânica
#   dano_jogador   — impacto pesado + distorção
#   level_up       — acorde ascendente
#   fase_completa  — fanfarra curta
#   boss_hit       — impacto metálico grave
#   boss_morte     — explosão épica multicamada
#   power_up       — sweep ascendente
#   coleta_xp      — ping suave
##########################################################

import pygame
import math
import array


def _gerar_onda(duracao_ms: int, freq: float, forma: str = "sine",
                volume: float = 0.6, decay: float = 1.0,
                sample_rate: int = 22050) -> pygame.mixer.Sound:
    """
    Gera um som sintético simples.
    forma: 'sine' | 'square' | 'sawtooth' | 'noise'
    decay: 1.0 = sem decay | 3.0 = decay rápido
    """
    import random
    n_samples = int(sample_rate * duracao_ms / 1000)
    buf = array.array('h', [0] * n_samples)

    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-decay * t * (1000 / duracao_ms))  # envelope exponencial

        if forma == "sine":
            val = math.sin(2 * math.pi * freq * t)
        elif forma == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
        elif forma == "sawtooth":
            val = 2 * ((freq * t) % 1.0) - 1.0
        elif forma == "noise":
            val = random.uniform(-1, 1)
        else:
            val = math.sin(2 * math.pi * freq * t)

        buf[i] = int(val * env * volume * 32767)

    snd = pygame.mixer.Sound(buffer=buf)
    return snd


def _misturar(*ondas) -> pygame.mixer.Sound:
    """Mistura múltiplos arrays de samples somando-os (clamp em 32767)."""
    if not ondas:
        return None
    tamanho = max(len(o) for o in ondas)
    buf = array.array('h', [0] * tamanho)
    for onda in ondas:
        for i, v in enumerate(onda):
            buf[i] = max(-32767, min(32767, buf[i] + v))
    snd = pygame.mixer.Sound(buffer=buf)
    return snd


def _buf(duracao_ms: int, freq: float, forma: str = "sine",
         volume: float = 0.6, decay: float = 1.0,
         freq_end: float = None,
         sample_rate: int = 22050) -> array.array:
    """Igual a _gerar_onda mas retorna array (para misturar)."""
    import random
    n_samples = int(sample_rate * duracao_ms / 1000)
    buf = array.array('h', [0] * n_samples)

    for i in range(n_samples):
        t = i / sample_rate
        env = math.exp(-decay * t * (1000 / duracao_ms))

        # Sweep de frequência (glide)
        if freq_end is not None:
            prog = i / n_samples
            f = freq + (freq_end - freq) * prog
        else:
            f = freq

        if forma == "sine":
            val = math.sin(2 * math.pi * f * t)
        elif forma == "square":
            val = 1.0 if math.sin(2 * math.pi * f * t) > 0 else -1.0
        elif forma == "sawtooth":
            val = 2 * ((f * t) % 1.0) - 1.0
        elif forma == "noise":
            val = random.uniform(-1, 1)
        else:
            val = math.sin(2 * math.pi * f * t)

        buf[i] = int(val * env * volume * 32767)

    return buf


def _gerar_musica_ambiente(fase: int = 1, sample_rate: int = 22050) -> pygame.mixer.Sound:
    """
    Gera música ambiente procedural em loop para a fase dada.
    Estilo: drone ambiental biomecânico com arpejo lento.
    Fase 1–2: tom verde orgânico  | Fase 3–4: tensão roxa | Fase 5+: vermelho agressivo
    """
    import random as _r
    duracao_ms = 6000   # 6 segundos por loop
    n = int(sample_rate * duracao_ms / 1000)
    buf = array.array('h', [0] * n)

    # Paleta de notas por fase (frequências em Hz)
    paletas = [
        [110, 146, 164, 196],   # Fase 1-2: Am pentatônica grave — orgânico
        [130, 155, 185, 220],   # Fase 3-4: tensão cromática
        [82,  98,  123, 138],   # Fase 5+:  grave agressivo
    ]
    idx_paleta = 0 if fase <= 2 else (1 if fase <= 4 else 2)
    notas = paletas[idx_paleta]

    vol_drone   = 0.10
    vol_arpejo  = 0.06
    vol_pulso   = 0.04

    for i in range(n):
        t = i / sample_rate
        v = 0.0

        # Drone de fundo: duas frequências base com batimento lento
        v += math.sin(2 * math.pi * notas[0] * t) * vol_drone
        v += math.sin(2 * math.pi * notas[0] * 1.005 * t) * vol_drone * 0.6

        # Arpejo lento (nota muda a cada 1.5s)
        idx_nota = int(t / 1.5) % len(notas)
        freq_arp = notas[idx_nota]
        env_arp  = math.exp(-2.0 * (t % 1.5))
        v += math.sin(2 * math.pi * freq_arp * 2 * t) * vol_arpejo * env_arp

        # Pulso rítmico suave (16bpm grave)
        pulso_t = t % (60 / 16)
        env_pulso = math.exp(-8 * pulso_t)
        v += math.sin(2 * math.pi * notas[0] * 0.5 * t) * vol_pulso * env_pulso

        # Fade in/out para loop suave (evita clique no corte)
        fade_frames = int(sample_rate * 0.15)
        if i < fade_frames:
            v *= i / fade_frames
        elif i > n - fade_frames:
            v *= (n - i) / fade_frames

        buf[i] = max(-32767, min(32767, int(v * 32767)))

    return pygame.mixer.Sound(buffer=buf)


class GerenciadorSom:
    """
    Ponto central de acesso a todos os sons do jogo.
    Inicializa o mixer e gera os sons proceduralmente.
    Expõe métodos play_* para cada evento sonoro.
    """

    # Volume global (0.0 – 1.0) — ajustável pelo menu
    VOLUME_SFX   = 0.5
    VOLUME_MUSICA = 0.25

    def __init__(self):
        # Inicializa mixer se ainda não estiver rodando
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            except Exception:
                self._ativo = False
                return
        self._ativo = True
        self._sons: dict[str, pygame.mixer.Sound] = {}
        self._musica_atual: pygame.mixer.Sound | None = None
        self._canal_musica: pygame.mixer.Channel | None = None
        self._fase_musica  = 0   # fase da música tocando agora
        self._gerar_todos()
        self._iniciar_musica(1)

    # ── Geração ──────────────────────────────────────────────────────

    def _gerar_todos(self):
        """Gera e armazena todos os sons de uma vez na inicialização."""
        try:
            # Tiro pistola — clique seco transiente
            b1 = _buf(80,  800,  "square",   0.35, decay=18)
            b2 = _buf(80,  200,  "noise",    0.20, decay=25)
            self._sons["tiro_pistola"] = _misturar(b1, b2)

            # Tiro metralhadora — burst curto e grave
            b1 = _buf(55,  600,  "square",   0.30, decay=22)
            b2 = _buf(55,  150,  "noise",    0.18, decay=30)
            self._sons["tiro_metra"] = _misturar(b1, b2)

            # Tiro shotgun — explosão difusa
            b1 = _buf(150, 120,  "noise",    0.45, decay=10)
            b2 = _buf(150, 300,  "sawtooth", 0.20, decay=12, freq_end=80)
            self._sons["tiro_shotgun"] = _misturar(b1, b2)

            # Hit inimigo — estalo seco
            b1 = _buf(60,  1200, "square",   0.25, decay=30)
            b2 = _buf(60,  400,  "noise",    0.15, decay=35)
            self._sons["hit_inimigo"] = _misturar(b1, b2)

            # Morte inimigo — queda orgânica
            b1 = _buf(120, 180,  "sawtooth", 0.35, decay=8, freq_end=60)
            b2 = _buf(120, 900,  "noise",    0.20, decay=12)
            self._sons["morte_inimigo"] = _misturar(b1, b2)

            # Dano jogador — impacto pesado
            b1 = _buf(200, 80,   "square",   0.55, decay=6)
            b2 = _buf(200, 1800, "noise",    0.30, decay=8)
            self._sons["dano_jogador"] = _misturar(b1, b2)

            # Level up — acorde ascendente
            b1 = _buf(400, 523,  "sine",     0.30, decay=3)   # C5
            b2 = _buf(400, 659,  "sine",     0.25, decay=3)   # E5
            b3 = _buf(400, 784,  "sine",     0.20, decay=3)   # G5
            b4 = _buf(400, 1047, "sine",     0.15, decay=3)   # C6
            self._sons["level_up"] = _misturar(b1, b2, b3, b4)

            # Fase completa — fanfarra
            b1 = _buf(500, 392,  "sine",     0.28, decay=2)   # G4
            b2 = _buf(500, 523,  "sine",     0.22, decay=2)   # C5
            b3 = _buf(500, 659,  "sine",     0.18, decay=2)   # E5
            self._sons["fase_completa"] = _misturar(b1, b2, b3)

            # Boss hit — impacto metálico
            b1 = _buf(100, 150,  "square",   0.45, decay=10)
            b2 = _buf(100, 2000, "noise",    0.25, decay=15)
            self._sons["boss_hit"] = _misturar(b1, b2)

            # Boss morte — explosão épica
            b1 = _buf(800, 60,   "sawtooth", 0.50, decay=2, freq_end=30)
            b2 = _buf(800, 3000, "noise",    0.35, decay=3)
            b3 = _buf(800, 110,  "square",   0.30, decay=2)
            self._sons["boss_morte"] = _misturar(b1, b2, b3)

            # Power up — sweep
            b1 = _buf(300, 300,  "sine",     0.35, decay=3, freq_end=1200)
            b2 = _buf(300, 600,  "sine",     0.20, decay=3, freq_end=2400)
            self._sons["power_up"] = _misturar(b1, b2)

            # Coleta XP — ping suave
            b1 = _buf(80,  1400, "sine",     0.18, decay=15)
            b2 = _buf(80,  2800, "sine",     0.10, decay=18)
            self._sons["coleta_xp"] = _misturar(b1, b2)

            # Aplicar volume a todos
            for snd in self._sons.values():
                if snd:
                    snd.set_volume(self.VOLUME_SFX)

        except Exception as e:
            # Falha silenciosa — jogo roda sem som
            self._ativo = False

    # ── API pública ───────────────────────────────────────────────────

    def _play(self, nome: str, volume_override: float = None):
        if not self._ativo:
            return
        snd = self._sons.get(nome)
        if snd:
            if volume_override is not None:
                snd.set_volume(volume_override)
            snd.play()

    def play_tiro(self, tipo: str = "pistola"):
        mapa = {
            "pistola":      "tiro_pistola",
            "metralhadora": "tiro_metra",
            "shotgun":      "tiro_shotgun",
        }
        self._play(mapa.get(tipo, "tiro_pistola"))

    def play_hit_inimigo(self):
        self._play("hit_inimigo")

    def play_morte_inimigo(self):
        self._play("morte_inimigo")

    def play_dano_jogador(self):
        self._play("dano_jogador")

    def play_level_up(self):
        self._play("level_up")

    def play_fase_completa(self):
        self._play("fase_completa")

    def play_boss_hit(self):
        self._play("boss_hit")

    def play_boss_morte(self):
        self._play("boss_morte")

    def play_power_up(self):
        self._play("power_up")

    def play_coleta_xp(self):
        self._play("coleta_xp")

    # ── Música ambiente ───────────────────────────────────────────────

    def _iniciar_musica(self, fase: int):
        """Gera e inicia a música ambiente para a fase dada em loop."""
        if not self._ativo:
            return
        try:
            # Reserva canal dedicado (canal 0) para a música
            pygame.mixer.set_num_channels(max(8, pygame.mixer.get_num_channels()))
            self._canal_musica = pygame.mixer.Channel(0)
            self._musica_atual = _gerar_musica_ambiente(fase)
            self._musica_atual.set_volume(self.VOLUME_MUSICA)
            self._canal_musica.play(self._musica_atual, loops=-1)
            self._fase_musica = fase
        except Exception:
            pass  # falha silenciosa

    def atualizar_musica_fase(self, fase: int):
        """Troca a música quando a fase muda de faixa (1-2, 3-4, 5+)."""
        if not self._ativo:
            return
        faixa_nova   = 1 if fase <= 2 else (2 if fase <= 4 else 3)
        faixa_atual  = 1 if self._fase_musica <= 2 else (2 if self._fase_musica <= 4 else 3)
        if faixa_nova != faixa_atual:
            self._iniciar_musica(fase)

    def pausar_musica(self):
        """Pausa a música (ex: durante menus)."""
        if self._canal_musica:
            self._canal_musica.pause()

    def retomar_musica(self):
        """Retoma a música pausada."""
        if self._canal_musica:
            self._canal_musica.unpause()

    def set_volume_musica(self, v: float):
        """Ajusta volume da música em tempo real."""
        self.VOLUME_MUSICA = max(0.0, min(1.0, v))
        if self._musica_atual:
            self._musica_atual.set_volume(self.VOLUME_MUSICA)

    def set_volume_sfx(self, v: float):
        self.VOLUME_SFX = max(0.0, min(1.0, v))
        for snd in self._sons.values():
            if snd:
                snd.set_volume(self.VOLUME_SFX)

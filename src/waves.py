##########################################################
#  Sistema de Ondas (Wave System)
#
#  FILOSOFIA:
#   Bullet-hell de qualidade não spawna inimigos aleatórios
#   infinitamente. Cada fase tem uma composição definida,
#   seguida de um momento de respiro antes da próxima onda.
#
#  ESTRUTURA DE UMA ONDA:
#   {
#       "inimigos": [("normal", 5), ("rapido", 2)],
#       "intervalo_ms": 800,   # ms entre spawns individuais
#       "respiro_ms":  3000,   # pausa após a onda terminar
#   }
#
#  ESTADOS DA MÁQUINA:
#   SPAWNING  → despeja inimigos conforme fila
#   CLEARING  → aguarda todos os inimigos morrerem
#   RESPIRO   → pausa com contagem regressiva na tela
#   COMPLETA  → fase concluída, main.py avança a fase
##########################################################

import pygame


# ── Definição das ondas por fase ──────────────────────────────────────
# Índice = fase - 1  (fase 1 → ONDAS[0])
# A partir da fase 6 o jogo entra em modo infinito (veja _gerar_onda_infinita)

ONDAS = [
    # Fase 1 — tutorial suave
    {"inimigos": [("normal", 5)],
     "intervalo_ms": 1200, "respiro_ms": 3000},

    # Fase 2 — introduz rápidos
    {"inimigos": [("normal", 4), ("rapido", 3)],
     "intervalo_ms": 1000, "respiro_ms": 2500},

    # Fase 3 — introduz tanks
    {"inimigos": [("normal", 5), ("rapido", 2), ("tank", 1)],
     "intervalo_ms": 900, "respiro_ms": 2500},

    # Fase 4 — introduz atiradores
    {"inimigos": [("normal", 4), ("rapido", 3), ("tank", 1), ("atirador", 2)],
     "intervalo_ms": 800, "respiro_ms": 2000},

    # Fase 5 — horda antes do boss
    {"inimigos": [("normal", 6), ("rapido", 4), ("tank", 2), ("atirador", 2)],
     "intervalo_ms": 700, "respiro_ms": 1500},

    # Fase 6+ → gerada dinamicamente (veja _gerar_onda_infinita)
]


def _gerar_onda_infinita(fase: int) -> dict:
    """
    Gera uma onda escalada para fases além das pré-definidas.
    Aumenta a quantidade e reduz o intervalo gradualmente.
    """
    extra    = fase - len(ONDAS)          # quantas fases além do limite
    base_n   = 5 + extra * 2              # inimigos normais
    base_r   = 3 + extra                  # rápidos
    base_t   = 1 + extra // 2             # tanks
    base_a   = 2 + extra // 2             # atiradores
    intervalo = max(400, 800 - extra * 40)
    respiro   = max(1000, 2000 - extra * 100)

    return {
        "inimigos": [
            ("normal",   base_n),
            ("rapido",   base_r),
            ("tank",     base_t),
            ("atirador", base_a),
        ],
        "intervalo_ms": intervalo,
        "respiro_ms":   respiro,
    }


class GerenciadorOndas:
    """
    Controla o ciclo spawn → clear → respiro → próxima onda.
    O main.py chama update() e spawn_tick() a cada frame,
    e consulta inimigo_a_spawnar() para criar sprites.
    """

    SPAWNING = "spawning"
    CLEARING = "clearing"
    RESPIRO  = "respiro"
    COMPLETA = "completa"
    IDLE     = "idle"

    def __init__(self):
        self._estado           = self.IDLE
        self._fila_spawn: list = []        # lista de strings de tipo a spawnar
        self._ultimo_spawn_ms  = 0
        self._intervalo_ms     = 800
        self._respiro_ms       = 2000
        self._respiro_inicio   = 0
        self._fase_atual       = 0
        self._pendente         = None      # tipo aguardando ser coletado

    # ── API pública ───────────────────────────────────────────────────

    def iniciar_fase(self, fase: int):
        """Chame quando uma nova fase começar."""
        self._fase_atual = fase
        onda = ONDAS[fase - 1] if fase <= len(ONDAS) else _gerar_onda_infinita(fase)

        # Constrói a fila expandida: [("normal", 3)] → ["normal","normal","normal"]
        self._fila_spawn = []
        for tipo, qtd in onda["inimigos"]:
            self._fila_spawn.extend([tipo] * qtd)

        self._intervalo_ms    = onda["intervalo_ms"]
        self._respiro_ms      = onda["respiro_ms"]
        self._ultimo_spawn_ms = pygame.time.get_ticks()
        self._estado          = self.SPAWNING
        self._pendente        = None

    @property
    def estado(self):
        return self._estado

    @property
    def em_respiro(self):
        return self._estado == self.RESPIRO

    @property
    def completa(self):
        return self._estado == self.COMPLETA

    def tempo_respiro_restante_ms(self) -> int:
        """Retorna ms restantes no respiro (0 se não estiver em respiro)."""
        if self._estado != self.RESPIRO:
            return 0
        decorrido = pygame.time.get_ticks() - self._respiro_inicio
        return max(0, self._respiro_ms - decorrido)

    def inimigo_a_spawnar(self) -> str | None:
        """
        Consumível: retorna o tipo do próximo inimigo UMA VEZ por tick,
        ou None se não for hora de spawnar.
        Chame a cada frame e crie o sprite se não for None.
        """
        if self._pendente is not None:
            t = self._pendente
            self._pendente = None
            return t
        return None

    def update(self, n_inimigos_vivos: int):
        """
        Avança a máquina de estados.
        n_inimigos_vivos: len(grupo_inimigos) do main.py
        """
        agora = pygame.time.get_ticks()

        if self._estado == self.SPAWNING:
            if self._fila_spawn:
                if agora - self._ultimo_spawn_ms >= self._intervalo_ms:
                    self._pendente        = self._fila_spawn.pop(0)
                    self._ultimo_spawn_ms = agora
            else:
                # Todos spawnados; aguarda limpeza
                self._estado = self.CLEARING

        elif self._estado == self.CLEARING:
            if n_inimigos_vivos == 0:
                self._estado         = self.RESPIRO
                self._respiro_inicio = agora

        elif self._estado == self.RESPIRO:
            if agora - self._respiro_inicio >= self._respiro_ms:
                self._estado = self.COMPLETA

        # IDLE e COMPLETA não fazem nada até o main.py reiniciar

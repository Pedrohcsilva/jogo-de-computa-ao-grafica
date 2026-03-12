##########################################################
#  Sistema de Partículas — versão otimizada.
#
#  PROBLEMA ANTERIOR:
#   Cada partícula criava pygame.Surface() a cada frame.
#   200 partículas = 200 alocações/frame → FPS drop garantido.
#
#  SOLUÇÃO — cache de superfícies:
#   _get_surf() retorna uma Surface pré-renderizada por
#   (raio, cor, alpha quantizado). Zero alocação por frame
#   em regime estacionário.
#
#  MATEMÁTICA:
#   vel *= 0.88          → atrito (decaimento exponencial)
#   vel.y += gravidade   → parábola para sangue/detritos
#   alpha = 255 * prog   → fade-out linear
#   raio  = raio * prog  → encolhe proporcionalmente
##########################################################

import pygame
import random
import math

# ── Cache global de superfícies ───────────────────────────────────────
# Chave: (raio, cor_rgb, alpha_quantizado)  →  Surface pré-desenhada
# Alpha é quantizado em passos de 32 (8 níveis) para maximizar hits.
_SURF_CACHE: dict = {}

def _get_surf(raio: int, cor: tuple, alpha: int) -> pygame.Surface:
    alpha_q = (alpha // 32) * 32       # quantiza: 8 níveis de transparência
    key     = (raio, cor, alpha_q)
    if key not in _SURF_CACHE:
        if len(_SURF_CACHE) > 512:     # evita crescimento ilimitado
            _SURF_CACHE.clear()
        surf = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*cor, alpha_q), (raio, raio), raio)
        _SURF_CACHE[key] = surf
    return _SURF_CACHE[key]


class Particula:
    """Partícula leve com __slots__ — sem dict interno."""
    __slots__ = ("pos", "vel", "cor", "raio", "vida", "vida_max", "gravidade")

    def __init__(self, pos, vel, cor, raio=3, vida=30, gravidade=0.0):
        self.pos       = pygame.math.Vector2(pos)
        self.vel       = pygame.math.Vector2(vel)
        self.cor       = cor
        self.raio      = raio
        self.vida      = vida
        self.vida_max  = vida
        self.gravidade = gravidade

    def update(self):
        self.vel   *= 0.88
        self.vel.y += self.gravidade
        self.pos   += self.vel
        self.vida  -= 1

    @property
    def vivo(self):
        return self.vida > 0

    def desenhar(self, superficie, offset):
        prog       = self.vida / self.vida_max
        alpha      = int(255 * prog)
        raio_atual = max(1, int(self.raio * prog))
        surf       = _get_surf(raio_atual, self.cor, alpha)
        pt         = self.pos + offset
        superficie.blit(surf, (int(pt.x) - raio_atual, int(pt.y) - raio_atual))


class GerenciadorParticulas:
    """Pool plano. Update/remoção em O(n) por list comprehension."""

    MAX_PARTICULAS = 800  # teto de segurança contra boss fights intensos

    def __init__(self):
        self.particulas: list[Particula] = []

    def _add(self, p: Particula):
        if len(self.particulas) < self.MAX_PARTICULAS:
            self.particulas.append(p)

    # ── Fábricas ──────────────────────────────────────────────────────

    def explosao(self, pos, cor_base, quantidade=25, raio_max=5):
        for _ in range(quantidade):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(2, 7)
            cor = (
                min(255, max(0, cor_base[0] + random.randint(-30, 30))),
                min(255, max(0, cor_base[1] + random.randint(-30, 30))),
                min(255, max(0, cor_base[2] + random.randint(-30, 30))),
            )
            self._add(Particula(pos,
                (math.cos(ang)*spd, math.sin(ang)*spd),
                cor, raio=random.randint(2, raio_max),
                vida=random.randint(20, 40)))

    def rastro_bala(self, pos, direcao, cor):
        vel = -direcao * random.uniform(1, 3) + pygame.math.Vector2(
            random.uniform(-1, 1), random.uniform(-1, 1))
        self._add(Particula(pos, vel, cor, raio=2, vida=10))

    def hit_sparks(self, pos, quantidade=8):
        for _ in range(quantidade):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(3, 6)
            cor = random.choice([(255,255,180),(255,220,50),(255,255,255)])
            self._add(Particula(pos,
                (math.cos(ang)*spd, math.sin(ang)*spd),
                cor, raio=2, vida=15))

    def sangue(self, pos, quantidade=12):
        for _ in range(quantidade):
            ang = random.uniform(-math.pi, 0)
            spd = random.uniform(1, 5)
            self._add(Particula(pos,
                (math.cos(ang)*spd, math.sin(ang)*spd),
                (200, 0, 0), raio=random.randint(2,4),
                vida=25, gravidade=0.3))

    def nivel_up_burst(self, pos):
        for _ in range(50):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(3, 10)
            self._add(Particula(pos,
                (math.cos(ang)*spd, math.sin(ang)*spd),
                (255, 215, 0), raio=random.randint(3,7), vida=50))

    def transicao_fase(self, largura, altura):
        """Pontos brancos espalhados na tela ao avançar de fase."""
        for _ in range(60):
            pos = (random.uniform(0, largura), random.uniform(0, altura))
            ang = random.uniform(0, math.tau)
            spd = random.uniform(0.5, 2.5)
            self._add(Particula(pos,
                (math.cos(ang)*spd, math.sin(ang)*spd),
                (200, 200, 255), raio=random.randint(1,4),
                vida=random.randint(30, 60)))

    # ── Loop ──────────────────────────────────────────────────────────

    def update(self):
        for p in self.particulas:
            p.update()
        self.particulas = [p for p in self.particulas if p.vivo]

    def desenhar(self, superficie, offset):
        for p in self.particulas:
            p.desenhar(superficie, offset)

    @property
    def count(self):
        return len(self.particulas)

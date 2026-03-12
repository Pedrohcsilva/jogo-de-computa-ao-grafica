##########################################################
#  Menu de Pausa — Interface visual melhorada
#
#  OPÇÕES:
#   - Continuar jogo
#   - Reiniciar fase
#   - Voltar ao menu principal
#   - Sair do jogo
##########################################################

import pygame
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *


class MenuPausa:
    """Menu visual de pausa com opções interativas e tela de opções de volume."""
    
    def __init__(self, largura: int, altura: int):
        self.largura = largura
        self.altura = altura
        self.visivel = False
        self._selecionado = 0
        self._tick = 0
        self._estado = "principal"   # "principal" | "opcoes"
        
        # Volume (0.0 – 1.0)
        self.volume_sfx   = 0.5
        self.volume_musica = 0.25
        self._opcao_volume = 0  # qual slider está selecionado em opcoes
        
        # Fontes
        self._fonte_titulo = pygame.font.SysFont("Arial", 64, bold=True)
        self._fonte_opcao = pygame.font.SysFont("Arial", 32, bold=True)
        self._fonte_hint = pygame.font.SysFont("Arial", 20)
        self._fonte_sm = pygame.font.SysFont("Arial", 18)
        
        # Opções do menu principal
        self._opcoes = [
            {"label": "◄  CONTINUAR",     "acao": "continuar"},
            {"label": "⚙  OPÇÕES",         "acao": "opcoes"},
            {"label": "↻  REINICIAR FASE", "acao": "reiniciar"},
            {"label": "⌂  MENU PRINCIPAL", "acao": "menu"},
            {"label": "✕  SAIR DO JOGO",   "acao": "sair"},
        ]
    
    def processar_evento(self, evento) -> str | None:
        """
        Processa eventos de entrada no menu de pausa.
        
        Returns:
            'continuar', 'reiniciar', 'menu', 'sair', 'volume_changed' ou None
        """
        if not self.visivel:
            return None

        # ── Tela de Opções ───────────────────────────────────────────
        if self._estado == "opcoes":
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self._estado = "principal"
                elif evento.key in (pygame.K_UP, pygame.K_w):
                    self._opcao_volume = (self._opcao_volume - 1) % 2
                elif evento.key in (pygame.K_DOWN, pygame.K_s):
                    self._opcao_volume = (self._opcao_volume + 1) % 2
                elif evento.key in (pygame.K_LEFT, pygame.K_a):
                    self._ajustar_volume(-0.05)
                    return "volume_changed"
                elif evento.key in (pygame.K_RIGHT, pygame.K_d):
                    self._ajustar_volume(+0.05)
                    return "volume_changed"
            return None

        # ── Menu Principal ───────────────────────────────────────────
        if evento.type == pygame.KEYDOWN:
            if evento.key in (pygame.K_UP, pygame.K_w):
                self._selecionado = (self._selecionado - 1) % len(self._opcoes)
            elif evento.key in (pygame.K_DOWN, pygame.K_s):
                self._selecionado = (self._selecionado + 1) % len(self._opcoes)
            elif evento.key in (pygame.K_RETURN, pygame.K_SPACE):
                acao = self._opcoes[self._selecionado]["acao"]
                if acao == "opcoes":
                    self._estado = "opcoes"
                    self._opcao_volume = 0
                    return None
                return acao
            elif evento.key == pygame.K_ESCAPE:
                return "continuar"  # ESC retorna ao jogo
        
        elif evento.type == pygame.JOYBUTTONDOWN:
            if evento.button == 0:  # A button (continuar)
                return self._opcoes[self._selecionado]["acao"]
            elif evento.button == 7:  # Start (voltar ao jogo)
                return "continuar"
            elif evento.button == 12:  # D-pad up
                self._selecionado = (self._selecionado - 1) % len(self._opcoes)
            elif evento.button == 13:  # D-pad down
                self._selecionado = (self._selecionado + 1) % len(self._opcoes)
        
        elif evento.type == pygame.MOUSEMOTION:
            # Hover com mouse
            for i in range(len(self._opcoes)):
                rect = self._rect_opcao(i)
                if rect.collidepoint(evento.pos):
                    self._selecionado = i
        
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if evento.button == 1:  # Click esquerdo
                if self._estado == "opcoes":
                    # Clique nas áreas de volume
                    for i in range(2):
                        rect = self._rect_slider(i)
                        if rect.collidepoint(evento.pos):
                            self._opcao_volume = i
                            # Ajusta volume pelo clique na barra
                            pct = (evento.pos[0] - rect.x) / rect.width
                            if i == 0:
                                self.volume_sfx = max(0.0, min(1.0, pct))
                            else:
                                self.volume_musica = max(0.0, min(1.0, pct))
                            return "volume_changed"
                else:
                    for i in range(len(self._opcoes)):
                        if self._rect_opcao(i).collidepoint(evento.pos):
                            acao = self._opcoes[i]["acao"]
                            if acao == "opcoes":
                                self._estado = "opcoes"
                                self._opcao_volume = 0
                                return None
                            return acao
        
        return None

    def _ajustar_volume(self, delta: float):
        """Ajusta o volume da opção selecionada."""
        if self._opcao_volume == 0:
            self.volume_sfx = max(0.0, min(1.0, self.volume_sfx + delta))
        else:
            self.volume_musica = max(0.0, min(1.0, self.volume_musica + delta))

    def _rect_slider(self, idx: int) -> pygame.Rect:
        """Retorna o rect da barra de volume para clique."""
        cx = self.largura // 2
        cy = self.altura // 2 - 20 + idx * 80
        return pygame.Rect(cx - 150, cy + 10, 300, 20)
    
    def atualizar(self):
        """Atualiza animações do menu."""
        self._tick += 1
    
    def desenhar(self, tela: pygame.Surface):
        """Desenha o menu de pausa na tela."""
        if not self.visivel:
            return
        
        # ── Overlay escuro semi-transparente ────────────────
        overlay = pygame.Surface((self.largura, self.altura))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        tela.blit(overlay, (0, 0))

        if self._estado == "opcoes":
            self._desenhar_opcoes(tela)
            return
        
        # ── Título "PAUSADO" ───────────────────────────────
        titulo = self._fonte_titulo.render("II  PAUSADO", True, (255, 200, 0))
        titulo_rect = titulo.get_rect(center=(self.largura // 2, self.altura // 4))
        # Glow effect
        sombra = self._fonte_titulo.render("II  PAUSADO", True, (255, 100, 0))
        tela.blit(sombra, (titulo_rect.x + 4, titulo_rect.y + 4))
        tela.blit(titulo, titulo_rect)
        
        # ── Opções do menu ─────────────────────────────────
        cy = self.altura // 2 - 80
        for i, opcao in enumerate(self._opcoes):
            self._desenhar_opcao(tela, i, opcao, cy + i * 65)
        
        # ── Hints de controle ───────────────────────────────
        hint = self._fonte_hint.render("↑↓ Navegar   ENTER: Selecionar   ESC: Continuar", 
                                       True, (150, 150, 150))
        hint_rect = hint.get_rect(center=(self.largura // 2, self.altura - 40))
        tela.blit(hint, hint_rect)

    def _desenhar_opcoes(self, tela: pygame.Surface):
        """Desenha a tela de opções com sliders de volume."""
        import math
        cx = self.largura // 2
        
        # Título
        titulo = self._fonte_titulo.render("⚙  OPÇÕES", True, (0, 220, 180))
        sombra = self._fonte_titulo.render("⚙  OPÇÕES", True, (0, 80, 60))
        tela.blit(sombra, titulo.get_rect(center=(cx + 4, self.altura // 4 + 4)))
        tela.blit(titulo,  titulo.get_rect(center=(cx,     self.altura // 4)))

        rotulos = ["🔊  Volume SFX", "🎵  Volume Música"]
        volumes  = [self.volume_sfx, self.volume_musica]

        for i, (rotulo, vol) in enumerate(zip(rotulos, volumes)):
            cy = self.altura // 2 - 20 + i * 80
            selecionado = i == self._opcao_volume

            # Label
            cor_lbl = (0, 255, 180) if selecionado else (180, 180, 180)
            lbl = self._fonte_opcao.render(rotulo, True, cor_lbl)
            tela.blit(lbl, lbl.get_rect(center=(cx, cy - 10)))

            # Barra de slider
            bw, bh = 300, 20
            bx = cx - bw // 2
            by = cy + 10
            pygame.draw.rect(tela, (30, 40, 30), (bx, by, bw, bh), border_radius=6)
            fill_w = int(vol * bw)
            cor_bar = (0, 255, 150) if selecionado else (0, 160, 100)
            if fill_w > 0:
                pygame.draw.rect(tela, cor_bar, (bx, by, fill_w, bh), border_radius=6)
            pygame.draw.rect(tela, (80, 120, 80), (bx, by, bw, bh), width=2, border_radius=6)

            # Handle do slider
            hx = bx + fill_w
            pygame.draw.circle(tela, (255, 255, 255), (hx, by + bh // 2), 10)
            pygame.draw.circle(tela, cor_bar, (hx, by + bh // 2), 8)

            # Percentagem
            pct_txt = self._fonte_sm.render(f"{int(vol * 100)}%", True, (200, 220, 200))
            tela.blit(pct_txt, (bx + bw + 12, by + 2))

            # Seta selecionada
            if selecionado:
                seta = self._fonte_opcao.render("◄  ►", True, (0, 255, 150))
                tela.blit(seta, seta.get_rect(center=(cx, by + bh + 18)))

        hint = self._fonte_hint.render("↑↓ Selecionar slider   ◄► Ajustar   ESC Voltar",
                                       True, (100, 140, 100))
        tela.blit(hint, hint.get_rect(center=(cx, self.altura - 40)))
    
    def _desenhar_opcao(self, tela: pygame.Surface, idx: int, opcao: dict, cy: int):
        """Desenha uma opção individual do menu."""
        selecionado = idx == self._selecionado
        
        # Cor baseia-se na seleção
        cor = (0, 255, 150) if selecionado else (200, 200, 200)
        
        # Escala pulsante se selecionado
        escala = 1.15 if selecionado else 1.0
        if selecionado:
            # Pulso sinusoidal
            import math
            escala += math.sin(self._tick * 0.1) * 0.05
        
        # Renderizar texto
        texto = self._fonte_opcao.render(opcao["label"], True, cor)
        
        if escala != 1.0:
            novo_tamanho = (int(texto.get_width() * escala), 
                          int(texto.get_height() * escala))
            texto = pygame.transform.scale(texto, novo_tamanho)
        
        # Desenhar com sombra de profundidade
        rect = texto.get_rect(center=(self.largura // 2, cy))
        
        if selecionado:
            # Sombra colorida
            sombra = self._fonte_opcao.render(opcao["label"], True, (0, 100, 50))
            if escala != 1.0:
                novo_tamanho = (int(sombra.get_width() * escala), 
                              int(sombra.get_height() * escala))
                sombra = pygame.transform.scale(sombra, novo_tamanho)
            tela.blit(sombra, (rect.x + 3, rect.y + 3))
            
            # Box de seleção
            box_rect = rect.inflate(40, 20)
            pygame.draw.rect(tela, (0, 255, 150), box_rect, 3, border_radius=10)
        
        tela.blit(texto, rect)
    
    def _rect_opcao(self, idx: int) -> pygame.Rect:
        """Retorna o rect aproximado de uma opção para hover detection."""
        cy = self.altura // 2 - 60 + idx * 70
        return pygame.Rect(self.largura // 2 - 200, cy - 25, 400, 50)
    
    def mostrar(self):
        """Mostra o menu de pausa."""
        self.visivel = True
        self._selecionado = 0
        self._estado = "principal"
    
    def esconder(self):
        """Esconde o menu de pausa."""
        self.visivel = False

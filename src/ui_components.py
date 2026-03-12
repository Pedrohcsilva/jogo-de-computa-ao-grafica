##########################################################
#  UI Components — Componentes de interface reutilizáveis
#
#  - BarraProgressao
#  - BarraHP
#  - ContadorTexto
#  - Tooltip
##########################################################

import pygame
import math
import sys
import os

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *


class BarraProgressao:
    """Barra de progresso visual com efeitos."""
    
    def __init__(self, x: int, y: int, largura: int, altura: int, cor_fundo: tuple, cor_preenchimento: tuple):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.cor_fundo = cor_fundo
        self.cor_preenchimento = cor_preenchimento
        self.valor = 0.0
        self.valor_maximo = 1.0
        self._tick = 0
    
    def atualizar(self, novo_valor: float):
        """Atualiza o valor da barra."""
        self.valor = max(0.0, min(1.0, novo_valor / self.valor_maximo if self.valor_maximo > 0 else 0))
        self._tick += 1
    
    def desenhar(self, tela: pygame.Surface):
        """Desenha a barra."""
        # Fundo
        pygame.draw.rect(tela, self.cor_fundo, (self.x, self.y, self.largura, self.altura), border_radius=4)
        
        # Preenchimento com brilho
        larg_preench = int(self.largura * self.valor)
        pygame.draw.rect(tela, self.cor_preenchimento, (self.x, self.y, larg_preench, self.altura), border_radius=4)
        
        # Brilho interno (gradiente sutil)
        if larg_preench > 2:
            brilho = pygame.Surface((larg_preench - 2, self.altura - 2), pygame.SRCALPHA)
            for i in range(brilho.get_width()):
                alpha = int(40 * (1 - i / brilho.get_width()))
                pygame.draw.line(brilho, (255, 255, 255, alpha), (i, 0), (i, brilho.get_height()))
            tela.blit(brilho, (self.x + 1, self.y + 1))
        
        # Borda
        pygame.draw.rect(tela, (100, 100, 100), (self.x, self.y, self.largura, self.altura), width=2, border_radius=4)


class BarraHP:
    """Barra de HP com visualização de dano atrasado."""
    
    def __init__(self, x: int, y: int, largura: int = 260, altura: int = 24):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.hp = 100
        self.hp_max = 100
        self.hp_delayed = 100
    
    def atualizar(self, hp_atual: int, hp_maximo: int):
        """Atualiza valores de HP."""
        self.hp = hp_atual
        self.hp_max = hp_maximo
        # hp_delayed segue lentamente quando HP cai (efeito Dark Souls)
        if hp_atual < self.hp_delayed:
            self.hp_delayed = max(hp_atual, self.hp_delayed - (self.hp_max * 0.003))
        else:
            # Quando HP sobe (cura), hp_delayed acompanha imediatamente
            self.hp_delayed = hp_atual
    
    def desenhar(self, tela: pygame.Surface):
        """Desenha a barra de HP com efeitos."""
        # Fundo escuro
        pygame.draw.rect(tela, (40, 40, 50), (self.x, self.y, self.largura, self.altura), border_radius=6)
        
        # Camada de dano (amarela) — hp_delayed
        larg_delayed = max(0, (self.hp_delayed / self.hp_max) * self.largura) if self.hp_max > 0 else 0
        pygame.draw.rect(tela, (255, 200, 0), (self.x, self.y, int(larg_delayed), self.altura), border_radius=6)
        
        # Barra de HP atual (verde ou vermelho)
        cor_hp = VERDE if self.hp > self.hp_max * 0.3 else VERMELHO
        larg_hp = max(0, (self.hp / self.hp_max) * self.largura) if self.hp_max > 0 else 0
        pygame.draw.rect(tela, cor_hp, (self.x, self.y, int(larg_hp), self.altura), border_radius=6)
        
        # Brilho
        if larg_hp > 2:
            brilho = pygame.Surface((int(larg_hp) - 2, self.altura - 2), pygame.SRCALPHA)
            for i in range(brilho.get_width()):
                alpha = int(60 * (1 - i / max(1, brilho.get_width())))
                pygame.draw.line(brilho, (255, 255, 255, alpha), (i, 0), (i, brilho.get_height()))
            tela.blit(brilho, (self.x + 1, self.y + 1))
        
        # Borda brilhante
        pygame.draw.rect(tela, (180, 180, 180), (self.x, self.y, self.largura, self.altura), width=2, border_radius=6)
        
        # Texto de HP
        fonte = pygame.font.SysFont("Arial", 16, bold=True)
        txt_hp = fonte.render(f"{int(self.hp)} / {int(self.hp_max)}", True, BRANCO)
        tela.blit(txt_hp, (self.x + 8, self.y + self.altura // 2 - txt_hp.get_height() // 2))


class ContadorTexto:
    """Contador de texto com animação de aumento."""
    
    def __init__(self, x: int, y: int, fonte_size: int = 24):
        self.x = x
        self.y = y
        self.fonte = pygame.font.SysFont("Arial", fonte_size, bold=True)
        self.valor = 0
        self.valor_formatado = ""
        self._anim_timer = 0
    
    def atualizar(self, novo_valor: int):
        """Atualiza o valor."""
        if novo_valor != self.valor:
            self._anim_timer = 10
        self.valor = novo_valor
        self.valor_formatado = f"{novo_valor:,}" if novo_valor >= 1000 else str(novo_valor)
    
    def desenhar(self, tela: pygame.Surface, cor: tuple = BRANCO):
        """Desenha o contador."""
        escala = 1.0 + (self._anim_timer / 10) * 0.2 if self._anim_timer > 0 else 1.0
        
        txt = self.fonte.render(self.valor_formatado, True, cor)
        if escala != 1.0:
            novo_tamanho = (int(txt.get_width() * escala), int(txt.get_height() * escala))
            txt = pygame.transform.scale(txt, novo_tamanho)
        
        rect = txt.get_rect(center=(self.x, self.y))
        tela.blit(txt, rect)
        
        if self._anim_timer > 0:
            self._anim_timer -= 1


class PainelInfo:
    """Painel de informações com ícones."""
    
    def __init__(self, x: int, y: int, largura: int = 300, altura: int = 40):
        self.x = x
        self.y = y
        self.largura = largura
        self.altura = altura
        self.fonte = pygame.font.SysFont("Arial", 18, bold=True)
        self.informacoes = []
    
    def adicionar_info(self, icone: str, texto: str, cor: tuple = BRANCO):
        """Adiciona uma linha de informação."""
        self.informacoes.append({"icone": icone, "texto": texto, "cor": cor})
    
    def limpar(self):
        """Limpa as informações."""
        self.informacoes = []
    
    def desenhar(self, tela: pygame.Surface):
        """Desenha o painel."""
        # Fundo semi-transparente
        painel = pygame.Surface((self.largura, self.altura), pygame.SRCALPHA)
        painel.fill((20, 20, 30, 200))
        tela.blit(painel, (self.x, self.y))
        
        # Borda
        pygame.draw.rect(tela, (100, 100, 120), (self.x, self.y, self.largura, self.altura), width=2)
        
        # Conteúdo
        x_offset = self.x + 10
        y_offset = self.y + (self.altura - 20) // 2
        
        for info in self.informacoes:
            txt = self.fonte.render(f"{info['icone']} {info['texto']}", True, info['cor'])
            tela.blit(txt, (x_offset, y_offset - txt.get_height() // 2))
            x_offset += txt.get_width() + 15

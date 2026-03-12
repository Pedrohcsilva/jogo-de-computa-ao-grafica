##########################################################
#  Sistema de Controle — Teclado + Gamepad
#
#  MAPEAMENTO:
#   Movimento: WASD / Analógico esquerdo
#   Tiro: Mouse / Analógico direito
#   Pausa: ESC / START
#   Poder: ESPAÇO / Y (Xbox) / Triangle (PS)
#
#  DETECÇÃO AUTOMÁTICA DE GAMEPAD
##########################################################

import pygame
import sys
import os
import math

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *


class ControladorEntrada:
    """Gerencia entrada de teclado e gamepad."""
    
    # Deadzone para analógico (0-1)
    DEADZONE = 0.15
    DEADZONE_TRIGGER = 0.1
    
    def __init__(self):
        pygame.joystick.init()
        self.gamepad = None
        self._detectar_gamepad()
        
        # Estado atual de entrada
        self.movimento = pygame.math.Vector2(0, 0)
        self.direcao_tiro = pygame.math.Vector2(0, 0)
        self.pausa_pressionado = False
        self.poder_pressionado = False
    
    def _detectar_gamepad(self):
        """Detecta e inicializa o primeiro gamepad conectado."""
        joystick_count = pygame.joystick.get_count()
        if joystick_count > 0:
            self.gamepad = pygame.joystick.Joystick(0)
            self.gamepad.init()
            print(f"✓ Gamepad detectado: {self.gamepad.get_name()}")
        else:
            print("ℹ Nenhum gamepad detectado (teclado/mouse habilitados)")
    
    def atualizar(self, eventos):
        """
        Processa eventos e atualiza estado de entrada.
        
        Args:
            eventos: lista de eventos pygame
        
        Returns:
            dict com estado atual de entrada
        """
        # Reset estado
        self.movimento = pygame.math.Vector2(0, 0)
        self.direcao_tiro = pygame.math.Vector2(0, 0)
        self.pausa_pressionado = False
        self.poder_pressionado = False
        
        # Processar teclado
        self._processar_teclado()
        
        # Processar gamepad
        if self.gamepad:
            self._processar_gamepad()
        
        # Processar eventos de tiro com mouse
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # botão esquerdo do mouse
            mouse_pos = pygame.mouse.get_pos()
            # Obtém posição do jogador (será passado via evento)
            # Por enquanto, retorna normalizado
            pass
        
        # Processar eventos pygame para detectar pressionamentos específicos
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.pausa_pressionado = True
                if evento.key == pygame.K_SPACE:
                    self.poder_pressionado = True
            elif evento.type == pygame.JOYBUTTONDOWN:
                if evento.button == 7:  # Start button
                    self.pausa_pressionado = True
                if evento.button == 3:  # Y button (Xbox)
                    self.poder_pressionado = True
        
        return self.obter_estado()
    
    def _processar_teclado(self):
        """Processa entrada de teclado."""
        keys = pygame.key.get_pressed()
        
        # Movimento
        if keys[pygame.K_w]:
            self.movimento.y -= 1
        if keys[pygame.K_s]:
            self.movimento.y += 1
        if keys[pygame.K_a]:
            self.movimento.x -= 1
        if keys[pygame.K_d]:
            self.movimento.x += 1
        
        # Normalizar movimento diagonal
        if self.movimento.length() > 0:
            self.movimento = self.movimento.normalize()
    
    def _processar_gamepad(self):
        """Processa entrada de gamepad."""
        if not self.gamepad:
            return
        
        # Analógico esquerdo — movimento
        lx = self.gamepad.get_axis(0)  # Left stick X
        ly = self.gamepad.get_axis(1)  # Left stick Y
        
        # Aplicar deadzone
        if abs(lx) < self.DEADZONE:
            lx = 0
        if abs(ly) < self.DEADZONE:
            ly = 0
        
        mov_raw = pygame.math.Vector2(lx, ly)
        # Clamp para nunca exceder comprimento 1 (proteção contra hardware ruidoso)
        if mov_raw.length() > 1.0:
            mov_raw = mov_raw.normalize()
        self.movimento = mov_raw
        
        # Analógico direito — direção de tiro
        rx = self.gamepad.get_axis(2)  # Right stick X
        ry = self.gamepad.get_axis(3)  # Right stick Y
        
        # Aplicar deadzone
        if abs(rx) < self.DEADZONE:
            rx = 0
        if abs(ry) < self.DEADZONE:
            ry = 0
        
        if rx != 0 or ry != 0:
            self.direcao_tiro = pygame.math.Vector2(rx, ry).normalize()
        
        # Triggers — tiro alternativo (LT/RT)
        lt = self.gamepad.get_axis(2)  # Left trigger (pode variar)
        rt = self.gamepad.get_axis(5)  # Right trigger
        
        # Se RT pressionado, mantém direção de tiro
        if rt > self.DEADZONE_TRIGGER:
            pass  # já processado acima
    
    def obter_estado(self):
        """Retorna dicionário com estado atual de entrada."""
        return {
            "movimento": self.movimento,
            "direcao_tiro": self.direcao_tiro,
            "pausa": self.pausa_pressionado,
            "poder": self.poder_pressionado,
            "tem_gamepad": self.gamepad is not None,
        }
    
    def tem_gamepad(self):
        """Verifica se há gamepad conectado."""
        return self.gamepad is not None

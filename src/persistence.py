##########################################################
#  Sistema de Persistência — Save/Load do Progresso
#
#  DADOS SALVOS:
#   - Fase atual
#   - HP do jogador
#   - Arma equipada
#   - Upgrades adquiridos
#   - Score/combo
#   - Timestamp
#
#  ARQUIVO: save_game.json
##########################################################

import json
import os
import sys

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import *


SAVE_FILE = "save_game.json"


class SistemaPeristencia:
    """Gerenciador de save/load do jogo."""
    
    @staticmethod
    def salvar_jogo(dados_jogo):
        """
        Salva o estado atual do jogo em JSON.
        
        Args:
            dados_jogo (dict): Dicionário com estado do jogo
        """
        save_data = {
            "fase": dados_jogo.get("fase", 1),
            "hp_jogador": dados_jogo.get("hp_jogador", HP_MAX),
            "hp_max": dados_jogo.get("hp_max", HP_MAX),
            "arma_equipada": dados_jogo.get("arma_equipada", "pistola"),
            "upgrades": dados_jogo.get("upgrades", []),
            "score": dados_jogo.get("score", 0),
            "combo": dados_jogo.get("combo", 0),
            "xp_atual": dados_jogo.get("xp_atual", 0),
            "timestamp": dados_jogo.get("timestamp", ""),
        }
        
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(save_data, f, indent=2)
            print(f"✓ Jogo salvo em '{SAVE_FILE}'")
            return True
        except Exception as e:
            print(f"✗ Erro ao salvar: {e}")
            return False
    
    @staticmethod
    def carregar_jogo():
        """
        Carrega o estado do jogo do JSON.
        
        Returns:
            dict: Estado salvo ou None se arquivo não existe
        """
        if not os.path.exists(SAVE_FILE):
            print(f"Nenhum save encontrado em '{SAVE_FILE}'")
            return None
        
        try:
            with open(SAVE_FILE, 'r') as f:
                dados = json.load(f)
            print(f"✓ Jogo carregado de '{SAVE_FILE}'")
            return dados
        except Exception as e:
            print(f"✗ Erro ao carregar: {e}")
            return None
    
    @staticmethod
    def deletar_save():
        """Apaga o arquivo de save."""
        if os.path.exists(SAVE_FILE):
            try:
                os.remove(SAVE_FILE)
                print(f"✓ Save deletado")
                return True
            except Exception as e:
                print(f"✗ Erro ao deletar: {e}")
                return False
        return False
    
    @staticmethod
    def existe_save():
        """Verifica se existe um save."""
        return os.path.exists(SAVE_FILE)

"""自動入力ユーティリティ

環境変数 DEFAULT_CHOICES を使用して、インタラクティブな入力を自動化します。
"""
import os
from typing import Optional


class AutoInputManager:
    """自動入力を管理するクラス"""
    
    def __init__(self):
        """初期化"""
        choices_str = os.environ.get('DEFAULT_CHOICES', '')
        self.choices = [c.strip() for c in choices_str.split(',') if c.strip()] if choices_str else []
        self.index = 0
        self.enabled = bool(self.choices)
    
    def get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """自動入力または手動入力を取得
        
        Args:
            prompt: 入力プロンプト
            default: デフォルト値（手動入力時のみ使用）
            
        Returns:
            入力された値
        """
        # 自動入力モードの場合
        if self.enabled and self.index < len(self.choices):
            value = self.choices[self.index]
            print(f"{prompt}{value} (自動入力)")
            self.index += 1
            return value
        
        # 手動入力モード
        user_input = input(prompt).strip()
        return user_input if user_input else (default or '')
    
    def reset(self):
        """インデックスをリセット"""
        self.index = 0


# グローバルインスタンスとしても使用可能
_global_manager = AutoInputManager()


def get_auto_input(prompt: str, default: Optional[str] = None) -> str:
    """グローバルな自動入力関数
    
    Args:
        prompt: 入力プロンプト
        default: デフォルト値（手動入力時のみ使用）
        
    Returns:
        入力された値
    """
    return _global_manager.get_input(prompt, default)


def reset_auto_input():
    """グローバルな自動入力のインデックスをリセット"""
    _global_manager.reset()
"""
ドメイン層の基底例外クラス
"""


class DomainException(Exception):
    """
    ドメイン層の基底例外クラス
    
    すべてのドメイン層の例外はこのクラスを継承する
    """
    
    def __init__(self, message: str = "Domain exception occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message
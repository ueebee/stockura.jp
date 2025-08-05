"""投資部門別売買状況エンティティ"""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class TradesSpec:
    """投資部門別売買状況を表すエンティティ
    
    J-Quants API から取得する投資部門別の売買データを表現する。
    金額の単位は千円。
    """
    
    # 基本情報
    code: str  # 銘柄コード
    trade_date: date  # 日付
    section: Optional[str] = None  # 市場区分
    
    # 自己勘定（証券会社）
    sales_proprietary: Optional[int] = None  # 売り
    purchases_proprietary: Optional[int] = None  # 買い
    balance_proprietary: Optional[int] = None  # 差引き
    
    # 委託（個人）
    sales_consignment_individual: Optional[int] = None  # 売り
    purchases_consignment_individual: Optional[int] = None  # 買い
    balance_consignment_individual: Optional[int] = None  # 差引き
    
    # 委託（法人）
    sales_consignment_corporate: Optional[int] = None  # 売り
    purchases_consignment_corporate: Optional[int] = None  # 買い
    balance_consignment_corporate: Optional[int] = None  # 差引き
    
    # 委託（投資信託）
    sales_consignment_investment_trust: Optional[int] = None  # 売り
    purchases_consignment_investment_trust: Optional[int] = None  # 買い
    balance_consignment_investment_trust: Optional[int] = None  # 差引き
    
    # 委託（外国人）
    sales_consignment_foreign: Optional[int] = None  # 売り
    purchases_consignment_foreign: Optional[int] = None  # 買い
    balance_consignment_foreign: Optional[int] = None  # 差引き
    
    # 委託（その他法人）
    sales_consignment_other_corporate: Optional[int] = None  # 売り
    purchases_consignment_other_corporate: Optional[int] = None  # 買い
    balance_consignment_other_corporate: Optional[int] = None  # 差引き
    
    # 委託（その他）
    sales_consignment_other: Optional[int] = None  # 売り
    purchases_consignment_other: Optional[int] = None  # 買い
    balance_consignment_other: Optional[int] = None  # 差引き
    
    # 合計
    sales_total: Optional[int] = None  # 売り合計
    purchases_total: Optional[int] = None  # 買い合計
    balance_total: Optional[int] = None  # 差引き合計
    
    def __post_init__(self):
        """エンティティの妥当性を検証"""
        if not self.code:
            raise ValueError("銘柄コードは必須です")
        
        if not self.trade_date:
            raise ValueError("取引日は必須です")
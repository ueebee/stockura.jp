"""投資部門別売買状況 DTO 定義"""
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional


@dataclass
class TradesSpecDTO:
    """投資部門別売買状況 DTO"""
    
    # 基本情報
    code: str
    trade_date: date
    section: Optional[str] = None
    
    # 自己勘定（証券会社）
    sales_proprietary: Optional[int] = None
    purchases_proprietary: Optional[int] = None
    balance_proprietary: Optional[int] = None
    
    # 委託（個人）
    sales_consignment_individual: Optional[int] = None
    purchases_consignment_individual: Optional[int] = None
    balance_consignment_individual: Optional[int] = None
    
    # 委託（法人）
    sales_consignment_corporate: Optional[int] = None
    purchases_consignment_corporate: Optional[int] = None
    balance_consignment_corporate: Optional[int] = None
    
    # 委託（投資信託）
    sales_consignment_investment_trust: Optional[int] = None
    purchases_consignment_investment_trust: Optional[int] = None
    balance_consignment_investment_trust: Optional[int] = None
    
    # 委託（外国人）
    sales_consignment_foreign: Optional[int] = None
    purchases_consignment_foreign: Optional[int] = None
    balance_consignment_foreign: Optional[int] = None
    
    # 委託（その他法人）
    sales_consignment_other_corporate: Optional[int] = None
    purchases_consignment_other_corporate: Optional[int] = None
    balance_consignment_other_corporate: Optional[int] = None
    
    # 委託（その他）
    sales_consignment_other: Optional[int] = None
    purchases_consignment_other: Optional[int] = None
    balance_consignment_other: Optional[int] = None
    
    # 合計
    sales_total: Optional[int] = None
    purchases_total: Optional[int] = None
    balance_total: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "TradesSpecDTO":
        """API レスポンスから DTO を作成
        
        Args:
            data: API レスポンスデータ
            
        Returns:
            TradesSpecDTO インスタンス
        """
        # 日付の変換
        trade_date = date.fromisoformat(data["Date"])
        
        # 数値フィールドの変換（null の場合は None）
        def to_int_or_none(value: Any) -> Optional[int]:
            if value is None or value == "":
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        return cls(
            code=data["Code"],
            trade_date=trade_date,
            section=data.get("Section"),
            
            # 自己勘定
            sales_proprietary=to_int_or_none(data.get("Sales_Proprietary")),
            purchases_proprietary=to_int_or_none(data.get("Purchases_Proprietary")),
            balance_proprietary=to_int_or_none(data.get("Balance_Proprietary")),
            
            # 委託（個人）
            sales_consignment_individual=to_int_or_none(data.get("Sales_Consignment_Individual")),
            purchases_consignment_individual=to_int_or_none(data.get("Purchases_Consignment_Individual")),
            balance_consignment_individual=to_int_or_none(data.get("Balance_Consignment_Individual")),
            
            # 委託（法人）
            sales_consignment_corporate=to_int_or_none(data.get("Sales_Consignment_Corporate")),
            purchases_consignment_corporate=to_int_or_none(data.get("Purchases_Consignment_Corporate")),
            balance_consignment_corporate=to_int_or_none(data.get("Balance_Consignment_Corporate")),
            
            # 委託（投資信託）
            sales_consignment_investment_trust=to_int_or_none(data.get("Sales_Consignment_InvestmentTrust")),
            purchases_consignment_investment_trust=to_int_or_none(data.get("Purchases_Consignment_InvestmentTrust")),
            balance_consignment_investment_trust=to_int_or_none(data.get("Balance_Consignment_InvestmentTrust")),
            
            # 委託（外国人）
            sales_consignment_foreign=to_int_or_none(data.get("Sales_Consignment_Foreign")),
            purchases_consignment_foreign=to_int_or_none(data.get("Purchases_Consignment_Foreign")),
            balance_consignment_foreign=to_int_or_none(data.get("Balance_Consignment_Foreign")),
            
            # 委託（その他法人）
            sales_consignment_other_corporate=to_int_or_none(data.get("Sales_Consignment_OtherCorporate")),
            purchases_consignment_other_corporate=to_int_or_none(data.get("Purchases_Consignment_OtherCorporate")),
            balance_consignment_other_corporate=to_int_or_none(data.get("Balance_Consignment_OtherCorporate")),
            
            # 委託（その他）
            sales_consignment_other=to_int_or_none(data.get("Sales_Consignment_Other")),
            purchases_consignment_other=to_int_or_none(data.get("Purchases_Consignment_Other")),
            balance_consignment_other=to_int_or_none(data.get("Balance_Consignment_Other")),
            
            # 合計
            sales_total=to_int_or_none(data.get("Sales_Total")),
            purchases_total=to_int_or_none(data.get("Purchases_Total")),
            balance_total=to_int_or_none(data.get("Balance_Total")),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """DTO を辞書形式に変換
        
        Returns:
            辞書形式のデータ
        """
        return {
            "code": self.code,
            "trade_date": self.trade_date.isoformat(),
            "section": self.section,
            "sales_proprietary": self.sales_proprietary,
            "purchases_proprietary": self.purchases_proprietary,
            "balance_proprietary": self.balance_proprietary,
            "sales_consignment_individual": self.sales_consignment_individual,
            "purchases_consignment_individual": self.purchases_consignment_individual,
            "balance_consignment_individual": self.balance_consignment_individual,
            "sales_consignment_corporate": self.sales_consignment_corporate,
            "purchases_consignment_corporate": self.purchases_consignment_corporate,
            "balance_consignment_corporate": self.balance_consignment_corporate,
            "sales_consignment_investment_trust": self.sales_consignment_investment_trust,
            "purchases_consignment_investment_trust": self.purchases_consignment_investment_trust,
            "balance_consignment_investment_trust": self.balance_consignment_investment_trust,
            "sales_consignment_foreign": self.sales_consignment_foreign,
            "purchases_consignment_foreign": self.purchases_consignment_foreign,
            "balance_consignment_foreign": self.balance_consignment_foreign,
            "sales_consignment_other_corporate": self.sales_consignment_other_corporate,
            "purchases_consignment_other_corporate": self.purchases_consignment_other_corporate,
            "balance_consignment_other_corporate": self.balance_consignment_other_corporate,
            "sales_consignment_other": self.sales_consignment_other,
            "purchases_consignment_other": self.purchases_consignment_other,
            "balance_consignment_other": self.balance_consignment_other,
            "sales_total": self.sales_total,
            "purchases_total": self.purchases_total,
            "balance_total": self.balance_total,
        }


@dataclass
class FetchTradesSpecResult:
    """投資部門別売買状況取得結果"""
    
    success: bool
    fetched_count: int
    saved_count: int
    section: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    error_message: Optional[str] = None
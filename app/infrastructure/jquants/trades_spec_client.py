"""J-Quants API trades_spec エンドポイント用クライアント"""
from datetime import date
from typing import Dict, List, Optional, Any

from app.domain.entities.trades_spec import TradesSpec
from app.infrastructure.jquants.base_client import JQuantsBaseClient


class TradesSpecClient(JQuantsBaseClient):
    """投資部門別売買状況データ取得用クライアント"""
    
    async def fetch_trades_spec(
        self,
        section: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        pagination_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """投資部門別売買状況データを取得する
        
        Args:
            section: 市場区分 (e.g., "TSEPrime")
            from_date: 開始日
            to_date: 終了日
            pagination_key: ページネーションキー
            
        Returns:
            API レスポンス（生データ）
        """
        params = {}
        
        if section:
            params["section"] = section
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
        if pagination_key:
            params["pagination_key"] = pagination_key
            
        return await self.get("/markets/trades_spec", params=params)
    
    async def fetch_all_trades_spec(
        self,
        section: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        max_pages: Optional[int] = None,
    ) -> List[TradesSpec]:
        """投資部門別売買状況データを全件取得する（ページネーション対応）
        
        Args:
            section: 市場区分
            from_date: 開始日
            to_date: 終了日
            max_pages: 最大取得ページ数
            
        Returns:
            TradesSpec エンティティのリスト
        """
        params = {}
        
        if section:
            params["section"] = section
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%d")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%d")
            
        # ページネーション対応で全データ取得
        trades_specs = []
        pagination_key = None
        page_count = 0
        
        while True:
            # ページ数制限チェック
            if max_pages and page_count >= max_pages:
                break
                
            # パラメータにページネーションキーを追加
            current_params = params.copy()
            if pagination_key:
                current_params["pagination_key"] = pagination_key
                
            # API 呼び出し
            response = await self.get("/markets/trades_spec", params=current_params)
            
            # データ取得
            if "trades_spec" in response:
                for item in response["trades_spec"]:
                    trades_spec = self._convert_to_entity(item)
                    if trades_spec:
                        trades_specs.append(trades_spec)
                        
            page_count += 1
            
            # 次のページネーションキーを確認
            if "pagination_key" in response:
                pagination_key = response["pagination_key"]
            else:
                # ページネーションキーがない場合は終了
                break
                
        return trades_specs
    
    def _convert_to_entity(self, data: Dict[str, Any]) -> Optional[TradesSpec]:
        """API レスポンスデータをエンティティに変換する
        
        Args:
            data: API レスポンスの 1 レコード
            
        Returns:
            TradesSpec エンティティ、変換できない場合は None
        """
        try:
            # 日付の変換（PublishedDate を使用）
            trade_date = date.fromisoformat(data["PublishedDate"])
            
            # 数値フィールドの変換（null の場合は None）
            def to_int_or_none(value: Any) -> Optional[int]:
                if value is None or value == "":
                    return None
                try:
                    # float から int に変換（千円単位）
                    return int(float(value))
                except (ValueError, TypeError):
                    return None
            
            # 市場全体のデータなので、 code は市場区分を使用
            code = data.get("Section", "MARKET")
            
            return TradesSpec(
                code=code,  # 市場区分をコードとして使用
                trade_date=trade_date,
                section=data.get("Section"),
                
                # 自己勘定
                sales_proprietary=to_int_or_none(data.get("ProprietarySales")),
                purchases_proprietary=to_int_or_none(data.get("ProprietaryPurchases")),
                balance_proprietary=to_int_or_none(data.get("ProprietaryBalance")),
                
                # 委託（個人）
                sales_consignment_individual=to_int_or_none(data.get("IndividualsSales")),
                purchases_consignment_individual=to_int_or_none(data.get("IndividualsPurchases")),
                balance_consignment_individual=to_int_or_none(data.get("IndividualsBalance")),
                
                # 委託（法人）
                sales_consignment_corporate=to_int_or_none(data.get("BusinessCosSales")),
                purchases_consignment_corporate=to_int_or_none(data.get("BusinessCosPurchases")),
                balance_consignment_corporate=to_int_or_none(data.get("BusinessCosBalance")),
                
                # 委託（投資信託）
                sales_consignment_investment_trust=to_int_or_none(data.get("InvestmentTrustsSales")),
                purchases_consignment_investment_trust=to_int_or_none(data.get("InvestmentTrustsPurchases")),
                balance_consignment_investment_trust=to_int_or_none(data.get("InvestmentTrustsBalance")),
                
                # 委託（外国人）
                sales_consignment_foreign=to_int_or_none(data.get("ForeignersSales")),
                purchases_consignment_foreign=to_int_or_none(data.get("ForeignersPurchases")),
                balance_consignment_foreign=to_int_or_none(data.get("ForeignersBalance")),
                
                # 委託（その他法人）- API では OtherCos として提供
                sales_consignment_other_corporate=to_int_or_none(data.get("OtherCosSales")),
                purchases_consignment_other_corporate=to_int_or_none(data.get("OtherCosPurchases")),
                balance_consignment_other_corporate=to_int_or_none(data.get("OtherCosBalance")),
                
                # 委託（その他）- 証券会社など他のカテゴリーを合算
                # 注: API には「その他」カテゴリーがないため、証券会社のデータを使用
                sales_consignment_other=to_int_or_none(data.get("SecuritiesCosSales")),
                purchases_consignment_other=to_int_or_none(data.get("SecuritiesCosPurchases")),
                balance_consignment_other=to_int_or_none(data.get("SecuritiesCosBalance")),
                
                # 合計
                sales_total=to_int_or_none(data.get("TotalSales")),
                purchases_total=to_int_or_none(data.get("TotalPurchases")),
                balance_total=to_int_or_none(data.get("TotalBalance")),
            )
            
        except (KeyError, ValueError) as e:
            # 必須フィールドが不足している場合やデータ変換エラー
            # ログに記録して None を返す
            import logging
            logging.error(f"Failed to convert trades_spec data: {e}, data: {data}")
            return None
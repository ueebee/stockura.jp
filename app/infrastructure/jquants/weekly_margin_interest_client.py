"""週次信用取引残高 J-Quants API クライアント"""

from datetime import date, datetime
from typing import Dict, List, Optional

from app.domain.entities import WeeklyMarginInterest
from app.infrastructure.jquants.base_client import JQuantsBaseClient


class WeeklyMarginInterestClient(JQuantsBaseClient):
    """週次信用取引残高データを取得するクライアント"""

    async def fetch_weekly_margin_interest(
        self,
        code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[WeeklyMarginInterest]:
        """週次信用取引残高データを取得する

        Args:
            code: 銘柄コード（省略可）
            from_date: 開始日（省略可）
            to_date: 終了日（省略可）

        Returns:
            週次信用取引残高エンティティのリスト
        """
        params: Dict[str, str] = {}

        if code:
            params["code"] = code
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = await self.get("/markets/weekly_margin_interest", params=params)

        result = []
        for item in data.get("weekly_margin_interest", []):
            entity = self._convert_to_entity(item)
            if entity:
                result.append(entity)

        return result

    async def fetch_all_weekly_margin_interest(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[WeeklyMarginInterest]:
        """全銘柄の週次信用取引残高データを取得する

        Args:
            from_date: 開始日（省略可）
            to_date: 終了日（省略可）

        Returns:
            週次信用取引残高エンティティのリスト
        """
        all_data: List[WeeklyMarginInterest] = []
        pagination_key = None

        while True:
            params: Dict[str, str] = {}

            # APIは少なくともdateまたはcodeパラメータが必要
            # dateパラメータを使用して特定日のデータを取得
            if to_date:
                params["date"] = to_date.strftime("%Y%m%d")
            elif from_date:
                params["date"] = from_date.strftime("%Y%m%d")
            else:
                # 日付が指定されていない場合は、今日の日付を使用
                from datetime import date as date_type
                params["date"] = date_type.today().strftime("%Y%m%d")
                
            if pagination_key:
                params["pagination_key"] = pagination_key

            data = await self.get("/markets/weekly_margin_interest", params=params)

            # データの変換
            for item in data.get("weekly_margin_interest", []):
                entity = self._convert_to_entity(item)
                if entity:
                    all_data.append(entity)

            # ページネーション処理
            pagination_key = data.get("pagination_key")
            if not pagination_key:
                break

        return all_data

    @staticmethod
    def _convert_to_entity(data: Dict) -> Optional[WeeklyMarginInterest]:
        """API レスポンスをエンティティに変換する

        Args:
            data: API レスポンスデータ

        Returns:
            WeeklyMarginInterest エンティティ（変換失敗時は None）
        """
        try:
            # 日付の変換
            date_str = data.get("Date")
            if not date_str:
                return None

            # YYYY-MM-DD 形式を date オブジェクトに変換
            if isinstance(date_str, str):
                entity_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            else:
                return None

            # float 値の安全な変換
            def safe_float(value) -> Optional[float]:
                if value is None or value == "":
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None

            return WeeklyMarginInterest(
                code=data.get("Code", ""),
                date=entity_date,
                short_margin_trade_volume=safe_float(
                    data.get("ShortMarginTradeVolume")
                ),
                long_margin_trade_volume=safe_float(data.get("LongMarginTradeVolume")),
                short_negotiable_margin_trade_volume=safe_float(
                    data.get("ShortNegotiableMarginTradeVolume")
                ),
                long_negotiable_margin_trade_volume=safe_float(
                    data.get("LongNegotiableMarginTradeVolume")
                ),
                short_standardized_margin_trade_volume=safe_float(
                    data.get("ShortStandardizedMarginTradeVolume")
                ),
                long_standardized_margin_trade_volume=safe_float(
                    data.get("LongStandardizedMarginTradeVolume")
                ),
                issue_type=data.get("IssueType"),
            )
        except Exception as e:
            # ログ出力などのエラー処理
            print(f"Error converting weekly margin interest data: {e}")
            return None

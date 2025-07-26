"""
J-Quantsリクエストビルダー

J-Quants APIへのリクエストを構築するヘルパークラス
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import date


class JQuantsRequestBuilder:
    """
    J-Quantsリクエストビルダー
    
    APIリクエストのエンドポイント、パラメータ、ヘッダーを構築
    """
    
    # APIエンドポイント
    LISTED_INFO_ENDPOINT = "/v1/listed/info"
    DAILY_QUOTES_ENDPOINT = "/v1/prices/daily_quotes"
    
    def build_listed_info_request(
        self,
        code: Optional[str] = None,
        target_date: Optional[date] = None,
        access_token: str = None
    ) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        上場企業情報リクエストを構築
        
        Args:
            code: 銘柄コード（4桁）
            target_date: 基準日
            access_token: アクセストークン
            
        Returns:
            Tuple[str, Dict[str, Any], Dict[str, str]]: (エンドポイント, パラメータ, ヘッダー)
        """
        # パラメータ構築
        params = {}
        if code:
            params["code"] = self._format_company_code(code)
        if target_date:
            params["date"] = self._format_date(target_date)
        
        # ヘッダー構築
        headers = self._build_headers(access_token)
        
        return self.LISTED_INFO_ENDPOINT, params, headers
    
    def build_daily_quotes_request(
        self,
        code: Optional[str] = None,
        date: Optional[date] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        pagination_key: Optional[str] = None,
        access_token: str = None
    ) -> Tuple[str, Dict[str, Any], Dict[str, str]]:
        """
        日次株価リクエストを構築
        
        Args:
            code: 銘柄コード（5桁）
            date: 取得日付
            from_date: 取得開始日
            to_date: 取得終了日
            pagination_key: ページネーションキー
            access_token: アクセストークン
            
        Returns:
            Tuple[str, Dict[str, Any], Dict[str, str]]: (エンドポイント, パラメータ, ヘッダー)
        """
        # パラメータ構築
        params = {}
        if code:
            params["code"] = self._format_stock_code(code)
        if date:
            params["date"] = self._format_date_hyphen(date)
        if from_date:
            params["from"] = self._format_date_hyphen(from_date)
        if to_date:
            params["to"] = self._format_date_hyphen(to_date)
        if pagination_key:
            params["pagination_key"] = pagination_key
        
        # ヘッダー構築
        headers = self._build_headers(access_token)
        
        return self.DAILY_QUOTES_ENDPOINT, params, headers
    
    def _build_headers(self, access_token: Optional[str]) -> Dict[str, str]:
        """
        リクエストヘッダーを構築
        
        Args:
            access_token: アクセストークン
            
        Returns:
            Dict[str, str]: ヘッダー辞書
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        return headers
    
    def _format_company_code(self, code: str) -> str:
        """
        企業コードをフォーマット（4桁）
        
        Args:
            code: 銘柄コード
            
        Returns:
            str: フォーマットされたコード
        """
        # 数値部分のみ抽出
        numeric_code = ''.join(filter(str.isdigit, str(code)))
        # 4桁にパディング
        return numeric_code.zfill(4)[:4]
    
    def _format_stock_code(self, code: str) -> str:
        """
        株式コードをフォーマット（5桁）
        
        Args:
            code: 銘柄コード
            
        Returns:
            str: フォーマットされたコード
        """
        # 数値部分のみ抽出
        numeric_code = ''.join(filter(str.isdigit, str(code)))
        
        # 4桁の場合は末尾に0を追加
        if len(numeric_code) == 4:
            return f"{numeric_code}0"
        
        # 5桁にパディング
        return numeric_code.zfill(5)[:5]
    
    def _format_date(self, date_obj: date) -> str:
        """
        日付をYYYYMMDD形式にフォーマット
        
        Args:
            date_obj: 日付オブジェクト
            
        Returns:
            str: フォーマットされた日付
        """
        return date_obj.strftime("%Y%m%d")
    
    def _format_date_hyphen(self, date_obj: date) -> str:
        """
        日付をYYYY-MM-DD形式にフォーマット
        
        Args:
            date_obj: 日付オブジェクト
            
        Returns:
            str: フォーマットされた日付
        """
        return date_obj.strftime("%Y-%m-%d")
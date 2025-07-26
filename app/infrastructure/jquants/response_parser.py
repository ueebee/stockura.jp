"""
J-Quantsレスポンスパーサー

J-Quants APIのレスポンスを解析・検証するクラス
"""

import logging
from typing import Dict, Any, List, Union
from datetime import date

from app.domain.dto import CompanyInfoDTO, DailyQuoteDTO
from app.domain.exceptions import DataValidationError

logger = logging.getLogger(__name__)


class JQuantsResponseParser:
    """
    J-Quantsレスポンスパーサー
    
    APIレスポンスをDTOに変換し、データの検証を行う
    """
    
    def parse_response(
        self,
        data: Dict[str, Any],
        response_type: str
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        レスポンスをパース
        
        Args:
            data: APIレスポンスデータ
            response_type: レスポンスタイプ（"listed_info" or "daily_quotes"）
            
        Returns:
            Union[List[Dict[str, Any]], Dict[str, Any]]: パースされたデータ
            
        Raises:
            DataValidationError: データ検証エラー
        """
        if response_type == "listed_info":
            return self._parse_listed_info(data)
        elif response_type == "daily_quotes":
            return self._parse_daily_quotes(data)
        else:
            raise DataValidationError(
                message=f"Unknown response type: {response_type}",
                error_code="INVALID_RESPONSE_TYPE"
            )
    
    def _parse_listed_info(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        上場企業情報レスポンスをパース
        
        Args:
            data: APIレスポンスデータ
            
        Returns:
            List[Dict[str, Any]]: パースされた企業情報リスト
            
        Raises:
            DataValidationError: データ検証エラー
        """
        try:
            # "info"フィールドから企業情報を取得
            if "info" not in data:
                logger.warning("No 'info' field in listed info response")
                return []
            
            companies = data["info"]
            if not isinstance(companies, list):
                raise DataValidationError(
                    message="Expected 'info' to be a list",
                    field="info",
                    value=type(companies).__name__
                )
            
            # 各企業情報を検証
            validated_companies = []
            for idx, company in enumerate(companies):
                try:
                    validated = self._validate_company_data(company)
                    validated_companies.append(validated)
                except DataValidationError as e:
                    logger.warning(f"Invalid company data at index {idx}: {e}")
                    # 無効なデータはスキップ
                    continue
            
            logger.info(f"Parsed {len(validated_companies)} companies from response")
            return validated_companies
            
        except Exception as e:
            logger.error(f"Failed to parse listed info response: {e}")
            raise DataValidationError(
                message=f"Failed to parse listed info response: {str(e)}",
                error_code="PARSE_ERROR"
            )
    
    def _parse_daily_quotes(
        self,
        data: Dict[str, Any]
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        日次株価レスポンスをパース
        
        Args:
            data: APIレスポンスデータ
            
        Returns:
            Union[List[Dict[str, Any]], Dict[str, Any]]: 
                パースされた株価データ（ページネーションありの場合は辞書）
            
        Raises:
            DataValidationError: データ検証エラー
        """
        try:
            # ページネーション対応チェック
            if "daily_quotes" in data:
                # ページネーションありのレスポンス
                quotes = data["daily_quotes"]
                if not isinstance(quotes, list):
                    raise DataValidationError(
                        message="Expected 'daily_quotes' to be a list",
                        field="daily_quotes",
                        value=type(quotes).__name__
                    )
                
                # 各株価データを検証
                validated_quotes = []
                for idx, quote in enumerate(quotes):
                    try:
                        validated = self._validate_quote_data(quote)
                        validated_quotes.append(validated)
                    except DataValidationError as e:
                        logger.warning(f"Invalid quote data at index {idx}: {e}")
                        # 無効なデータはスキップ
                        continue
                
                result = {"daily_quotes": validated_quotes}
                
                # ページネーションキーがある場合は含める
                if "pagination_key" in data:
                    result["pagination_key"] = data["pagination_key"]
                
                logger.info(f"Parsed {len(validated_quotes)} quotes from paginated response")
                return result
            else:
                # 単一レスポンス（後方互換性のため）
                if not isinstance(data, list):
                    # 単一の株価データ
                    return [self._validate_quote_data(data)]
                else:
                    # 株価データのリスト
                    validated_quotes = []
                    for idx, quote in enumerate(data):
                        try:
                            validated = self._validate_quote_data(quote)
                            validated_quotes.append(validated)
                        except DataValidationError as e:
                            logger.warning(f"Invalid quote data at index {idx}: {e}")
                            continue
                    
                    logger.info(f"Parsed {len(validated_quotes)} quotes from response")
                    return validated_quotes
            
        except Exception as e:
            logger.error(f"Failed to parse daily quotes response: {e}")
            raise DataValidationError(
                message=f"Failed to parse daily quotes response: {str(e)}",
                error_code="PARSE_ERROR"
            )
    
    def _validate_company_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        企業データを検証
        
        Args:
            data: 企業データ
            
        Returns:
            Dict[str, Any]: 検証済みデータ
            
        Raises:
            DataValidationError: データ検証エラー
        """
        # 必須フィールドの確認
        required_fields = ["Code", "CompanyName"]
        for field in required_fields:
            if field not in data or not data[field]:
                raise DataValidationError(
                    message=f"Missing required field: {field}",
                    field=field
                )
        
        # コードの検証（4桁または5桁の英数字）
        code = str(data["Code"])
        if not code.isalnum() or (len(code) != 4 and len(code) != 5):
            raise DataValidationError(
                message=f"Invalid company code format: {code}",
                field="Code",
                value=code
            )
        
        return data
    
    def _validate_quote_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        株価データを検証
        
        Args:
            data: 株価データ
            
        Returns:
            Dict[str, Any]: 検証済みデータ
            
        Raises:
            DataValidationError: データ検証エラー
        """
        # 必須フィールドの確認
        required_fields = ["Code", "Date"]
        for field in required_fields:
            if field not in data:
                raise DataValidationError(
                    message=f"Missing required field: {field}",
                    field=field
                )
        
        # コードの検証（5桁の英数字）
        code = str(data["Code"])
        if not code.isalnum() or len(code) != 5:
            raise DataValidationError(
                message=f"Invalid stock code format: {code}",
                field="Code",
                value=code
            )
        
        # 日付の検証
        try:
            # 日付形式の確認（YYYY-MM-DD）
            date.fromisoformat(data["Date"])
        except (ValueError, TypeError) as e:
            raise DataValidationError(
                message=f"Invalid date format: {data['Date']}",
                field="Date",
                value=data["Date"]
            )
        
        # 数値フィールドの検証（存在する場合）
        numeric_fields = [
            "Open", "High", "Low", "Close", "Volume", "TurnoverValue",
            "AdjustmentFactor", "AdjustmentOpen", "AdjustmentHigh",
            "AdjustmentLow", "AdjustmentClose", "AdjustmentVolume"
        ]
        
        for field in numeric_fields:
            if field in data and data[field] is not None:
                try:
                    # 数値に変換可能か確認
                    float(data[field])
                except (ValueError, TypeError):
                    logger.warning(f"Invalid numeric value for {field}: {data[field]}")
                    # 無効な数値はNoneに置き換え
                    data[field] = None
        
        return data
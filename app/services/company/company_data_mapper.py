"""
企業データマッピングサービス

J-Quants APIレスポンスとDBモデル間のデータ変換を担当
"""

import logging
from typing import Dict, Any, Optional, Tuple

from app.services.interfaces.company_sync_interfaces import ICompanyDataMapper, DataValidationError

logger = logging.getLogger(__name__)


class CompanyDataMapper(ICompanyDataMapper):
    """企業データマッピングサービスの実装"""
    
    # 必須フィールドの定義
    REQUIRED_FIELDS = ["Code", "CompanyName"]
    
    # APIフィールドとモデルフィールドのマッピング
    FIELD_MAPPING = {
        "Code": "code",
        "CompanyName": "company_name",
        "CompanyNameEnglish": "company_name_english",
        "Sector17Code": "sector17_code",
        "Sector33Code": "sector33_code",
        "ScaleCategory": "scale_category",
        "MarketCode": "market_code",
        "MarginCode": "margin_code"
    }
    
    def map_to_model(self, api_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        APIデータをモデル用にマッピング
        
        Args:
            api_data: J-Quants APIレスポンスデータ
            
        Returns:
            Optional[Dict[str, Any]]: モデル用にマッピングされたデータ（無効な場合はNone）
        """
        try:
            # データ検証
            is_valid, error_message = self.validate_data(api_data)
            if not is_valid:
                logger.warning(f"Invalid data: {error_message}")
                return None
            
            # マッピング実行
            mapped_data = {}
            
            # フィールドマッピング
            for api_field, model_field in self.FIELD_MAPPING.items():
                if api_field in api_data:
                    value = api_data[api_field]
                    # 値の変換処理
                    if api_field == "Code":
                        # 銘柄コードは文字列として保存
                        value = str(value)
                    elif value is not None and api_field in ["CompanyName", "CompanyNameEnglish"]:
                        # 企業名は文字列として保存
                        value = str(value)
                    
                    mapped_data[model_field] = value
            
            # デフォルト値の設定
            mapped_data["is_active"] = True
            
            logger.debug(f"Successfully mapped company data for code: {mapped_data.get('code')}")
            return mapped_data
            
        except Exception as e:
            logger.error(f"Error mapping company data: {e}", exc_info=True)
            return None
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        データ検証
        
        Args:
            data: 検証対象データ
            
        Returns:
            Tuple[bool, Optional[str]]: (検証結果, エラーメッセージ)
        """
        # 必須フィールドのチェック
        for field in self.REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                return False, f"Missing required field: {field}"
        
        # 銘柄コードの検証
        code = data.get("Code")
        if code:
            code_str = str(code)
            # 銘柄コードは通常4桁の数字
            if not code_str.isdigit() or len(code_str) != 4:
                logger.warning(f"Invalid code format: {code}")
                # ただし、特殊な銘柄コードも存在する可能性があるため、エラーとはしない
        
        # 企業名の検証
        company_name = data.get("CompanyName")
        if company_name is not None:
            company_name_str = str(company_name).strip()
            if len(company_name_str) == 0:
                return False, "Company name cannot be empty"
            if len(company_name_str) > 255:
                return False, f"Company name too long: {len(company_name_str)} characters"
        
        # セクターコードの検証（オプショナル）
        sector17_code = data.get("Sector17Code")
        if sector17_code is not None:
            try:
                # セクターコードは数値または文字列
                sector17_str = str(sector17_code)
                if len(sector17_str) > 10:
                    logger.warning(f"Sector17Code too long: {sector17_str}")
            except Exception:
                logger.warning(f"Invalid Sector17Code format: {sector17_code}")
        
        sector33_code = data.get("Sector33Code")
        if sector33_code is not None:
            try:
                # セクターコードは数値または文字列
                sector33_str = str(sector33_code)
                if len(sector33_str) > 10:
                    logger.warning(f"Sector33Code too long: {sector33_str}")
            except Exception:
                logger.warning(f"Invalid Sector33Code format: {sector33_code}")
        
        # マーケットコードの検証（オプショナル）
        market_code = data.get("MarketCode")
        if market_code is not None:
            market_code_str = str(market_code)
            if len(market_code_str) > 10:
                logger.warning(f"MarketCode too long: {market_code_str}")
        
        return True, None
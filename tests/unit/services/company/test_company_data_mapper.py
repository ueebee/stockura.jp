"""
CompanyDataMapperの単体テスト
"""

import pytest
from app.services.company.company_data_mapper import CompanyDataMapper


class TestCompanyDataMapper:
    """CompanyDataMapperのテストクラス"""
    
    @pytest.fixture
    def mapper(self):
        """テスト用のマッパーインスタンス"""
        return CompanyDataMapper()
    
    @pytest.fixture
    def valid_api_data(self):
        """正常なAPIデータ"""
        return {
            "Code": "1234",
            "CompanyName": "テスト株式会社",
            "CompanyNameEnglish": "Test Corporation",
            "Sector17Code": "1",
            "Sector33Code": "101",
            "ScaleCategory": "TOPIX Large70",
            "MarketCode": "0111",
            "MarginCode": "1"
        }
    
    def test_map_to_model_with_valid_data(self, mapper, valid_api_data):
        """正常なデータのマッピングテスト"""
        result = mapper.map_to_model(valid_api_data)
        
        assert result is not None
        assert result["code"] == "1234"
        assert result["company_name"] == "テスト株式会社"
        assert result["company_name_english"] == "Test Corporation"
        assert result["sector17_code"] == "1"
        assert result["sector33_code"] == "101"
        assert result["scale_category"] == "TOPIX Large70"
        assert result["market_code"] == "0111"
        assert result["margin_code"] == "1"
        assert result["is_active"] is True
    
    def test_map_to_model_with_minimum_required_fields(self, mapper):
        """必須フィールドのみのマッピングテスト"""
        minimal_data = {
            "Code": "5678",
            "CompanyName": "最小データ株式会社"
        }
        
        result = mapper.map_to_model(minimal_data)
        
        assert result is not None
        assert result["code"] == "5678"
        assert result["company_name"] == "最小データ株式会社"
        assert result["is_active"] is True
        # オプショナルフィールドは含まれない
        assert "company_name_english" not in result
        assert "sector17_code" not in result
    
    def test_map_to_model_with_missing_required_field(self, mapper):
        """必須フィールドが欠けている場合のテスト"""
        # Codeが欠けている
        invalid_data = {"CompanyName": "テスト株式会社"}
        result = mapper.map_to_model(invalid_data)
        assert result is None
        
        # CompanyNameが欠けている
        invalid_data = {"Code": "1234"}
        result = mapper.map_to_model(invalid_data)
        assert result is None
    
    def test_map_to_model_with_null_values(self, mapper):
        """NULL値を含むデータのマッピングテスト"""
        data_with_nulls = {
            "Code": "1234",
            "CompanyName": "テスト株式会社",
            "CompanyNameEnglish": None,
            "Sector17Code": None
        }
        
        result = mapper.map_to_model(data_with_nulls)
        
        assert result is not None
        assert result["code"] == "1234"
        assert result["company_name"] == "テスト株式会社"
        assert result.get("company_name_english") is None
        assert result.get("sector17_code") is None
    
    def test_validate_data_with_valid_data(self, mapper, valid_api_data):
        """正常なデータの検証テスト"""
        is_valid, error_message = mapper.validate_data(valid_api_data)
        
        assert is_valid is True
        assert error_message is None
    
    def test_validate_data_with_missing_code(self, mapper):
        """Codeが欠けている場合の検証テスト"""
        invalid_data = {"CompanyName": "テスト株式会社"}
        is_valid, error_message = mapper.validate_data(invalid_data)
        
        assert is_valid is False
        assert error_message == "Missing required field: Code"
    
    def test_validate_data_with_missing_company_name(self, mapper):
        """CompanyNameが欠けている場合の検証テスト"""
        invalid_data = {"Code": "1234"}
        is_valid, error_message = mapper.validate_data(invalid_data)
        
        assert is_valid is False
        assert error_message == "Missing required field: CompanyName"
    
    def test_validate_data_with_empty_company_name(self, mapper):
        """空の企業名の検証テスト"""
        invalid_data = {
            "Code": "1234",
            "CompanyName": ""
        }
        is_valid, error_message = mapper.validate_data(invalid_data)
        
        assert is_valid is False
        assert error_message == "Company name cannot be empty"
    
    def test_validate_data_with_long_company_name(self, mapper):
        """長すぎる企業名の検証テスト"""
        invalid_data = {
            "Code": "1234",
            "CompanyName": "あ" * 256  # 256文字
        }
        is_valid, error_message = mapper.validate_data(invalid_data)
        
        assert is_valid is False
        assert "Company name too long" in error_message
    
    def test_code_conversion_to_string(self, mapper):
        """銘柄コードの文字列変換テスト"""
        # 数値として渡された場合
        data_with_numeric_code = {
            "Code": 1234,  # 数値
            "CompanyName": "テスト株式会社"
        }
        
        result = mapper.map_to_model(data_with_numeric_code)
        
        assert result is not None
        assert result["code"] == "1234"  # 文字列に変換される
        assert isinstance(result["code"], str)
    
    def test_special_code_format(self, mapper):
        """特殊な銘柄コード形式のテスト"""
        # 5桁の銘柄コード（警告は出るが、エラーにはならない）
        data_with_special_code = {
            "Code": "12345",
            "CompanyName": "特殊コード株式会社"
        }
        
        result = mapper.map_to_model(data_with_special_code)
        
        assert result is not None
        assert result["code"] == "12345"
    
    def test_field_mapping_completeness(self, mapper, valid_api_data):
        """全フィールドマッピングの完全性テスト"""
        result = mapper.map_to_model(valid_api_data)
        
        # マッピング定義に含まれる全フィールドが正しく変換されているか確認
        expected_mappings = {
            "Code": "code",
            "CompanyName": "company_name",
            "CompanyNameEnglish": "company_name_english",
            "Sector17Code": "sector17_code",
            "Sector33Code": "sector33_code",
            "ScaleCategory": "scale_category",
            "MarketCode": "market_code",
            "MarginCode": "margin_code"
        }
        
        for api_field, model_field in expected_mappings.items():
            if api_field in valid_api_data:
                assert model_field in result
                if api_field == "Code":
                    assert result[model_field] == str(valid_api_data[api_field])
                else:
                    assert result[model_field] == valid_api_data[api_field]
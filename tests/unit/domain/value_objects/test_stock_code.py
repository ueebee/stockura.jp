"""StockCode バリューオブジェクトのユニットテスト"""
import pytest

from app.domain.value_objects.stock_code import StockCode


class TestStockCode:
    """StockCode バリューオブジェクトのテストクラス"""

    def test_create_valid_numeric_code(self):
        """有効な数値コードでの作成テスト"""
        # Act
        code = StockCode("7203")
        
        # Assert
        assert code.value == "7203"

    def test_create_valid_alphanumeric_code(self):
        """有効な英数字コードでの作成テスト"""
        # Act
        code = StockCode("AAPL")
        
        # Assert
        assert code.value == "AAPL"

    def test_create_with_hyphen(self):
        """ハイフン含むコードでの作成テスト"""
        # Act
        code = StockCode("1301-T")
        
        # Assert
        assert code.value == "1301-T"

    def test_create_with_underscore(self):
        """アンダースコア含むコードでの作成テスト"""
        # Act
        code = StockCode("TEST_CODE")
        
        # Assert
        assert code.value == "TEST_CODE"

    def test_create_mixed_format(self):
        """複合形式コードでの作成テスト"""
        # Act
        code = StockCode("ABC-123_JP")
        
        # Assert
        assert code.value == "ABC-123_JP"

    def test_create_single_character(self):
        """1 文字コードでの作成テスト"""
        # Act
        code = StockCode("A")
        
        # Assert
        assert code.value == "A"

    def test_create_max_length(self):
        """最大長コードでの作成テスト"""
        # Act
        code = StockCode("1234567890")  # 10 文字
        
        # Assert
        assert code.value == "1234567890"
        assert len(code.value) == 10

    def test_create_empty_code_raises_error(self):
        """空コードでのエラーテスト"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            StockCode("")
        
        assert "銘柄コードは空にできません" in str(exc_info.value)

    def test_create_too_long_code_raises_error(self):
        """長すぎるコードでのエラーテスト"""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            StockCode("12345678901")  # 11 文字
        
        assert "銘柄コードは 10 文字以下である必要があります" in str(exc_info.value)

    def test_create_with_invalid_characters_raises_error(self):
        """無効な文字を含むコードでのエラーテスト"""
        # Arrange
        invalid_codes = [
            "1234!",      # 感嘆符
            "ABC@123",    # アットマーク
            "TEST#CODE",  # シャープ
            "ABC 株式",    # 日本語
            "123.45",     # ピリオド
            "A B C",      # スペース
            "A/B",        # スラッシュ
        ]
        
        # Act & Assert
        for invalid_code in invalid_codes:
            with pytest.raises(ValueError) as exc_info:
                StockCode(invalid_code)
            
            assert "銘柄コードは英数字、ハイフン、アンダースコアのみ使用可能です" in str(exc_info.value)

    def test_immutability(self):
        """不変性のテスト"""
        # Arrange
        code = StockCode("7203")
        
        # Act & Assert
        with pytest.raises(AttributeError):
            code.value = "1301"  # frozen=True のため変更不可

    def test_equality(self):
        """等価性のテスト"""
        # Arrange
        code1 = StockCode("7203")
        code2 = StockCode("7203")
        code3 = StockCode("1301")
        
        # Assert
        assert code1 == code2
        assert code1 != code3
        assert code2 != code3

    def test_hash(self):
        """ハッシュ値のテスト"""
        # Arrange
        code1 = StockCode("7203")
        code2 = StockCode("7203")
        code3 = StockCode("1301")
        
        # Assert
        assert hash(code1) == hash(code2)
        assert hash(code1) != hash(code3)

    def test_can_be_used_in_set(self):
        """セットでの使用テスト"""
        # Arrange
        codes = {
            StockCode("7203"),
            StockCode("1301"),
            StockCode("7203"),  # 重複
            StockCode("9984")
        }
        
        # Assert
        assert len(codes) == 3  # 重複は除外される
        assert StockCode("7203") in codes
        assert StockCode("1301") in codes
        assert StockCode("9984") in codes

    def test_can_be_used_as_dict_key(self):
        """辞書のキーとしての使用テスト"""
        # Arrange
        stock_data = {
            StockCode("7203"): "トヨタ自動車",
            StockCode("1301"): "極洋",
            StockCode("9984"): "ソフトバンクグループ"
        }
        
        # Assert
        assert stock_data[StockCode("7203")] == "トヨタ自動車"
        assert stock_data[StockCode("1301")] == "極洋"
        assert stock_data[StockCode("9984")] == "ソフトバンクグループ"

    def test_string_representation(self):
        """文字列表現のテスト"""
        # Arrange
        code = StockCode("7203")
        
        # Act
        str_repr = str(code)
        repr_repr = repr(code)
        
        # Assert
        assert "7203" in str_repr
        assert "StockCode" in repr_repr
        assert "7203" in repr_repr
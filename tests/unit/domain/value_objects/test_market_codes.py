"""MarketCode および SectorCode Enum のユニットテスト"""
import pytest

from app.domain.value_objects.market_codes import MarketCode, SectorCode17, SectorCode33


class TestMarketCode:
    """MarketCode Enum のテストクラス"""

    def test_market_code_values(self):
        """市場コード値の確認テスト"""
        # Assert
        assert MarketCode.PRIME.value == "0101"
        assert MarketCode.STANDARD.value == "0102"
        assert MarketCode.GROWTH.value == "0103"
        assert MarketCode.OTHERS.value == "0104"
        assert MarketCode.PRE_PRIME.value == "0105"
        assert MarketCode.PRE_STANDARD.value == "0106"
        assert MarketCode.PRE_GROWTH.value == "0107"
        assert MarketCode.PRO_MARKET.value == "0108"
        assert MarketCode.OLD_TSE1.value == "0109"
        assert MarketCode.OLD_TSE2.value == "0110"
        assert MarketCode.OLD_MOTHERS.value == "0111"
        assert MarketCode.OLD_JASDAQ_STANDARD.value == "0112"
        assert MarketCode.OLD_JASDAQ_GROWTH.value == "0113"

    def test_market_code_names(self):
        """市場コード名の確認テスト"""
        # Assert
        assert MarketCode.PRIME.name == "PRIME"
        assert MarketCode.STANDARD.name == "STANDARD"
        assert MarketCode.GROWTH.name == "GROWTH"
        assert MarketCode.OLD_TSE1.name == "OLD_TSE1"
        assert MarketCode.OLD_MOTHERS.name == "OLD_MOTHERS"

    def test_market_code_from_value(self):
        """値から市場コードを取得するテスト"""
        # Act & Assert
        assert MarketCode("0101") == MarketCode.PRIME
        assert MarketCode("0102") == MarketCode.STANDARD
        assert MarketCode("0103") == MarketCode.GROWTH
        assert MarketCode("0109") == MarketCode.OLD_TSE1

    def test_market_code_invalid_value(self):
        """無効な値でのエラーテスト"""
        # Act & Assert
        with pytest.raises(ValueError):
            MarketCode("9999")
        
        with pytest.raises(ValueError):
            MarketCode("INVALID")

    def test_market_code_comparison(self):
        """市場コードの比較テスト"""
        # Assert
        assert MarketCode.PRIME == MarketCode.PRIME
        assert MarketCode.PRIME != MarketCode.STANDARD
        assert MarketCode.GROWTH != MarketCode.OLD_MOTHERS

    def test_market_code_membership(self):
        """市場コードのメンバーシップテスト"""
        # Assert
        assert MarketCode.PRIME in MarketCode
        assert MarketCode.STANDARD in MarketCode
        assert MarketCode.OLD_JASDAQ_GROWTH in MarketCode

    def test_market_code_iteration(self):
        """市場コードの反復処理テスト"""
        # Act
        all_codes = list(MarketCode)
        
        # Assert
        assert len(all_codes) == 13
        assert MarketCode.PRIME in all_codes
        assert MarketCode.OLD_JASDAQ_GROWTH in all_codes


class TestSectorCode17:
    """SectorCode17 Enum のテストクラス"""

    def test_sector_code_17_values(self):
        """17 業種コード値の確認テスト"""
        # Assert
        assert SectorCode17.FOODS.value == "1"
        assert SectorCode17.ENERGY_RESOURCES.value == "2"
        assert SectorCode17.CONSTRUCTION_MATERIALS.value == "3"
        assert SectorCode17.MATERIALS_CHEMICALS.value == "4"
        assert SectorCode17.PHARMACEUTICALS.value == "5"
        assert SectorCode17.AUTOMOBILES_TRANSPORTATION.value == "6"
        assert SectorCode17.STEEL_NONFERROUS.value == "7"
        assert SectorCode17.MACHINERY.value == "8"
        assert SectorCode17.ELECTRICAL_PRECISION.value == "9"
        assert SectorCode17.IT_COMMUNICATIONS_SERVICES.value == "10"
        assert SectorCode17.ELECTRIC_GAS.value == "11"
        assert SectorCode17.TRANSPORTATION_LOGISTICS.value == "12"
        assert SectorCode17.WHOLESALE_TRADE.value == "13"
        assert SectorCode17.RETAIL_TRADE.value == "14"
        assert SectorCode17.BANKS.value == "15"
        assert SectorCode17.FINANCIAL_EXCL_BANKS.value == "16"
        assert SectorCode17.REAL_ESTATE.value == "17"

    def test_sector_code_17_from_value(self):
        """値から 17 業種コードを取得するテスト"""
        # Act & Assert
        assert SectorCode17("1") == SectorCode17.FOODS
        assert SectorCode17("10") == SectorCode17.IT_COMMUNICATIONS_SERVICES
        assert SectorCode17("17") == SectorCode17.REAL_ESTATE

    def test_sector_code_17_count(self):
        """17 業種コードの数確認テスト"""
        # Act
        all_sectors = list(SectorCode17)
        
        # Assert
        assert len(all_sectors) == 17


class TestSectorCode33:
    """SectorCode33 Enum のテストクラス"""

    def test_sector_code_33_sample_values(self):
        """33 業種コードのサンプル値確認テスト"""
        # Assert
        assert SectorCode33.FISHERY_AGRICULTURE_FORESTRY.value == "0050"
        assert SectorCode33.MINING.value == "1050"
        assert SectorCode33.CONSTRUCTION.value == "2050"
        assert SectorCode33.FOODS.value == "3050"
        assert SectorCode33.CHEMICALS.value == "3200"
        assert SectorCode33.PHARMACEUTICAL.value == "3250"
        assert SectorCode33.IRON_STEEL.value == "3450"
        assert SectorCode33.MACHINERY.value == "3600"
        assert SectorCode33.ELECTRIC_APPLIANCES.value == "3650"
        assert SectorCode33.TRANSPORTATION_EQUIPMENT.value == "3700"
        assert SectorCode33.ELECTRIC_POWER_GAS.value == "4050"
        assert SectorCode33.INFORMATION_COMMUNICATION.value == "5250"
        assert SectorCode33.WHOLESALE_TRADE.value == "6050"
        assert SectorCode33.RETAIL_TRADE.value == "6100"
        assert SectorCode33.BANKS.value == "7050"
        assert SectorCode33.REAL_ESTATE.value == "8050"
        assert SectorCode33.SERVICES.value == "9050"

    def test_sector_code_33_from_value(self):
        """値から 33 業種コードを取得するテスト"""
        # Act & Assert
        assert SectorCode33("0050") == SectorCode33.FISHERY_AGRICULTURE_FORESTRY
        assert SectorCode33("3250") == SectorCode33.PHARMACEUTICAL
        assert SectorCode33("9050") == SectorCode33.SERVICES

    def test_sector_code_33_invalid_value(self):
        """無効な値でのエラーテスト"""
        # Act & Assert
        with pytest.raises(ValueError):
            SectorCode33("0000")
        
        with pytest.raises(ValueError):
            SectorCode33("9999")

    def test_sector_code_33_count(self):
        """33 業種コードの数確認テスト"""
        # Act
        all_sectors = list(SectorCode33)
        
        # Assert
        assert len(all_sectors) == 33  # 実際のコード数

    def test_cross_enum_independence(self):
        """異なる Enum 間の独立性テスト"""
        # Assert
        # 同じ名前のメンバーが異なる値を持つことを確認
        assert SectorCode17.FOODS.value == "1"
        assert SectorCode33.FOODS.value == "3050"
        
        assert SectorCode17.BANKS.value == "15"
        assert SectorCode33.BANKS.value == "7050"
        
        assert SectorCode17.REAL_ESTATE.value == "17"
        assert SectorCode33.REAL_ESTATE.value == "8050"
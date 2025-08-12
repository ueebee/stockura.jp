"""Tests for ListedInfoService."""
import pytest
from datetime import date

from app.domain.entities.jquants_listed_info import JQuantsListedInfo
from app.domain.services.jquants_listed_info_service import ListedInfoService
from app.domain.value_objects.stock_code import StockCode


class TestListedInfoService:
    """ListedInfoService tests."""
    
    @pytest.fixture
    def sample_listed_infos(self):
        """サンプル上場銘柄情報"""
        return [
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english="TOYOTA MOTOR CORPORATION",
                sector_17_code="6",
                sector_17_code_name="自動車・輸送機",
                sector_33_code="3700",
                sector_33_code_name="輸送用機器",
                scale_category="TOPIX Large70",
                market_code="0111",
                market_code_name="プライム",
                margin_code="1",
                margin_code_name="信用",
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("9984"),
                company_name="ソフトバンクグループ",
                company_name_english="SOFTBANK GROUP CORP.",
                sector_17_code="10",
                sector_17_code_name="情報・通信",
                sector_33_code="5250",
                sector_33_code_name="情報・通信業",
                scale_category="TOPIX Large70",
                market_code="0111",
                market_code_name="プライム",
                margin_code="1",
                margin_code_name="信用",
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("4755"),
                company_name="楽天グループ",
                company_name_english="Rakuten Group, Inc.",
                sector_17_code="10",
                sector_17_code_name="情報・通信",
                sector_33_code="5250",
                sector_33_code_name="情報・通信業",
                scale_category="TOPIX Mid400",
                market_code="0111",
                market_code_name="プライム",
                margin_code="0",
                margin_code_name=None,
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("3769"),
                company_name="ＧＭＯペイメントゲートウェイ",
                company_name_english=None,
                sector_17_code="10",
                sector_17_code_name="情報・通信",
                sector_33_code="5250",
                sector_33_code_name="情報・通信業",
                scale_category="TOPIX Small",
                market_code="0111",
                market_code_name="プライム",
                margin_code="1",
                margin_code_name="信用",
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("2371"),
                company_name="カカクコム",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code="0112",
                market_code_name="スタンダード",
                margin_code="0",
                margin_code_name=None,
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("3990"),
                company_name="UUUM",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code="0113",
                market_code_name="グロース",
                margin_code="1",
                margin_code_name="信用",
            ),
        ]
    
    def test_filter_by_market(self, sample_listed_infos):
        """市場コードによるフィルタリングテスト"""
        result = ListedInfoService.filter_by_market(sample_listed_infos, "0111")
        assert len(result) == 4
        assert all(info.market_code == "0111" for info in result)
    
    def test_filter_prime_market(self, sample_listed_infos):
        """プライム市場フィルタリングテスト"""
        result = ListedInfoService.filter_prime_market(sample_listed_infos)
        assert len(result) == 4
        assert all(info.is_prime_market() for info in result)
    
    def test_filter_standard_market(self, sample_listed_infos):
        """スタンダード市場フィルタリングテスト"""
        result = ListedInfoService.filter_standard_market(sample_listed_infos)
        assert len(result) == 1
        assert result[0].code.value == "2371"
    
    def test_filter_growth_market(self, sample_listed_infos):
        """グロース市場フィルタリングテスト"""
        result = ListedInfoService.filter_growth_market(sample_listed_infos)
        assert len(result) == 1
        assert result[0].code.value == "3990"
    
    def test_filter_by_sector_17(self, sample_listed_infos):
        """17 業種コードによるフィルタリングテスト"""
        result = ListedInfoService.filter_by_sector_17(sample_listed_infos, "10")
        assert len(result) == 3
        assert all(info.sector_17_code == "10" for info in result)
    
    def test_filter_marginable(self, sample_listed_infos):
        """信用取引可能銘柄フィルタリングテスト"""
        result = ListedInfoService.filter_marginable(sample_listed_infos)
        assert len(result) == 4
        assert all(info.is_marginable() for info in result)
    
    def test_filter_large_cap(self, sample_listed_infos):
        """大型株フィルタリングテスト"""
        result = ListedInfoService.filter_large_cap(sample_listed_infos)
        assert len(result) == 2
        assert all(info.is_large_cap() for info in result)
    
    def test_filter_mid_cap(self, sample_listed_infos):
        """中型株フィルタリングテスト"""
        result = ListedInfoService.filter_mid_cap(sample_listed_infos)
        assert len(result) == 1
        assert result[0].code.value == "4755"
    
    def test_find_by_code(self, sample_listed_infos):
        """銘柄コードによる検索テスト"""
        result = ListedInfoService.find_by_code(sample_listed_infos, StockCode("7203"))
        assert result is not None
        assert result.company_name == "トヨタ自動車"
        
        # 存在しないコード
        result = ListedInfoService.find_by_code(sample_listed_infos, StockCode("9999"))
        assert result is None
    
    def test_find_by_codes(self, sample_listed_infos):
        """複数銘柄コードによる検索テスト"""
        codes = [StockCode("7203"), StockCode("9984"), StockCode("9999")]
        result = ListedInfoService.find_by_codes(sample_listed_infos, codes)
        
        assert len(result) == 2
        assert set(info.code.value for info in result) == {"7203", "9984"}
    
    def test_group_by_market(self, sample_listed_infos):
        """市場別グループ化テスト"""
        result = ListedInfoService.group_by_market(sample_listed_infos)
        
        assert len(result) == 3
        assert "0111" in result
        assert "0112" in result
        assert "0113" in result
        assert len(result["0111"]) == 4
        assert len(result["0112"]) == 1
        assert len(result["0113"]) == 1
    
    def test_group_by_sector_17(self, sample_listed_infos):
        """17 業種別グループ化テスト"""
        result = ListedInfoService.group_by_sector_17(sample_listed_infos)
        
        assert "6" in result
        assert "10" in result
        assert None in result
        assert len(result["10"]) == 3
        assert len(result["6"]) == 1
    
    def test_extract_codes(self, sample_listed_infos):
        """銘柄コード抽出テスト"""
        result = ListedInfoService.extract_codes(sample_listed_infos)
        
        assert len(result) == 6
        assert all(isinstance(code, StockCode) for code in result)
        assert StockCode("7203") in result
    
    def test_extract_unique_codes(self, sample_listed_infos):
        """重複なし銘柄コード抽出テスト"""
        # 重複データを追加
        duplicate_info = JQuantsListedInfo(
            date=date(2024, 1, 5),
            code=StockCode("7203"),
            company_name="トヨタ自動車",
            company_name_english=None,
            sector_17_code=None,
            sector_17_code_name=None,
            sector_33_code=None,
            sector_33_code_name=None,
            scale_category=None,
            market_code=None,
            market_code_name=None,
            margin_code=None,
            margin_code_name=None,
        )
        
        infos_with_duplicate = sample_listed_infos + [duplicate_info]
        result = ListedInfoService.extract_unique_codes(infos_with_duplicate)
        
        assert len(result) == 6  # 重複は除かれる
        assert isinstance(result, set)
    
    def test_find_changes(self):
        """差分検出テスト"""
        old_infos = [
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code="0111",
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("9984"),
                company_name="ソフトバンクグループ",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code="0111",
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
        ]
        
        new_infos = [
            JQuantsListedInfo(
                date=date(2024, 1, 5),  # 日付が変更
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code="0111",
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("4755"),  # 新規追加
                company_name="楽天グループ",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code="0111",
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
        ]
        
        result = ListedInfoService.find_changes(old_infos, new_infos)
        
        assert len(result["added"]) == 1
        assert result["added"][0].code.value == "4755"
        
        assert len(result["removed"]) == 1
        assert result["removed"][0].code.value == "9984"
        
        assert len(result["changed"]) == 1
        assert result["changed"][0].code.value == "7203"
    
    def test_filter_by_date(self):
        """日付によるフィルタリングテスト"""
        infos = [
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code=None,
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 5),
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code=None,
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
        ]
        
        result = ListedInfoService.filter_by_date(infos, date(2024, 1, 4))
        assert len(result) == 1
        assert result[0].date == date(2024, 1, 4)
    
    def test_get_latest_by_code(self):
        """銘柄コード別最新情報取得テスト"""
        infos = [
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code=None,
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 5),
                code=StockCode("7203"),
                company_name="トヨタ自動車",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code="0112",  # 変更あり
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
            JQuantsListedInfo(
                date=date(2024, 1, 4),
                code=StockCode("9984"),
                company_name="ソフトバンクグループ",
                company_name_english=None,
                sector_17_code=None,
                sector_17_code_name=None,
                sector_33_code=None,
                sector_33_code_name=None,
                scale_category=None,
                market_code=None,
                market_code_name=None,
                margin_code=None,
                margin_code_name=None,
            ),
        ]
        
        result = ListedInfoService.get_latest_by_code(infos)
        
        assert len(result) == 2
        assert result[StockCode("7203")].date == date(2024, 1, 5)
        assert result[StockCode("7203")].market_code == "0112"
        assert result[StockCode("9984")].date == date(2024, 1, 4)
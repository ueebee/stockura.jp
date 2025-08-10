"""Listed info domain service."""
from datetime import date
from typing import Dict, List, Optional, Set

from app.domain.entities.listed_info import ListedInfo
from app.domain.value_objects.stock_code import StockCode


class ListedInfoService:
    """Listed info domain service.
    
    上場銘柄情報に関するドメインロジックを集約
    """
    
    @staticmethod
    def filter_by_market(
        listed_infos: List[ListedInfo],
        market_code: str
    ) -> List[ListedInfo]:
        """市場コードで上場銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            market_code: 市場コード
            
        Returns:
            該当市場の上場銘柄リスト
        """
        return [info for info in listed_infos if info.market_code == market_code]
    
    @staticmethod
    def filter_prime_market(listed_infos: List[ListedInfo]) -> List[ListedInfo]:
        """プライム市場の銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            プライム市場の上場銘柄リスト
        """
        return [info for info in listed_infos if info.is_prime_market()]
    
    @staticmethod
    def filter_standard_market(listed_infos: List[ListedInfo]) -> List[ListedInfo]:
        """スタンダード市場の銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            スタンダード市場の上場銘柄リスト
        """
        return [info for info in listed_infos if info.is_standard_market()]
    
    @staticmethod
    def filter_growth_market(listed_infos: List[ListedInfo]) -> List[ListedInfo]:
        """グロース市場の銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            グロース市場の上場銘柄リスト
        """
        return [info for info in listed_infos if info.is_growth_market()]
    
    @staticmethod
    def filter_by_sector_17(
        listed_infos: List[ListedInfo],
        sector_code: str
    ) -> List[ListedInfo]:
        """17 業種コードで銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            sector_code: 17 業種コード
            
        Returns:
            該当業種の上場銘柄リスト
        """
        return [info for info in listed_infos if info.belongs_to_sector_17(sector_code)]
    
    @staticmethod
    def filter_by_sector_33(
        listed_infos: List[ListedInfo],
        sector_code: str
    ) -> List[ListedInfo]:
        """33 業種コードで銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            sector_code: 33 業種コード
            
        Returns:
            該当業種の上場銘柄リスト
        """
        return [info for info in listed_infos if info.belongs_to_sector_33(sector_code)]
    
    @staticmethod
    def filter_marginable(listed_infos: List[ListedInfo]) -> List[ListedInfo]:
        """信用取引可能な銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            信用取引可能な上場銘柄リスト
        """
        return [info for info in listed_infos if info.is_marginable()]
    
    @staticmethod
    def filter_by_scale(
        listed_infos: List[ListedInfo],
        scale_category: str
    ) -> List[ListedInfo]:
        """規模カテゴリで銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            scale_category: 規模カテゴリ
            
        Returns:
            該当規模の上場銘柄リスト
        """
        return [info for info in listed_infos if info.scale_category == scale_category]
    
    @staticmethod
    def filter_large_cap(listed_infos: List[ListedInfo]) -> List[ListedInfo]:
        """大型株をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            大型株の上場銘柄リスト
        """
        return [info for info in listed_infos if info.is_large_cap()]
    
    @staticmethod
    def filter_mid_cap(listed_infos: List[ListedInfo]) -> List[ListedInfo]:
        """中型株をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            中型株の上場銘柄リスト
        """
        return [info for info in listed_infos if info.is_mid_cap()]
    
    @staticmethod
    def filter_small_cap(listed_infos: List[ListedInfo]) -> List[ListedInfo]:
        """小型株をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            小型株の上場銘柄リスト
        """
        return [info for info in listed_infos if info.is_small_cap()]
    
    @staticmethod
    def find_by_code(
        listed_infos: List[ListedInfo],
        code: StockCode
    ) -> Optional[ListedInfo]:
        """銘柄コードで銘柄を検索
        
        Args:
            listed_infos: 上場銘柄リスト
            code: 銘柄コード
            
        Returns:
            該当する上場銘柄、見つからない場合は None
        """
        for info in listed_infos:
            if info.code == code:
                return info
        return None
    
    @staticmethod
    def find_by_codes(
        listed_infos: List[ListedInfo],
        codes: List[StockCode]
    ) -> List[ListedInfo]:
        """複数の銘柄コードで銘柄を検索
        
        Args:
            listed_infos: 上場銘柄リスト
            codes: 銘柄コードリスト
            
        Returns:
            該当する上場銘柄リスト
        """
        code_set = set(codes)
        return [info for info in listed_infos if info.code in code_set]
    
    @staticmethod
    def group_by_market(listed_infos: List[ListedInfo]) -> Dict[Optional[str], List[ListedInfo]]:
        """市場別に銘柄をグループ化
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            市場コードをキーとした上場銘柄の辞書
        """
        grouped: Dict[Optional[str], List[ListedInfo]] = {}
        for info in listed_infos:
            market = info.market_code
            if market not in grouped:
                grouped[market] = []
            grouped[market].append(info)
        return grouped
    
    @staticmethod
    def group_by_sector_17(listed_infos: List[ListedInfo]) -> Dict[Optional[str], List[ListedInfo]]:
        """17 業種別に銘柄をグループ化
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            17 業種コードをキーとした上場銘柄の辞書
        """
        grouped: Dict[Optional[str], List[ListedInfo]] = {}
        for info in listed_infos:
            sector = info.sector_17_code
            if sector not in grouped:
                grouped[sector] = []
            grouped[sector].append(info)
        return grouped
    
    @staticmethod
    def group_by_sector_33(listed_infos: List[ListedInfo]) -> Dict[Optional[str], List[ListedInfo]]:
        """33 業種別に銘柄をグループ化
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            33 業種コードをキーとした上場銘柄の辞書
        """
        grouped: Dict[Optional[str], List[ListedInfo]] = {}
        for info in listed_infos:
            sector = info.sector_33_code
            if sector not in grouped:
                grouped[sector] = []
            grouped[sector].append(info)
        return grouped
    
    @staticmethod
    def extract_codes(listed_infos: List[ListedInfo]) -> List[StockCode]:
        """銘柄コードのリストを抽出
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            銘柄コードリスト
        """
        return [info.code for info in listed_infos]
    
    @staticmethod
    def extract_unique_codes(listed_infos: List[ListedInfo]) -> Set[StockCode]:
        """重複のない銘柄コードのセットを抽出
        
        Args:
            listed_infos: 上場銘柄リスト
            
        Returns:
            銘柄コードのセット
        """
        return {info.code for info in listed_infos}
    
    @staticmethod
    def find_changes(
        old_infos: List[ListedInfo],
        new_infos: List[ListedInfo]
    ) -> Dict[str, List[ListedInfo]]:
        """2 つの上場銘柄リストの差分を検出
        
        Args:
            old_infos: 古い上場銘柄リスト
            new_infos: 新しい上場銘柄リスト
            
        Returns:
            'added': 新規追加銘柄、'removed': 削除銘柄、'changed': 変更銘柄
        """
        old_by_code = {info.code: info for info in old_infos}
        new_by_code = {info.code: info for info in new_infos}
        
        added = []
        removed = []
        changed = []
        
        # 新規追加を検出
        for code, info in new_by_code.items():
            if code not in old_by_code:
                added.append(info)
            elif not info.is_same_listing(old_by_code[code]):
                changed.append(info)
        
        # 削除を検出
        for code, info in old_by_code.items():
            if code not in new_by_code:
                removed.append(info)
        
        return {
            'added': added,
            'removed': removed,
            'changed': changed
        }
    
    @staticmethod
    def filter_by_date(
        listed_infos: List[ListedInfo],
        target_date: date
    ) -> List[ListedInfo]:
        """特定の日付の上場銘柄をフィルタリング
        
        Args:
            listed_infos: 上場銘柄リスト
            target_date: 対象日付
            
        Returns:
            該当日付の上場銘柄リスト
        """
        return [info for info in listed_infos if info.date == target_date]
    
    @staticmethod
    def get_latest_by_code(listed_infos: List[ListedInfo]) -> Dict[StockCode, ListedInfo]:
        """各銘柄コードの最新の情報を取得
        
        Args:
            listed_infos: 上場銘柄リスト（複数日付を含む）
            
        Returns:
            銘柄コードをキーとした最新の上場銘柄情報の辞書
        """
        latest: Dict[StockCode, ListedInfo] = {}
        for info in listed_infos:
            if info.code not in latest or info.date > latest[info.code].date:
                latest[info.code] = info
        return latest
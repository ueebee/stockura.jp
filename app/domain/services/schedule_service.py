"""Schedule domain service."""
from typing import List, Optional
from uuid import UUID

from app.domain.entities.schedule import Schedule


class ScheduleService:
    """Schedule domain service.
    
    スケジュールに関するドメインロジックを集約
    """
    
    @staticmethod
    def filter_executable_schedules(schedules: List[Schedule]) -> List[Schedule]:
        """実行可能なスケジュールのみをフィルタリング
        
        Args:
            schedules: スケジュールリスト
            
        Returns:
            実行可能なスケジュールのリスト
        """
        return [schedule for schedule in schedules if schedule.can_execute()]
    
    @staticmethod
    def filter_by_category(
        schedules: List[Schedule],
        category: str
    ) -> List[Schedule]:
        """カテゴリでスケジュールをフィルタリング
        
        Args:
            schedules: スケジュールリスト
            category: カテゴリ名
            
        Returns:
            該当カテゴリのスケジュールリスト
        """
        return [schedule for schedule in schedules if schedule.has_category(category)]
    
    @staticmethod
    def filter_by_tags(
        schedules: List[Schedule],
        tags: List[str],
        match_all: bool = False
    ) -> List[Schedule]:
        """タグでスケジュールをフィルタリング
        
        Args:
            schedules: スケジュールリスト
            tags: タグリスト
            match_all: True の場合、すべてのタグを持つスケジュールのみ返す
            
        Returns:
            該当タグを持つスケジュールリスト
        """
        if match_all:
            return [schedule for schedule in schedules if schedule.has_all_tags(tags)]
        else:
            return [schedule for schedule in schedules if schedule.has_any_tag(tags)]
    
    @staticmethod
    def filter_by_task_name(
        schedules: List[Schedule],
        task_name: str
    ) -> List[Schedule]:
        """タスク名でスケジュールをフィルタリング
        
        Args:
            schedules: スケジュールリスト
            task_name: タスク名
            
        Returns:
            該当タスク名のスケジュールリスト
        """
        return [schedule for schedule in schedules if schedule.is_task(task_name)]
    
    @staticmethod
    def find_auto_generated_schedules(schedules: List[Schedule]) -> List[Schedule]:
        """自動生成されたスケジュールを検索
        
        Args:
            schedules: スケジュールリスト
            
        Returns:
            自動生成されたスケジュールリスト
        """
        return [schedule for schedule in schedules if schedule.is_auto_generated()]
    
    @staticmethod
    def find_by_id(schedules: List[Schedule], schedule_id: UUID) -> Optional[Schedule]:
        """ID でスケジュールを検索
        
        Args:
            schedules: スケジュールリスト
            schedule_id: スケジュール ID
            
        Returns:
            該当するスケジュール、見つからない場合は None
        """
        for schedule in schedules:
            if schedule.id == schedule_id:
                return schedule
        return None
    
    @staticmethod
    def group_by_category(schedules: List[Schedule]) -> dict[Optional[str], List[Schedule]]:
        """カテゴリ別にスケジュールをグループ化
        
        Args:
            schedules: スケジュールリスト
            
        Returns:
            カテゴリをキーとしたスケジュールの辞書
        """
        grouped: dict[Optional[str], List[Schedule]] = {}
        for schedule in schedules:
            category = schedule.category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(schedule)
        return grouped
    
    @staticmethod
    def group_by_task_name(schedules: List[Schedule]) -> dict[str, List[Schedule]]:
        """タスク名別にスケジュールをグループ化
        
        Args:
            schedules: スケジュールリスト
            
        Returns:
            タスク名をキーとしたスケジュールの辞書
        """
        grouped: dict[str, List[Schedule]] = {}
        for schedule in schedules:
            task_name = schedule.task_name
            if task_name not in grouped:
                grouped[task_name] = []
            grouped[task_name].append(schedule)
        return grouped
    
    @staticmethod
    def validate_cron_expression(cron_expression: str) -> bool:
        """Cron 式の妥当性を検証
        
        Args:
            cron_expression: Cron 式
            
        Returns:
            妥当な場合 True
        """
        # 簡易的な検証（5 つのフィールドがあるか）
        parts = cron_expression.strip().split()
        return len(parts) == 5
    
    @staticmethod
    def apply_complex_filter(
        schedules: List[Schedule],
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Schedule]:
        """複雑な条件でスケジュールをフィルタリング
        
        Args:
            schedules: スケジュールリスト
            category: カテゴリフィルタ
            tags: タグフィルタ（いずれかのタグを持つ場合に一致）
            task_name: タスク名フィルタ
            enabled_only: 有効なスケジュールのみ
            
        Returns:
            フィルタリングされたスケジュールリスト
        """
        return [
            schedule for schedule in schedules
            if schedule.matches_filter(
                category=category,
                tags=tags,
                task_name=task_name,
                enabled_only=enabled_only
            )
        ]
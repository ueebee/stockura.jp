"""Schedule entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class Schedule:
    """Schedule entity for Celery Beat tasks."""

    id: UUID
    name: str
    task_name: str
    cron_expression: str
    enabled: bool = True
    args: List[Any] = None
    kwargs: Dict[str, Any] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = None
    execution_policy: str = "allow"
    auto_generated_name: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Post initialization."""
        if self.args is None:
            self.args = []
        if self.kwargs is None:
            self.kwargs = {}
        if self.tags is None:
            self.tags = []

    def can_execute(self) -> bool:
        """実行可能かどうかを判定"""
        return self.enabled and self.execution_policy == "allow"

    def has_category(self, category: str) -> bool:
        """指定されたカテゴリに属するか

        Args:
            category: カテゴリ名

        Returns:
            該当する場合 True
        """
        return self.category == category

    def has_tag(self, tag: str) -> bool:
        """指定されたタグを持つか

        Args:
            tag: タグ名

        Returns:
            該当する場合 True
        """
        return tag in self.tags

    def has_any_tag(self, tags: List[str]) -> bool:
        """指定されたタグのいずれかを持つか

        Args:
            tags: タグ名のリスト

        Returns:
            いずれかのタグを持つ場合 True
        """
        return any(tag in self.tags for tag in tags)

    def has_all_tags(self, tags: List[str]) -> bool:
        """指定されたタグをすべて持つか

        Args:
            tags: タグ名のリスト

        Returns:
            すべてのタグを持つ場合 True
        """
        return all(tag in self.tags for tag in tags)

    def is_auto_generated(self) -> bool:
        """自動生成されたスケジュールかどうか"""
        return self.auto_generated_name

    def is_task(self, task_name: str) -> bool:
        """指定されたタスク名と一致するか

        Args:
            task_name: タスク名

        Returns:
            一致する場合 True
        """
        return self.task_name == task_name

    def matches_filter(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        task_name: Optional[str] = None,
        enabled_only: bool = False,
    ) -> bool:
        """フィルタ条件に一致するかどうかを判定

        Args:
            category: カテゴリフィルタ
            tags: タグフィルタ（いずれかのタグを持つ場合に一致）
            task_name: タスク名フィルタ
            enabled_only: 有効なスケジュールのみ

        Returns:
            フィルタ条件に一致する場合 True
        """
        if enabled_only and not self.enabled:
            return False
        
        if category and not self.has_category(category):
            return False
        
        if tags and not self.has_any_tag(tags):
            return False
        
        if task_name and not self.is_task(task_name):
            return False
        
        return True
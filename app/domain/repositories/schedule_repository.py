"""スケジュールリポジトリのインターフェース"""
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.entities.schedule import Schedule


class ScheduleRepository(ABC):
    """スケジュールリポジトリのインターフェース"""
    
    @abstractmethod
    async def save(self, schedule: Schedule) -> Schedule:
        """スケジュールを保存する"""
        pass
    
    @abstractmethod
    async def find_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        """ID でスケジュールを検索する"""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Schedule]:
        """名前でスケジュールを検索する"""
        pass
    
    @abstractmethod
    async def find_by_category(
        self, 
        category: str,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Schedule]:
        """カテゴリでスケジュールを検索する"""
        pass
    
    @abstractmethod
    async def update(self, schedule: Schedule) -> Schedule:
        """スケジュールを更新する"""
        pass
    
    @abstractmethod
    async def delete(self, schedule_id: UUID) -> None:
        """スケジュールを削除する"""
        pass
    
    @abstractmethod
    async def find_all(
        self,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Schedule]:
        """すべてのスケジュールを取得する"""
        pass
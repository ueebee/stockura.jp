"""Base domain event classes."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent(ABC):
    """基底ドメインイベントクラス"""
    
    aggregate_id: Optional[UUID] = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.now)
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """イベントタイプを返す"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """イベントを辞書形式に変換"""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": str(self.aggregate_id) if self.aggregate_id else None,
        }


class EventPublisher(ABC):
    """イベントパブリッシャーのインターフェース"""
    
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """イベントを発行する
        
        Args:
            event: 発行するドメインイベント
        """
        pass
    
    @abstractmethod
    async def publish_batch(self, events: list[DomainEvent]) -> None:
        """複数のイベントをバッチで発行する
        
        Args:
            events: 発行するドメインイベントのリスト
        """
        pass


class EventHandler(ABC):
    """イベントハンドラーのインターフェース"""
    
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """このハンドラーがイベントを処理できるかを判定
        
        Args:
            event: ドメインイベント
            
        Returns:
            処理可能な場合 True
        """
        pass
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """イベントを処理する
        
        Args:
            event: 処理するドメインイベント
        """
        pass
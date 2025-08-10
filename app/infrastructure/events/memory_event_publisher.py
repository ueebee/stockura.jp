"""In-memory event publisher implementation."""
from typing import List

from app.core.logger import get_logger
from app.domain.events.base import DomainEvent, EventHandler, EventPublisher

logger = get_logger(__name__)


class MemoryEventPublisher(EventPublisher):
    """メモリ内でイベントを処理するパブリッシャー
    
    開発・テスト用の実装。本番環境では Redis/RabbitMQ 等を使用する。
    """
    
    def __init__(self):
        self.handlers: List[EventHandler] = []
    
    def register_handler(self, handler: EventHandler) -> None:
        """イベントハンドラーを登録
        
        Args:
            handler: 登録するイベントハンドラー
        """
        self.handlers.append(handler)
        logger.info(f"Registered event handler: {handler.__class__.__name__}")
    
    async def publish(self, event: DomainEvent) -> None:
        """イベントを発行する
        
        Args:
            event: 発行するドメインイベント
        """
        logger.debug(
            f"Publishing event: {event.event_type}",
            extra={"event_id": str(event.event_id)}
        )
        
        handled_count = 0
        for handler in self.handlers:
            if handler.can_handle(event):
                try:
                    await handler.handle(event)
                    handled_count += 1
                except Exception as e:
                    logger.error(
                        f"Error handling event {event.event_type} with {handler.__class__.__name__}",
                        exc_info=e,
                        extra={
                            "event_id": str(event.event_id),
                            "handler": handler.__class__.__name__,
                        }
                    )
        
        logger.debug(
            f"Event {event.event_type} handled by {handled_count} handlers",
            extra={"event_id": str(event.event_id)}
        )
    
    async def publish_batch(self, events: List[DomainEvent]) -> None:
        """複数のイベントをバッチで発行する
        
        Args:
            events: 発行するドメインイベントのリスト
        """
        logger.debug(f"Publishing batch of {len(events)} events")
        
        for event in events:
            await self.publish(event)
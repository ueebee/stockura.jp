"""listed_info スケジュール管理ユースケース"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.domain.entities.schedule import Schedule
from app.domain.exceptions.schedule_exceptions import (
    ScheduleConflictException,
    ScheduleNotFoundException,
    ScheduleValidationException
)
from app.domain.repositories.schedule_repository import ScheduleRepository
from app.domain.validators.cron_validator import validate_cron_expression, get_next_run_time
from app.domain.helpers.schedule_presets import get_preset_cron_expression
from app.infrastructure.events.schedule_event_publisher import ScheduleEventPublisher

logger = logging.getLogger(__name__)


class ManageListedInfoScheduleUseCase:
    """listed_info スケジュール管理ユースケース"""
    
    def __init__(
        self,
        schedule_repository: ScheduleRepository,
        event_publisher: Optional[ScheduleEventPublisher] = None
    ):
        """
        コンストラクタ
        
        Args:
            schedule_repository: スケジュールリポジトリ
            event_publisher: スケジュールイベントパブリッシャー（オプション）
        """
        self._schedule_repository = schedule_repository
        self._event_publisher = event_publisher
    
    async def create_schedule(
        self,
        name: str,
        cron_expression: str,
        period_type: str,
        description: Optional[str] = None,
        enabled: bool = True,
        codes: Optional[List[str]] = None,
        market: Optional[str] = None,
        preset_name: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Schedule:
        """
        新しいスケジュールを作成する
        
        Args:
            name: スケジュール名
            cron_expression: cron 式（preset が指定されている場合は無視される）
            period_type: 期間タイプ（"yesterday", "7days", "30days", "custom"）
            description: 説明
            enabled: 有効フラグ
            codes: 銘柄コードリスト（指定しない場合は全銘柄）
            market: 市場コード（指定しない場合は全市場）
            preset_name: プリセット名（指定された場合は cron_expression より優先）
            
        Returns:
            作成されたスケジュール
            
        Raises:
            ScheduleConflictException: 同名のスケジュールが既に存在する場合
            ScheduleValidationException: バリデーションエラー
        """
        # プリセットが指定されている場合は cron 式を取得
        if preset_name:
            preset_cron = get_preset_cron_expression(preset_name)
            if preset_cron:
                cron_expression = preset_cron
            else:
                raise ScheduleValidationException(f"無効なプリセット名です: {preset_name}")
        
        # cron 式の検証
        validate_cron_expression(cron_expression)
        
        # period_type の検証
        valid_period_types = ["yesterday", "7days", "30days", "custom"]
        if period_type not in valid_period_types:
            raise ScheduleValidationException(
                f"無効な period_type です: {period_type}. "
                f"有効な値: {', '.join(valid_period_types)}"
            )
        
        # 同名のスケジュールが存在しないか確認
        existing = await self._schedule_repository.find_by_name(name)
        if existing:
            raise ScheduleConflictException(f"同名のスケジュールが既に存在します: {name}")
        
        # period_type が custom の場合、 from_date と to_date が必要
        if period_type == "custom":
            if not from_date or not to_date:
                raise ScheduleValidationException(
                    "period_type が 'custom' の場合、 from_date と to_date は必須です"
                )
        
        # kwargs を構築
        task_kwargs = {
            "period_type": period_type,
            "codes": codes or [],
            "market": market,
        }
        
        # custom の場合は日付を追加
        if period_type == "custom":
            task_kwargs["from_date"] = from_date
            task_kwargs["to_date"] = to_date
        
        # スケジュールエンティティを作成
        schedule = Schedule(
            name=name,
            task_name="fetch_listed_info_task",
            cron_expression=cron_expression,
            enabled=enabled,
            kwargs=task_kwargs,
            description=description,
            category="listed_info",
            tags=["listed_info", period_type],
        )
        
        # リポジトリに保存
        saved_schedule = await self._schedule_repository.save(schedule)
        
        logger.info(f"スケジュールを作成しました: {saved_schedule.name} (ID: {saved_schedule.id})")
        
        # イベント発行
        if self._event_publisher:
            await self._event_publisher.publish_schedule_created(str(saved_schedule.id))
        
        return saved_schedule
    
    async def update_schedule(
        self,
        schedule_id: UUID,
        name: Optional[str] = None,
        cron_expression: Optional[str] = None,
        period_type: Optional[str] = None,
        description: Optional[str] = None,
        enabled: Optional[bool] = None,
        codes: Optional[List[str]] = None,
        market: Optional[str] = None,
    ) -> Schedule:
        """
        既存のスケジュールを更新する
        
        Args:
            schedule_id: スケジュール ID
            name: 新しいスケジュール名
            cron_expression: 新しい cron 式
            period_type: 新しい期間タイプ
            description: 新しい説明
            enabled: 新しい有効フラグ
            codes: 新しい銘柄コードリスト
            market: 新しい市場コード
            
        Returns:
            更新されたスケジュール
            
        Raises:
            ScheduleNotFoundException: スケジュールが見つからない場合
            ScheduleConflictException: 新しい名前が既に使用されている場合
            ScheduleValidationException: バリデーションエラー
        """
        # スケジュールを取得
        schedule = await self._schedule_repository.find_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundException(f"スケジュールが見つかりません: {schedule_id}")
        
        # 名前変更の場合は重複チェック
        if name and name != schedule.name:
            existing = await self._schedule_repository.find_by_name(name)
            if existing:
                raise ScheduleConflictException(f"同名のスケジュールが既に存在します: {name}")
            schedule.name = name
        
        # cron 式の更新と検証
        if cron_expression:
            validate_cron_expression(cron_expression)
            schedule.cron_expression = cron_expression
        
        # その他のフィールドを更新
        if description is not None:
            schedule.description = description
        
        if enabled is not None:
            schedule.enabled = enabled
        
        # kwargs の更新
        kwargs = schedule.kwargs or {}
        
        if period_type:
            valid_period_types = ["yesterday", "7days", "30days", "custom"]
            if period_type not in valid_period_types:
                raise ScheduleValidationException(
                    f"無効な period_type です: {period_type}. "
                    f"有効な値: {', '.join(valid_period_types)}"
                )
            kwargs["period_type"] = period_type
        
        if codes is not None:
            kwargs["codes"] = codes
        
        if market is not None:
            kwargs["market"] = market
        
        schedule.kwargs = kwargs
        
        # リポジトリで更新
        updated_schedule = await self._schedule_repository.update(schedule)
        
        logger.info(f"スケジュールを更新しました: {updated_schedule.name} (ID: {updated_schedule.id})")
        
        # イベント発行
        if self._event_publisher:
            await self._event_publisher.publish_schedule_updated(str(updated_schedule.id))
        
        return updated_schedule
    
    async def delete_schedule(self, schedule_id: UUID) -> None:
        """
        スケジュールを削除する
        
        Args:
            schedule_id: スケジュール ID
            
        Raises:
            ScheduleNotFoundException: スケジュールが見つからない場合
        """
        # スケジュールの存在確認
        schedule = await self._schedule_repository.find_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundException(f"スケジュールが見つかりません: {schedule_id}")
        
        # 削除実行
        await self._schedule_repository.delete(schedule_id)
        
        logger.info(f"スケジュールを削除しました: {schedule.name} (ID: {schedule_id})")
        
        # イベント発行
        if self._event_publisher:
            await self._event_publisher.publish_schedule_deleted(str(schedule_id))
    
    async def get_schedule(self, schedule_id: UUID) -> Schedule:
        """
        スケジュールを取得する
        
        Args:
            schedule_id: スケジュール ID
            
        Returns:
            スケジュール
            
        Raises:
            ScheduleNotFoundException: スケジュールが見つからない場合
        """
        schedule = await self._schedule_repository.find_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundException(f"スケジュールが見つかりません: {schedule_id}")
        
        return schedule
    
    async def list_schedules(
        self,
        category: Optional[str] = "listed_info",
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Schedule]:
        """
        スケジュール一覧を取得する
        
        Args:
            category: カテゴリでフィルタ（デフォルト: "listed_info"）
            enabled_only: 有効なスケジュールのみ取得
            limit: 取得件数上限
            offset: オフセット
            
        Returns:
            スケジュールのリスト
        """
        schedules = await self._schedule_repository.find_by_category(
            category=category,
            limit=limit,
            offset=offset,
        )
        
        # 有効なもののみフィルタ
        if enabled_only:
            schedules = [s for s in schedules if s.enabled]
        
        # 次回実行時刻を計算して追加
        for schedule in schedules:
            try:
                schedule.next_run_at = get_next_run_time(schedule.cron_expression)
            except Exception:
                schedule.next_run_at = None
        
        return schedules
    
    async def toggle_schedule(self, schedule_id: UUID) -> Schedule:
        """
        スケジュールの有効/無効を切り替える
        
        Args:
            schedule_id: スケジュール ID
            
        Returns:
            更新されたスケジュール
            
        Raises:
            ScheduleNotFoundException: スケジュールが見つからない場合
        """
        schedule = await self.get_schedule(schedule_id)
        schedule.enabled = not schedule.enabled
        
        updated_schedule = await self._schedule_repository.update(schedule)
        
        status = "有効" if updated_schedule.enabled else "無効"
        logger.info(f"スケジュールを{status}にしました: {updated_schedule.name} (ID: {schedule_id})")
        
        return updated_schedule
    
    async def get_schedule_history(
        self,
        schedule_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[dict]:
        """
        スケジュールの実行履歴を取得する
        
        Args:
            schedule_id: スケジュール ID
            limit: 取得件数上限
            offset: オフセット
            
        Returns:
            実行履歴のリスト
            
        Raises:
            ScheduleNotFoundException: スケジュールが見つからない場合
        """
        # スケジュールの存在確認
        await self.get_schedule(schedule_id)
        
        # TaskLogRepository から履歴を取得
        # TODO: TaskLogRepository の実装後に完成させる
        # history = await self._task_log_repository.find_by_schedule_id(
        #     schedule_id=schedule_id,
        #     limit=limit,
        #     offset=offset,
        # )
        
        # 仮の実装
        return []
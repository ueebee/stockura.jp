"""Schedule エンティティのユニットテスト"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.entities.schedule import Schedule


class TestSchedule:
    """Schedule エンティティのテストクラス"""

    def test_create_minimal(self):
        """最小パラメータでの作成テスト"""
        # Arrange
        schedule_id = uuid4()
        
        # Act
        schedule = Schedule(
            id=schedule_id,
            name="test_schedule",
            task_name="test_task",
            cron_expression="0 0 * * *"
        )
        
        # Assert
        assert schedule.id == schedule_id
        assert schedule.name == "test_schedule"
        assert schedule.task_name == "test_task"
        assert schedule.cron_expression == "0 0 * * *"
        assert schedule.enabled is True
        assert schedule.args == []
        assert schedule.kwargs == {}
        assert schedule.description is None
        assert schedule.created_at is None
        assert schedule.updated_at is None

    def test_create_with_all_fields(self):
        """全フィールド指定での作成テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        args = ["arg1", "arg2"]
        kwargs = {"key1": "value1", "key2": "value2"}
        
        # Act
        schedule = Schedule(
            id=schedule_id,
            name="full_schedule",
            task_name="fetch_listed_info",
            cron_expression="0 9 * * 1-5",
            enabled=False,
            args=args,
            kwargs=kwargs,
            description="Complete schedule",
            created_at=now,
            updated_at=now
        )
        
        # Assert
        assert schedule.id == schedule_id
        assert schedule.name == "full_schedule"
        assert schedule.task_name == "fetch_listed_info"
        assert schedule.cron_expression == "0 9 * * 1-5"
        assert schedule.enabled is False
        assert schedule.args == args
        assert schedule.kwargs == kwargs
        assert schedule.description == "Complete schedule"
        assert schedule.created_at == now
        assert schedule.updated_at == now

    def test_post_init_with_none_args_kwargs(self):
        """args/kwargs が None の場合の初期化テスト"""
        # Act
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            args=None,
            kwargs=None
        )
        
        # Assert
        assert schedule.args == []
        assert schedule.kwargs == {}

    def test_post_init_with_existing_args_kwargs(self):
        """args/kwargs が既存の場合の初期化テスト"""
        # Arrange
        existing_args = ["existing"]
        existing_kwargs = {"existing": "value"}
        
        # Act
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            args=existing_args,
            kwargs=existing_kwargs
        )
        
        # Assert
        assert schedule.args == existing_args
        assert schedule.kwargs == existing_kwargs

    def test_can_execute(self):
        """can_execute メソッドのテスト"""
        # 有効かつ実行ポリシーが allow のスケジュール
        enabled_schedule = Schedule(
            id=uuid4(),
            name="enabled",
            task_name="test_task",
            cron_expression="0 0 * * *",
            enabled=True,
            execution_policy="allow"
        )
        assert enabled_schedule.can_execute() is True
        
        # 無効なスケジュール
        disabled_schedule = Schedule(
            id=uuid4(),
            name="disabled",
            task_name="test_task",
            cron_expression="0 0 * * *",
            enabled=False
        )
        assert disabled_schedule.can_execute() is False
        
        # 実行ポリシーが skip のスケジュール
        skip_schedule = Schedule(
            id=uuid4(),
            name="skip",
            task_name="test_task",
            cron_expression="0 0 * * *",
            enabled=True,
            execution_policy="skip"
        )
        assert skip_schedule.can_execute() is False

    def test_category_methods(self):
        """カテゴリ関連メソッドのテスト"""
        # カテゴリを持つスケジュール
        schedule_with_category = Schedule(
            id=uuid4(),
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            category="data_fetch"
        )
        
        assert schedule_with_category.has_category("data_fetch") is True
        assert schedule_with_category.has_category("analysis") is False
        
        # カテゴリを持たないスケジュール
        schedule_without_category = Schedule(
            id=uuid4(),
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            category=None
        )
        
        assert schedule_without_category.has_category("data_fetch") is False

    def test_tag_methods(self):
        """タグ関連メソッドのテスト"""
        # 複数のタグを持つスケジュール
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            tags=["jquants", "daily", "listed_info"]
        )
        
        # has_tag
        assert schedule.has_tag("jquants") is True
        assert schedule.has_tag("weekly") is False
        
        # has_any_tag
        assert schedule.has_any_tag(["weekly", "monthly"]) is False
        assert schedule.has_any_tag(["weekly", "daily"]) is True
        assert schedule.has_any_tag(["jquants", "daily"]) is True
        
        # has_all_tags
        assert schedule.has_all_tags(["jquants", "daily"]) is True
        assert schedule.has_all_tags(["jquants", "daily", "listed_info"]) is True
        assert schedule.has_all_tags(["jquants", "weekly"]) is False
        assert schedule.has_all_tags([]) is True  # 空リストは常に True

    def test_is_auto_generated(self):
        """is_auto_generated メソッドのテスト"""
        # 自動生成されたスケジュール
        auto_schedule = Schedule(
            id=uuid4(),
            name="auto_generated",
            task_name="test_task",
            cron_expression="0 0 * * *",
            auto_generated_name=True
        )
        assert auto_schedule.is_auto_generated() is True
        
        # 手動作成されたスケジュール
        manual_schedule = Schedule(
            id=uuid4(),
            name="manual",
            task_name="test_task",
            cron_expression="0 0 * * *",
            auto_generated_name=False
        )
        assert manual_schedule.is_auto_generated() is False

    def test_is_task(self):
        """is_task メソッドのテスト"""
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="fetch_listed_info",
            cron_expression="0 0 * * *"
        )
        
        assert schedule.is_task("fetch_listed_info") is True
        assert schedule.is_task("fetch_stock_prices") is False

    def test_matches_filter(self):
        """matches_filter メソッドのテスト"""
        schedule = Schedule(
            id=uuid4(),
            name="test",
            task_name="fetch_listed_info",
            cron_expression="0 0 * * *",
            enabled=True,
            category="data_fetch",
            tags=["jquants", "daily"]
        )
        
        # カテゴリフィルタ
        assert schedule.matches_filter(category="data_fetch") is True
        assert schedule.matches_filter(category="analysis") is False
        
        # タグフィルタ
        assert schedule.matches_filter(tags=["daily"]) is True
        assert schedule.matches_filter(tags=["weekly", "daily"]) is True
        assert schedule.matches_filter(tags=["weekly", "monthly"]) is False
        
        # タスク名フィルタ
        assert schedule.matches_filter(task_name="fetch_listed_info") is True
        assert schedule.matches_filter(task_name="other_task") is False
        
        # 有効フィルタ
        assert schedule.matches_filter(enabled_only=True) is True
        
        # 複合フィルタ
        assert schedule.matches_filter(
            category="data_fetch",
            tags=["daily"],
            task_name="fetch_listed_info",
            enabled_only=True
        ) is True
        
        # 無効なスケジュールでのテスト
        disabled_schedule = Schedule(
            id=uuid4(),
            name="disabled",
            task_name="test_task",
            cron_expression="0 0 * * *",
            enabled=False
        )
        assert disabled_schedule.matches_filter(enabled_only=True) is False
        assert disabled_schedule.matches_filter(enabled_only=False) is True

    def test_equality(self):
        """等価性テスト"""
        # Arrange
        schedule_id = uuid4()
        now = datetime.now()
        
        schedule1 = Schedule(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            created_at=now,
            updated_at=now
        )
        
        schedule2 = Schedule(
            id=schedule_id,
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            created_at=now,
            updated_at=now
        )
        
        schedule3 = Schedule(
            id=uuid4(),  # 異なる ID
            name="test",
            task_name="test_task",
            cron_expression="0 0 * * *",
            created_at=now,
            updated_at=now
        )
        
        # Assert
        assert schedule1 == schedule2
        assert schedule1 != schedule3
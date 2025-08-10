"""Tests for ScheduleService."""
import pytest
from uuid import uuid4

from app.domain.entities.schedule import Schedule
from app.domain.services.schedule_service import ScheduleService


class TestScheduleService:
    """ScheduleService tests."""
    
    @pytest.fixture
    def sample_schedules(self):
        """サンプルスケジュール"""
        return [
            Schedule(
                id=uuid4(),
                name="data_fetch_daily",
                task_name="fetch_listed_info",
                cron_expression="0 9 * * *",
                enabled=True,
                category="data_fetch",
                tags=["jquants", "daily"],
                execution_policy="allow"
            ),
            Schedule(
                id=uuid4(),
                name="data_fetch_weekly",
                task_name="fetch_listed_info",
                cron_expression="0 9 * * 1",
                enabled=True,
                category="data_fetch",
                tags=["jquants", "weekly"],
                execution_policy="allow"
            ),
            Schedule(
                id=uuid4(),
                name="analysis_daily",
                task_name="analyze_stocks",
                cron_expression="0 10 * * *",
                enabled=False,
                category="analysis",
                tags=["analysis", "daily"],
                execution_policy="allow"
            ),
            Schedule(
                id=uuid4(),
                name="auto_report",
                task_name="generate_report",
                cron_expression="0 18 * * *",
                enabled=True,
                category="reporting",
                tags=["report", "auto"],
                execution_policy="skip",
                auto_generated_name=True
            ),
        ]
    
    def test_filter_executable_schedules(self, sample_schedules):
        """実行可能なスケジュールのフィルタリングテスト"""
        result = ScheduleService.filter_executable_schedules(sample_schedules)
        
        # enabled=True かつ execution_policy="allow" のスケジュールのみ
        assert len(result) == 2
        assert all(s.can_execute() for s in result)
    
    def test_filter_by_category(self, sample_schedules):
        """カテゴリによるフィルタリングテスト"""
        result = ScheduleService.filter_by_category(sample_schedules, "data_fetch")
        
        assert len(result) == 2
        assert all(s.category == "data_fetch" for s in result)
        
        result = ScheduleService.filter_by_category(sample_schedules, "analysis")
        assert len(result) == 1
        assert result[0].category == "analysis"
    
    def test_filter_by_tags(self, sample_schedules):
        """タグによるフィルタリングテスト"""
        # いずれかのタグを持つ
        result = ScheduleService.filter_by_tags(sample_schedules, ["daily"])
        assert len(result) == 2
        
        result = ScheduleService.filter_by_tags(sample_schedules, ["daily", "weekly"])
        assert len(result) == 3
        
        # すべてのタグを持つ
        result = ScheduleService.filter_by_tags(
            sample_schedules, ["jquants", "daily"], match_all=True
        )
        assert len(result) == 1
        assert result[0].name == "data_fetch_daily"
    
    def test_filter_by_task_name(self, sample_schedules):
        """タスク名によるフィルタリングテスト"""
        result = ScheduleService.filter_by_task_name(sample_schedules, "fetch_listed_info")
        
        assert len(result) == 2
        assert all(s.task_name == "fetch_listed_info" for s in result)
    
    def test_find_auto_generated_schedules(self, sample_schedules):
        """自動生成スケジュールの検索テスト"""
        result = ScheduleService.find_auto_generated_schedules(sample_schedules)
        
        assert len(result) == 1
        assert result[0].name == "auto_report"
        assert result[0].is_auto_generated()
    
    def test_find_by_id(self, sample_schedules):
        """ID による検索テスト"""
        target_id = sample_schedules[0].id
        result = ScheduleService.find_by_id(sample_schedules, target_id)
        
        assert result is not None
        assert result.id == target_id
        
        # 存在しない ID
        result = ScheduleService.find_by_id(sample_schedules, uuid4())
        assert result is None
    
    def test_group_by_category(self, sample_schedules):
        """カテゴリ別グループ化テスト"""
        result = ScheduleService.group_by_category(sample_schedules)
        
        assert len(result) == 3
        assert "data_fetch" in result
        assert "analysis" in result
        assert "reporting" in result
        
        assert len(result["data_fetch"]) == 2
        assert len(result["analysis"]) == 1
        assert len(result["reporting"]) == 1
    
    def test_group_by_task_name(self, sample_schedules):
        """タスク名別グループ化テスト"""
        result = ScheduleService.group_by_task_name(sample_schedules)
        
        assert len(result) == 3
        assert "fetch_listed_info" in result
        assert "analyze_stocks" in result
        assert "generate_report" in result
        
        assert len(result["fetch_listed_info"]) == 2
    
    def test_validate_cron_expression(self):
        """Cron 式検証テスト"""
        # 有効な Cron 式
        assert ScheduleService.validate_cron_expression("0 9 * * *") is True
        assert ScheduleService.validate_cron_expression("*/5 * * * *") is True
        assert ScheduleService.validate_cron_expression("0 0 1 * *") is True
        
        # 無効な Cron 式
        assert ScheduleService.validate_cron_expression("0 9 * *") is False
        assert ScheduleService.validate_cron_expression("0 9 * * * *") is False
        assert ScheduleService.validate_cron_expression("") is False
    
    def test_apply_complex_filter(self, sample_schedules):
        """複雑なフィルタリングテスト"""
        # カテゴリとタグの組み合わせ
        result = ScheduleService.apply_complex_filter(
            sample_schedules,
            category="data_fetch",
            tags=["daily"]
        )
        assert len(result) == 1
        assert result[0].name == "data_fetch_daily"
        
        # 有効なスケジュールのみ
        result = ScheduleService.apply_complex_filter(
            sample_schedules,
            enabled_only=True
        )
        assert len(result) == 3  # enabled=True のスケジュール
        
        # タスク名と有効フィルタ
        result = ScheduleService.apply_complex_filter(
            sample_schedules,
            task_name="fetch_listed_info",
            enabled_only=True
        )
        assert len(result) == 2
        assert all(s.task_name == "fetch_listed_info" and s.enabled for s in result)
        
        # すべての条件
        result = ScheduleService.apply_complex_filter(
            sample_schedules,
            category="data_fetch",
            tags=["jquants"],
            task_name="fetch_listed_info",
            enabled_only=True
        )
        assert len(result) == 2
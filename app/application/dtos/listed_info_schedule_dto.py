"""listed_info スケジュール関連の DTO 定義"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.domain.validators.cron_validator import validate_cron_expression


class CreateListedInfoScheduleDTO(BaseModel):
    """listed_info スケジュール作成 DTO"""
    
    name: str = Field(..., description="スケジュール名", min_length=1, max_length=255)
    cron_expression: Optional[str] = Field(None, description="cron 式（プリセット使用時は省略可）")
    period_type: str = Field(..., description="期間タイプ（yesterday, 7days, 30days, custom）")
    description: Optional[str] = Field(None, description="スケジュールの説明", max_length=1000)
    enabled: bool = Field(True, description="有効フラグ")
    codes: Optional[List[str]] = Field(None, description="銘柄コードリスト")
    market: Optional[str] = Field(None, description="市場コード")
    preset_name: Optional[str] = Field(None, description="プリセット名")
    from_date: Optional[str] = Field(None, description="開始日 (YYYY-MM-DD) - period_type が custom の場合必須")
    to_date: Optional[str] = Field(None, description="終了日 (YYYY-MM-DD) - period_type が custom の場合必須")
    
    @validator("cron_expression")
    def validate_cron(cls, v: Optional[str], values: dict) -> Optional[str]:
        """cron 式の検証（プリセット使用時はスキップ）"""
        if v and not values.get("preset_name"):
            try:
                validate_cron_expression(v)
            except Exception as e:
                raise ValueError(str(e))
        return v
    
    @validator("period_type")
    def validate_period_type(cls, v: str) -> str:
        """期間タイプの検証"""
        valid_types = ["yesterday", "7days", "30days", "custom"]
        if v not in valid_types:
            raise ValueError(
                f"無効な period_type です: {v}. 有効な値: {', '.join(valid_types)}"
            )
        return v
    
    @validator("codes")
    def validate_codes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """銘柄コードの検証"""
        if v:
            for code in v:
                if not code or len(code) > 10:
                    raise ValueError(f"無効な銘柄コードです: {code}")
        return v
    
    @validator("to_date")
    def validate_custom_dates(cls, v: Optional[str], values: dict) -> Optional[str]:
        """custom period_type の場合の日付検証"""
        period_type = values.get("period_type")
        from_date = values.get("from_date")
        
        if period_type == "custom":
            if not from_date or not v:
                raise ValueError(
                    "period_type が 'custom' の場合、 from_date と to_date は必須です"
                )
            
            # 日付形式の検証
            try:
                from datetime import datetime
                datetime.strptime(from_date, "%Y-%m-%d")
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("日付は YYYY-MM-DD 形式で指定してください")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "daily_listed_info_fetch",
                "cron_expression": "0 9 * * *",
                "period_type": "yesterday",
                "description": "毎日 9 時に前日分のデータを取得",
                "enabled": True,
                "codes": [],
                "market": None,
                "preset_name": None
            }
        }


class UpdateListedInfoScheduleDTO(BaseModel):
    """listed_info スケジュール更新 DTO"""
    
    name: Optional[str] = Field(None, description="スケジュール名", min_length=1, max_length=255)
    cron_expression: Optional[str] = Field(None, description="cron 式")
    period_type: Optional[str] = Field(None, description="期間タイプ")
    description: Optional[str] = Field(None, description="スケジュールの説明", max_length=1000)
    enabled: Optional[bool] = Field(None, description="有効フラグ")
    codes: Optional[List[str]] = Field(None, description="銘柄コードリスト")
    market: Optional[str] = Field(None, description="市場コード")
    
    @validator("cron_expression")
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        """cron 式の検証"""
        if v:
            try:
                validate_cron_expression(v)
            except Exception as e:
                raise ValueError(str(e))
        return v
    
    @validator("period_type")
    def validate_period_type(cls, v: Optional[str]) -> Optional[str]:
        """期間タイプの検証"""
        if v:
            valid_types = ["yesterday", "7days", "30days", "custom"]
            if v not in valid_types:
                raise ValueError(
                    f"無効な period_type です: {v}. 有効な値: {', '.join(valid_types)}"
                )
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "enabled": False,
                "description": "一時的に無効化"
            }
        }


class ListedInfoScheduleDTO(BaseModel):
    """listed_info スケジュール情報 DTO"""
    
    id: UUID = Field(..., description="スケジュール ID")
    name: str = Field(..., description="スケジュール名")
    task_name: str = Field(..., description="タスク名")
    cron_expression: str = Field(..., description="cron 式")
    enabled: bool = Field(..., description="有効フラグ")
    kwargs: Dict = Field(..., description="タスクパラメータ")
    description: Optional[str] = Field(None, description="説明")
    category: Optional[str] = Field(None, description="カテゴリ")
    tags: List[str] = Field(default_factory=list, description="タグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    next_run_at: Optional[datetime] = Field(None, description="次回実行予定時刻")
    last_run_at: Optional[datetime] = Field(None, description="最終実行時刻")
    
    @property
    def period_type(self) -> Optional[str]:
        """kwargs から period_type を取得"""
        return self.kwargs.get("period_type")
    
    @property
    def codes(self) -> List[str]:
        """kwargs から codes を取得"""
        return self.kwargs.get("codes", [])
    
    @property
    def market(self) -> Optional[str]:
        """kwargs から market を取得"""
        return self.kwargs.get("market")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "daily_listed_info_fetch",
                "task_name": "fetch_listed_info_task",
                "cron_expression": "0 9 * * *",
                "enabled": True,
                "kwargs": {
                    "period_type": "yesterday",
                    "codes": [],
                    "market": None
                },
                "description": "毎日 9 時に前日分のデータを取得",
                "category": "listed_info",
                "tags": ["listed_info", "yesterday"],
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "next_run_at": "2024-01-02T09:00:00Z",
                "last_run_at": "2024-01-01T09:00:00Z"
            }
        }


class ListedInfoScheduleListDTO(BaseModel):
    """listed_info スケジュール一覧 DTO"""
    
    schedules: List[ListedInfoScheduleDTO] = Field(..., description="スケジュールリスト")
    total: int = Field(..., description="総件数")
    limit: int = Field(..., description="取得件数上限")
    offset: int = Field(..., description="オフセット")
    
    class Config:
        schema_extra = {
            "example": {
                "schedules": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "daily_listed_info_fetch",
                        "task_name": "fetch_listed_info_task",
                        "cron_expression": "0 9 * * *",
                        "enabled": True,
                        "kwargs": {
                            "period_type": "yesterday",
                            "codes": [],
                            "market": None
                        },
                        "description": "毎日 9 時に前日分のデータを取得",
                        "category": "listed_info",
                        "tags": ["listed_info", "yesterday"],
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                        "next_run_at": "2024-01-02T09:00:00Z",
                        "last_run_at": "2024-01-01T09:00:00Z"
                    }
                ],
                "total": 1,
                "limit": 100,
                "offset": 0
            }
        }


class ScheduleHistoryItemDTO(BaseModel):
    """スケジュール実行履歴アイテム DTO"""
    
    id: UUID = Field(..., description="実行 ID")
    schedule_id: UUID = Field(..., description="スケジュール ID")
    task_name: str = Field(..., description="タスク名")
    status: str = Field(..., description="実行ステータス")
    started_at: datetime = Field(..., description="開始時刻")
    completed_at: Optional[datetime] = Field(None, description="完了時刻")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")
    result_summary: Optional[Dict] = Field(None, description="実行結果サマリ")
    
    class Config:
        orm_mode = True


class ScheduleHistoryDTO(BaseModel):
    """スケジュール実行履歴 DTO"""
    
    schedule_id: UUID = Field(..., description="スケジュール ID")
    history: List[ScheduleHistoryItemDTO] = Field(..., description="実行履歴リスト")
    total: int = Field(..., description="総件数")
    limit: int = Field(..., description="取得件数上限")
    offset: int = Field(..., description="オフセット")
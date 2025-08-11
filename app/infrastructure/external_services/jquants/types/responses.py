"""J-Quants API response types."""
from typing import Optional, TypedDict


class JQuantsListedInfoResponse(TypedDict):
    """J-Quants 上場銘柄情報レスポンス型."""
    
    Date: str
    Code: str
    CompanyName: str
    CompanyNameEnglish: Optional[str]
    Sector17Code: Optional[str]
    Sector17CodeName: Optional[str]
    Sector33Code: Optional[str]
    Sector33CodeName: Optional[str]
    ScaleCategory: Optional[str]
    MarketCode: str
    MarketCodeName: str


class JQuantsListedInfoBulkResponse(TypedDict):
    """J-Quants 上場銘柄情報一括取得レスポンス型."""
    
    info: list[JQuantsListedInfoResponse]


class JQuantsPricesDailyQuotesResponse(TypedDict):
    """J-Quants 株価四本値レスポンス型."""
    
    Date: str
    Code: str
    Open: Optional[float]
    High: Optional[float]
    Low: Optional[float]
    Close: Optional[float]
    UpperLimit: Optional[float]
    LowerLimit: Optional[float]
    Volume: Optional[float]
    TurnoverValue: Optional[float]
    AdjustmentFactor: Optional[float]
    AdjustmentOpen: Optional[float]
    AdjustmentHigh: Optional[float]
    AdjustmentLow: Optional[float]
    AdjustmentClose: Optional[float]
    AdjustmentVolume: Optional[float]


class JQuantsPricesDailyQuotesBulkResponse(TypedDict):
    """J-Quants 株価四本値一括取得レスポンス型."""
    
    daily_quotes: list[JQuantsPricesDailyQuotesResponse]


class JQuantsFinStatementsResponse(TypedDict):
    """J-Quants 財務諸表レスポンス型."""
    
    DisclosedDate: str
    DisclosedTime: Optional[str]
    LocalCode: str
    DisclosureNumber: str
    TypeOfDocument: str
    TypeOfCurrentPeriod: str
    CurrentPeriodStartDate: Optional[str]
    CurrentPeriodEndDate: Optional[str]
    CurrentFiscalYearStartDate: Optional[str]
    CurrentFiscalYearEndDate: Optional[str]
    NextFiscalYearStartDate: Optional[str]
    NextFiscalYearEndDate: Optional[str]
    NetSales: Optional[float]
    OperatingProfit: Optional[float]
    OrdinaryProfit: Optional[float]
    Profit: Optional[float]
    EarningsPerShare: Optional[float]
    TotalAssets: Optional[float]
    Equity: Optional[float]
    EquityToAssetRatio: Optional[float]
    BookValuePerShare: Optional[float]


class JQuantsFinStatementsBulkResponse(TypedDict):
    """J-Quants 財務諸表一括取得レスポンス型."""
    
    statements: list[JQuantsFinStatementsResponse]
"""
Yahoo Finance client with rate limiting
"""

import asyncio
from typing import Any, Dict, List, Optional

import yfinance as yf

from app.domain.interfaces.rate_limiter import IRateLimiter


class YFinanceClient:
    """
    yfinance ライブラリのレート制限付きラッパー
    
    yfinance は HTTP クライアントを内部で管理しているため、
    レートリミッターを外部から適用する
    """
    
    def __init__(self, rate_limiter: IRateLimiter):
        """
        Args:
            rate_limiter: レート制限実装
        """
        self.rate_limiter = rate_limiter
    
    async def get_ticker_info(self, symbol: str) -> Dict[str, Any]:
        """
        銘柄情報を取得
        
        Args:
            symbol: 銘柄コード
            
        Returns:
            dict: 銘柄情報
        """
        await self.rate_limiter.wait_if_needed()
        
        try:
            # 同期関数を非同期で実行
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            await self.rate_limiter.record_request()
            return info
            
        except Exception:
            await self.rate_limiter.record_request()
            raise
    
    async def get_history(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        **kwargs: Any
    ) -> List[Dict[str, Any]]:
        """
        価格履歴を取得
        
        Args:
            symbol: 銘柄コード
            period: 期間（1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
            interval: 間隔（1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo）
            **kwargs: yfinance.history() に渡す追加引数
            
        Returns:
            list: 価格履歴データ
        """
        await self.rate_limiter.wait_if_needed()
        
        try:
            # 同期関数を非同期で実行
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            
            # history 関数を非同期で実行
            hist = await loop.run_in_executor(
                None,
                lambda: ticker.history(period=period, interval=interval, **kwargs)
            )
            
            # DataFrame を dict 形式に変換
            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.isoformat(),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            await self.rate_limiter.record_request()
            return data
            
        except Exception:
            await self.rate_limiter.record_request()
            raise
    
    async def download_batch(
        self,
        tickers: List[str],
        period: str = "1mo",
        interval: str = "1d",
        **kwargs: Any
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        複数銘柄のデータを一括取得
        
        Args:
            tickers: 銘柄コードのリスト
            period: 期間
            interval: 間隔
            **kwargs: yfinance.download() に渡す追加引数
            
        Returns:
            dict: 銘柄コードをキーとする価格履歴データ
        """
        # 複数銘柄の場合も 1 リクエストとしてカウント
        await self.rate_limiter.wait_if_needed()
        
        try:
            # 同期関数を非同期で実行
            loop = asyncio.get_event_loop()
            
            # yf.download を非同期で実行
            data = await loop.run_in_executor(
                None,
                lambda: yf.download(
                    tickers=tickers,
                    period=period,
                    interval=interval,
                    group_by='ticker',
                    **kwargs
                )
            )
            
            # データを整形
            result = {}
            for ticker in tickers:
                ticker_data = []
                
                if len(tickers) == 1:
                    # 単一銘柄の場合
                    hist = data
                else:
                    # 複数銘柄の場合
                    if ticker not in data.columns.levels[0]:
                        continue
                    hist = data[ticker]
                
                for date, row in hist.iterrows():
                    try:
                        ticker_data.append({
                            "date": date.isoformat(),
                            "open": float(row['Open']),
                            "high": float(row['High']),
                            "low": float(row['Low']),
                            "close": float(row['Close']),
                            "volume": int(row['Volume'])
                        })
                    except (KeyError, ValueError):
                        # データが欠損している場合はスキップ
                        continue
                
                if ticker_data:
                    result[ticker] = ticker_data
            
            await self.rate_limiter.record_request()
            return result
            
        except Exception:
            await self.rate_limiter.record_request()
            raise
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        現在のレート制限状態を取得
        
        Returns:
            dict: レート制限の状態情報
        """
        remaining = await self.rate_limiter.get_remaining_requests()
        reset_time = await self.rate_limiter.get_reset_time()
        
        return {
            "remaining_requests": remaining,
            "reset_time": reset_time,
            "is_limited": remaining == 0
        }
import time
import yfinance as yf
from typing import Dict, List, Optional
from celery import current_task
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def fetch_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> Dict:
    """株価データを取得するタスク"""
    print(f"Fetching stock data for {symbol}, period: {period}, interval: {interval}")
    
    try:
        # 進捗を更新
        self.update_state(
            state="PROGRESS",
            meta={"message": f"Fetching data for {symbol}..."}
        )
        
        # yfinanceを使用してデータを取得
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        # 進捗を更新
        self.update_state(
            state="PROGRESS",
            meta={"message": f"Processing data for {symbol}..."}
        )
        
        # データを整形
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
        
        result = {
            "symbol": symbol,
            "company_name": ticker.info.get('longName', symbol),
            "currency": ticker.info.get('currency', 'USD'),
            "period": period,
            "interval": interval,
            "data": data,
            "status": "success"
        }
        
        print(f"Stock data fetched successfully for {symbol}: {len(data)} records")
        return result
        
    except Exception as e:
        error_msg = f"Error fetching stock data for {symbol}: {str(e)}"
        print(error_msg)
        return {
            "symbol": symbol,
            "status": "error",
            "error": str(e)
        }

@celery_app.task(bind=True)
def fetch_multiple_stocks(self, symbols: List[str], period: str = "1mo") -> Dict:
    """複数の銘柄の株価データを取得するタスク"""
    print(f"Fetching data for multiple stocks: {symbols}")
    
    results = {}
    total_symbols = len(symbols)
    
    for i, symbol in enumerate(symbols):
        try:
            # 進捗を更新
            progress = (i / total_symbols) * 100
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": total_symbols,
                    "progress": progress,
                    "message": f"Processing {symbol} ({i+1}/{total_symbols})"
                }
            )
            
            # 個別のタスクを実行
            result = fetch_stock_data.delay(symbol, period)
            stock_data = result.get()
            
            results[symbol] = stock_data
            
            # レート制限を考慮して少し待機
            time.sleep(0.5)
            
        except Exception as e:
            results[symbol] = {
                "symbol": symbol,
                "status": "error",
                "error": str(e)
            }
    
    return {
        "status": "completed",
        "total_symbols": total_symbols,
        "results": results
    }

@celery_app.task(bind=True, max_retries=3)
def fetch_stock_data_with_retry(self, symbol: str, period: str = "1mo") -> Dict:
    """リトライ機能付きの株価データ取得タスク"""
    print(f"Fetching stock data with retry for {symbol}")
    
    try:
        result = fetch_stock_data.delay(symbol, period)
        return result.get()
        
    except Exception as e:
        print(f"Error fetching data for {symbol}, retrying... Error: {e}")
        raise self.retry(countdown=10, exc=e)

@celery_app.task(bind=True)
def analyze_stock_data(self, symbol: str, period: str = "1mo") -> Dict:
    """株価データを分析するタスク"""
    print(f"Analyzing stock data for {symbol}")
    
    try:
        # データを取得
        data_result = fetch_stock_data.delay(symbol, period)
        stock_data = data_result.get()
        
        if stock_data.get("status") == "error":
            return stock_data
        
        data = stock_data["data"]
        
        if not data:
            return {
                "symbol": symbol,
                "status": "error",
                "error": "No data available for analysis"
            }
        
        # 基本的な分析を実行
        prices = [d["close"] for d in data]
        
        analysis = {
            "symbol": symbol,
            "status": "success",
            "analysis": {
                "current_price": prices[-1],
                "price_change": prices[-1] - prices[0],
                "price_change_percent": ((prices[-1] - prices[0]) / prices[0]) * 100,
                "highest_price": max(prices),
                "lowest_price": min(prices),
                "average_price": sum(prices) / len(prices),
                "volatility": (max(prices) - min(prices)) / min(prices) * 100,
                "data_points": len(data)
            }
        }
        
        print(f"Analysis completed for {symbol}")
        return analysis
        
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "error": str(e)
        }

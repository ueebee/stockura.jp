from .jquants_strategy import JQuantsStrategy
from .yfinance_strategy import YFinanceStrategy
from .. import StrategyRegistry

# ストラテジーの登録
StrategyRegistry.register("jquants", JQuantsStrategy)
StrategyRegistry.register("yfinance", YFinanceStrategy) 
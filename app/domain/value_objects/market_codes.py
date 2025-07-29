"""Market and sector code enums."""
from enum import Enum


class MarketCode(Enum):
    """市場区分コード"""

    PRIME = "0101"  # プライム市場
    STANDARD = "0102"  # スタンダード市場
    GROWTH = "0103"  # グロース市場
    OTHERS = "0104"  # その他
    PRE_PRIME = "0105"  # プライム市場（内国株式以外）
    PRE_STANDARD = "0106"  # スタンダード市場（内国株式以外）
    PRE_GROWTH = "0107"  # グロース市場（内国株式以外）
    PRO_MARKET = "0108"  # PRO Market
    OLD_TSE1 = "0109"  # 東証 1 部（旧）
    OLD_TSE2 = "0110"  # 東証 2 部（旧）
    OLD_MOTHERS = "0111"  # マザーズ（旧）
    OLD_JASDAQ_STANDARD = "0112"  # JASDAQ スタンダード（旧）
    OLD_JASDAQ_GROWTH = "0113"  # JASDAQ グロース（旧）


class SectorCode17(Enum):
    """17 業種コード"""

    FOODS = "1"  # 食品
    ENERGY_RESOURCES = "2"  # エネルギー資源
    CONSTRUCTION_MATERIALS = "3"  # 建設・資材
    MATERIALS_CHEMICALS = "4"  # 素材・化学
    PHARMACEUTICALS = "5"  # 医薬品
    AUTOMOBILES_TRANSPORTATION = "6"  # 自動車・輸送機
    STEEL_NONFERROUS = "7"  # 鉄鋼・非鉄
    MACHINERY = "8"  # 機械
    ELECTRICAL_PRECISION = "9"  # 電機・精密
    IT_COMMUNICATIONS_SERVICES = "10"  # 情報通信・サービスその他
    ELECTRIC_GAS = "11"  # 電気・ガス
    TRANSPORTATION_LOGISTICS = "12"  # 運輸・物流
    WHOLESALE_TRADE = "13"  # 卸売
    RETAIL_TRADE = "14"  # 小売
    BANKS = "15"  # 銀行
    FINANCIAL_EXCL_BANKS = "16"  # 金融（除く銀行）
    REAL_ESTATE = "17"  # 不動産


class SectorCode33(Enum):
    """33 業種コード"""

    FISHERY_AGRICULTURE_FORESTRY = "0050"  # 水産・農林業
    MINING = "1050"  # 鉱業
    CONSTRUCTION = "2050"  # 建設業
    FOODS = "3050"  # 食料品
    TEXTILES_APPARELS = "3100"  # 繊維製品
    PULP_PAPER = "3150"  # パルプ・紙
    CHEMICALS = "3200"  # 化学
    PHARMACEUTICAL = "3250"  # 医薬品
    OIL_COAL_PRODUCTS = "3300"  # 石油・石炭製品
    RUBBER_PRODUCTS = "3350"  # ゴム製品
    GLASS_CERAMICS_PRODUCTS = "3400"  # ガラス・土石製品
    IRON_STEEL = "3450"  # 鉄鋼
    NONFERROUS_METALS = "3500"  # 非鉄金属
    METAL_PRODUCTS = "3550"  # 金属製品
    MACHINERY = "3600"  # 機械
    ELECTRIC_APPLIANCES = "3650"  # 電気機器
    TRANSPORTATION_EQUIPMENT = "3700"  # 輸送用機器
    PRECISION_INSTRUMENTS = "3750"  # 精密機器
    OTHER_PRODUCTS = "3800"  # その他製品
    ELECTRIC_POWER_GAS = "4050"  # 電気・ガス業
    LAND_TRANSPORTATION = "5050"  # 陸運業
    MARINE_TRANSPORTATION = "5100"  # 海運業
    AIR_TRANSPORTATION = "5150"  # 空運業
    WAREHOUSING_HARBOR_TRANSPORTATION = "5200"  # 倉庫・運輸関連業
    INFORMATION_COMMUNICATION = "5250"  # 情報・通信業
    WHOLESALE_TRADE = "6050"  # 卸売業
    RETAIL_TRADE = "6100"  # 小売業
    BANKS = "7050"  # 銀行業
    SECURITIES_COMMODITY_FUTURES = "7100"  # 証券、商品先物取引業
    INSURANCE = "7150"  # 保険業
    OTHER_FINANCING_BUSINESS = "7200"  # その他金融業
    REAL_ESTATE = "8050"  # 不動産業
    SERVICES = "9050"  # サービス業
"""insert_master_data

Revision ID: 8aff57aa15b6
Revises: c2e3a9be79f7
Create Date: 2025-06-26 09:54:14.699041

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '8aff57aa15b6'
down_revision: Union[str, None] = 'c2e3a9be79f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    current_time = datetime.utcnow()
    
    # 市場マスターデータの投入
    connection.execute(text("""
        INSERT INTO market_masters (code, name, name_english, description, display_order, is_active, created_at, updated_at) VALUES
        ('0101', '東証1部', 'Tokyo Stock Exchange 1st Section', '東京証券取引所第一部（旧制度）', 1, true, :created_at, :updated_at),
        ('0102', '東証2部', 'Tokyo Stock Exchange 2nd Section', '東京証券取引所第二部（旧制度）', 2, true, :created_at, :updated_at),
        ('0104', 'マザーズ', 'Mothers', '東証マザーズ（旧制度）', 3, true, :created_at, :updated_at),
        ('0105', 'TOKYO PRO MARKET', 'TOKYO PRO MARKET', '東京プロマーケット', 4, true, :created_at, :updated_at),
        ('0106', 'JASDAQ(スタンダード)', 'JASDAQ Standard', 'JASDAQスタンダード', 5, true, :created_at, :updated_at),
        ('0107', 'JASDAQ(グロース)', 'JASDAQ Growth', 'JASDAQグロース', 6, true, :created_at, :updated_at),
        ('0109', 'その他', 'Others', 'その他の市場', 7, true, :created_at, :updated_at),
        ('0111', 'プライム', 'Prime', '東証プライム市場', 8, true, :created_at, :updated_at),
        ('0112', 'スタンダード', 'Standard', '東証スタンダード市場', 9, true, :created_at, :updated_at),
        ('0113', 'グロース', 'Growth', '東証グロース市場', 10, true, :created_at, :updated_at)
    """), {"created_at": current_time, "updated_at": current_time})
    
    # 17業種マスターデータの投入
    connection.execute(text("""
        INSERT INTO sector17_masters (code, name, name_english, description, display_order, is_active, created_at, updated_at) VALUES
        ('1', '食品', 'Food', '食品関連業種', 1, true, :created_at, :updated_at),
        ('2', 'エネルギー資源', 'Energy Resources', 'エネルギー・資源関連業種', 2, true, :created_at, :updated_at),
        ('3', '建設・資材', 'Construction & Materials', '建設・資材関連業種', 3, true, :created_at, :updated_at),
        ('4', '素材・化学', 'Materials & Chemicals', '素材・化学関連業種', 4, true, :created_at, :updated_at),
        ('5', '医薬品', 'Pharmaceuticals', '医薬品関連業種', 5, true, :created_at, :updated_at),
        ('6', '自動車・輸送機', 'Automobiles & Transportation Equipment', '自動車・輸送機器関連業種', 6, true, :created_at, :updated_at),
        ('7', '鉄鋼・非鉄', 'Steel & Non-Ferrous Metals', '鉄鋼・非鉄金属関連業種', 7, true, :created_at, :updated_at),
        ('8', '機械', 'Machinery', '機械関連業種', 8, true, :created_at, :updated_at),
        ('9', '電機・精密', 'Electronics & Precision Instruments', '電機・精密機器関連業種', 9, true, :created_at, :updated_at),
        ('10', '情報通信・サービスその他', 'Information & Communication Services, Others', '情報通信・サービス・その他関連業種', 10, true, :created_at, :updated_at),
        ('11', '電気・ガス', 'Electricity & Gas', '電気・ガス関連業種', 11, true, :created_at, :updated_at),
        ('12', '運輸・物流', 'Transportation & Logistics', '運輸・物流関連業種', 12, true, :created_at, :updated_at),
        ('13', '商社・卸売', 'Trading Companies & Wholesale', '商社・卸売関連業種', 13, true, :created_at, :updated_at),
        ('14', '小売', 'Retail', '小売関連業種', 14, true, :created_at, :updated_at),
        ('15', '銀行', 'Banking', '銀行関連業種', 15, true, :created_at, :updated_at),
        ('16', '金融（除く銀行）', 'Financial Services, excluding Banking', '金融（銀行除く）関連業種', 16, true, :created_at, :updated_at),
        ('17', '不動産', 'Real Estate', '不動産関連業種', 17, true, :created_at, :updated_at),
        ('99', 'その他', 'Others', 'その他業種', 99, true, :created_at, :updated_at)
    """), {"created_at": current_time, "updated_at": current_time})
    
    # 33業種マスターデータの投入
    connection.execute(text("""
        INSERT INTO sector33_masters (code, name, name_english, description, sector17_code, display_order, is_active, created_at, updated_at) VALUES
        ('0050', '水産・農林業', 'Fisheries and Forestry', '水産業・農林業', '1', 1, true, :created_at, :updated_at),
        ('1050', '鉱業', 'Mining', '鉱業', '2', 2, true, :created_at, :updated_at),
        ('2050', '建設業', 'Construction', '建設業', '3', 3, true, :created_at, :updated_at),
        ('3050', '食料品', 'Food Products', '食料品製造業', '1', 4, true, :created_at, :updated_at),
        ('3100', '繊維製品', 'Textile Products', '繊維製品製造業', '4', 5, true, :created_at, :updated_at),
        ('3150', 'パルプ・紙', 'Pulp and Paper', 'パルプ・紙製造業', '4', 6, true, :created_at, :updated_at),
        ('3200', '化学', 'Chemicals', '化学工業', '4', 7, true, :created_at, :updated_at),
        ('3250', '医薬品', 'Pharmaceuticals', '医薬品製造業', '5', 8, true, :created_at, :updated_at),
        ('3300', '石油・石炭製品', 'Petroleum and Coal Products', '石油・石炭製品製造業', '2', 9, true, :created_at, :updated_at),
        ('3350', 'ゴム製品', 'Rubber Products', 'ゴム製品製造業', '4', 10, true, :created_at, :updated_at),
        ('3400', 'ガラス・土石製品', 'Glass and Ceramic Products', 'ガラス・土石製品製造業', '3', 11, true, :created_at, :updated_at),
        ('3450', '鉄鋼', 'Iron and Steel', '鉄鋼業', '7', 12, true, :created_at, :updated_at),
        ('3500', '非鉄金属', 'Non-Ferrous Metals', '非鉄金属製造業', '7', 13, true, :created_at, :updated_at),
        ('3550', '金属製品', 'Metal Products', '金属製品製造業', '7', 14, true, :created_at, :updated_at),
        ('3600', '機械', 'Machinery', '機械製造業', '8', 15, true, :created_at, :updated_at),
        ('3650', '電気機器', 'Electrical Machinery', '電気機器製造業', '9', 16, true, :created_at, :updated_at),
        ('3700', '輸送用機器', 'Transportation Equipment', '輸送用機器製造業', '6', 17, true, :created_at, :updated_at),
        ('3750', '精密機器', 'Precision Instruments', '精密機器製造業', '9', 18, true, :created_at, :updated_at),
        ('3800', 'その他製品', 'Other Products', 'その他製品製造業', '10', 19, true, :created_at, :updated_at),
        ('4050', '電気・ガス業', 'Electric Power and Gas', '電気・ガス業', '11', 20, true, :created_at, :updated_at),
        ('5050', '陸運業', 'Land Transportation', '陸運業', '12', 21, true, :created_at, :updated_at),
        ('5100', '海運業', 'Marine Transportation', '海運業', '12', 22, true, :created_at, :updated_at),
        ('5150', '空運業', 'Air Transportation', '空運業', '12', 23, true, :created_at, :updated_at),
        ('5200', '倉庫・運輸関連業', 'Warehousing and Transportation', '倉庫・運輸関連業', '12', 24, true, :created_at, :updated_at),
        ('5250', '情報・通信業', 'Information and Communications', '情報・通信業', '10', 25, true, :created_at, :updated_at),
        ('6050', '卸売業', 'Wholesale Trade', '卸売業', '13', 26, true, :created_at, :updated_at),
        ('6100', '小売業', 'Retail Trade', '小売業', '14', 27, true, :created_at, :updated_at),
        ('7050', '銀行業', 'Banking', '銀行業', '15', 28, true, :created_at, :updated_at),
        ('7100', '証券・商品先物取引業', 'Securities and Commodity Futures', '証券・商品先物取引業', '16', 29, true, :created_at, :updated_at),
        ('7150', '保険業', 'Insurance', '保険業', '16', 30, true, :created_at, :updated_at),
        ('7200', 'その他金融業', 'Other Financial Services', 'その他金融業', '16', 31, true, :created_at, :updated_at),
        ('8050', '不動産業', 'Real Estate', '不動産業', '17', 32, true, :created_at, :updated_at),
        ('9050', 'サービス業', 'Services', 'サービス業', '10', 33, true, :created_at, :updated_at),
        ('9999', 'その他', 'Others', 'その他の業種', '99', 34, true, :created_at, :updated_at)
    """), {"created_at": current_time, "updated_at": current_time})


def downgrade() -> None:
    connection = op.get_bind()
    
    # 33業種マスターデータの削除
    connection.execute(text("DELETE FROM sector33_masters"))
    
    # 17業種マスターデータの削除  
    connection.execute(text("DELETE FROM sector17_masters"))
    
    # 市場マスターデータの削除
    connection.execute(text("DELETE FROM market_masters"))

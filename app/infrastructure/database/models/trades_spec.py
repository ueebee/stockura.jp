"""投資部門別売買状況データベースモデル"""
from sqlalchemy import Column, Date, String, BigInteger, DateTime, Index, PrimaryKeyConstraint
from sqlalchemy.sql import func

from app.infrastructure.database.connection import Base


class TradesSpecModel(Base):
    """投資部門別売買状況 SQLAlchemy モデル"""
    
    __tablename__ = "trades_spec"
    __table_args__ = (
        PrimaryKeyConstraint("code", "trade_date"),
        Index("idx_trades_spec_code", "code"),
        Index("idx_trades_spec_date", "trade_date"),
        Index("idx_trades_spec_section", "section"),
        Index("idx_trades_spec_date_section", "trade_date", "section"),
    )
    
    # 基本情報
    code = Column(String(10), nullable=False)  # 銘柄コード
    trade_date = Column(Date, nullable=False)  # 取引日
    section = Column(String(50), nullable=True)  # 市場区分
    
    # 自己勘定（証券会社）
    sales_proprietary = Column(BigInteger, nullable=True)  # 売り（千円）
    purchases_proprietary = Column(BigInteger, nullable=True)  # 買い（千円）
    balance_proprietary = Column(BigInteger, nullable=True)  # 差引き（千円）
    
    # 委託（個人）
    sales_consignment_individual = Column(BigInteger, nullable=True)  # 売り（千円）
    purchases_consignment_individual = Column(BigInteger, nullable=True)  # 買い（千円）
    balance_consignment_individual = Column(BigInteger, nullable=True)  # 差引き（千円）
    
    # 委託（法人）
    sales_consignment_corporate = Column(BigInteger, nullable=True)  # 売り（千円）
    purchases_consignment_corporate = Column(BigInteger, nullable=True)  # 買い（千円）
    balance_consignment_corporate = Column(BigInteger, nullable=True)  # 差引き（千円）
    
    # 委託（投資信託）
    sales_consignment_investment_trust = Column(BigInteger, nullable=True)  # 売り（千円）
    purchases_consignment_investment_trust = Column(BigInteger, nullable=True)  # 買い（千円）
    balance_consignment_investment_trust = Column(BigInteger, nullable=True)  # 差引き（千円）
    
    # 委託（外国人）
    sales_consignment_foreign = Column(BigInteger, nullable=True)  # 売り（千円）
    purchases_consignment_foreign = Column(BigInteger, nullable=True)  # 買い（千円）
    balance_consignment_foreign = Column(BigInteger, nullable=True)  # 差引き（千円）
    
    # 委託（その他法人）
    sales_consignment_other_corporate = Column(BigInteger, nullable=True)  # 売り（千円）
    purchases_consignment_other_corporate = Column(BigInteger, nullable=True)  # 買い（千円）
    balance_consignment_other_corporate = Column(BigInteger, nullable=True)  # 差引き（千円）
    
    # 委託（その他）
    sales_consignment_other = Column(BigInteger, nullable=True)  # 売り（千円）
    purchases_consignment_other = Column(BigInteger, nullable=True)  # 買い（千円）
    balance_consignment_other = Column(BigInteger, nullable=True)  # 差引き（千円）
    
    # 合計
    sales_total = Column(BigInteger, nullable=True)  # 売り合計（千円）
    purchases_total = Column(BigInteger, nullable=True)  # 買い合計（千円）
    balance_total = Column(BigInteger, nullable=True)  # 差引き合計（千円）
    
    # タイムスタンプ
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        """文字列表現"""
        return f"<TradesSpecModel(code='{self.code}', trade_date='{self.trade_date}', section='{self.section}')>"
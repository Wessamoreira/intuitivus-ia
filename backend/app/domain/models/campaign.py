from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.db.database import Base

class CampaignStatus(str, enum.Enum):
    """Status da campanha"""
    DRAFT = "draft"          # Rascunho
    ACTIVE = "active"        # Ativa
    PAUSED = "paused"        # Pausada
    COMPLETED = "completed"  # Finalizada
    CANCELLED = "cancelled"  # Cancelada

class CampaignPlatform(str, enum.Enum):
    """Plataforma da campanha"""
    GOOGLE_ADS = "google_ads"
    META_ADS = "meta_ads"
    TIKTOK_ADS = "tiktok_ads"
    LINKEDIN_ADS = "linkedin_ads"

class Campaign(Base):
    """Modelo de campanha de marketing"""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configurações da campanha
    platform = Column(Enum(CampaignPlatform), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    
    # Orçamento
    budget_total = Column(String(20), nullable=True)    # Orçamento total
    budget_daily = Column(String(20), nullable=True)    # Orçamento diário
    spent_amount = Column(String(20), default="0.00")   # Valor gasto
    
    # Datas
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Configurações específicas da plataforma
    platform_config = Column(JSON, nullable=True)  # Configurações específicas
    targeting = Column(JSON, nullable=True)         # Configurações de segmentação
    creatives = Column(JSON, nullable=True)         # Criativos (textos, imagens)
    
    # IDs externos
    external_campaign_id = Column(String(255), nullable=True)  # ID na plataforma
    external_account_id = Column(String(255), nullable=True)   # ID da conta
    
    # Métricas
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    ctr = Column(String(10), default="0.00")    # Click-through rate
    cpc = Column(String(20), default="0.00")    # Cost per click
    roas = Column(String(10), default="0.00")   # Return on ad spend
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="campaigns")
    
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    agent = relationship("Agent")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name='{self.name}', platform='{self.platform}')>"
    
    @property
    def budget_remaining(self) -> float:
        """Calcula o orçamento restante"""
        if not self.budget_total:
            return 0.0
        return float(self.budget_total) - float(self.spent_amount)

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProviderRefreshRun(Base):
    __tablename__ = "provider_refresh_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    sport: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    quota_remaining: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(180), primary_key=True)
    sport: Mapped[str] = mapped_column(String(20), nullable=False)
    league: Mapped[str] = mapped_column(String(120), nullable=False)
    home_team: Mapped[str] = mapped_column(String(160), nullable=False)
    away_team: Mapped[str] = mapped_column(String(160), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProviderEventMapping(Base):
    __tablename__ = "provider_event_mappings"
    __table_args__ = (
        Index("ix_provider_event_mappings_provider_raw", "provider", "provider_event_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(180), nullable=False)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OfferObservation(Base):
    __tablename__ = "offer_observations"
    __table_args__ = (
        Index(
            "ix_offer_observations_event_market_bookmaker_time",
            "event_id",
            "market_type",
            "bookmaker",
            "observed_at",
        ),
        Index("ix_offer_observations_event_market", "event_id", "market_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    bookmaker: Mapped[str] = mapped_column(String(120), nullable=False)
    market_type: Mapped[str] = mapped_column(String(80), nullable=False)
    selection: Mapped[str] = mapped_column(String(180), nullable=False)
    line: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_american: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    price_decimal: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    player_name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    provider_offer_id: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    provider_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deep_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
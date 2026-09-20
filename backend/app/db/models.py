from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase): pass

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    league_id: Mapped[int] = mapped_column(Integer, index=True)
    league_name: Mapped[str] = mapped_column(String(120))
    season: Mapped[int] = mapped_column(Integer)
    kickoff: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    home_team: Mapped[str] = mapped_column(String(120))
    away_team: Mapped[str] = mapped_column(String(120))
    home_logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    away_logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_corners: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_corners: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_xg: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("external_id", name="uq_match_external"),)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(Integer, index=True)
    model_version: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class ModelRun(Base):
    __tablename__ = "model_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(100), unique=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    rows: Mapped[int] = mapped_column(Integer)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    successful: Mapped[bool] = mapped_column(Boolean, default=True)

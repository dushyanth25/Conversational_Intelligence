from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

class Call(Base):
    __tablename__ = "calls"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    audio_path: Mapped[Optional[str]] = mapped_column(String(1024))
    duration: Mapped[Optional[float]] = mapped_column(Float)
    language: Mapped[Optional[str]] = mapped_column(String(10))
    speaker_count: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="PROCESSING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    transcript_segments: Mapped[List["TranscriptSegment"]] = relationship(back_populates="call", cascade="all, delete-orphan")
    insights: Mapped[List["Insight"]] = relationship(back_populates="call", cascade="all, delete-orphan")

class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[str] = mapped_column(ForeignKey("calls.call_id"))
    start_time: Mapped[float] = mapped_column(Float)
    end_time: Mapped[float] = mapped_column(Float)
    speaker_id: Mapped[str] = mapped_column(String(100))
    speaker_role: Mapped[Optional[str]] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(String)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    call: Mapped["Call"] = relationship(back_populates="transcript_segments")
    
    __table_args__ = (
        Index("ix_transcript_segments_call_id", "call_id"),
        Index("ix_transcript_segments_start_time", "start_time"),
    )

class Insight(Base):
    __tablename__ = "insights"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[str] = mapped_column(ForeignKey("calls.call_id"))
    parameter: Mapped[str] = mapped_column(String(255))
    result: Mapped[Any] = mapped_column(JSONB)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    call: Mapped["Call"] = relationship(back_populates="insights")
    evidence: Mapped[List["InsightEvidence"]] = relationship(back_populates="insight", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("call_id", "parameter", name="uq_insight_call_parameter"),
    )

class InsightEvidence(Base):
    __tablename__ = "insight_evidence"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    insight_id: Mapped[int] = mapped_column(ForeignKey("insights.id", ondelete="CASCADE"))
    timestamp: Mapped[Optional[str]] = mapped_column(String(50))
    speaker: Mapped[Optional[str]] = mapped_column(String(100))
    text: Mapped[str] = mapped_column(String)
    segment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("transcript_segments.id", ondelete="SET NULL"))
    
    insight: Mapped["Insight"] = relationship(back_populates="evidence")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    call_id: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    error_type: Mapped[Optional[str]] = mapped_column(String(255))
    error_message: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BatchRun(Base):
    __tablename__ = "batch_runs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    call_id: Mapped[str] = mapped_column(String(255), index=True)
    batch_id: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("call_id", "batch_id", name="uq_batch_run_call_batch"),
    )

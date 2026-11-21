from datetime import datetime
from sqlalchemy import (DateTime, Float, ForeignKey, Index, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), unique=True)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        UniqueConstraint("repository_id", "github_run_id", "run_attempt"),
        Index("ix_runs_repo_sha", "repository_id", "head_sha"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    github_run_id: Mapped[int]
    run_attempt: Mapped[int]
    head_sha: Mapped[str] = mapped_column(String(40))
    branch: Mapped[str] = mapped_column(String(200))
    event: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime)

    outcomes: Mapped[list["CaseOutcome"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class CaseOutcome(Base):
    __tablename__ = "case_outcomes"
    __table_args__ = (
        UniqueConstraint("run_id", "test_id"),
        Index("ix_outcomes_test", "test_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"))
    test_id: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(10))
    # passed/failed/error/skipped
    duration: Mapped[float] = mapped_column(Float)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    run: Mapped[WorkflowRun] = relationship(back_populates="outcomes")

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from .models import CaseOutcome, Repository, WorkflowRun
from .parser import CaseResult


@dataclass(frozen=True)
class RunInfo:
    github_run_id: int
    run_attempt: int
    head_sha: str
    branch: str
    event: str
    created_at: datetime


def get_or_create_repo(session: Session, full_name: str) -> Repository:
    repo = session.scalar(select(Repository).where(
        Repository.full_name == full_name))
    if repo is None:
        repo = Repository(full_name=full_name)
        session.add(repo)
        session.flush()
    return repo


def ingest_report(
    session: Session, repo_full_name: str, run: RunInfo,
    results: list[CaseResult]
) -> bool:
    """Store one run. Returns False if this run attempt was already stored."""
    repo = get_or_create_repo(session, repo_full_name)

    existing = session.scalar(
        select(WorkflowRun).where(
            WorkflowRun.repository_id == repo.id,
            WorkflowRun.github_run_id == run.github_run_id,
            WorkflowRun.run_attempt == run.run_attempt,
        )
    )
    if existing is not None:
        return False  # duplicate delivery, safely ignored

    # If a report lists the same test_id twice, keep the last one
    unique = {r.test_id: r for r in results}

    wr = WorkflowRun(
        repository_id=repo.id,
        github_run_id=run.github_run_id,
        run_attempt=run.run_attempt,
        head_sha=run.head_sha,
        branch=run.branch,
        event=run.event,
        created_at=run.created_at,
        outcomes=[
            CaseOutcome(
                test_id=r.test_id, status=r.status, duration=r.duration,
                message=r.message
            )
            for r in unique.values()
        ],
    )
    session.add(wr)
    session.commit()
    return True


def same_commit_conflicts(
        session: Session, repo_full_name: str) -> dict[str, int]:
    """For each test: on how many commits did it both pass AND fail?"""
    conflicts = (
        select(CaseOutcome.test_id, WorkflowRun.head_sha)
        .join(WorkflowRun, CaseOutcome.run_id == WorkflowRun.id)
        .join(Repository, WorkflowRun.repository_id == Repository.id)
        .where(
            Repository.full_name == repo_full_name,
            CaseOutcome.status.in_(["passed", "failed"]),
        )
        .group_by(CaseOutcome.test_id, WorkflowRun.head_sha)
        .having(func.count(distinct(CaseOutcome.status)) == 2)
        .subquery()
    )
    rows = session.execute(
        select(conflicts.c.test_id, func.count()).group_by(conflicts.c.test_id)
    ).all()
    return dict(rows)

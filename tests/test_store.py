from datetime import datetime
from flaky_detective.db import make_session_factory
from flaky_detective.parser import CaseResult
from flaky_detective.store import RunInfo, ingest_report, same_commit_conflicts

T0 = datetime(2026, 11, 20, 10, 0)


def results(*pairs):
    return [
        CaseResult(
            test_id=t, classname="c", name=t, status=s,
            duration=0.1, message=None)
        for t, s in pairs
    ]


def test_duplicate_run_is_ignored():
    Session = make_session_factory("sqlite://")
    with Session() as s:
        run = RunInfo(1, 1, "abc", "main", "push", T0)
        assert ingest_report(
            s, "acme/shop", run, results(("t1", "passed"))) is True
        assert ingest_report(
            s, "acme/shop", run, results(("t1", "passed"))) is False


def test_same_commit_conflict_detected():
    Session = make_session_factory("sqlite://")
    with Session() as s:
        # attempt 1 fails, re-run (attempt 2) passes, same commit
        ingest_report(s, "acme/shop", RunInfo(1, 1, "abc", "main", "push", T0),
                      results(("t_flaky", "failed"), ("t_stable", "passed")))
        ingest_report(s, "acme/shop", RunInfo(1, 2, "abc", "main", "push", T0),
                      results(("t_flaky", "passed"), ("t_stable", "passed")))

        assert same_commit_conflicts(
            s, "acme/shop") == {"t_flaky": 1}

from dataclasses import dataclass
from pathlib import Path
from defusedxml import ElementTree as ET


@dataclass(frozen=True)
class CaseResult:
    test_id: str
    # "tests.test_flaky::test_random_failure_20_percent"
    classname: str
    name: str
    status: str             # "passed" | "failed" | "error" | "skipped"
    duration: float         # seconds
    message: str | None     # short error message, if any


def parse_junit(path: str | Path) -> list[CaseResult]:
    root = ET.parse(path).getroot()
    results: list[CaseResult] = list()
    for case in root.iter("testcase"):
        classname = case.get("classname", "")
        name = case.get("name", "")

        status = "passed"
        message = None
        for tag, label in (("failure", "failed"), ("error", "error"),
                           ("skipped", "skipped")):
            node = case.find(tag)
            if node is not None:
                status = label
                message = node.get("message")
                break

        results.append(
            CaseResult(
                test_id=f"{classname}::{name}",
                classname=classname,
                name=name,
                status=status,
                duration=float(case.get("time", 0.0)),
                message=message,
            )
        )
    return results

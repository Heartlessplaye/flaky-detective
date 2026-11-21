from flaky_detective.parser import parse_junit

sample = """<?xml version="1.0" encoding="utf-8"?>
<testsuites>
  <testsuite name="pytest" tests="4">
    <testcase classname="tests.test_a" name="test_ok" time="0.01"/>
    <testcase classname="tests.test_a" name="test_bad" time="0.02">
      <failure message="assert 1 == 2">traceback</failure>
    </testcase>
    <testcase classname="tests.test_a" name="test_crash" time="0.03">
      <error message="fixture failed">traceback</error>
    </testcase>
    <testcase classname="tests.test_a" name="test_skip" time="0.00">
      <skipped message="not today"/>
    </testcase>
  </testsuite>
</testsuites>
"""


def test_parses_all_statuses(tmp_path):
    f = tmp_path / "report.xml"
    f.write_text(sample)

    results = {r.name: r for r in parse_junit(f)}

    assert results["test_ok"].status == "passed"
    assert results["test_bad"].status == "failed"
    assert results["test_bad"].message == "assert 1 == 2"
    assert results["test_crash"].status == "error"
    assert results["test_skip"].status == "skipped"
    assert results["test_ok"].test_id == "tests.test_a::test_ok"

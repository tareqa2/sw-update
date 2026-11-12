"""Push pytest results (JUnit XML) to a Prometheus Pushgateway, so Grafana can show them.

Prometheus *pulls* metrics and cannot reach CI machines, so test jobs *push* their
latest result to the Pushgateway, and Prometheus scrapes the Pushgateway.

Each suite gets its own group (job="sw_update_tests", suite="<name>"); a new push
replaces the previous result for that suite.

Uses only the Python standard library.

    python scripts/push_test_results.py --url http://pushgateway.monitoring.svc.cluster.local:9091 \\
        --suite sanity --junit sanity-report.xml --commit a18accf
"""
import argparse
import time
import urllib.request
import xml.etree.ElementTree as ET


def read_junit(path):
    root = ET.parse(path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    return {
        "passed": total - failed - errors - skipped,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "duration": float(suite.get("time", 0.0)),
    }


def to_exposition(result, commit):
    """Prometheus text format. Gauges, because each push is a snapshot of the latest run."""
    lines = [
        "# TYPE swupdate_tests gauge",
        "# HELP swupdate_tests Test cases in the latest run, by result",
    ]
    for key in ("passed", "failed", "errors", "skipped"):
        lines.append(f'swupdate_tests{{result="{key}",commit="{commit}"}} {result[key]}')
    ok = 1 if result["failed"] == 0 and result["errors"] == 0 else 0
    lines += [
        "# TYPE swupdate_tests_success gauge",
        "# HELP swupdate_tests_success 1 if the latest run had no failures or errors",
        f'swupdate_tests_success{{commit="{commit}"}} {ok}',
        "# TYPE swupdate_tests_duration_seconds gauge",
        f'swupdate_tests_duration_seconds{{commit="{commit}"}} {result["duration"]:.3f}',
        "# TYPE swupdate_tests_last_run_timestamp_seconds gauge",
        f'swupdate_tests_last_run_timestamp_seconds{{commit="{commit}"}} {int(time.time())}',
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--url", required=True, help="Pushgateway base URL")
    ap.add_argument("--suite", required=True, choices=["sanity", "regression", "e2e"])
    ap.add_argument("--junit", required=True, help="pytest --junitxml report file")
    ap.add_argument("--commit", default="local", help="commit SHA the tests ran against")
    args = ap.parse_args()

    result = read_junit(args.junit)
    body = to_exposition(result, args.commit).encode()
    # PUT replaces every metric in this suite's group, so old values never linger.
    url = f"{args.url.rstrip('/')}/metrics/job/sw_update_tests/suite/{args.suite}"
    req = urllib.request.Request(url, data=body, method="PUT", headers={"Content-Type": "text/plain"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"pushed {args.suite}: {result} -> {resp.status}")


if __name__ == "__main__":
    main()

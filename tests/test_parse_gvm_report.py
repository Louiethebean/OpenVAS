import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from parse_gvm_report import (  # noqa: E402
    dedupe_by_host_and_name,
    parse_gvm_file,
    rank_results,
    to_markdown,
)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_report.xml")


def test_parse_gvm_file_counts_all_results():
    results = parse_gvm_file(FIXTURE)
    assert len(results) == 4


def test_dedupe_collapses_same_host_and_name():
    results = parse_gvm_file(FIXTURE)
    deduped = dedupe_by_host_and_name(results)
    # the two TLS findings on 192.168.1.10 share the same (host, name) key
    assert len(deduped) == 3


def test_rank_results_sorts_highest_first():
    results = parse_gvm_file(FIXTURE)
    deduped = dedupe_by_host_and_name(results)
    ranked = rank_results(deduped)
    assert ranked[0].severity == 10.0
    assert "Log4j" in ranked[0].name


def test_rank_results_filters_by_min_severity():
    results = parse_gvm_file(FIXTURE)
    deduped = dedupe_by_host_and_name(results)
    ranked = rank_results(deduped, min_severity=5.0)
    assert all(r.severity >= 5.0 for r in ranked)
    assert len(ranked) == 2


def test_severity_band_classification():
    results = parse_gvm_file(FIXTURE)
    log4j = next(r for r in results if "Log4j" in r.name)
    assert log4j.band == "Critical"
    icmp = next(r for r in results if "ICMP" in r.name)
    assert icmp.band == "Log"


def test_to_markdown_empty():
    md = to_markdown([])
    assert "No findings" in md

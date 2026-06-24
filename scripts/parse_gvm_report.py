#!/usr/bin/env python3
"""Parse a GVM/OpenVAS XML report export into a deduplicated, severity-ranked summary.

Usage:
    python parse_gvm_report.py report.xml [--format md|csv] [--min-severity 5.0]
"""
import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List


def _severity_band(score: float) -> str:
    if score >= 9.0:
        return "Critical"
    if score >= 7.0:
        return "High"
    if score >= 4.0:
        return "Medium"
    if score > 0.0:
        return "Low"
    return "Log"


@dataclass
class Result:
    host: str
    name: str
    severity: float
    cves: List[str] = field(default_factory=list)
    port: str = ""

    @property
    def band(self) -> str:
        return _severity_band(self.severity)


def parse_gvm_file(path: str) -> List[Result]:
    tree = ET.parse(path)
    root = tree.getroot()
    results: List[Result] = []

    for result in root.iter("result"):
        host_elem = result.find("host")
        host = host_elem.text.strip() if host_elem is not None and host_elem.text else "unknown-host"

        name_elem = result.find("name")
        name = name_elem.text.strip() if name_elem is not None and name_elem.text else "Unnamed finding"

        severity_elem = result.find("severity")
        severity = float(severity_elem.text) if severity_elem is not None and severity_elem.text else 0.0

        port_elem = result.find("port")
        port = port_elem.text.strip() if port_elem is not None and port_elem.text else ""

        cves = []
        refs = result.find("nvt/refs")
        if refs is not None:
            for ref in refs.findall("ref"):
                if ref.get("type") == "cve":
                    cves.append(ref.get("id"))

        results.append(Result(host=host, name=name, severity=severity, cves=cves, port=port))

    return results


def dedupe_by_host_and_name(results: List[Result]) -> List[Result]:
    """Collapse duplicate (host, name) pairs, keeping the highest-severity instance."""
    best = {}
    for r in results:
        key = (r.host, r.name)
        if key not in best or r.severity > best[key].severity:
            best[key] = r
    return list(best.values())


def rank_results(results: List[Result], min_severity: float = 0.0) -> List[Result]:
    filtered = [r for r in results if r.severity >= min_severity]
    return sorted(filtered, key=lambda r: -r.severity)


def severity_histogram(results: List[Result]) -> dict:
    hist = defaultdict(int)
    for r in results:
        hist[r.band] += 1
    return dict(hist)


def to_markdown(results: List[Result]) -> str:
    if not results:
        return "# OpenVAS/GVM Findings Report\n\nNo findings at or above the requested severity threshold.\n"

    hist = severity_histogram(results)
    order = ["Critical", "High", "Medium", "Low", "Log"]
    summary = ", ".join(f"{band}: {hist[band]}" for band in order if band in hist)

    lines = ["# OpenVAS/GVM Findings Report", ""]
    lines.append(f"**Total findings (deduplicated):** {len(results)}")
    lines.append(f"**By severity:** {summary}")
    lines.append("")
    lines.append("| Severity | CVSS | Host | Port | Finding | CVEs |")
    lines.append("|---|---|---|---|---|---|")
    for r in results:
        cve_str = ", ".join(r.cves) if r.cves else "-"
        lines.append(f"| {r.band} | {r.severity} | {r.host} | {r.port or '-'} | {r.name} | {cve_str} |")
    return "\n".join(lines) + "\n"


def to_csv(results: List[Result], out) -> None:
    writer = csv.writer(out)
    writer.writerow(["severity_band", "cvss", "host", "port", "finding", "cves"])
    for r in results:
        writer.writerow([r.band, r.severity, r.host, r.port, r.name, ";".join(r.cves)])


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse a GVM/OpenVAS XML report into a deduplicated summary.")
    parser.add_argument("report", help="Path to a GVM XML report export")
    parser.add_argument("--format", choices=["md", "csv"], default="md")
    parser.add_argument("--min-severity", type=float, default=0.0, help="Minimum CVSS score to include")
    args = parser.parse_args()

    results = parse_gvm_file(args.report)
    deduped = dedupe_by_host_and_name(results)
    ranked = rank_results(deduped, args.min_severity)

    if args.format == "md":
        sys.stdout.write(to_markdown(ranked))
    else:
        to_csv(ranked, sys.stdout)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import json
from pathlib import Path

from app.services.rule_quality import RULE_QUALITY_GOLDEN_VERSION, compare_passes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", default="evaluation/rules/golden-v1.json")
    parser.add_argument("--candidates", default="evaluation/rules/release-candidates-v1.json")
    parser.add_argument("--output", default="artifacts/rule-quality-report.json")
    args = parser.parse_args()

    golden = json.loads(Path(args.golden).read_text(encoding="utf-8"))
    candidates = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    if golden.get("version") != RULE_QUALITY_GOLDEN_VERSION:
        raise ValueError("Golden-set version does not match production rule-quality contract")
    if candidates.get("golden_version") != golden.get("version"):
        raise ValueError("Candidate fixture targets a different golden-set version")

    golden_by_slug = {game["slug"]: game for game in golden["games"]}
    report = {"golden_version": golden["version"], "games": [], "release_pass": True}
    for candidate in candidates["games"]:
        slug = candidate["slug"]
        comparison = compare_passes(golden_by_slug[slug], candidate["first"], candidate["second"])
        report["games"].append({"slug": slug, **comparison})
        report["release_pass"] = report["release_pass"] and comparison["release_pass"]

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["release_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

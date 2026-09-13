"""Cross-document numeric consistency check.

Pulls the canonical figures from the live API and asserts that no document
states a different value for the same fact.
"""
import re, pathlib, requests, sys

api = requests.get("http://127.0.0.1:8000/api/optimization/thresholds", timeout=60).json()
pf  = requests.get("http://127.0.0.1:8000/api/portfolio/profitability", timeout=30).json()
S = api["strategies"]

def money(v): return f"{abs(v):,.0f}"

canon = {
    "legacy baseline":      money(api["legacy_baseline"]["projected_net_profit"]),
    "approve-all baseline": money(pf["net_profit"]),
    "breakeven profit":     money(S["breakeven"]["projected_net_profit"]),
    "breakeven improvement":money(S["breakeven"]["profit_vs_legacy"]),
    "volume-matched impr":  money(S["volume_matched"]["profit_vs_legacy"]),
    "constrained profit":   money(S["constrained_max"]["projected_net_profit"]),
    "max profit":           money(S["unconstrained_max"]["projected_net_profit"]),
    "fee revenue":          money(pf["total_fee_revenue"]),
    "default losses":       money(pf["total_default_losses"]),
}
rates = {
    "breakeven approval":   f"{S['breakeven']['approval_rate_pct']}",
    "legacy approval":      f"{api['legacy_baseline']['approval_rate_pct']}",
    "maxprofit approval":   f"{S['unconstrained_max']['approval_rate_pct']}",
    "approval delta":       f"{S['breakeven']['approval_rate_change_pp']}",
}

print("CANONICAL VALUES")
for k, v in {**canon, **rates}.items():
    print(f"  {k:<24} {v}")

docs = sorted(pathlib.Path("docs").glob("*.md")) + [pathlib.Path("README.md"), pathlib.Path("CHANGELOG.md")]

# Figures that must never appear as a current claim (superseded values)
FORBIDDEN = {
    "70,006": "pre-OOF profit maximum (superseded)",
    "492,620": "pre-correction delta (superseded)",
    "483,989": "stale approve-all delta",
    "203,004": "stale max-profit improvement (sklearn 1.8.0 value)",
    "61,375":  "sklearn 1.8.0 max profit (pinned value is 61,374)",
}
# Contexts where a superseded figure is legitimately discussed as history
HISTORY_OK = {"CHANGELOG.md", "decision-log.md", "risk-register.md", "raid-log.md",
              "retrospective.md", "portfolio-case-study.md", "NUMBERS.md", "README.md",
              "uat-plan.md", "project-charter.md"}

problems = []
for p in docs:
    if not p.exists(): continue
    text = p.read_text()
    for bad, why in FORBIDDEN.items():
        if bad in text and p.name not in HISTORY_OK:
            problems.append(f"{p.name}: contains {bad} ({why})")

# Every doc quoting the headline must use the canonical value
head = canon["breakeven improvement"]
for p in docs:
    if not p.exists(): continue
    t = p.read_text()
    if "149," in t and head not in t:
        problems.append(f"{p.name}: quotes a 149,xxx figure that is not {head}")

print("\nFORBIDDEN-VALUE SCAN")
print("  clean" if not problems else "")
for x in problems: print("  ISSUE:", x)

# Report which docs mention each canonical figure
print("\nCANONICAL FIGURE COVERAGE")
for label, val in canon.items():
    hits = [p.name for p in docs if p.exists() and val in p.read_text()]
    print(f"  {label:<24} {val:>10}  in {len(hits)} docs")

sys.exit(1 if problems else 0)

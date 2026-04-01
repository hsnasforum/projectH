#!/usr/bin/env python3
import json
import sys
from pathlib import Path

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".pipeline/logs")

# baseline
def count(path):
    try:
        return sum(1 for _ in open(path))
    except:
        return 0

b_raw = count(base / "baseline/raw.jsonl")
b_sup = count(base / "baseline/suppressed.jsonl")
b_dis = count(base / "baseline/dispatch.jsonl")

# experimental (분모는 dispatch_candidate만)
e_all = []
try:
    e_all = [json.loads(l) for l in open(base / "experimental/raw.jsonl")]
except:
    pass
e_raw = sum(1 for l in e_all if l.get("event") == "dispatch_candidate")
e_sup = count(base / "experimental/suppressed.jsonl")
e_dis = count(base / "experimental/dispatch.jsonl")

print(f"\n=== A/B Comparison ===")
print(f"{'side':<14} {'raw':>6} {'suppressed':>10} {'dispatch':>9} {'sup_rate':>10} {'dis_rate':>10}")
print(f"{'baseline':<14} {b_raw:>6} {b_sup:>10} {b_dis:>9} {b_sup/b_raw if b_raw else 0:>10.4f} {b_dis/b_raw if b_raw else 0:>10.4f}")
print(f"{'experimental':<14} {e_raw:>6} {e_sup:>10} {e_dis:>9} {e_sup/e_raw if e_raw else 0:>10.4f} {e_dis/e_raw if e_raw else 0:>10.4f}")
print()

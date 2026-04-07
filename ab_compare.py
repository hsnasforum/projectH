#!/usr/bin/env python3
import json
import sys
from pathlib import Path

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".pipeline/logs")

def count(path):
    try:
        return sum(1 for _ in open(path))
    except:
        return 0

# baseline
b_raw = count(base / "baseline/raw.jsonl")
b_sup = count(base / "baseline/suppressed.jsonl")
b_dis = count(base / "baseline/dispatch.jsonl")

# experimental
# 분모: suppressed + dispatch 합계 (실제 판단이 일어난 건수)
e_sup = count(base / "experimental/suppressed.jsonl")
e_dis = count(base / "experimental/dispatch.jsonl")
e_raw = e_sup + e_dis  # 실질 분모

print(f"\n=== A/B Comparison ===")
print(f"{'side':<14} {'candidates':>10} {'suppressed':>10} {'dispatch':>9} {'sup_rate':>10} {'dis_rate':>10}")
print(f"{'baseline':<14} {b_raw:>10} {b_sup:>10} {b_dis:>9} {b_sup/b_raw if b_raw else 0:>10.4f} {b_dis/b_raw if b_raw else 0:>10.4f}")
print(f"{'experimental':<14} {e_raw:>10} {e_sup:>10} {e_dis:>9} {e_sup/e_raw if e_raw else 0:>10.4f} {e_dis/e_raw if e_raw else 0:>10.4f}")
print()

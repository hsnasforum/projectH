#!/bin/bash
# ab_compare.sh — baseline vs experimental A/B 비율 집계
# 사용: bash ab_compare.sh [.pipeline 경로]

PIPELINE_DIR="${1:-.pipeline}"
EXP="$PIPELINE_DIR/logs/experimental"
BASE="$PIPELINE_DIR/logs/baseline"

# experimental: 분모는 dispatch_candidate만
EXP_RAW=$(jq -s 'map(select(.event=="dispatch_candidate")) | length' "$EXP/raw.jsonl" 2>/dev/null || echo 0)
EXP_SUP=$(jq -s 'length' "$EXP/suppressed.jsonl" 2>/dev/null || echo 0)
EXP_DIS=$(jq -s 'length' "$EXP/dispatch.jsonl"   2>/dev/null || echo 0)

# baseline: raw.jsonl 전체를 분모
BASE_RAW=$(jq -s 'length' "$BASE/raw.jsonl"        2>/dev/null || echo 0)
BASE_SUP=$(jq -s 'length' "$BASE/suppressed.jsonl" 2>/dev/null || echo 0)
BASE_DIS=$(jq -s 'length' "$BASE/dispatch.jsonl"   2>/dev/null || echo 0)

echo ""
echo "=== A/B Comparison ==="
printf "%-12s  %8s  %8s  %8s  %14s  %14s\n" \
    "side" "raw" "suppressed" "dispatch" "suppression_rate" "dispatch_rate"
printf "%-12s  %8d  %8d  %8d  %14.6f  %14.6f\n" \
    "experimental" "$EXP_RAW" "$EXP_SUP" "$EXP_DIS" \
    "$(awk "BEGIN {print ($EXP_RAW>0)?$EXP_SUP/$EXP_RAW:0}")" \
    "$(awk "BEGIN {print ($EXP_RAW>0)?$EXP_DIS/$EXP_RAW:0}")"
printf "%-12s  %8d  %8d  %8d  %14.6f  %14.6f\n" \
    "baseline" "$BASE_RAW" "$BASE_SUP" "$BASE_DIS" \
    "$(awk "BEGIN {print ($BASE_RAW>0)?$BASE_SUP/$BASE_RAW:0}")" \
    "$(awk "BEGIN {print ($BASE_RAW>0)?$BASE_DIS/$BASE_RAW:0}")"
echo ""

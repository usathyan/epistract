#!/usr/bin/env bash
# Repo audit: scan for items that should not be in the remote repository
set -euo pipefail

ERRORS=0
WARNINGS=0

echo "=== Epistract Repository Audit ==="
echo ""

# Check 1: .planning/ not tracked
PLANNING_FILES=$(git ls-files .planning/ 2>/dev/null | wc -l | tr -d ' ')
if [ "$PLANNING_FILES" -gt 0 ]; then
  echo "FAIL: .planning/ has $PLANNING_FILES tracked files (should be 0)"
  ERRORS=$((ERRORS + 1))
else
  echo "PASS: .planning/ not tracked"
fi

# Check 2: No large binaries (>500KB)
LARGE_FILES=$(git ls-files -z | xargs -0 -I{} sh -c 'test -f "{}" && size=$(wc -c < "{}") && [ "$size" -gt 512000 ] && echo "{} ($size bytes)"' 2>/dev/null || true)
if [ -n "$LARGE_FILES" ]; then
  echo "WARN: Large tracked files (>500KB):"
  echo "$LARGE_FILES" | sed 's/^/  /'
  WARNINGS=$((WARNINGS + 1))
else
  echo "PASS: No large tracked files"
fi

# Check 3: No .env files tracked
ENV_FILES=$(git ls-files '*.env' '.env*' 2>/dev/null | grep -v '.env.example' || true)
if [ -n "$ENV_FILES" ]; then
  echo "FAIL: .env files tracked: $ENV_FILES"
  ERRORS=$((ERRORS + 1))
else
  echo "PASS: No .env files tracked"
fi

# Check 4: No __pycache__ tracked
PYCACHE=$(git ls-files '*__pycache__*' '*.pyc' 2>/dev/null || true)
if [ -n "$PYCACHE" ]; then
  echo "FAIL: __pycache__/pyc files tracked: $PYCACHE"
  ERRORS=$((ERRORS + 1))
else
  echo "PASS: No __pycache__ tracked"
fi

# Check 5: No node_modules tracked
NODE_MODULES=$(git ls-files 'node_modules/' 2>/dev/null | wc -l | tr -d ' ')
if [ "$NODE_MODULES" -gt 0 ]; then
  echo "FAIL: node_modules has $NODE_MODULES tracked files"
  ERRORS=$((ERRORS + 1))
else
  echo "PASS: No node_modules tracked"
fi

# Check 6: No .venv tracked
VENV_FILES=$(git ls-files '.venv/' 2>/dev/null | wc -l | tr -d ' ')
if [ "$VENV_FILES" -gt 0 ]; then
  echo "FAIL: .venv has $VENV_FILES tracked files"
  ERRORS=$((ERRORS + 1))
else
  echo "PASS: No .venv tracked"
fi

# Check 7: No STA contract data tracked
STA_FILES=$(git ls-files 'sample-contracts/' 'sample-output/' '*akka-*.json' '*akka-*.pdf' 2>/dev/null || true)
if [ -n "$STA_FILES" ]; then
  echo "FAIL: STA data tracked: $STA_FILES"
  ERRORS=$((ERRORS + 1))
else
  echo "PASS: No STA contract data tracked"
fi

# Check 8: .claude/worktrees not tracked
WORKTREE_FILES=$(git ls-files '.claude/worktrees/' 2>/dev/null | wc -l | tr -d ' ')
if [ "$WORKTREE_FILES" -gt 0 ]; then
  echo "FAIL: .claude/worktrees has $WORKTREE_FILES tracked files"
  ERRORS=$((ERRORS + 1))
else
  echo "PASS: No .claude/worktrees tracked"
fi

echo ""
echo "=== Audit Summary ==="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"

if [ "$ERRORS" -gt 0 ]; then
  echo "RESULT: FAIL — fix errors before pushing"
  exit 1
elif [ "$WARNINGS" -gt 0 ]; then
  echo "RESULT: PASS with warnings"
  exit 0
else
  echo "RESULT: PASS"
  exit 0
fi

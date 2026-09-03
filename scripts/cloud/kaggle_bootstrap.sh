#!/usr/bin/env bash
# Bootstrap a Kaggle notebook working copy. Kaggle storage is not Drive-persistent:
# publish large artefacts as a private dataset or download them before session end.
set -euo pipefail

repo_url="${1:?Usage: bash scripts/cloud/kaggle_bootstrap.sh https://github.com/<org>/<repo>.git}"
checkout="${KAGGLE_WORKING_DIR:-/kaggle/working/sih-2026}"
if command -v nvidia-smi >/dev/null; then
  nvidia-smi
else
  echo "WARNING: GPU not enabled. Enable an accelerator in Kaggle settings before Phase 2." >&2
fi
git clone "$repo_url" "$checkout"
python -m pip install -r "$checkout/requirements.txt"
echo "Ready: $checkout"

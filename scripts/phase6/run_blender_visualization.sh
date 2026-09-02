#!/usr/bin/env bash
# Build a Blender scene from the hydrodynamic output rasters.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
preview_flag=""
if [[ "${1:-}" == "--preview-legacy" ]]; then
  preview_flag="--allow-unverified"
fi

python3 "$repo_root/scripts/phase6/prepare_viz_data.py" $preview_flag
blender_bin="${BLENDER_BIN:-blender}"
"$blender_bin" --background --python "$repo_root/scripts/phase6/build_blender_scene.py"

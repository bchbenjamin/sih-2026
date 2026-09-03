#!/usr/bin/env bash
# Build a Blender scene from the hydrodynamic output rasters.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ "${1:-}" == "--mantaflow" || "${2:-}" == "--mantaflow" ]]; then
  export DAM_VISUAL_MODE=mantaflow
fi

python3 "$repo_root/scripts/phase6/prepare_viz_data.py"
blender_bin="${BLENDER_BIN:-blender}"
"$blender_bin" --background --python "$repo_root/scripts/phase6/build_blender_scene.py"

#!/usr/bin/env bash
set -euo pipefail

manifest="${1:-}"
if [[ -z "${manifest}" ]]; then
  echo "Usage: $0 /path/to/dualsphysics_manifest.json" >&2
  exit 2
fi

find_dualsphysics_bin() {
  local root
  for root in \
    "${DUALSPHYSICS_ROOT:-}" \
    "${PWD}/DualSPHysics_src" \
    "${PWD}/DualSPHysics" \
    "${HOME}/DualSPHysics" \
    "/opt/DualSPHysics" \
    "/usr/local/DualSPHysics" \
    "/mnt/WindowsDrive/Fedora/Projects" \
  ; do
    [[ -n "${root}" ]] || continue
    if [[ -d "${root}" ]]; then
      while IFS= read -r candidate; do
        if [[ -x "${candidate}" ]]; then
          printf '%s\n' "${candidate}"
          return 0
        fi
      done < <(find "${root}" -type f \( -iname 'DualSPHysics*' -o -iname 'DualSPHysics*.*' \) 2>/dev/null | sort)
    fi
  done
  return 1
}

bin_path="$(find_dualsphysics_bin || true)"
if [[ -z "${bin_path}" ]]; then
  echo "DualSPHysics is not installed or not buildable in this environment." >&2
  echo "The project requires a real DualSPHysics install, not a placeholder path." >&2
  echo "Install upstream source manually or provide the real binary location in DUALSPHYSICS_ROOT." >&2
  exit 1
fi

# This wrapper is intentionally transparent. It does not hardcode a fake executable.
# The project expects the wrapper to receive the manifest path and then perform the
# real DualSPHysics workflow: GenCase, DualSPHysics, FlowTool, IsoSurface.
# Replace the command below with the actual site-specific solver invocation as
# required by your DualSPHysics install.

echo "Using DualSPHysics binary: ${bin_path}"

echo "Manifest: ${manifest}"

echo "This is a template wrapper; the real workflow must be mapped to your actual installation." >&2
exit 1

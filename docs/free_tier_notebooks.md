# Free-tier notebook execution

Use Colab as the primary GPU worker and Kaggle as the same-day fallback. Both
are disposable runtimes: keep the repository, DEM, particle output, exported
mesh sequence, and any compiled DualSPHysics binary outside the runtime.

## Colab

1. In Colab, select a GPU runtime and run `!nvidia-smi`. Stop if no GPU is
   assigned; a CPU runtime cannot complete the intended DualSPHysics run.
2. Clone the project directly into Drive, not `/content`:

   ```bash
   !python scripts/cloud/colab_bootstrap.py \
     --repo-url https://github.com/bchbenjamin/sih-2026.git
   ```

3. Download a compatible upstream DualSPHysics Linux GPU release or build it
   from source. Cache the completed binary under Drive, then set
   `DUALSPHYSICS_ROOT` to that directory for every new session.
4. Use ANUGA as the free-tier far-field path unless the team’s explicit,
   one-day Delft3D FM time-box succeeds. Do not spend the rest of the project
   retrying Delft3D FM builds after that decision.
5. Copy critical results out of the runtime before disconnect. Do not store API
   keys in the Git checkout; create `.env` only in the notebook runtime/Drive
   and keep it ignored.

## Kaggle fallback

Enable a GPU in notebook settings, then run:

```bash
!bash scripts/cloud/kaggle_bootstrap.sh https://github.com/bchbenjamin/sih-2026.git
```

Kaggle’s working directory is session-scoped. Attach a private Kaggle dataset
for cached binaries/data or export those artefacts at the end of the session.

## Blender

Run the flat-plane smoke test before any real terrain scene. In Colab, first
test a trivial headless render; Eevee may require an EGL-capable setup. Cycles
GPU rendering is the preferred fallback when a T4 is available.

```bash
blender --background --python scripts/phase6/mantaflow_smoke_test.py
blender --background --python scripts/phase6/build_blender_scene.py
```

The generated scene remains a visualization consumer. The solver rasters and
damage CSV remain the authoritative export sources.

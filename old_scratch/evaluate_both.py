import numpy as np
from pathlib import Path
import sys

# Import max_relative_error from validate_timeseries
sys.path.insert(0, str(Path("scripts")))
from validate_timeseries import max_relative_error, read_series

ref_t, ref_v = read_series(Path("cases/stoker/stoker_analytical_reference.csv"), "wave_height_m")
model_t, model_v = read_series(Path("cases/stoker/stoker_out/stoker_model_output.csv"), "wave_height_m")

# Full run error
full_error = max_relative_error(ref_t, ref_v, model_t, model_v)

# Early window (0.1 to 0.2s)
t_min, t_max = 0.1, 0.2
mask = (ref_t >= t_min) & (ref_t <= t_max)
ref_t_early, ref_v_early = ref_t[mask], ref_v[mask]
early_error = max_relative_error(ref_t_early, ref_v_early, model_t, model_v)

print(f"Full-run Error: {full_error:.2f}%")
print(f"Early-window Error: {early_error:.2f}%")

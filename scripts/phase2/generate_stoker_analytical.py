#!/usr/bin/env python3
import csv
import math
import os
from pathlib import Path

def generate_reference():
    H0 = 2.0
    g = 9.81
    x0 = 1.0
    probe_x = 0.2
    
    c0 = math.sqrt(g * H0)
    x_prime = probe_x - x0
    
    t_arrival = -x_prime / c0 if x_prime < 0 else 0.0
    
    out_dir = Path(__file__).resolve().parents[2] / "cases" / "stoker"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "stoker_analytical_reference.csv"
    
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time_s', 'wave_height_m'])
        
        # DualSPHysics output is typically every 0.01s (TimeOut=0.01)
        # TimeMax = 2.0
        for i in range(201):
            t = i * 0.01
            if t < t_arrival:
                h = H0
            else:
                # Ritter solution
                h = (1.0 / (9.0 * g)) * (2 * c0 - (x_prime / t))**2
                # Clamp to 0
                if h < 0: h = 0
            writer.writerow([f"{t:.2f}", f"{h:.6f}"])

if __name__ == "__main__":
    generate_reference()

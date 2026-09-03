# Chorabari / Kedarnath GLOF 2013 — Data Provenance

## Primary Event Parameters
The 17 June 2013 outburst of Chorabari Lake (Gandhi Sarovar) caused devastating flooding in the Mandakini valley, severely impacting Kedarnath town.

### Breach Width and Setup Geometry
- **Source:** Das, S., Kar, N.S., Bandyopadhyay, S. (2015). "Glacial lake outburst flood at Kedarnath, Indian Himalaya: a study using digital elevation models and satellite images." *Natural Hazards*, 77(2), 769–786. https://doi.org/10.1007/s11069-015-1629-6
- **Values Derived:**
  - `breach_width_m: 60.0` (Directly measured 60 m breach width along the 9–10 m moraine ridge).
  - Released Volume: ~0.43 × 10⁶ m³.
  - Validation Peak Discharge: 1,352.2 m³/s (SRTM-based estimate).

### Breach Duration and Alternative Discharge Estimate
- **Source:** Rafiq, M., Romshoo, S.A., Mishra, A.K., Jalal, F. (2019). "Modelling Chorabari Lake outburst flood, Kedarnath, India." *Journal of Mountain Science*, 16(1), 64–76. https://doi.org/10.1007/s11629-018-4972-8
- **Values Derived:**
  - `breach_time_s: 750` (Midpoint of the 10-15 minute / 600-900s observed event window).
  - Validation Peak Discharge: 1,699 m³/s (BREACH model estimate).

*Note: The target validation range for numerical solver output is 1,352–1,699 m³/s. The difference between these two studies reflects differing methodologies (SRTM-based predictive equations vs. BREACH modelling) and is considered normal scientific variance, not a data quality problem.*

*Note on Analytical Regression:* The Peng & Zhang (2012) simplified peak-discharge equation underpredicts the target peak discharge for this case (yielding ~642.9 m³/s). This is a known limitation of generalized landslide dam breach regressions, which commonly exhibit ~2x prediction spreads across diverse real cases. We document this as a floor-check, but the DualSPHysics near-field solver will provide the definitive prediction to validate against the literature targets.

## Geospatial Data
- **DEM:** SRTM GL1 (30m) via OpenTopography API.
- **Buildings & Landuse:** OpenStreetMap via Overpass API.
- **Bounding Box:** `[79.00, 30.65, 79.10, 30.80]`

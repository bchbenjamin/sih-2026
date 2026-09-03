# Rishiganga scenario: numeric-value provenance

This is a **counterfactual breach scenario**, not a reconstruction of the 7
February 2021 flood. Shugar et al. identify the event as a rock-and-ice
avalanche/debris-flow cascade and describe a lake that formed subsequently.
No output from this repository may be described as an observed-event replay.

* `case_name: rishiganga` — scenario identifier, project-defined.
* `dam_name: Rishiganga moraine-dammed lake` — descriptive project label;
  Shugar et al. (2021), main text, reports a lake behind the deposit in the
  Rishiganga valley.
* `dam_coordinates: [30.467794, 79.736056]` — lake location from the reported
  30°28′04.06″N, 79°44′09.8″E in Sati et al. (2021), *Current Science* 121(11),
  p. 1486. Decimal degrees are a coordinate conversion, not a published
  measurement.
* `formation_date: 2021-02-07` — NDMA Joint Study Team (2022), Table 7.
* `lake_length_m: 750` — midpoint of the reported 700 m initial length (Shugar
  et al., 2021, main text) and ~800 m later length (Kothyari et al., 2022,
  *Journal of Hydrology: Regional Studies*, section 1). Derived midpoint, not
  a direct measurement.
* `lake_front_width_m: 100` — Kothyari et al. (2022), section 1, reports a
  front width of about 100 m.
* `lake_depth_m: 46` — Kothyari et al. (2022), section 1, reports about 46 m,
  including roughly 10 m of newly deposited debris/silt.
* `reservoir_volume_m3: 1725000` — derived via triangular-prism approximation:
  `0.5 × lake_length_m × lake_front_width_m × lake_depth_m`. It is an input
  scenario estimate, **not** a published bathymetric volume.
* `downstream_reach_km: 25` — project modelling extent, selected to include
  downstream hydropower exposure; not a source measurement.
* `dem_bbox` — project processing extent around the study reach, not a source
  measurement.
* `downstream_points` — the named assets/exposure locations are supported by
  NDMA (2022), Figure 28, and the Geological Survey of India/PIB release of 28
  June 2021, both of which identify Raini, Rishiganga HEP and Tapovan
  Vishnugad HEP in the affected corridor. The decimal coordinate pairs and
  `distance_km` fields are **project digitisation/chainage estimates** and not
  published surveyed coordinates; replace them with surveyed/OSM-derived
  coordinates and record the feature IDs before using them as validation
  points.
* `execution.model_scale_Lr: 40` — project-selected Froude model scale within
  the plan's stated 1:20–1:50 range; it is a model decision, not a field
  measurement. `Vr`, `Tr`, and `Qr` are derived in `scale_config.yaml` through
  Froude similarity.
* `execution.delft3d_timebox_days: 1` — project scheduling decision for the
  Colab/Kaggle workflow, not a physical value. `execution.farfield_backend:
  anuga` is the selected free-tier backend.

## Full references

1. Shugar, D. H. et al. (2021), “A massive rock and ice avalanche caused the
   2021 disaster at Chamoli, Indian Himalaya,” *Science*, 373(6552), 300–306,
   doi:10.1126/science.abh4455.
2. National Disaster Management Authority (2022), *Detailed Report:
   Uttarakhand Disaster on 7th February 2021*, Joint Study Team, Table 7.
3. Kothyari, G. C. et al. (2022), “Understanding the flash flood event of 7th
   February 2021 in Rishi Ganga basin, Central Himalaya using remote sensing
   technique,” *Journal of Hydrology: Regional Studies*, 40, 100999,
   doi:10.1016/j.ejrh.2022.100999.
4. Peng, M. & Zhang, L. M. (2012), “Breaching parameters of landslide dams,”
   *Landslides*, 9, 13–31, doi:10.1007/s10346-011-0271-y.
5. Walder, J. S. & O’Connor, J. E. (1997), “Methods for predicting peak
   discharge of floods caused by failure of natural and constructed earthen
   dams,” *Water Resources Research*, 33(10), 2337–2348,
   doi:10.1029/97WR01616.
6. Press Information Bureau / Geological Survey of India (2021), “GSI Brings
   to Light the Causes of the Chamoli Disaster,” 28 June 2021.

`breach_params.json` records its formula/equation source, input values,
assumptions, and calibration choice separately. Do not promote a provisional
formula result to a sourced field in this file.

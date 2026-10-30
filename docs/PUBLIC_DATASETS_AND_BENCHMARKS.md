# Public Datasets and Independent Benchmarks

**Scope:** AIOps UPS/PAC research and V12 staging validation  
**Last documentation review:** 2026-10-30

This document separates public reference datasets from operational Zabbix telemetry. Public benchmark data is for independent, offline evaluation only. It must not be mixed into the production Zabbix learning or inference path without an explicitly reviewed methodology.

## 1. Dataset status at publication

| Dataset | Official source verified | Native dataset acquired and checksum verified | Benchmark status |
|---|---|---|---|
| LBNL RTU FDD | Yes | Not verified / not acquired | Simulation framework reported; real-file benchmark not established |
| NASA PCoE Battery #5 | Yes | Not verified / not acquired | Simulation framework reported; real-file benchmark not established |
| NASA PCoE Randomized Battery #11 | Yes | Not verified / not acquired | Reference only; benchmark not established |

The Phase 87.3 summary reports `STAGED_REFERENCE_VERIFIED` and `EXECUTED_SIMULATION`. These statuses mean that the sources/framework were recorded and simulation tests were run. They do **not** establish that the original public dataset archives were downloaded, hashed, profiled, or used as benchmark input.

The repository's historical `shadow_v5/PUBLIC_DATASET_ACQUISITION_MANIFEST.json` records `STAGED_OFFLINE_FIXTURE` and the SHA-256 of an empty payload for both historical entries. An empty-payload hash is not a dataset checksum. Until non-empty source files, actual byte sizes, and matching SHA-256 values are recorded, use `NOT_ACQUIRED` for native dataset acquisition.

## 2. LBNL Fault Detection and Diagnostics — RTU

**Publisher:** Lawrence Berkeley National Laboratory (LBNL), with contributing national-laboratory and research partners.

- Official FDD data catalogue: https://faultdetection.lbl.gov/data/
- Official RTU dataset page: https://faultdetection.lbl.gov/dataset/rtu/
- Dataset DOI: https://doi.org/10.25984/1881324
- Simulated RTU dataset ZIP (74 CSV files; listed as approximately 292 MB): https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU.zip
- All three RTU dataset files (listed as approximately 293 MB): https://fdddata.lbl.gov/data/Simulated_LBNL_FDD_Data_Sets_RTU/LBNL_FDD_Data_Sets_RTU_all_3.zip

The RTU collection describes simulated, laboratory, and field-measured data. The RTU page states that the simulated archive contains 74 CSV files covering 10 fault types at different severity levels and 7 fault-free cases. The page also describes a one-minute sample rate and multiple data-generation settings.

**Access note:** the LBNL download page presents a resource-download form and notes that cookies must be enabled. Use the official page and complete any required user information truthfully. Do not fabricate a person, organization, or email to bypass the form. Direct archive URLs are included for convenience but access may still be subject to the site's download flow.

**Intended AIOps use:** an independent HVAC/RTU fault-detection benchmark relevant to selected PAC concepts, such as temperature, fan, compressor, and fault-state patterns.

**Domain limitation:** an RTU is not the same equipment as the production Precision Air Conditioner (PAC). Map features only where physical meaning, unit, sampling, and operating context are compatible. Otherwise classify the relationship as `CONCEPTUAL_BENCHMARK_ONLY` or `NOT_COMPARABLE`. Do not transfer LBNL thresholds directly to production PAC equipment.

**License note:** the Data.gov catalogue lists a Creative Commons Attribution 4.0 license for the LBNL FDD collection. Confirm the applicable terms on the dataset's primary landing page and preserve attribution before redistribution or derivative publication.

## 3. NASA Prognostics Center of Excellence — Battery

**Publisher:** NASA Prognostics Center of Excellence (PCoE); Battery Data Set citation credits B. Saha and K. Goebel (2007).

- Official NASA PCoE repository: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/
- Battery Data Set #5 — direct ZIP: https://phm-datasets.s3.amazonaws.com/NASA/5.+Battery+Data+Set.zip

NASA describes Dataset #5 as lithium-ion battery experiments involving charging and discharging at different temperatures, with impedance recorded as a damage criterion.

**Optional supplementary dataset:**
- Randomized Battery Usage Data Set #11 — direct ZIP: https://phm-datasets.s3.amazonaws.com/NASA/11.+Randomized+Battery+Usage+Data+Set.zip

Dataset #11 uses randomized battery cycling and periodic reference charging/discharging to support battery state-of-health studies.

**Intended AIOps use:** independent evaluation of battery degradation analysis and prognostics methodology where the dataset provides suitable cycle, capacity, impedance, or reference information.

**Domain limitation:** NASA lithium-ion test cells are not automatically representative of the chemistry, configuration, load profile, temperature, or operating conditions of the UPS batteries in the data center. Confirm the production UPS battery chemistry and sensor definitions before making any direct comparison. Do not apply NASA-derived thresholds directly to production UPS devices.

**Citation:** B. Saha and K. Goebel (2007), “Battery Data Set,” NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA.

**License note:** the NASA repository page provides citation and use-at-own-risk language; this document does not assume a separate dataset-specific redistribution license. Review applicable terms before redistribution.

## 4. Required acquisition evidence

A dataset can be marked `ACQUIRED_VERIFIED` only when all applicable evidence is recorded:

1. Official source URL and access date.
2. Actual local file path in the isolated staging workspace.
3. Non-zero file size in bytes.
4. SHA-256 computed from the actual downloaded archive.
5. Archive integrity and safe file-list inspection.
6. Dataset version, file inventory, and data dictionary.
7. License/terms review.
8. Profiling results: records, features, units, timestamps, missing values, labels, and time range.

A URL, empty placeholder, fixture, or successful simulation is not proof of public dataset acquisition.

## 5. Benchmark status vocabulary

| Status | Meaning |
|---|---|
| `PUBLIC_REFERENCE` | Official source and citation are documented |
| `NOT_ACQUIRED` | Native dataset files have not been verified locally |
| `PARTIALLY_ACQUIRED` | Some files were acquired, but the expected dataset is incomplete |
| `ACQUIRED_VERIFIED` | Actual files and checksums were verified |
| `PREPROCESSED_VALIDATED` | A derived copy was profiled and validated |
| `BENCHMARK_EXECUTED` | An evaluation was run on verified native public-dataset files, with input manifest and results |
| `SIMULATION_TEST_ONLY` | Benchmark code was exercised with simulated or fixture inputs, not native dataset files |
| `BLOCKED_USER_INPUT` | Official source requires truthful user information that has not been supplied |
| `BLOCKED_LICENSE_REVIEW` | Usage or redistribution terms require review |

Do not use `BENCHMARK_EXECUTED` for a simulation-only run.

## 6. Independent evaluation policy

Keep these three evidence streams separate:

1. **Operational telemetry:** real Zabbix UPS/PAC records, with item-level provenance and data-quality evidence.
2. **LBNL HVAC benchmark:** LBNL RTU source files and their own labels/scenarios.
3. **NASA battery benchmark:** NASA battery cycles and their own reference/health information.

Do not pool these data into a single training set merely because feature names appear similar. First establish physical meaning, units, sampling semantics, equipment domain, label quality, and an evaluation split that prevents time-series or unit-level leakage.

For LBNL, report per-scenario or per-unit precision, recall, F1, false-alarm rate, and confusion matrix only when verified labels and predictions are available.

For NASA, report battery-cycle degradation metrics and RUL metrics only when a defensible target or end-of-life definition is available. Otherwise use `NOT_MEASURABLE`.

Public benchmark metrics are not production UPS/PAC accuracy claims.

## 7. AIOps current limitations

- TTF and RUL accuracy remain `NOT_MEASURABLE` without verified failure/ground-truth outcomes for the relevant production equipment.
- Historical documentation values of TTF ±15% and RUL ±20% are design targets only, not empirically demonstrated accuracy.
- Isolation Forest `contamination=0.05` is a model configuration parameter; it is not a 5% error rate or a claim of 95% accuracy.
- A Health Score is an analytical index, not a calibrated probability that equipment is healthy.
- Sensor provenance must be checked before using historical Zabbix values as physical ground truth, especially where earlier runtime code could publish derived or synthetic values.

## 8. References

- LBNL FDD data catalogue: https://faultdetection.lbl.gov/data/
- LBNL RTU dataset: https://faultdetection.lbl.gov/dataset/rtu/
- LBNL FDD Data.gov catalogue: https://catalog.data.gov/dataset/lbnl-fault-detection-and-diagnostics-datasets
- NASA PCoE Data Set Repository: https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/

# Public Dataset Catalog — AIOps Shadow v5 Expansion

This catalog establishes the inventory of official public datasets for offline benchmarking, anomaly detection, and prognostic modeling under AIOps Shadow v5, isolating all experiments in `/root/grafan_aiops/shadow_v5/` without touching production Zabbix or mutating core systems.

## Summary Table

| Dataset ID | Publisher | Domain / Asset | Verified Landing URL | Suitability | Status |
|---|---|---|---|---|---|
| `lbnl_fdd` | Lawrence Berkeley National Laboratory (LBNL) | HVAC Systems / Air Handling Units / Chillers | `https://faultdetection.lbl.gov/data/` | PAC / HVAC Anomaly Detection | `NOT VERIFIED` (Requires offline inspection) |
| `nasa_pcoe_battery` | NASA Prognostics Center of Excellence (PCoE) | Li-ion Battery Prognostics | `https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/` | UPS / Battery Prognostics & RUL | `NOT VERIFIED` |
| `nasa_server_health` | NASA / National Aeronautics and Space Administration | Computer Servers & Hardware Telemetry | `https://data.nasa.gov/dataset/health-monitoring-and-prognostics-for-computer-servers` | Server Health & Hardware Monitoring | `NOT VERIFIED` |
| `ashrae_data` | ASHRAE (American Society of Heating, Refrigerating and Air-Conditioning Engineers) | Building Energy & Thermal Systems | `https://data.ashrae.org/` | General Thermal & Energy Benchmarks | `NOT VERIFIED` |

---

## Detailed Dataset Profiles

### 1. LBNL Fault Detection and Diagnostics (LBNL FDD)
- **Publisher:** Lawrence Berkeley National Laboratory (LBNL).
- **Landing Page URL:** `https://faultdetection.lbl.gov/data/` (HTTPS verified).
- **Download URL:** `NOT VERIFIED` (Specific archive endpoints require landing page traversal/verification).
- **Equipment / Domain:** HVAC systems, Air Handling Units (AHUs), Variable Air Volume (VAV) boxes, Chillers.
- **Number of Sensors & Features:** `NOT VERIFIED` (Typically multi-variable time-series including temperatures, pressures, damper positions, flow rates).
- **Time Range & Sampling Frequency:** `NOT VERIFIED` (Typically 1-minute to 15-minute intervals spanning weeks or months).
- **Label Types & Ground Truth:** Controlled faults injected or naturally occurring operational faults (expert-labeled).
- **Format & Estimated File Size:** CSV / MAT / Excel format; `NOT VERIFIED` exact file size.
- **License & Usage Terms:** `NOT VERIFIED` (Public research use, subject to publisher terms).
- **Acquisition Method & Checksum:** HTTPS GET with domain allowlist, temporary file staging, SHA-256 calculation.
- **Suitability for AIOps:** High suitability for PAC (Precision Air Conditioning) fault detection and HVAC diagnostics.
- **Transfer Limitations:** Laboratory or simulated building HVAC characteristics may differ from enterprise data center PAC units (e.g., control loop tunings, environmental dynamics).

### 2. NASA Prognostics Data Repository — Li-ion Battery (NASA PCoE)
- **Publisher:** NASA Ames Research Center, Prognostics Center of Excellence (PCoE).
- **Landing Page URL:** `https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/` (HTTPS verified).
- **Download URL:** `NOT VERIFIED`.
- **Equipment / Domain:** Commercial Li-ion 18650 battery cells subjected to charge, discharge, and impedance operations at different temperatures.
- **Number of Sensors & Features:** Voltage, current, temperature, impedance, capacity.
- **Time Range & Sampling Frequency:** Operational cycles over battery lifetime (charge/discharge cycles).
- **Label Types & Ground Truth:** Remaining Useful Life (RUL), capacity degradation curves, end-of-life (EOL) markers.
- **Format & Estimated File Size:** MAT / CSV / ZIP archives; estimated size `NOT VERIFIED` (typically tens to hundreds of MBs).
- **License & Usage Terms:** Public government dataset (NASA Open Data / public domain terms).
- **Acquisition Method & Checksum:** HTTPS GET with domain allowlist, temporary file staging, SHA-256 calculation.
- **Suitability for AIOps:** High suitability for UPS battery health monitoring, degradation prediction, and RUL estimation.
- **Transfer Limitations:** Cell-level battery aging dynamics require appropriate scaling when transferring to enterprise multi-rack UPS battery string configurations.

### 3. NASA Health Monitoring and Prognostics for Computer Servers
- **Publisher:** NASA.
- **Landing Page URL:** `https://data.nasa.gov/dataset/health-monitoring-and-prognostics-for-computer-servers` (HTTPS verified).
- **Download URL:** `NOT VERIFIED`.
- **Equipment / Domain:** Computer servers, CPU/memory/storage telemetry, fan speeds, power consumption, temperature sensors.
- **Number of Sensors & Features:** `NOT VERIFIED`.
- **Time Range & Sampling Frequency:** `NOT VERIFIED`.
- **Label Types & Ground Truth:** Component degradation, failure events, anomaly annotations.
- **Format & Estimated File Size:** `NOT VERIFIED`.
- **License & Usage Terms:** `NOT VERIFIED`.
- **Acquisition Method & Checksum:** HTTPS GET with domain allowlist, temporary staging, SHA-256 calculation.
- **Suitability for AIOps:** Direct suitability for physical server hardware health monitoring, CPU temperature anomalies, and fan/power telemetry.
- **Transfer Limitations:** Server workload characteristics and hardware vendor specifics (e.g. Dell iDRAC vs. generic testbeds) require calibration.

### 4. ASHRAE Data Repository
- **Publisher:** ASHRAE.
- **Landing Page URL:** `https://data.ashrae.org/` (HTTPS verified).
- **Download URL:** `NOT VERIFIED`.
- **Equipment / Domain:** Building thermal energy, HVAC, environmental monitoring.
- **Number of Sensors & Features:** `NOT VERIFIED`.
- **Time Range & Sampling Frequency:** `NOT VERIFIED`.
- **Label Types & Ground Truth:** `NOT VERIFIED`.
- **Format & Estimated File Size:** `NOT VERIFIED`.
- **License & Usage Terms:** `NOT VERIFIED`.
- **Acquisition Method & Checksum:** HTTPS GET with domain allowlist, temporary staging, SHA-256 calculation.
- **Suitability for AIOps:** General thermal baseline modeling and energy efficiency trend analysis.
- **Transfer Limitations:** General building datasets often aggregate coarse spatial data compared to high-density server room/facility telemetry.

---

## Safety & Operational Guidelines
1. **No Production Access:** Zero Zabbix queries, zero API calls, zero database writes.
2. **Isolation:** All work strictly in `/root/grafan_aiops/shadow_v5/`.
3. **Controlled Acquisition:** All downloads require verification, SHA-256 manifest tracking, and strict size/domain bounds.
4. **No Unverified Claims:** Unknown attributes are explicitly marked `NOT VERIFIED`.

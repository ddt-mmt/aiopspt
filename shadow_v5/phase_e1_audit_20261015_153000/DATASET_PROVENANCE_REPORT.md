# Dataset Provenance Report — Phase E.1

## Overview
This report details the provenance status of datasets evaluated under Phase E.1.

## 1. LBNL FDD (HVAC/PAC)
- **Official Source URL:** `https://faultdetection.lbl.gov/data/`
- **Acquisition Status:** `BLOCKED` (Direct unauthenticated raw CSV endpoint requires interactive web session or portal registration).
- **Fallback Fixture:** Verified synthetic fixture (`lbnl_fdd_raw_synthetic.json`, 1,000 records, SHA-256 computed).
- **License / Terms:** `NOT VERIFIED` for live download; synthetic fixture used solely for offline algorithm validation.

## 2. NASA PCoE Battery
- **Official Source URL:** `https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/`
- **Acquisition Status:** `BLOCKED` (Direct unauthenticated raw file endpoint requires repository portal navigation).
- **Fallback Fixture:** Verified synthetic fixture (`nasa_pcoe_battery_raw_synthetic.json`, 500 cycles, SHA-256 computed).
- **License / Terms:** Public government dataset terms; synthetic fixture used solely for offline algorithm validation.

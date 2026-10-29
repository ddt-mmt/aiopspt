# Data Quality Report (`data_quality_report.md`)

- **Extraction Timestamp:** 2026-10-16T13:11:45.421979+00:00
- **Total Events Extracted:** 2
- **Total Sensor Records Used:** 14365
- **Active Sensor Items Analyzed:** 21
- **Actual Available Event Period:** 2026-02-03T09:01:23+00:00 to 2026-02-03T09:01:24+00:00

## Observations & Limitations
1. **Zabbix Retention:** Zabbix event history retention policies may limit event availability to less than the full 365 days depending on server cleanup jobs.
2. **Missing Maintenance Logs:** External physical maintenance logs are absent; labels rely purely on Zabbix triggers and recovery timestamps.
3. **Communication vs. Physical:** Communication/ping alerts comprise a portion of events and are isolated to prevent misclassification as equipment failure.

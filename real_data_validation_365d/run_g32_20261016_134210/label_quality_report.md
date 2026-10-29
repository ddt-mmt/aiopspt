# Isolated Model Robustness & Label Validity Audit (`label_quality_report.md`)

- **Timestamp:** 2026-10-16T13:42:10.545163+00:00
- **Status Decision:** **`PARTIAL`**
- **Label Quality & Source:** Labels are derived directly from Zabbix event severity (`severity >= 1` vs `severity == 0`). They represent **Zabbix alarm event severity**, not physical equipment damage.
- **Test Set Limitations:** Test split contains 27 samples, which provides initial mathematical verification but requires larger, multi-incident soaking before live deployment.
- **Per-Host Coverage:** 
  - `ME_UPS1`: Samples = 2, Status = `EVALUATED`
  - `ME_UPS2`: Samples = 17, Status = `EVALUATED`
  - `ME_UPS3`: Samples = 8, Status = `EVALUATED`
  - `ME_PAC1`: Samples = 0, Status = `NOT_EVALUABLE`
  - `ME_PAC2`: Samples = 0, Status = `NOT_EVALUABLE`
  - `ME_PAC3`: Samples = 0, Status = `NOT_EVALUABLE`
  - `ME_PAC4`: Samples = 0, Status = `NOT_EVALUABLE`

- **Safety Compliance:** Production changes = 0, Zabbix writes = 0, Restarts = 0.
- **Deployment Authorization:** `NOT_AUTHORIZED_FOR_DEPLOYMENT`.

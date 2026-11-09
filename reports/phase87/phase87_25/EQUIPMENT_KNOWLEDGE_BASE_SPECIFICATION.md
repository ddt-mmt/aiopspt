# Equipment Knowledge Base (EKB) Specification

## 1. Purpose
The Equipment Knowledge Base (EKB) provides authoritative manufacturer and engineering specifications for every equipment category (UPS, PAC, battery, etc.) monitored by AIOps V12.

## 2. Record Structure
Each EKB record contains:
- **Equipment Identity:** ID, host ID, manufacturer, model, serial number, category.
- **Manufacturer Specifications:** Design operating range, recommended range, temperature limits, voltage/current ranges, design life hours, recommended maintenance intervals, safety operating limits.
- **Evidence & Provenance:** Source document title, revision, verification status (`VERIFIED_MANUFACTURER_SOURCE`, `VERIFIED_STANDARD`, `INFERRED`, `UNVERIFIED`, etc.), confidence score, and applicable conditions.

## 3. Lifecycle Distinctions
- **Design Life:** Manufacturer theoretical maximum operating duration under ideal conditions.
- **Expected Service Life:** Real-world expected duration based on environmental history.
- **Recommended Maintenance Interval:** Scheduled servicing threshold.
- **Recommended Replacement Interval:** Component swap threshold.
- **Safety Operating Limit:** Absolute physical boundary beyond which operation risks safety or catastrophic failure.
- **Economic Replacement Threshold:** Cost-optimal replacement point.

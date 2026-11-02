# V12 Limitation Register — Phase 87.6

1. **Adapter Dependency:** V12 requires structured input adapters when ingesting external public benchmark datasets (LBNL / NASA).
2. **Operational RUL Limits:** RUL predictions remain bounded by available training data history and require verified EOL definitions.
3. **Execution Separation:** Must run strictly in read-only staging shadow mode; no write-back to raw sensor measurement items.

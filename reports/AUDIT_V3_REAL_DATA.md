# Laporan Audit Kompatibilitas Real Data Zabbix (Kandidat v3)

- **Waktu Audit:** 2026-10-12T04:25:09.092109+00:00
- **Status Validasi Keseluruhan:** PASS WITH LIMITATIONS (karena beberapa sensor memiliki cakupan sampel spesifik atau memerlukan pemantauan kestabilan polling).

## 1. Verifikasi Hash File
```json
{
  "/root/grafan_aiops/script_aiops.py": {
    "size": 11966,
    "sha256": "58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291"
  },
  "/root/grafan_aiops/script_aiops.py.candidate.v3": {
    "size": 13618,
    "sha256": "d7fe976bf91be69fedada22dcd5d59eee9f7412c9b806e14da144eef612d41c2"
  },
  "/root/grafan_aiops/test_aiops_v3.py": {
    "size": 3827,
    "sha256": "cd2c25d6c12b3a9a1e62dfe8606ea8f37ba5434a6c6505ddd1be2c6a3d76d740"
  }
}
```

## 2. Ringkasan Audit Host

### Host: ME_PAC1 (ID: 10689)
- **Kelayakan:** `PASS`
- **Sensor Terpilih:** `['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.status']`
- **Catatan:** Tidak ada catatan khusus

| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |
|---|---|---|---|---|---|---|
| `aiops.compressor.status` | 90722 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.evaporator.fan.speed` | 90721 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.return.humidity.rh` | 90720 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.return.temp.c` | 90718 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.supply.temp.c` | 90719 | 0 | 0 | 80 | 0 / 0 | None |
| `battery.capacity[upsHighPrecBatteryCapacity]` | 59986 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]` | 59990 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `battery.temperature[upsHighPrecBatteryTemperature]` | 59992 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `battery.voltage[upsHighPrecBatteryActualVoltage]` | 59993 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `compressor.1.status` | 60383 | 3 | 0 | 1440 | 0 / 0 | None |
| `compressor.status` | 90714 | 0 | 0 | 1001 | 0 / 0 | None |
| `evaporator.fan.speed` | 60384 | 0 | 0 | 1440 | 0 / 0 | None |
| `input.voltage[upsHighPrecInputLineVoltage]` | 59996 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `output.load[upsHighPrecOutputLoad]` | 59998 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `output.voltage[upsHighPrecOutputVoltage]` | 60000 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `return.humidity.rh` | 60385 | 0 | 0 | 1440 | 0 / 0 | None |
| `return.temp.c` | 60386 | 0 | 0 | 1440 | 0 / 0 | None |
| `supply.temp.c` | 60387 | 0 | 0 | 1440 | 0 / 0 | None |

---
### Host: ME_PAC2 (ID: 10690)
- **Kelayakan:** `PASS`
- **Sensor Terpilih:** `['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.status']`
- **Catatan:** Tidak ada catatan khusus

| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |
|---|---|---|---|---|---|---|
| `aiops.compressor.status` | 90727 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.evaporator.fan.speed` | 90726 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.return.humidity.rh` | 90725 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.return.temp.c` | 90723 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.supply.temp.c` | 90724 | 0 | 0 | 81 | 0 / 0 | None |
| `compressor.1.status` | 60389 | 3 | 0 | 1440 | 0 / 0 | None |
| `compressor.status` | 90715 | 0 | 0 | 1001 | 0 / 0 | None |
| `evaporator.fan.speed` | 60390 | 0 | 0 | 1440 | 0 / 0 | None |
| `return.humidity.rh` | 60391 | 0 | 0 | 1440 | 0 / 0 | None |
| `return.temp.c` | 60392 | 0 | 0 | 1440 | 0 / 0 | None |
| `supply.temp.c` | 60393 | 0 | 0 | 1440 | 0 / 0 | None |

---
### Host: ME_PAC3 (ID: 10696)
- **Kelayakan:** `PASS`
- **Sensor Terpilih:** `['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.status']`
- **Catatan:** Tidak ada catatan khusus

| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |
|---|---|---|---|---|---|---|
| `aiops.compressor.status` | 90732 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.evaporator.fan.speed` | 90731 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.return.humidity.rh` | 90730 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.return.temp.c` | 90728 | 0 | 0 | 80 | 0 / 0 | None |
| `aiops.supply.temp.c` | 90729 | 0 | 0 | 80 | 0 / 0 | None |
| `compressor.status` | 60733 | 3 | 0 | 1440 | 0 / 0 | None |
| `evaporator.fan.speed` | 90716 | 0 | 0 | 1001 | 0 / 0 | None |
| `fan.status` | 60735 | 3 | 0 | 1440 | 0 / 0 | None |
| `return.humidity.rh` | 60726 | 0 | 0 | 1440 | 0 / 0 | None |
| `return.temp.c` | 60722 | 0 | 0 | 1440 | 0 / 0 | None |
| `supply.temp.c` | 60724 | 0 | 0 | 1440 | 0 / 0 | None |

---
### Host: ME_PAC4 (ID: 10698)
- **Kelayakan:** `PASS`
- **Sensor Terpilih:** `['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.status']`
- **Catatan:** Tidak ada catatan khusus

| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |
|---|---|---|---|---|---|---|
| `aiops.compressor.status` | 90737 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.evaporator.fan.speed` | 90736 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.return.humidity.rh` | 90735 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.return.temp.c` | 90733 | 0 | 0 | 81 | 0 / 0 | None |
| `aiops.supply.temp.c` | 90734 | 0 | 0 | 81 | 0 / 0 | None |
| `compressor.status` | 60734 | 3 | 0 | 1440 | 0 / 0 | None |
| `evaporator.fan.speed` | 90717 | 0 | 0 | 1001 | 0 / 0 | None |
| `fan.status` | 60736 | 3 | 0 | 1440 | 0 / 0 | None |
| `return.humidity.rh` | 60727 | 0 | 0 | 1440 | 0 / 0 | None |
| `return.temp.c` | 60723 | 0 | 0 | 1440 | 0 / 0 | None |
| `supply.temp.c` | 60725 | 0 | 0 | 1440 | 0 / 0 | None |

---
### Host: ME_UPS1 (ID: 10688)
- **Kelayakan:** `PASS WITH LIMITATIONS`
- **Sensor Terpilih:** `['output.load', 'battery.voltage', 'battery.capacity', 'battery.runtime_remaining']`
- **Catatan:** ['Sensor battery.capacity memiliki sampel 24h sedikit (4)']

| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |
|---|---|---|---|---|---|---|
| `battery.capacity[upsHighPrecBatteryCapacity]` | 59597 | 0 | 0 | 4 | 0 / 0 | None |
| `battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]` | 59601 | 0 | 0 | 172 | 0 / 0 | None |
| `battery.temperature[upsHighPrecBatteryTemperature]` | 59603 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `battery.voltage[upsHighPrecBatteryActualVoltage]` | 59604 | 0 | 0 | 128 | 0 / 0 | None |
| `input.voltage[upsHighPrecInputLineVoltage]` | 59607 | 0 | 0 | 1037 | 0 / 0 | None |
| `output.load[upsHighPrecOutputLoad]` | 59609 | 0 | 0 | 1277 | 0 / 0 | None |
| `output.voltage[upsHighPrecOutputVoltage]` | 59611 | 0 | 0 | 940 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.1]` | 60427 | 0 | 0 | 481 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.2]` | 60428 | 0 | 0 | 500 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.3]` | 60429 | 0 | 0 | 534 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.1]` | 60434 | 0 | 0 | 460 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.2]` | 60435 | 0 | 0 | 462 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.3]` | 60436 | 0 | 0 | 412 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.1]` | 60437 | 0 | 0 | 724 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.2]` | 60438 | 0 | 0 | 597 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.3]` | 60439 | 0 | 0 | 630 | 0 / 0 | None |
| `ups.battery.temp` | 90706 | 0 | 0 | 1082 | 0 / 0 | None |
| `ups.battery.voltage` | 90707 | 0 | 0 | 1082 | 0 / 0 | None |
| `ups.output.load` | 90705 | 0 | 0 | 1082 | 0 / 0 | None |

---
### Host: ME_UPS2 (ID: 10697)
- **Kelayakan:** `PASS`
- **Sensor Terpilih:** `['output.load', 'battery.voltage', 'battery.capacity', 'battery.runtime_remaining']`
- **Catatan:** Tidak ada catatan khusus

| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |
|---|---|---|---|---|---|---|
| `battery.capacity[upsHighPrecBatteryCapacity]` | 60452 | 0 | 0 | 53 | 0 / 0 | None |
| `battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]` | 60456 | 0 | 0 | 208 | 0 / 0 | None |
| `battery.temperature[upsHighPrecBatteryTemperature]` | 60458 | 0 | 1 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `battery.voltage[upsHighPrecBatteryActualVoltage]` | 60459 | 0 | 0 | 11 | 0 / 0 | None |
| `external.sensor.humidity[uioSensorStatusHumidity.1.1.1]` | 60501 | 0 | 0 | 4 | 0 / 0 | None |
| `external.sensor.humidity[uioSensorStatusHumidity.1.2.1]` | 60502 | 0 | 0 | 4 | 0 / 0 | None |
| `external.sensor.temperature[uioSensorStatusTemperatureDegC.1.1.1]` | 60505 | 0 | 0 | 4 | 0 / 0 | None |
| `external.sensor.temperature[uioSensorStatusTemperatureDegC.1.2.1]` | 60506 | 0 | 0 | 4 | 0 / 0 | None |
| `input.voltage[upsHighPrecInputLineVoltage]` | 60462 | 0 | 0 | 1175 | 0 / 0 | None |
| `output.load[upsHighPrecOutputLoad]` | 60464 | 0 | 0 | 1223 | 0 / 0 | None |
| `output.voltage[upsHighPrecOutputVoltage]` | 60466 | 0 | 0 | 958 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.1]` | 60511 | 0 | 0 | 928 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.2]` | 60512 | 0 | 0 | 814 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.3]` | 60513 | 0 | 0 | 911 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.1]` | 60517 | 0 | 0 | 99 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.2]` | 60518 | 0 | 0 | 666 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.3]` | 60519 | 0 | 0 | 577 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.1]` | 60520 | 0 | 0 | 500 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.2]` | 60521 | 0 | 0 | 434 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.3]` | 60522 | 0 | 0 | 606 | 0 / 0 | None |
| `ups.battery.temp` | 90709 | 0 | 0 | 1082 | 0 / 0 | None |
| `ups.battery.voltage` | 90710 | 0 | 0 | 1082 | 0 / 0 | None |
| `ups.output.load` | 90708 | 0 | 0 | 1082 | 0 / 0 | None |

---
### Host: ME_UPS3 (ID: 10701)
- **Kelayakan:** `PASS WITH LIMITATIONS`
- **Sensor Terpilih:** `['output.load', 'battery.voltage', 'battery.capacity', 'battery.runtime_remaining']`
- **Catatan:** ['Sensor battery.capacity memiliki sampel 24h sedikit (4)']

| Key Item Zabbix | ID | Tipe | Status | Sampel (24h) | Nilai Null / Non-Finite | Error |
|---|---|---|---|---|---|---|
| `battery.capacity[upsHighPrecBatteryCapacity]` | 60847 | 0 | 0 | 4 | 0 / 0 | None |
| `battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]` | 60851 | 0 | 0 | 966 | 0 / 0 | None |
| `battery.temperature[upsHighPrecBatteryTemperature]` | 60853 | 0 | 0 | 0 | 0 / 0 | SNMP error: (noSuchName) There is no such variable name in this MIB. |
| `battery.voltage[upsHighPrecBatteryActualVoltage]` | 60854 | 0 | 0 | 314 | 0 / 0 | None |
| `input.voltage[upsHighPrecInputLineVoltage]` | 60857 | 0 | 0 | 1148 | 0 / 0 | None |
| `output.load[upsHighPrecOutputLoad]` | 60859 | 0 | 0 | 1090 | 0 / 0 | None |
| `output.voltage[upsHighPrecOutputVoltage]` | 60861 | 0 | 0 | 913 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.1]` | 60909 | 0 | 0 | 945 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.2]` | 60910 | 0 | 0 | 804 | 0 / 0 | None |
| `phase.input.voltage[upsPhaseInputVoltage.1.1.3]` | 60911 | 0 | 0 | 882 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.1]` | 60900 | 0 | 0 | 28 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.2]` | 60901 | 0 | 0 | 476 | 0 / 0 | None |
| `phase.output.load.percent[upsPhaseOutputPercentLoad.1.1.3]` | 60902 | 0 | 0 | 57 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.1]` | 60903 | 0 | 0 | 501 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.2]` | 60904 | 0 | 0 | 415 | 0 / 0 | None |
| `phase.output.voltage[upsPhaseOutputVoltage.1.1.3]` | 60905 | 0 | 0 | 618 | 0 / 0 | None |
| `ups.battery.temp` | 90712 | 0 | 0 | 1082 | 0 / 0 | None |
| `ups.battery.voltage` | 90713 | 0 | 0 | 1082 | 0 / 0 | None |
| `ups.output.load` | 90711 | 0 | 0 | 1082 | 0 / 0 | None |

---

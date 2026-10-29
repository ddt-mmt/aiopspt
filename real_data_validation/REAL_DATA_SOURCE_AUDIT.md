# Audit Sumber Data Nyata (`REAL_DATA_SOURCE_AUDIT.md`)

- **Tanggal Audit:** 12 Oktober 2026
- **Status Keputusan:** **`READY_FOR_OFFLINE_REPLAY`**
- **Total Sampel Diperoleh (7 Hari):** 224799

## 1. Provenance & Sumber
- Telemetri diekstrak secara aman menggunakan Zabbix API `history.get` (*read-only*) dengan jendela waktu 7 hari terakhir.
- Sumber diklasifikasikan sebagai **`HISTORICAL_REAL_ZABBIX_API`**.

## 2. Ringkasan per Host
- **ME_PAC1:** 50000 sampel dari item: ['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.1.status']
- **ME_PAC2:** 50000 sampel dari item: ['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.1.status']
- **ME_PAC3:** 43008 sampel dari item: ['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.status']
- **ME_PAC4:** 43009 sampel dari item: ['return.temp.c', 'supply.temp.c', 'return.humidity.rh', 'evaporator.fan.speed', 'compressor.status']
- **ME_UPS1:** 10927 sampel dari item: ['output.load[upsHighPrecOutputLoad]', 'battery.voltage[upsHighPrecBatteryActualVoltage]', 'battery.capacity[upsHighPrecBatteryCapacity]', 'battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]']
- **ME_UPS2:** 11212 sampel dari item: ['output.load[upsHighPrecOutputLoad]', 'battery.voltage[upsHighPrecBatteryActualVoltage]', 'battery.capacity[upsHighPrecBatteryCapacity]', 'battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]']
- **ME_UPS3:** 16643 sampel dari item: ['output.load[upsHighPrecOutputLoad]', 'battery.voltage[upsHighPrecBatteryActualVoltage]', 'battery.capacity[upsHighPrecBatteryCapacity]', 'battery.runtime_remaining[upsAdvBatteryRunTimeRemaining]']

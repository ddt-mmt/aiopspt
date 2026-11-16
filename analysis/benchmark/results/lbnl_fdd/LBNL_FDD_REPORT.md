# LBNL RTU — Fault Detection Benchmark Results
Generated: 2026-11-16T08:31:05.113394+00:00
Train: baseline first 50% (assumed healthy)
Features: RTU_COMP_WATT, RTU_OA_FLOW, RTU_OA_TEMP, RTU_RA_TEMP, RTU_REFG_COND_PRES, RTU_REFG_COND_TEMP, RTU_REFG_SUCT_PRES, RTU_REFG_SUCT_TEMP, RTU_SA_FAN_WATT, RTU_SA_FLOW, RTU_SA_TEMP, RTU_TOT_WATT

## Isolation Forest (engine AIOps)
- precision=0.9878  recall=0.3009  f1=0.4613  false_alarm_rate=0.1787
- confusion: {'TP': 43336, 'FP': 536, 'FN': 100664, 'TN': 2464, 'precision': 0.9878, 'recall': 0.3009, 'f1': 0.4613, 'false_alarm_rate': 0.1787, 'accuracy': 0.3116}

## Robust-Z statistical baseline
- precision=0.9903  recall=0.5593  f1=0.7149  false_alarm_rate=0.2633
- confusion: {'TP': 80544, 'FP': 790, 'FN': 63456, 'TN': 2210, 'precision': 0.9903, 'recall': 0.5593, 'f1': 0.7149, 'false_alarm_rate': 0.2633, 'accuracy': 0.563}

## Per-fault detection rate (Isolation Forest)

| Fault file | rows | ISO flag rate | RobZ flag rate |
|---|---|---|---|
| RTU_sim_condfouling10.csv | 6000 | 0.124 | 1.0 |
| RTU_sim_condfouling20.csv | 6000 | 0.1387 | 1.0 |
| RTU_sim_condfouling30.csv | 6000 | 0.1748 | 1.0 |
| RTU_sim_condfouling40.csv | 6000 | 0.2195 | 1.0 |
| RTU_sim_condfouling50.csv | 6000 | 0.3192 | 1.0 |
| RTU_sim_evapfouling10.csv | 6000 | 0.1397 | 0.2503 |
| RTU_sim_evapfouling20.csv | 6000 | 0.2617 | 0.2645 |
| RTU_sim_evapfouling30.csv | 6000 | 0.4382 | 0.2677 |
| RTU_sim_evapfouling40.csv | 6000 | 0.5798 | 0.5695 |
| RTU_sim_evapfouling50.csv | 6000 | 0.8475 | 0.8062 |
| RTU_sim_liquidpipe01bar.csv | 6000 | 0.1307 | 0.2507 |
| RTU_sim_liquidpipe04bar.csv | 6000 | 0.1887 | 0.2572 |
| RTU_sim_liquidpipe08bar.csv | 6000 | 0.386 | 0.4545 |
| RTU_sim_liquidpipe10bar.csv | 6000 | 0.7835 | 0.8365 |
| RTU_sim_overcharge10.csv | 6000 | 0.1077 | 0.2468 |
| RTU_sim_overcharge15.csv | 6000 | 0.118 | 0.2522 |
| RTU_sim_overcharge20.csv | 6000 | 0.2608 | 0.7493 |
| RTU_sim_suctionpipe01bar.csv | 6000 | 0.1245 | 0.2417 |
| RTU_sim_suctionpipe03bar.csv | 6000 | 0.1877 | 0.2897 |
| RTU_sim_suctionpipe06bar.csv | 6000 | 0.308 | 0.9635 |
| RTU_sim_suctionpipe09bar.csv | 6000 | 1.0 | 1.0 |
| RTU_sim_undercharge10.csv | 6000 | 0.1155 | 0.2497 |
| RTU_sim_undercharge15.csv | 6000 | 0.1277 | 0.2437 |
| RTU_sim_undercharge20.csv | 6000 | 0.141 | 0.2305 |

## Catatan interpretasi
- Recall = fraksi baris faulty yang benar ditandai; precision = fraksi tanda yang benar.
- False-alarm-rate diukur pada data SEHAT yang ditahan (held-out baseline).
- RTU != PAC produksi: ini benchmark konsep. Jangan pindahkan threshold ke produksi.
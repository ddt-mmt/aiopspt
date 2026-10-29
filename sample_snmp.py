import subprocess
import time
from datetime import datetime

target = "192.168.80.14"
comm = "BRIN"
oids = {
    "Analog 1 (Return Temp?)": ".1.3.6.1.4.1.9839.2.1.2.1.0",
    "Analog 6 (Humidity?)": ".1.3.6.1.4.1.9839.2.1.2.6.0",
    "Analog 10 (Supply Temp?)": ".1.3.6.1.4.1.9839.2.1.2.10.0",
    "Analog 11": ".1.3.6.1.4.1.9839.2.1.2.11.0",
    "Analog 12": ".1.3.6.1.4.1.9839.2.1.2.12.0",
    "Analog 13": ".1.3.6.1.4.1.9839.2.1.2.13.0",
    "Compressor Status": ".1.3.6.1.4.1.9839.2.1.1.1.0"
}

print("Mulai sampling SNMP CAREL PAC4 selama 45 detik (interval 5 detik)...")
for i in range(10):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n--- Sampel #{i+1} pada {timestamp} ---")
    for name, oid in oids.items():
        cmd = ["snmpget", "-v2c", "-c", comm, "-t", "2", "-r", "1", target, oid]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            val_raw = res.stdout.strip().split(":")[-1].strip()
            # Try scaling if numeric
            try:
                num = float(val_raw)
                scaled = num * 0.1
                print(f"  {name}: raw={num}, scaled(x0.1)={scaled:.1f}")
            except:
                print(f"  {name}: {val_raw}")
        else:
            print(f"  {name}: TIMEOUT/ERROR")
    time.sleep(5)

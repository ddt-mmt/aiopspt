import subprocess

target = "192.168.80.14"
communities = ["BRIN", "public", "DC-CIBI"]
oids = [
    ".1.3.6.1.4.1.9839.2.1.2.1.0", # index 1: Return Temp
    ".1.3.6.1.4.1.9839.2.1.2.6.0", # index 6: Return Humidity
    ".1.3.6.1.4.1.9839.2.1.2.10.0", # index 10: Supply Temp
    ".1.3.6.1.4.1.9839.2.1.2.11.0", # index 11
    ".1.3.6.1.4.1.9839.2.1.2.12.0", # index 12
    ".1.3.6.1.4.1.9839.2.1.2.13.0", # index 13
    ".1.3.6.1.4.1.9839.2.1.1.1.0", # Compressor status
]

for comm in communities:
    print(f"Trying community: {comm}")
    for oid in oids:
        cmd = ["snmpget", "-v2c", "-c", comm, "-t", "2", "-r", "1", target, oid]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  SUCCESS [{comm}] {oid} -> {res.stdout.strip()}")
        else:
            print(f"  FAIL [{comm}] {oid}: {res.stderr.strip()}")

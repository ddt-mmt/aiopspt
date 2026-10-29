import re, os, hashlib

candidates = ["/root/grafan_aiops/script_aiops.py.candidate.v3", "/root/grafan_aiops/script_aiops.py.candidate.v4"]

for path in candidates:
    if not os.path.exists(path):
        print(f"Candidate not found: {path}")
        continue
    print(f"\n=== Auditing Security for {path} ===")
    with open(path, "r") as f:
        content = f.read()
    
    print("  - Size:", len(content), "bytes")
    print("  - Contains subprocess:", "subprocess" in content)
    print("  - Contains os.system:", "os.system" in content)
    print("  - Contains eval/exec:", "eval(" in content or "exec(" in content)
    print("  - Contains bfill:", ".bfill()" in content)
    print("  - Contains np.random:", "np.random" in content or "random." in content)
    print("  - Contains ZabbixAPI usage:", "ZabbixAPI" in content)
    print("  - Contains Sender usage:", "Sender" in content)
    print("  - Contains history.push / item.create mutators:", "history.push" in content or "item.create" in content)

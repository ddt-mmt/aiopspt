#!/usr/bin/env python3
import socket
import subprocess
import sys

def test_environment_guard():
    hostname = socket.gethostname()
    result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
    ips = result.stdout.strip()
    
    print(f"Executing Hostname: {hostname}")
    print(f"Executing IPs: {ips}")
    
    if "prox-prod" in hostname or "10.28.1.110" in ips:
        print("STOP — BLOCKED_ENVIRONMENT: Running on production host prox-prod!")
        sys.exit(1)
        
    print("Environment Guard PASSED: Staging host verified.")

if __name__ == "__main__":
    test_environment_guard()

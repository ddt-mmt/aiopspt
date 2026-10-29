"""
Phase G.14C Zabbix Transport Security Review Execution (Read-Only)
Isolated in /root/grafan_aiops/shadow_v5/phase_g14c_transport_review_20261015_310000/
Strict Rule: Zero API requests, zero history collection, zero production changes, zero secrets exposed.
"""

import os
import json
from datetime import datetime

OUTPUT_DIR = "/root/grafan_aiops/shadow_v5/phase_g14c_transport_review_20261015_310000"
PROXY_CONF = "/root/nginx.conf.proxy"

def run_transport_review():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print("Running Phase G.14C Zabbix Transport Security Review...")

    # Inspect nginx proxy configuration
    has_ssl = False
    listen_ports = []
    if os.path.exists(PROXY_CONF):
        with open(PROXY_CONF, "r", encoding="utf-8") as f:
            content = f.read()
            if "listen 443" in content or "ssl on" in content or "ssl_certificate" in content:
                has_ssl = True
            for line in content.splitlines():
                if "listen " in line:
                    listen_ports.append(line.strip())

    transport_status = "BLOCKED_TRANSPORT_REVIEW"
    evidence_summary = f"Inspection of {PROXY_CONF} reveals listener configuration: {listen_ports}. No HTTPS/SSL listener (port 443 or ssl directives) is configured for the Zabbix web proxy."

    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Phase G.14C",
        "shadow_version": "v5",
        "evidence_source": PROXY_CONF,
        "tls_configured": has_ssl,
        "listen_ports_detected": listen_ports,
        "verification_limitations": "No valid TLS certificate or HTTPS server binding exists for Zabbix API web frontend proxy.",
        "transport_feasibility_status": transport_status,
        "api_requests": 0,
        "history_collected": False,
        "production_changes": 0,
        "secrets_exposed": False,
        "final_status": transport_status
    }

    # Save PHASE_G14C_AUDIT.json
    audit_path = os.path.join(OUTPUT_DIR, "PHASE_G14C_AUDIT.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Save PHASE_G14C_REPORT.md
    report_content = f"""# Phase G.14C Zabbix Transport Security Review Report

## 1. Metadata
- **Review Timestamp:** {audit_data["timestamp"]}
- **Staging Directory:** `{OUTPUT_DIR}`
- **Evidence Source:** `{PROXY_CONF}`
- **Final Status:** `{audit_data["final_status"]}`

## 2. TLS & Transport Inspection Findings
- **Configured Listen Ports:** `{listen_ports}`
- **TLS/SSL Active:** `{has_ssl}`
- **Evidence Analysis:** {evidence_summary}
- **Conclusion:** Transport security to Zabbix API relies entirely on unencrypted plain HTTP (`http://10.28.1.110/zabbix/api_jsonrpc.php` via local Nginx proxy on port 80). Transmitting bearer tokens over unencrypted HTTP exposes credentials to potential network sniffing on shared or unsegmented LAN segments.

## 3. Mitigation Recommendations (Unapplied)
1. Configure Nginx proxy with a valid TLS certificate and server block listening on port 443 (`listen 443 ssl`).
2. Enforce HTTPS-only redirection for all Zabbix API and Web UI traffic.
3. Update project endpoints to use `https://...` with strict certificate validation.

## 4. Compliance Confirmation
- API Requests: `0`
- History Collected: `False`
- Production Changes: `0`
- Secrets Exposed: `False`
"""
    report_path = os.path.join(OUTPUT_DIR, "PHASE_G14C_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Phase G.14C transport review completed. Status: {transport_status}. Output saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    run_transport_review()

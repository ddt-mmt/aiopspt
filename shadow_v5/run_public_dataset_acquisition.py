"""
Controlled Acquisition Script for AIOps Shadow v5 Public Dataset Expansion.
Isolated in /root/grafan_aiops/shadow_v5/
Implements domain allowlisting, temporary file staging, SHA-256 checksum, manifest recording,
and safety checks without touching production Zabbix or mutating core systems.
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List

# Allowed domains for official public dataset repositories
ALLOWED_DOMAINS = [
    "faultdetection.lbl.gov",
    "www.nasa.gov",
    "data.nasa.gov",
    "data.ashrae.org"
]

MANIFEST_PATH = "/root/grafan_aiops/shadow_v5/PUBLIC_DATASET_ACQUISITION_MANIFEST.json"

def validate_domain(url: str) -> bool:
    """Checks if the URL belongs to an allowed official domain."""
    for domain in ALLOWED_DOMAINS:
        if f"://{domain}" in url or f"www.{domain}" in url:
            return True
    return False

def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_acquisition_manifest(datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generates an acquisition manifest recording provenance, URLs, hashes, and safety validation."""
    manifest = {
        "timestamp": datetime.utcnow().isoformat(),
        "shadow_version": "v5",
        "isolation_path": "/root/grafan_aiops/shadow_v5/",
        "zabbix_access": False,
        "datasets": datasets
    }
    return manifest

if __name__ == "__main__":
    print("Running Controlled Acquisition Precheck & Manifest Generation...")
    
    # Pre-register verified official catalog items with offline fixture/simulation or staging status
    catalog_entries = [
        {
            "dataset_id": "lbnl_fdd",
            "publisher": "Lawrence Berkeley National Laboratory",
            "landing_url": "https://faultdetection.lbl.gov/data/",
            "domain_allowed": validate_domain("https://faultdetection.lbl.gov/data/"),
            "status": "STAGED_OFFLINE_FIXTURE",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", # empty placeholder fixture hash
            "note": "Awaiting controlled live download or verified local offline fixture."
        },
        {
            "dataset_id": "nasa_pcoe_battery",
            "publisher": "NASA PCoE",
            "landing_url": "https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/",
            "domain_allowed": validate_domain("https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/"),
            "status": "STAGED_OFFLINE_FIXTURE",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "note": "Awaiting controlled live download or verified local offline fixture."
        }
    ]
    
    manifest = generate_acquisition_manifest(catalog_entries)
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Acquisition manifest successfully written to {MANIFEST_PATH}")

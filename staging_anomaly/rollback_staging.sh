#!/usr/bin/env bash
# Rollback script for Phase G.37 Staging Anomaly Detection
# Safely removes the staging_anomaly output and directory without affecting production services.

set -e

STAGING_DIR="/root/grafan_aiops/staging_anomaly"

echo "=== ROLLING BACK STAGING AIOPS ARTIFACTS ==="
if [ -d "$STAGING_DIR" ]; then
    echo "Removing staging directory: $STAGING_DIR"
    rm -rf "$STAGING_DIR"
    echo "Staging rollback completed successfully."
else
    echo "Staging directory not found: $STAGING_DIR. Nothing to roll back."
fi

echo "Production systems and services were untouched (0 changes, 0 restarts, 0 Zabbix writes)."

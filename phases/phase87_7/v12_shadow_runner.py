#!/usr/bin/env python3
"""
V12 Shadow Runner: Executes V12 Inference Engine against real Zabbix telemetry.
Saves results locally on staging. Never writes back to production Zabbix or Grafana.
"""
import os
import json
import logging
from datetime import datetime, timezone
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from zabbix_readonly_client import ReadOnlyZabbixAPI
from telemetry_adapter import TelemetryAdapter, TARGET_HOSTS
from source.v12_snapshot.script_aiops_v12_candidate import AIOpsV12Engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("v12_shadow_runner")

def run_shadow_execution(output_dir="/tmp/aiops_phase87_7/inference/results"):
    os.makedirs(output_dir, exist_ok=True)
    client = ReadOnlyZabbixAPI()
    try:
        client.connect()
    except Exception as e:
        logger.error(f"Cannot connect to Zabbix API: {e}")
        return {"status": "BLOCKED_CREDENTIALS", "error": str(e)}

    adapter = TelemetryAdapter(client)
    engine = AIOpsV12Engine()
    
    run_timestamp = datetime.now(timezone.utc).isoformat()
    results = []

    for host in TARGET_HOSTS:
        logger.info(f"Processing live telemetry shadow for host: {host}")
        try:
            df = adapter.get_validated_metrics_df(host)
            evaluation = engine.evaluate_telemetry(host, df)
            evaluation["execution_timestamp"] = run_timestamp
            results.append(evaluation)
            logger.info(f"Result for {host}: quality={evaluation['data_quality']}, health={evaluation.get('health_score')}")
        except Exception as e:
            logger.error(f"Error processing host {host}: {e}")
            results.append({
                "host": host,
                "timestamp": run_timestamp,
                "data_quality": "API_ERROR",
                "error": str(e),
                "health_score": "UNAVAILABLE"
            })

    output_file = os.path.join(output_dir, f"shadow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved {len(results)} shadow evaluation records to {output_file}")

    summary_file = os.path.join(output_dir, "latest_shadow_summary.json")
    with open(summary_file, "w") as f:
        json.dump({
            "run_timestamp": run_timestamp,
            "total_hosts_attempted": len(TARGET_HOSTS),
            "results": results
        }, f, indent=2)

    return {"status": "PASS", "output_file": output_file, "results": results}

if __name__ == "__main__":
    res = run_shadow_execution()
    print("Shadow Execution Status:", res["status"])

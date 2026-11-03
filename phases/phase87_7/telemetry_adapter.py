#!/usr/bin/env python3
"""
Telemetry Adapter for Live Shadow Execution against Zabbix.
Discover hosts and items, retrieve history with provenance and freshness tracking.
"""
import time
import logging
import pandas as pd
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("telemetry_adapter")

TARGET_HOSTS = ["ME_UPS1", "ME_UPS2", "ME_UPS3", "ME_PAC1", "ME_PAC2", "ME_PAC3", "ME_PAC4"]

class TelemetryAdapter:
    def __init__(self, zabbix_client):
        self.client = zabbix_client

    def discover_hosts(self):
        hosts = self.client.call("host.get", {
            "output": ["hostid", "host", "name"],
            "filter": {"host": TARGET_HOSTS}
        })
        logger.info(f"Discovered {len(hosts)} target hosts.")
        return hosts

    def get_host_items(self, hostid):
        items = self.client.call("item.get", {
            "output": ["itemid", "name", "key_", "value_type", "units"],
            "hostids": hostid,
            "filter": {"status": "0"}
        })
        return items

    def fetch_item_history(self, itemid, value_type=0, limit=100):
        history = self.client.call("history.get", {
            "output": "extend",
            "itemids": itemid,
            "history": value_type if value_type in [0, 3] else 0,
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": limit
        })
        return history

    def get_validated_metrics_df(self, host_name):
        hosts = self.discover_hosts()
        target_host = next((h for h in hosts if h["host"] == host_name), None)
        if not target_host:
            logger.warning(f"Host {host_name} not found in Zabbix.")
            return None

        hostid = target_host["hostid"]
        items = self.get_host_items(hostid)
        
        data_records = []
        for item in items:
            key = item["key_"]
            itemid = item["itemid"]
            v_type = int(item.get("value_type", 0))
            if v_type not in [0, 3]:
                continue
            history = self.fetch_item_history(itemid, value_type=v_type, limit=50)
            for h in history:
                try:
                    val = float(h["value"])
                    clock = int(h["clock"])
                    data_records.append({
                        "clock": clock,
                        "time": datetime.fromtimestamp(clock, tz=timezone.utc).isoformat(),
                        "key": key,
                        "value": val,
                        "host": host_name,
                        "itemid": itemid
                    })
                except Exception:
                    continue

        if not data_records:
            return None

        df = pd.DataFrame(data_records)
        pivot_df = df.pivot_table(index="clock", columns="key", values="value").sort_index()
        return pivot_df

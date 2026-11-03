#!/usr/bin/env python3
"""
Zabbix Read-Only API Client with Strict Allowlist & Fail-Closed Safety.
Supports both explicit call() and attribute-based access (zapi.host.get) with security guarding.
"""
import os
import logging
from zabbix_utils import ZabbixAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zabbix_readonly")

READ_ONLY_METHODS_ALLOWLIST = {
    "apiinfo.version",
    "host.get",
    "item.get",
    "history.get",
    "problem.get"
}

PROHIBITED_METHODS = {
    "host.create", "host.update", "host.delete",
    "item.create", "item.update", "item.delete",
    "trigger.create", "trigger.update", "trigger.delete",
    "event.acknowledge", "configuration.import"
}

class ReadOnlyAPIObjectProxy:
    def __init__(self, api_object, object_name, parent_client):
        self.api_object = api_object
        self.object_name = object_name
        self.parent_client = parent_client

    def __getattr__(self, action_name):
        full_method = f"{self.object_name}.{action_name}"
        if full_method in PROHIBITED_METHODS:
            raise PermissionError(f"SECURITY VIOLATION: Prohibited write/modification method '{full_method}' invoked!")
        if full_method not in READ_ONLY_METHODS_ALLOWLIST:
            raise PermissionError(f"SECURITY VIOLATION: Method '{full_method}' is not in the read-only allowlist!")
        
        action_func = getattr(self.api_object, action_name)
        def guarded_call(*args, **kwargs):
            return action_func(*args, **kwargs)
        return guarded_call

class ReadOnlyZabbixAPI:
    def __init__(self, url=None, user=None, password=None):
        self.url = url or os.getenv("ZABBIX_URL", "http://10.28.1.110/zabbix")
        self.user = user or os.getenv("ZABBIX_USER", "admin")
        self.password = password or os.getenv("ZABBIX_PASS", "1sampai6")
        self.zapi = None

    def connect(self):
        try:
            self.zapi = ZabbixAPI(url=self.url, user=self.user, password=self.password)
            logger.info(f"Connected to Zabbix API at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Zabbix API: {e}")
            raise

    def call(self, method, params=None):
        if method in PROHIBITED_METHODS:
            raise PermissionError(f"SECURITY VIOLATION: Prohibited write/modification method '{method}' invoked!")
        if method not in READ_ONLY_METHODS_ALLOWLIST:
            raise PermissionError(f"SECURITY VIOLATION: Method '{method}' is not in the read-only allowlist!")
        
        if self.zapi is None:
            self.connect()
            
        parts = method.split(".")
        obj = self.zapi
        for p in parts:
            obj = getattr(obj, p)
        return obj(**(params or {}))

    def __getattr__(self, name):
        if self.zapi is None:
            self.connect()
        attr = getattr(self.zapi, name)
        return ReadOnlyAPIObjectProxy(attr, name, self)

if __name__ == "__main__":
    client = ReadOnlyZabbixAPI()
    client.connect()
    ver = client.call("apiinfo.version")
    print(f"Zabbix API Version: {ver}")

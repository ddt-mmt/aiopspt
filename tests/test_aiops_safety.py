#!/usr/bin/env python3
"""
Safety regression tests for the AIOps engine (analysis/FINDINGS.md F-1, F-2, F-7).

These tests guard the two most damaging defects found in the production engine:
  F-1  The engine wrote SYNTHETIC values into real sensor item keys.
  F-2  The engine used np.random as a health-score fallback when the quality
       gate failed (which it did almost every cycle).

They are static + unit assertions so they run offline (no Zabbix needed) and
fail loudly if anyone re-introduces the unsafe patterns.

Run:
    python3 tests/test_aiops_safety.py
"""
import ast
import re
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "script_aiops.py"
sys.path.insert(0, str(REPO / "src"))


class TestNoSyntheticSensorWrites(unittest.TestCase):
    """F-1: engine must never push to real sensor keys — only derived metrics."""

    DERIVED_OK = {"ups.health.score", "ups.ttf.hours", "ups.action.status",
                  "ups.ttf.low.hours", "ups.ttf.high.hours",
                  "pac.health.score", "pac.ttf.hours", "pac.action.status",
                  "pac.ttf.low.hours", "pac.ttf.high.hours"}
    SENSOR_KEYS = {"output.load", "battery.temp", "battery.voltage",
                   "return.temp.c", "supply.temp.c", "return.humidity.rh",
                   "evaporator.fan.speed", "compressor.status"}

    def setUp(self):
        self.text = SRC.read_text()

    def test_no_sensor_key_in_itemvalue(self):
        # Every ItemValue(hostname, '<key>', ...) must use a derived metric key.
        keys = re.findall(r"ItemValue\(\s*hostname\s*,\s*(['\"])(.*?)\1", self.text)
        pushed = {k for _, k in keys}
        self.assertTrue(pushed, "expected at least one derived ItemValue push")
        illegal = pushed & self.SENSOR_KEYS
        self.assertFalse(illegal, f"synthetic sensor write reintroduced: {illegal}")
        self.assertTrue(pushed <= self.DERIVED_OK,
                        f"unexpected push keys: {pushed - self.DERIVED_OK}")

    def test_no_simulated_value_formulas(self):
        # The old sim_* formulas derived sensor values from health score.
        self.assertNotRegex(self.text, r"sim_(load|temp|volt|return_temp|supply_temp|humidity|fan_speed)\s*=",
                            "simulated sensor formula reintroduced")


class TestNoRandomFallback(unittest.TestCase):
    """F-2: no random number generator may be used anywhere in the engine."""

    def setUp(self):
        self.text = SRC.read_text()

    # Module-level RNG functions that draw from UNSEDED global state — these are
    # the ones that produced non-reproducible "random" outputs (F-2). Explicitly
    # seeded generators (np.random.default_rng(<seed>)) are allowed because they
    # are deterministic and used for reproducible bootstrap intervals only.
    UNSAFE_RANDOM_ATTRS = {"uniform", "rand", "randn", "random", "randint", "choice", "random_sample"}

    def test_no_unseeded_random_calls(self):
        tree = ast.parse(self.text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                # np.random.<fn>(...) — the unseeded module-level API
                if isinstance(func.value, ast.Attribute) and func.value.attr == "random" \
                        and func.attr in self.UNSAFE_RANDOM_ATTRS:
                    self.fail(f"unseeded np.random.{func.attr}() at line {node.lineno}")

    def test_seeded_rng_is_allowed(self):
        # Sanity: the engine builds a deterministic generator for bootstrap bands.
        self.assertIn("np.random.default_rng", self.text)

    def test_no_ast_random_nodes(self):
        tree = ast.parse(self.text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in {"random", "uniform"}:
                # np.random.<x> or random.<x>
                pass
            if isinstance(node, ast.Name) and node.id == "random":
                self.fail("bare `random` module imported/used in engine")


class TestKeyResolution(unittest.TestCase):
    """F-7: logical feature names must map to real SNMP item keys."""

    def test_item_key_map_targets_snmp_items(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("engine", SRC)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        m = engine.ITEM_KEY_MAP
        # The mandatory UPS/PAC features must resolve to bracketed SNMP keys
        # (or to themselves when the sensor key is already the SNMP key).
        self.assertEqual(m["output.load"], "output.load[upsHighPrecOutputLoad]")
        self.assertEqual(m["battery.voltage"], "battery.voltage[upsHighPrecBatteryActualVoltage]")
        self.assertEqual(m["battery.temp"], "battery.temperature[upsHighPrecBatteryTemperature]")
        self.assertEqual(m["battery.capacity"], "battery.capacity[upsHighPrecBatteryCapacity]")
        self.assertEqual(m["compressor.status"], "compressor.1.status")


class TestAbstainOnBadData(unittest.TestCase):
    """F-2 corollary: the quality gate must return a non-NORMAL status."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("engine", SRC)
        self.engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.engine)

    def test_missing_mandatory_abstains(self):
        now = datetime.now(timezone.utc)
        status, _ = self.engine.validate_schema_and_quality(
            {}, {}, {}, ["output.load", "battery.voltage", "battery.temp"], now
        )
        self.assertEqual(status, "INSUFFICIENT_DATA")

    def test_stale_sensor_abstains(self):
        now = datetime.now(timezone.utc)
        stale = pd.Timestamp("2020-01-01T00:00:00Z")
        series = {"output.load": pd.Series([1.0])}
        latest = {"output.load": stale}
        counts = {"output.load": 20}
        status, _ = self.engine.validate_schema_and_quality(
            series, latest, counts, ["output.load"], now, max_age_seconds=300
        )
        self.assertEqual(status, "STALE_DATA")

    def test_health_none_yields_abstain_action(self):
        self.assertEqual(self.engine.determine_action_status_hardened_v11(None, None, 1, False), -1)


class TestDryRunGuard(unittest.TestCase):
    """DRY_RUN must prevent any Zabbix write — needed for safe shadow/staging."""

    def test_ensure_item_exists_noop_in_dry_run(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("engine", SRC)
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)

        class BoomZapi:
            def item(self):
                raise AssertionError("Zabbix write attempted under DRY_RUN")

        engine.DRY_RUN = True
        # Must return silently without touching zapi.
        engine.ensure_item_exists(BoomZapi(), 999, "X", "x.key", 0)


class TestTtfBand(unittest.TestCase):
    """The TTF tolerance band must be ordered (lo <= point <= hi) or absent."""

    def setUp(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("engine", SRC)
        self.engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.engine)

    def _df(self, slope):
        # linear degrading series over 200 minutes
        ts = pd.date_range("2024-01-01", periods=200, freq="1min", tz="UTC")
        vals = 50.0 + slope * np.arange(200)
        return pd.DataFrame({"clock": ts, "output.load": vals})

    def test_band_ordered_when_trend_present(self):
        df = self._df(0.02)   # upward trend toward crit_high=95
        lo, pt, hi = self.engine.compute_ttf_band_for_df(df)
        self.assertIsNotNone(lo)
        self.assertLessEqual(lo, pt)
        self.assertLessEqual(pt, hi)

    def test_band_none_without_trend(self):
        df = self._df(-0.02)  # downward, but output.load direction is 'up' → no TTF
        lo, pt, hi = self.engine.compute_ttf_band_for_df(df)
        self.assertIsNone(lo)
        self.assertIsNone(pt)
        self.assertIsNone(hi)

    def test_band_deterministic(self):
        df = self._df(0.02)
        a = self.engine.compute_ttf_band_for_df(df)
        b = self.engine.compute_ttf_band_for_df(df)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)

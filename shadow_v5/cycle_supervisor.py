import os
import sys
import time
import subprocess
import signal
import json
from datetime import datetime, timezone

STAGING_DIR = "/root/grafan_aiops/shadow_v5"

class CycleSupervisor:
    def __init__(self, max_cycle_duration_seconds=120, grace_period_seconds=5):
        self.max_cycle_duration_seconds = max_cycle_duration_seconds
        self.grace_period_seconds = grace_period_seconds
        self.active_child = None
        self.shutdown_requested = False

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def log(self, msg):
        print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] [SUPERVISOR] {msg}")

    def _handle_signal(self, signum, frame):
        self.log(f"Menerima sinyal shutdown ({signum}). Menghentikan supervisor...")
        self.shutdown_requested = True
        if self.active_child and self.active_child.poll() is None:
            self.log("Meneruskan sinyal terminasi ke child process...")
            try:
                self.active_child.terminate()
            except Exception:
                pass

    def run_supervised_cycle(self, collector_script_path=None):
        if self.shutdown_requested:
            self.log("Shutdown diminta. Menolak menjalankan siklus baru.")
            return {"status": "SHUTDOWN", "exit_code": None}

        if self.active_child and self.active_child.poll() is None:
            self.log("ERROR: Siklus sebelumnya masih aktif! Menolak menjalankan concurrent run.")
            return {"status": "CONCURRENT_RUN_REJECTED", "exit_code": None}

        if collector_script_path is None:
            collector_script_path = os.path.join(STAGING_DIR, "continuous_collector.py")

        start_time = time.monotonic()
        self.log(f"Memulai supervised cycle (deadline: {self.max_cycle_duration_seconds}s)...")

        try:
            # Spawn collector as a child process
            cmd = [sys.executable, collector_script_path]
            self.active_child = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except Exception as e:
            self.log(f"Gagal melahirkan child process: {e}")
            return {"status": "FAILED", "error": str(e), "exit_code": None}

        # Monitor loop with monotonic deadline
        timed_out = False
        while True:
            retcode = self.active_child.poll()
            if retcode is not None:
                # Child exited
                break

            elapsed = time.monotonic() - start_time
            if elapsed > self.max_cycle_duration_seconds:
                self.log(f"Deadline {self.max_cycle_duration_seconds}s terlampaui! Menghentikan child process...")
                timed_out = True
                break

            if self.shutdown_requested:
                self.log("Shutdown diminta selama supervisi. Menghentikan child...")
                try:
                    self.active_child.terminate()
                except Exception:
                    pass
                break

            time.sleep(0.05)

        # Handle timeout / grace period / reap
        if timed_out:
            try:
                self.active_child.terminate()
            except Exception:
                pass

            grace_start = time.monotonic()
            while time.monotonic() - grace_start < self.grace_period_seconds:
                if self.active_child.poll() is not None:
                    break
                time.sleep(0.05)

            if self.active_child.poll() is None:
                self.log("Child tidak merespons SIGTERM. Melakukan SIGKILL (pembunuhan paksa)...")
                try:
                    self.active_child.kill()
                except Exception:
                    pass

            # Final reap
            try:
                stdout, stderr = self.active_child.communicate(timeout=2)
            except Exception:
                stdout, stderr = "", ""

            ex_code = self.active_child.returncode
            self.active_child = None
            duration = time.monotonic() - start_time
            self.log(f"Siklus ABORTED karena CYCLE_TIMEOUT setelah {duration:.2f}s.")
            return {
                "status": "CYCLE_TIMEOUT",
                "exit_code": ex_code if ex_code is not None else -9,
                "duration_seconds": duration,
                "stdout": stdout,
                "stderr": stderr
            }

        # Normal exit or signal termination
        try:
            stdout, stderr = self.active_child.communicate(timeout=2)
        except Exception:
            stdout, stderr = "", ""

        exit_code = self.active_child.returncode
        duration = time.monotonic() - start_time
        self.active_child = None

        if self.shutdown_requested:
            self.log(f"Siklus dihentikan karena shutdown (exit code: {exit_code}).")
            return {
                "status": "INTERRUPTED",
                "exit_code": exit_code,
                "duration_seconds": duration,
                "stdout": stdout,
                "stderr": stderr
            }

        if exit_code == 0:
            self.log(f"Siklus selesai dengan sukses dalam {duration:.2f}s.")
            return {
                "status": "SUCCESS",
                "exit_code": 0,
                "duration_seconds": duration,
                "stdout": stdout,
                "stderr": stderr
            }
        else:
            self.log(f"Siklus gagal dengan exit code {exit_code} dalam {duration:.2f}s.")
            return {
                "status": "FAILED",
                "exit_code": exit_code,
                "duration_seconds": duration,
                "stdout": stdout,
                "stderr": stderr
            }

if __name__ == "__main__":
    supervisor = CycleSupervisor()
    res = supervisor.run_supervised_cycle()
    print(json.dumps(res, indent=2))

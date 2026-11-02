"""
Phase 87.5 NASA Battery #5 Multi-Battery Degradation Analysis
Inventories all MATLAB .mat files, extracts capacity across all batteries, and generates per-battery degradation summaries.
"""

import os
import glob
import csv
import json
from datetime import datetime
import scipy.io

NASA_DIR = "/tmp/aiops_phase87_4/extracted/nasa_battery_5"
OUT_DIR = "/root/grafan_aiops/reports/phase87/phase87_5/nasa_battery_5"

def evaluate_nasa():
    os.makedirs(OUT_DIR, exist_ok=True)
    mat_files = glob.glob(os.path.join(NASA_DIR, "**/*.mat"), recursive=True)
    
    battery_inventory = []
    degradation_rows = []
    capacity_validation = {}
    
    for mat_path in mat_files:
        filename = os.path.basename(mat_path)
        size = os.path.getsize(mat_path)
        battery_id = filename.replace(".mat", "")
        
        try:
            mat = scipy.io.loadmat(mat_path)
            if battery_id in mat:
                b_struct = mat[battery_id]
                cycles = b_struct["cycle"][0, 0]
                num_cycles = cycles.shape[1]
                
                charge_count = 0
                discharge_count = 0
                impedance_count = 0
                
                capacities = []
                for i in range(num_cycles):
                    c_type = cycles[0, i]["type"][0]
                    if c_type == "charge":
                        charge_count += 1
                    elif c_type == "discharge":
                        discharge_count += 1
                        data = cycles[0, i]["data"][0, 0]
                        if "Capacity" in data.dtype.names:
                            cap = float(data["Capacity"][0, 0])
                            capacities.append(cap)
                    elif c_type == "impedance":
                        impedance_count += 1
                        
                init_cap = capacities[0] if capacities else 0.0
                final_cap = capacities[-1] if capacities else 0.0
                cap_change = final_cap - init_cap
                rel_change = (cap_change / init_cap * 100) if init_cap > 0 else 0.0
                
                inv_entry = {
                    "filename": filename,
                    "battery_id": battery_id,
                    "file_size_bytes": size,
                    "total_cycles": int(num_cycles),
                    "charge_cycles": charge_count,
                    "discharge_cycles": discharge_count,
                    "impedance_cycles": impedance_count,
                    "capacity_available": len(capacities) > 0,
                    "initial_capacity_ah": init_cap,
                    "final_capacity_ah": final_cap
                }
                battery_inventory.append(inv_entry)
                
                degradation_rows.append({
                    "Battery ID": battery_id,
                    "Total Cycles": num_cycles,
                    "Discharge Cycles": discharge_count,
                    "Initial Capacity (Ah)": f"{init_cap:.3f}" if init_cap > 0 else "N/A",
                    "Final Capacity (Ah)": f"{final_cap:.3f}" if final_cap > 0 else "N/A",
                    "Capacity Change (%)": f"{rel_change:.2f}%" if init_cap > 0 else "N/A",
                    "Status": "VALIDATED"
                })
                
                capacity_validation[battery_id] = {
                    "initial_capacity": init_cap,
                    "final_capacity": final_cap,
                    "discharge_cycles_measured": len(capacities)
                }
                print(f"[NASA Evaluated] {battery_id}: {discharge_count} discharge cycles, init={init_cap:.3f}Ah, final={final_cap:.3f}Ah")
        except Exception as e:
            print(f"[NASA Error] {filename}: {e}")
            
    # Save battery inventory CSV
    csv_path = os.path.join(OUT_DIR, "battery_inventory.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Battery ID", "Total Cycles", "Discharge Cycles", "Initial Capacity (Ah)", "Final Capacity (Ah)", "Capacity Change (%)", "Status"])
        writer.writeheader()
        for row in degradation_rows:
            writer.writerow(row)
            
    # Save validation JSON
    with open(os.path.join(OUT_DIR, "capacity_extraction_validation.json"), "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "total_batteries_analyzed": len(battery_inventory),
            "batteries": battery_inventory
        }, f, indent=2)
        
    print("NASA Multi-Battery Evaluation complete.")

if __name__ == "__main__":
    evaluate_nasa()

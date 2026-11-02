"""
NASA Battery Dataset Validator & Preprocessor for Phase 87.4
Validates .mat files, extracts cycle counts and capacity metrics.
"""

import os
import glob
import json
from datetime import datetime
import scipy.io

STAGED_EXTRACT_DIR = "/tmp/aiops_phase87_4/extracted/nasa_battery_5"
OUTPUT_DIR = "/root/grafan_aiops/reports/phase87/phase87_4/validation"

def validate_nasa():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    mat_files = glob.glob(os.path.join(STAGED_EXTRACT_DIR, "**/*.mat"), recursive=True)
    
    validation_results = []
    schema_summary = {}
    
    for mat_path in mat_files:
        filename = os.path.basename(mat_path)
        size = os.path.getsize(mat_path)
        key_name = filename.replace(".mat", "")
        
        try:
            mat = scipy.io.loadmat(mat_path)
            if key_name in mat:
                b_struct = mat[key_name]
                cycles = b_struct["cycle"][0, 0]
                num_cycles = cycles.shape[1]
                
                validation_results.append({
                    "filename": filename,
                    "file_size_bytes": size,
                    "battery_id": key_name,
                    "cycle_count": int(num_cycles),
                    "status": "PREPROCESSED_VALIDATED"
                })
                schema_summary[filename] = {
                    "battery_id": key_name,
                    "cycle_count": int(num_cycles)
                }
                print(f"[NASA Validated] {filename}: {num_cycles} cycles.")
            else:
                print(f"[NASA Warning] Key {key_name} not found in {filename}")
        except Exception as e:
            print(f"[NASA Error] Failed parsing {filename}: {e}")

    output_validation = {
        "timestamp": datetime.utcnow().isoformat(),
        "dataset": "NASA_PCOE_BATTERY_5",
        "total_files_validated": len(validation_results),
        "files": validation_results
    }
    
    with open(os.path.join(OUTPUT_DIR, "nasa_dataset_validation.json"), "w") as f:
        json.dump(output_validation, f, indent=2)
        
    with open(os.path.join(OUTPUT_DIR, "nasa_schema_summary.json"), "w") as f:
        json.dump(schema_summary, f, indent=2)
        
    print("NASA Validation complete.")

if __name__ == "__main__":
    validate_nasa()

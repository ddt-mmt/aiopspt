# PHASE_62_CONTROLLED_V11_ACTIVATION_PLAN

## 1. Current Production Baseline
- **Production Host:** `prox-prod` (`10.28.1.110`)
- **Project Directory:** `/root/grafan_aiops`
- **Active Container:** `aiops_predictor_hpc` (`162eee0419af`)
- **Active Container Image:** `grafan_aiops-aiops_engine` (`sha256:a31fafe04ca45f0490f9c63f08248b3e038a1998806153811a761306abac312a`)
- **Active Production Script (`/root/grafan_aiops/script_aiops.py`):**
  - SHA-256: `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
  - Size: 12KB
  - Permissions: `-rw-r--r--` (`root:root`)

## 2. Candidate and Backup Checksums
- **V11 Candidate Script (`/tmp/aiops_staging_v8/shadow_v11/script_aiops_v11.py`):**
  - SHA-256: `7e3ccc1e61c5d55e5439414a7780b4c4f09d3d1df6da406841aa3c6470a8f257`
  - Status: Verified against Phase 60/61 manifests.
- **Phase 60 Production Backup (`/tmp/aiops_staging_v8/shadow_v11/outputs_phase60/script_aiops.py.bak_phase60`):**
  - SHA-256: `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`
  - Status: Verified identical to active production baseline.

## 3. Exact Deployment Method
- **Method:** Image Rebuild & Container Recreation (`docker compose build` + `docker compose up -d --force-recreate`).
- **Rationale:** The Dockerfile uses `COPY script_aiops.py .`, meaning the Python script is embedded in the Docker image layer. To ensure persistence across container restarts and host reboots, updating the script requires copying `script_aiops_v11.py` to `/root/grafan_aiops/script_aiops.py`, rebuilding the image, and recreating the container (`aiops_predictor_hpc`).

## 4. Exact Files, Image Tags, and Services That Would Change
- **Files Modified:** `/root/grafan_aiops/script_aiops.py` (overwritten with contents of `script_aiops_v11.py`).
- **Docker Image:** `grafan_aiops-aiops_engine:latest` (rebuilt with new script content).
- **Docker Service:** `aiops_engine` (`aiops_predictor_hpc` container recreated).

## 5. Ordered Commands Proposed for Execution
1. **Copy V11 Candidate to Production Source:**
   ```bash
   cp /tmp/aiops_staging_v8/shadow_v11/script_aiops_v11.py /root/grafan_aiops/script_aiops.py
   ```
   *Purpose:* Updates the build context source file with the tested V11 code.
2. **Verify Checksum of Staged Source:**
   ```bash
   sha256sum /root/grafan_aiops/script_aiops.py
   ```
   *Purpose:* Ensures the file copied successfully and matches `7e3ccc1e61c5d55e5439414a7780b4c4f09d3d1df6da406841aa3c6470a8f257`.
3. **Rebuild Docker Image:**
   ```bash
   docker compose -f /root/grafan_aiops/docker-compose.yml build aiops_engine
   ```
   *Purpose:* Bakes V11 into the container image layer.
4. **Recreate Container:**
   ```bash
   docker compose -f /root/grafan_aiops/docker-compose.yml up -d --force-recreate aiops_engine
   ```
   *Purpose:* Stops the old V10 container and starts the new V11 container with `unless-stopped` restart policy.

## 6. Expected Service Interruption and Risks
- **Service Interruption:** Brief downtime (< 10 seconds) during container recreation (`--force-recreate`).
- **Risks:** Minimal, mitigated by verified Phase 60 backup and rigorous offline shadow test execution.

## 7. Pre-Deployment and Post-Deployment Health Checks
- **Pre-Deployment:** Verify container status (`docker ps`), check logs (`docker logs --tail 20 aiops_predictor_hpc`).
- **Post-Deployment:**
  - Verify new container status: `docker ps --filter name=aiops_predictor_hpc`
  - Verify container image digest & startup logs: `docker logs -f --tail 50 aiops_predictor_hpc`
  - Verify Zabbix sensor metric ingestion and AIOps inference loop stability.

## 8. Rollback Commands and Their Prerequisites
- **Prerequisites:** Phase 60 backup file `/tmp/aiops_staging_v8/shadow_v11/outputs_phase60/script_aiops.py.bak_phase60` (SHA-256: `58f8065f171a34c612f2f0d4434b3235e1a525f916e6e648af6460bb12b2d291`).
- **Rollback Steps:**
  ```bash
  cp /tmp/aiops_staging_v8/shadow_v11/outputs_phase60/script_aiops.py.bak_phase60 /root/grafan_aiops/script_aiops.py
  docker compose -f /root/grafan_aiops/docker-compose.yml build aiops_engine
  docker compose -f /root/grafan_aiops/docker-compose.yml up -d --force-recreate aiops_engine
  ```

## 9. Explicit Stop Conditions
- Checksum mismatch at any step.
- Container startup failure or Python syntax/runtime error in container logs.
- Unanticipated service dependency failure or Zabbix connection refusal.

## 10. Final Decision
- **Status:** `READY_FOR_OPERATOR_CONFIRMATION`
- **Production State Change during Phase 62:** **NONE**. Phase 62 was strictly non-mutating (verification and planning only).

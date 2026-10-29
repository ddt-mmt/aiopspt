# Zabbix HTTPS/TLS Remediation Plan — Phase G.14D

## 1. Objective
Establish a secure, encrypted HTTPS transport channel between AIOps Shadow v5 and the Zabbix API web frontend proxy before executing any 24-hour multi-host history extraction across UPS and PAC assets.

## 2. Implementation Options & Recommendation
- **Recommended Option:** Configure Nginx reverse proxy (`nginx.conf.proxy`) to listen on port 443 with SSL enabled, utilizing a valid certificate issued by an internal trusted CA.
- **Alternative Option:** Deploy a dedicated TLS termination proxy in front of the Zabbix upstream.

## 3. Step-by-Step Remediation Procedure (Requires Operator Sign-Off & Execution)
1. **Certificate Provisioning:** Generate or acquire a valid TLS certificate and private key matching the proxy hostname/IP from the internal CA.
2. **Proxy Configuration Update:** Update `/root/nginx.conf.proxy` to add an `server` block listening on `443 ssl`:
   ```nginx
   server {
       listen 443 ssl;
       server_name 10.28.1.102; # or hostname
       ssl_certificate /path/to/cert.crt;
       ssl_certificate_key /path/to/key.key;
       ssl_protocols TLSv1.2 TLSv1.3;
       
       location /zabbix/ {
           proxy_pass http://10.28.1.110/zabbix/;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto https;
       }
   }
   ```
3. **Nginx Syntax Check & Reload:** Run `nginx -t` followed by `nginx -s reload` (or systemctl reload nginx).
4. **Client-Side Verification:** Test HTTPS connectivity without tokens using Python (`urllib.request` with CA bundle validation or `curl --cacert`) to ensure strict certificate and hostname validation succeed without insecure bypasses.

## 4. Acceptance Criteria for `TRANSPORT_VERIFIED`
- Successful HTTPS connection test (`apiinfo.version` over port 443) with valid certificate verification (zero SSL errors).
- Zero reliance on unencrypted HTTP (`port 80`) for API communication.
- Formal operator review and sign-off.

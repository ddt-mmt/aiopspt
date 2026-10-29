# Phase G.17 Read-Only Service & Port Inventory

## 1. Running Docker Containers
| Container Name | Image | Port Mappings | Status |
| :--- | :--- | :--- | :--- |
| `aiops_predictor_hpc` | `grafan_aiops-aiops_engine` | (Internal daemon script) | Up 4 days |
| `grafana` | `grafana/grafana:latest` | `0.0.0.0:3000->3000/tcp` | Up 6 days |
| `influxdb` | `influxdb:1.8` | `0.0.0.0:8086->8086/tcp` | Up 2 weeks |
| `netbox` | `netbox_migration-netbox` | `0.0.0.0:8001->8080/tcp` | Up 2 weeks |
| `semaphore` | `semaphoreui/semaphore:latest` | `0.0.0.0:3001->3000/tcp` | Up 2 weeks |
| `portainer_agent` | `portainer/agent:2.21.5` | `0.0.0.0:9001->9001/tcp` | Up 2 weeks |
| `telegraf` | `telegraf:latest` | `2055/udp` | Up 2 weeks |

## 2. Host Network Listeners (TCP / UDP)
| Port | Protocol | Binding Process / Service | Notes |
| :--- | :--- | :--- | :--- |
| **80** | TCP | `httpd` (Apache) | Standard HTTP web traffic |
| **8080** | TCP | `httpd` (Apache) | Secondary HTTP listener |
| **443** | TCP | *Unbound / Inactive* | Target for TLS termination |
| **3306** | TCP | `mariadbd` | Local MySQL database |
| **10050** | TCP | `zabbix_agentd` | Zabbix agent monitoring |
| **10051** | TCP | `zabbix_server` | Zabbix server & trapper listener |
| **162** | UDP | `snmptrapd` | SNMP trap listener |
| **3000, 3001, 8001, 8086, 9001** | TCP | `docker-proxy` | Mapped container ports |

## 3. Configuration File Status
- **Stored Template:** `/root/nginx.conf.proxy` (Contains reference proxy and upstream rules).
- **Active Runtime:** No active Nginx reverse proxy service is currently binding port 443.
- **Secrets & Credentials:** Completely redacted from all inventory documentation.

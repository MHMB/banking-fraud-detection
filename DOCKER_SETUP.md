# Docker Setup for Neo4j Banking Fraud Detection Analysis

This Docker setup provides a complete Neo4j graph database environment with GUI dashboards for analyzing Iranian banking fraud detection scenarios.

## Services Included

| Service | Container Name | URL | Port | Description |
|----------|-----------------|-----|-------------|
| **Neo4j Database** | banking_analysis_neo4j | http://localhost:7474 | 7474 (HTTP), 7473 (Bolt) | Graph database with persistent storage + Built-in Browser UI |
| **NeoDash** | banking_analysis_neodash | http://localhost:5000 | 5000 | Interactive dashboard builder for Neo4j |

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB RAM available (4GB minimum)
- 10GB disk space for data volumes

## Quick Start

### 1. Start All Services
```bash
# Navigate to project directory
cd /Users/mhmb/milit-service/banking_analysis

# Start Neo4j and GUI dashboards
docker-compose up -d

# Check service health
docker-compose ps
```

**Expected output:**
```
NAME                           STATUS         PORTS
banking_analysis_neo4j           Up (healthy)   0.0.0.0:7474->7474/tcp, 0.0.0.0:7473->7473/tcp
banking_analysis_neodash          Up (healthy)   0.0.0.0:5000->5000/tcp
banking_analysis_neo4j_browser    Up              0.0.0.0:7475->7475/tcp
```

### 2. Access GUI Interfaces

**Option A: NeoDash (Recommended for Dashboards)**
- URL: http://localhost:5000
- Username: `admin`
- Password: `admin123`
- Features:
  - Drag-and-drop dashboard building
  - Visual graphs, charts, and tables
  - Pre-built dashboard templates
  - Real-time data visualization

**Option B: Neo4j Browser (Built-in to Neo4j)**
- URL: http://localhost:7474
- Username: `neo4j`
- Password: `password123`
- Features:
  - Interactive Cypher query editor
  - Graph visualization
  - Node and property inspection
  - Query history
  - Database management

**Note:** Neo4j Browser is included in the main Neo4j database interface at port 7474.

### 3. Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Data Persistence

All data is stored in Docker volumes and persists across container restarts:

```bash
# List volumes
docker volume ls | grep banking_analysis

# Output:
# banking_analysis_neo4j_data        # Graph database files
# banking_analysis_neo4j_logs          # Transaction logs
# banking_analysis_neo4j_import        # Import files
# banking_analysis_neo4j_plugins       # Custom plugins
# banking_analysis_neodash_data         # Dashboard configurations
# banking_analysis_neodash_config       # NeoDash settings
# banking_analysis_neodash_logs         # NeoDash logs
```

### Backup Data
```bash
# Backup Neo4j data
docker run --rm -v banking_analysis_neo4j_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/neo4j_backup_$(date +%Y%m%d).tar.gz /data

# Restore from backup
docker run --rm -v banking_analysis_neo4j_data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/neo4j_backup_20250213.tar.gz -C /
```

## Loading Banking Data

### Option 1: Using NeoDash Import Wizard

1. Open NeoDash: http://localhost:5000
2. Create new dashboard: "Banking Analysis"
3. Click "Import Data" → "CSV Import"
4. Upload files:
   - `accounts_master.csv` → Nodes (Account/Person)
   - `scenario_XX/transactions.csv` → Relationships (TRANSACTION)

### Option 2: Using Cypher Shell (CLI)

```bash
# Enter Neo4j container
docker exec -it banking_analysis_neo4j cypher-shell

# Run import commands
# See import_data.cypher for full scripts
```

### Option 3: Using Neo4j Browser

1. Open Neo4j Browser (built into Neo4j): http://localhost:7474
2. Paste Cypher queries from `import_data.cypher`
3. Execute to load data

### Option 4: Using Python Driver

```python
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "password123"

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    # Load accounts
    with open('accounts_master.csv', 'r') as f:
        # Create nodes and relationships
        pass
```

## Configuration

### Change Passwords
Edit `docker-compose.yml`:
```yaml
environment:
  - NEO4J_AUTH=neo4j/YOUR_NEW_PASSWORD  # Change Neo4j password
  - NEO4J_AUTH_DISABLE_TO_LS=false
  - NEODASH_PASSWORD=YOUR_DASH_PASSWORD  # Change NeoDash password
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Adjust Memory Limits

For larger datasets or complex queries:
```yaml
environment:
  - NEO4J_dbms_memory_heap_max__size=4G  # Increase from 2G
  - NEO4J_dbms_memory_pagecache_size=2G  # Increase from 1G
```

### Enable Remote Access

To access from other machines on your network:
```yaml
ports:
  - "0.0.0.0:7474:7474"  # Neo4j (includes Browser UI)
  - "0.0.0.0:5000:5000"  # NeoDash
```

Then access via:
- Neo4j Browser: `http://YOUR_MACHINE_IP:7474`
- NeoDash: `http://YOUR_MACHINE_IP:5000`

## Monitoring and Logs

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f neo4j
docker-compose logs -f neodash
docker-compose logs -f neo4j_browser

# Last 100 lines
docker-compose logs --tail=100 neo4j
```

### Monitor Resource Usage
```bash
# Real-time stats
docker stats

# Specific container
docker stats banking_analysis_neo4j
```

### Health Checks
```bash
# Check service health
docker-compose ps

# Test Neo4j connection
curl -u neo4j:password123 http://localhost:7474/db/data/

# Test NeoDash
curl http://localhost:5000/health
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :7474

# Change port in docker-compose.yml
ports:
  - "7475:7474"  # Use different host port
```

### Out of Memory Errors
```bash
# Check container stats
docker stats banking_analysis_neo4j

# Increase memory limits (see Configuration section above)
```

### Cannot Connect to Neo4j
```bash
# Verify Neo4j is healthy
docker-compose ps

# Check logs for errors
docker-compose logs neo4j | grep -i error

# Restart Neo4j
docker-compose restart neo4j
```

### Data Lost After Restart
```bash
# Verify volumes exist
docker volume ls | grep banking_analysis

# Inspect volume
docker volume inspect banking_analysis_neo4j_data

# Ensure using volumes in docker-compose.yml
volumes:
  - neo4j_data:/data
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Docker Network                       │
│                                                        │
│  ┌─────────────┐    ┌─────────────┐      │
│  │    Neo4j     │    │   NeoDash     │      │
│  │  (Database +   │◄──┤ (Dashboard)   │      │
│  │   Browser UI) │    │     :5000      │      │
│  │  :7474, :7473│    └─────────────────┘      │
│  └──────┬────────┘                              │
│         │                                         │
│  ┌──────▼──────────────────────────────────────────┐  │
│  │         Persistent Docker Volumes ( survives restarts)      │  │
│  │  • neo4j_data        - Graph database files             │  │
│  │  • neo4j_logs          - Transaction logs              │  │
│  │  • neodash_data         - Dashboard configs             │  │
│  │  • neodash_config       - User settings                 │  │
│  └────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Next Steps

1. **Start services:** `docker-compose up -d`
2. **Open NeoDash:** http://localhost:5000
3. **Import data:** Use CSV files in this directory
4. **Build dashboards:** Create fraud detection visualizations
5. **Run analysis:** Execute Cypher queries for pattern detection

## References

- [Neo4j Docker Documentation](https://neo4j.com/docs/operations-manual/current/docker/)
- [NeoDash Documentation](https://neo4jlabs.github.io/neodash/)
- [Neo4j Browser Documentation](https://neo4j.com/docs/browser/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

**Setup Date:** 2025-02-13
**Project:** Iranian Banking Fraud Detection Analysis

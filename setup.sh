#!/bin/bash
# =============================================================
# Iranian Banking Fraud Detection - One-Command Setup Script
# =============================================================
# Usage:  bash setup.sh
# Run from your project root (where docker-compose.yml lives).
# Both setup.sh and import_data.cypher must be in the same folder.
# =============================================================

set -e  # Exit on first error

# --- Colors ---
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
header()  { echo -e "\n${BOLD}==> $1${NC}"; }

CONTAINER="banking_analysis_neo4j"
IMPORT_DIR="/var/lib/neo4j/import"

# =============================================================
# STEP 0: Preflight checks
# =============================================================
header "Checking requirements..."

[ -f "docker-compose.yml" ]   || error "docker-compose.yml not found. Run this from your project root."
[ -f "accounts_master.csv" ]  || error "accounts_master.csv not found."
[ -f "import_data.cypher" ]  || error "import_data.cypher not found. Place it in the same folder as this script."

command -v docker &>/dev/null || error "Docker is not installed or not in PATH."

# Prefer 'docker compose' (v2); fall back to legacy 'docker-compose' (v1)
if docker compose version &>/dev/null; then
  COMPOSE="docker compose"
else
  COMPOSE="docker-compose"
fi

success "All requirements met."

# =============================================================
# STEP 1: Start Neo4j
# =============================================================
header "Starting Neo4j container..."
$COMPOSE up -d
success "Container started."

# =============================================================
# STEP 2: Wait for Neo4j HTTP endpoint to respond
# Neo4j takes ~20-40s to fully boot. We poll instead of sleeping
# a fixed amount so the script proceeds as soon as it's ready.
# =============================================================
header "Waiting for Neo4j to be ready..."

MAX_WAIT=120
ELAPSED=0

while true; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:7474 2>/dev/null || echo "000")
  [ "$STATUS" = "200" ] && break

  [ "$ELAPSED" -ge "$MAX_WAIT" ] && \
    error "Neo4j did not become ready in ${MAX_WAIT}s. Check logs: docker logs ${CONTAINER}"

  echo -ne "    Waiting... (${ELAPSED}s, HTTP: ${STATUS})\r"
  sleep 5; ELAPSED=$((ELAPSED + 5))
done

success "Neo4j is up! (${ELAPSED}s)"
sleep 3  # Let the Bolt protocol finish initialising

# =============================================================
# STEP 3: Copy all CSV files into the Neo4j import directory
# Neo4j's LOAD CSV reads from inside the container, not your
# local filesystem, so every file needs to be copied in first.
# =============================================================
header "Copying CSV files into the container..."

docker cp accounts_master.csv ${CONTAINER}:${IMPORT_DIR}/
success "Copied accounts_master.csv"

for i in 01 02 03 04 05 06 07 08 09; do
  DIR="scenario_${i}"
  if [ -f "${DIR}/transactions.csv" ]; then
    docker exec ${CONTAINER} mkdir -p ${IMPORT_DIR}/${DIR}
    docker cp ${DIR}/transactions.csv ${CONTAINER}:${IMPORT_DIR}/${DIR}/
    success "Copied ${DIR}/transactions.csv"
  else
    warn "${DIR}/transactions.csv not found — skipping."
  fi
done

# =============================================================
# STEP 4: Copy the Cypher script and run it
# =============================================================
header "Copying import script into container..."
docker cp import_data.cypher ${CONTAINER}:${IMPORT_DIR}/
success "Copied import_data.cypher"

header "Running import (this may take a minute)..."
docker exec ${CONTAINER} cypher-shell \
  -u neo4j -p password123 \
  --file ${IMPORT_DIR}/import_data.cypher \
  --format plain

# =============================================================
# STEP 5: Quick verification — print node and relationship counts
# =============================================================
header "Verifying imported data..."

echo ""
echo "Node counts:"
docker exec ${CONTAINER} cypher-shell -u neo4j -p password123 --format plain \
  "MATCH (n) RETURN labels(n)[0] AS NodeType, count(n) AS Count ORDER BY Count DESC;"

echo ""
echo "Relationship counts:"
docker exec ${CONTAINER} cypher-shell -u neo4j -p password123 --format plain \
  "MATCH ()-[r]->() RETURN type(r) AS RelType, count(r) AS Count ORDER BY Count DESC;"

# =============================================================
# Done!
# =============================================================
echo ""
echo -e "${GREEN}${BOLD}================================================${NC}"
echo -e "${GREEN}${BOLD}  Setup complete! Your graph is ready.${NC}"
echo -e "${GREEN}${BOLD}================================================${NC}"
echo ""
echo -e "  ${BOLD}Neo4j Browser :${NC}  http://localhost:7474"
echo -e "  ${BOLD}Login         :${NC}  neo4j / password123"
echo -e "  ${BOLD}Bolt URL      :${NC}  bolt://localhost:7687"
echo ""
echo -e "  Try this in the browser to explore the graph:"
echo -e "  ${BLUE}MATCH (n) RETURN labels(n)[0], count(n) ORDER BY count(n) DESC;${NC}"
echo ""
echo -e "  To reset and reimport from scratch:"
echo -e "  ${YELLOW}docker-compose down -v && bash setup.sh${NC}"
echo ""
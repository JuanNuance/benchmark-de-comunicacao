#!/bin/bash
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "=== Starting 4 REST servers (ports 8001-8004) ==="
for port in 8001 8002 8003 8004; do
    python "$SCRIPT_DIR/rest_server.py" "$port" &
    echo "REST Server port $port PID=$!"
done
sleep 2

echo ""
echo "=== Launching 4 REST clients concurrently (20s each) ==="
C1_LOG=$(mktemp)
C2_LOG=$(mktemp)
C3_LOG=$(mktemp)
C4_LOG=$(mktemp)

python "$SCRIPT_DIR/rest_client.py" 8001 20 > "$C1_LOG" 2>&1 &
python "$SCRIPT_DIR/rest_client.py" 8002 20 > "$C2_LOG" 2>&1 &
python "$SCRIPT_DIR/rest_client.py" 8003 20  > "$C3_LOG" 2>&1 &
python "$SCRIPT_DIR/rest_client.py" 8004 20 > "$C4_LOG" 2>&1 &

echo "Waiting 27s for REST clients..."
sleep 27

echo ""
echo "================================================"
echo "  REST TERMINAL 1 (port 8001)"
echo "================================================"
cat "$C1_LOG"

echo ""
echo "================================================"
echo "  REST TERMINAL 2 (port 8002)"
echo "================================================"
cat "$C2_LOG"

echo ""
echo "================================================"
echo "  REST TERMINAL 3 (port 8003)"
echo "================================================"
cat "$C3_LOG"

echo ""
echo "================================================"
echo "  REST TERMINAL 4 (port 8004)"
echo "================================================"
cat "$C4_LOG"

echo ""
echo "=== Killing REST servers ==="
pkill -f "rest_server.py" 2>/dev/null || true

rm -f "$C1_LOG" "$C2_LOG" "$C3_LOG" "$C4_LOG"
echo "Done."
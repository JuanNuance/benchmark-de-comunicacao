#!/bin/bash
# Script para rodar simulação gRPC em 4 terminais

set -e
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Build absolute paths so background processes don't lose cwd
echo "=== Starting 4 gRPC servers ==="
cd "$SCRIPT_DIR"

python server.py 50051 &
S1=$!
sleep 0.5

python server.py 50052 &
S2=$!
sleep 0.5

python server.py 50053 &
S3=$!
sleep 0.5

python server.py 50054 &
S4=$!
sleep 1

echo "=== 4 SERVERS ONLINE ==="

echo "=== Launching 4 clients concurrently (20s each) ==="
C1_LOG=$(mktemp)
C2_LOG=$(mktemp)
C3_LOG=$(mktemp)
C4_LOG=$(mktemp)

python client.py 50051 20 > "$C1_LOG" 2>&1 &
python client.py 50052 20 > "$C2_LOG" 2>&1 &
python client.py 50053 20 > "$C3_LOG" 2>&1 &
python client.py 50054 20 > "$C4_LOG" 2>&1 &

echo "Waiting 25s for clients..."
sleep 25

echo ""
echo "================================================"
echo "  gRPC TERMINAL 1 (port 50051)"
echo "================================================"
cat "$C1_LOG"

echo ""
echo "================================================"
echo "  gRPC TERMINAL 2 (port 50052)"
echo "================================================"
cat "$C2_LOG"

echo ""
echo "================================================"
echo "  gRPC TERMINAL 3 (port 50053)"
echo "================================================"
cat "$C3_LOG"

echo ""
echo "================================================"
echo "  gRPC TERMINAL 4 (port 50054)"
echo "================================================"
cat "$C4_LOG"

echo ""
echo "=== Killing servers ==="
kill $S1 $S2 $S3 $S4 2>/dev/null || true
wait 2>/dev/null

rm -f "$C1_LOG" "$C2_LOG" "$C3_LOG" "$C4_LOG"
echo "Done."
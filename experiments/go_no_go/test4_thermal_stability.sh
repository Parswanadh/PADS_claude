#!/usr/bin/env bash
# GO/NO-GO TEST #4 -- Thermal stability check
# REQUIRES TARGET HARDWARE (Dell Latitude 5490).
#
# Runs a 30-minute sustained inference loop while logging CPU frequency and
# temperature. Business laptops throttle under sustained load; if this run
# shows throttling, the finding must be built into the benchmark PROTOCOL
# (warm-up period + discard first N runs) rather than treated as noise.
set -euo pipefail

MODEL_PATH="${1:-models/gguf/model-Q4_K_M.gguf}"
LLAMA_CLI="llama.cpp/build/bin/llama-cli"
DURATION_SEC=1800
LOG="experiments/results/test4_thermal_stability.csv"

mkdir -p experiments/results
echo "timestamp,cpu_freq_mhz,temp_c" > "$LOG"

if [ ! -f "$MODEL_PATH" ]; then
  echo "ERROR: model not found at $MODEL_PATH -- place a GGUF model first."
  exit 1
fi

echo "Starting 30-minute sustained inference loop. Logging every 10s to $LOG"
echo "Requires 'sensors' (lm-sensors) or 'turbostat' installed on the Latitude 5490."

( "$LLAMA_CLI" -m "$MODEL_PATH" -p "Sustained load test." -n 100000 > /dev/null 2>&1 & )
LLAMA_PID=$!

END=$((SECONDS + DURATION_SEC))
while [ $SECONDS -lt $END ]; do
  TS=$(date +%s)
  FREQ=$(grep -m1 "cpu MHz" /proc/cpuinfo | awk '{print $4}')
  TEMP=$(sensors 2>/dev/null | grep -m1 -oP 'Package id 0:\s*\+\K[0-9.]+' || echo "NA")
  echo "$TS,$FREQ,$TEMP" >> "$LOG"
  sleep 10
done

kill "$LLAMA_PID" 2>/dev/null || true
echo "Done. Inspect $LOG for a frequency/temperature drop over the run."
echo "If throttling is visible, log: Test 4: THROTTLING OBSERVED -> add warm-up"
echo "period + discard-first-N-runs to the standard benchmark protocol permanently."

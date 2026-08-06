#!/usr/bin/env bash
# GO/NO-GO TEST #6 -- Energy tooling check
# REQUIRES TARGET HARDWARE (Dell Latitude 5490).
#
# Tries RAPL via turbostat/powertop, in that order. If neither reports usable
# numbers on this exact BIOS/kernel, the fallback (USB in-line power meter on
# the charger cable) must be adopted NOW and documented in the methodology,
# not discovered as a gap at the end.
set -euo pipefail

echo "== Go/No-Go Test 6: energy measurement tooling =="

if command -v turbostat >/dev/null 2>&1; then
  echo "-- Trying turbostat (requires sudo) --"
  sudo turbostat --interval 5 --num_iterations 3 || echo "turbostat present but failed to read RAPL."
else
  echo "turbostat not installed. Install with: sudo apt install linux-tools-common linux-tools-\$(uname -r)"
fi

echo ""
if command -v powertop >/dev/null 2>&1; then
  echo "-- Trying powertop --"
  sudo powertop --csv=experiments/results/test6_powertop.csv --time=10 || echo "powertop present but failed."
else
  echo "powertop not installed. Install with: sudo apt install powertop"
fi

echo ""
echo "Checking RAPL sysfs directly:"
if [ -d /sys/class/powercap/intel-rapl ]; then
  find /sys/class/powercap/intel-rapl -maxdepth 1 -name "intel-rapl:*" -exec cat {}/name \; 2>/dev/null || echo "RAPL nodes present but unreadable (permissions?)."
else
  echo "No /sys/class/powercap/intel-rapl -- RAPL likely unavailable on this BIOS/kernel."
fi

echo ""
echo "DECISION RULE:"
echo "  If ANY of the above produced a plausible non-zero power reading across"
echo "  repeated runs -> log Test 6: PASSED (RAPL/turbostat/powertop usable)."
echo "  If NONE did -> log Test 6: FAILED -> adopt USB in-line power meter"
echo "  fallback now, and state this substitution explicitly in the methodology"
echo "  section of the report/paper."

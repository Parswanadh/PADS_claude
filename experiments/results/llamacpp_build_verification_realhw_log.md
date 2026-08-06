# llama.cpp Build Verification — real hardware (clone + configure only)

**Environment:** Alienware m16 R2, Intel Core Ultra 7 155H, 22 threads,
~15GB RAM. **Still not the Dell Latitude 5490** named as target hardware in
the docs (see `CLAUDE.md`) — this is a dev machine. Numbers here verify the
build tooling works on real multi-core hardware; they are not the final
target-hardware benchmark numbers.

This supersedes the "verifies the setup script is correct" scope of
`llamacpp_build_verification_log.md` (which ran in a 1-core sandbox) with an
actual multi-core, real-hardware run — but stops short of the full compile,
which is deferred to a separate session (see below).

## What was actually run (2026-08-07)

```
git clone --depth 1 https://github.com/ggml-org/llama.cpp
cmake -B build -DGGML_NATIVE=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_UI=OFF
```

`cmake --build` was **deliberately not run this session** — see "Why the
compile step is deferred" below.

## Result

- Shallow clone: **PASSED**, 202M on disk.
- `cmake` configure: **PASSED** cleanly, exit 0, 0.9s. Detected GNU 13.3.0
  (both C and CXX), OpenMP 4.5, x86_64, `GGML_SYSTEM_ARCH: x86`,
  `-march=native` applied (this machine's actual CPU flags, unlike the
  1-core sandbox's generic detection). ggml version 0.18.1.
- Only warning: OpenSSL not found → HTTPS disabled in the bundled server.
  Same as the sandbox run, still irrelevant to CLI/headless inference.
- Found a real safety gap in `setup/setup_llama_cpp.sh`: it hardcoded
  `-j "$(nproc)"` (22 threads on this machine) for the actual compile step,
  which conflicts with `CLAUDE.md`'s "start with conservative thread counts
  (nproc-1)" rule and risks memory pressure on a shared workstation running
  other foreground apps. **Fixed**: script now computes `nproc - 1` (minimum
  1) and uses that for `-j`.

## Why the compile step is deferred to a separate session

`cmake --build` is the actual CPU/RAM-heavy step (potentially several
minutes of sustained multi-core compilation). Session context at configure
time: available RAM had been trending down over this session's earlier work
(7.5GB → 6.7GB before recovering to 7.1GB) and load average had spiked to
3.22 before easing back to ~2. Both were within CLAUDE.md's safety
thresholds at every check, but the trend plus this being a shared, actively
used workstation (Docker Desktop VM, browser, editor, and another agent
session all running concurrently) argued for keeping this unit of work
small and stopping at a clean, verified checkpoint rather than kicking off
a multi-minute heavy compile in the same breath. Compiling is its own
atomic unit of work for a future session, run with a fresh resource check
and the now-fixed conservative `-j` default.

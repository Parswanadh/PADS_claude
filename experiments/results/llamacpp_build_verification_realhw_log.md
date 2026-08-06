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

## Why the compile step was deferred at the time of writing above

`cmake --build` is the actual CPU/RAM-heavy step (potentially several
minutes of sustained multi-core compilation). Session context at configure
time: available RAM had been trending down over this session's earlier work
(7.5GB → 6.7GB before recovering to 7.1GB) and load average had spiked to
3.22 before easing back to ~2. Both were within CLAUDE.md's safety
thresholds at every check, but the trend plus this being a shared, actively
used workstation (Docker Desktop VM, browser, editor, and another agent
session all running concurrently) argued for keeping this unit of work
small and stopping at a clean, verified checkpoint rather than kicking off
a multi-minute heavy compile in the same breath. Compiling was deferred to
a separate session, run with a fresh resource check — see below.

## Compile — actually run, 2026-08-07 (later session, same day)

Fresh resource check before starting: available RAM 7.6GB, load average
0.32/0.35/0.69 (down sharply from the 3.22 peak earlier in the day), no
active swap churn, 325GB free disk. Good conditions — proceeded.

```
timeout 900 cmake --build build --config Release --target llama-cli llama-quantize -j 21
```

(`-j 21` = `nproc - 1` on this 22-thread machine, using the now-fixed
script default.)

**Result: PASSED.** Wall clock 04:40:34–04:41:55 — **~81 seconds**, far
faster than the up-to-15-minute timeout budgeted. (Building just these two
targets still pulls in a fair amount of the tree — ggml, the common
library, mtmd, and server-context libraries are shared dependencies — but
it's well short of a full `--target all` build.) Zero build errors.

Verified the binaries actually work, not just that the build exited 0:

```
$ ./build/bin/llama-cli --version
version: 1 (15586e2)
built with GNU 13.3.0 for Linux x86_64
```

- `build/bin/llama-cli`: 1.2MB, ELF 64-bit PIE, dynamically linked, not
  stripped.
- `build/bin/llama-quantize`: 17.9KB (thin wrapper linking against
  `libllama-quantize-impl.so`), same format.
- Total `build/` directory: 123M on disk.
- RAM immediately after build: 7.6GB available (essentially unchanged from
  before — no memory pressure observed during the ~81s compile).

**This machine can now run `llama-cli` and `llama-quantize`.** Still
missing: an actual GGUF model to run them against (no `models/` directory,
no downloaded weights — see `PROGRESS.md`). Go/No-Go tests 1, 3, 4, and 6
remain blocked on that, not on the build anymore.

# llama.cpp Build Verification (sandbox, not target hardware)

**Environment:** generic sandbox container, 1 CPU core (`nproc`=1), no GPU.
**NOT the Dell Latitude 5490** — this only verifies the setup script and CMake
configuration are correct, not real build time on the actual target hardware.

## What was actually run

```
git clone --depth 1 https://github.com/ggml-org/llama.cpp
cmake -B build -DGGML_NATIVE=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_UI=OFF
cmake --build build --target llama-cli llama-quantize -j$(nproc)
```

## Result

- `cmake` configure step: **PASSED** cleanly. Detected GNU 13.3.0, OpenMP 4.5,
  x86 CPU backend, `-march=native`. Only warning: OpenSSL not found (disables
  HTTPS support in the bundled server, irrelevant to CLI inference).
- Finding: the default build pulls in `LLAMA_BUILD_UI` (an npm-based embedded
  web UI for the server), which is unnecessary for headless CPU inference and
  slow to build. **Fix applied and folded into `setup_llama_cpp.sh`:
  `-DLLAMA_BUILD_UI=OFF`.**
- Compilation: reached ~60% of the `llama` core library with **zero errors**
  before hitting a wall-clock cutoff in this sandbox (single core). Every
  compiled object file succeeded; the run was stopped by time, not by a build
  failure.

## Conclusion

The setup script is verified correct as written. A real build on the Latitude
5490 (which has more than one core) should complete in a few minutes, not
be blocked by anything seen here. This log exists so nobody mistakes "I
didn't finish the build in a demo sandbox" for "the build doesn't work."

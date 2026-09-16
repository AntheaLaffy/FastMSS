# External References

FastMSS keeps local checkouts of external projects and papers for research,
correctness validation, performance analysis, and implementation reference.

These source trees are **not vendored dependencies** and are intentionally
excluded from the FastMSS Git repository.

See [`manifest.toml`](./manifest.toml) for upstream URLs, roles, and the exact
local revisions inspected during development.

## Categories

- `baselines/` — end-to-end performance competitors such as OpenVINO and ggml
- `inference/` — model architecture, checkpoint, and correctness references
- `isa/` — x86-64 ISA and Rust SIMD/intrinsics references
- `kernels/` — industrial optimized kernel implementations such as oneDNN
- `runtimes/` — candidate and fallback execution runtimes such as CubeCL
- `papers/` — original algorithm papers

FastMSS does not aim to combine or vendor these projects. They are used to:

1. verify inference correctness;
2. study model implementations;
3. study optimized kernels and hardware-specific techniques;
4. establish serious C/C++ performance baselines;
5. reproduce benchmark environments.

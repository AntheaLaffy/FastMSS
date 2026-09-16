# AGENTS.md — uvr-fast Project Contract

This file is the operating contract for any AI or human contributor working on **uvr-fast**.

## 1. Mission

`uvr-fast` is a **special-purpose high-performance inference runtime for a fixed set of music-source-separation models**.

The project is intentionally **not** a general-purpose deep-learning framework.

Primary engineering goal:

> Use Rust, x86-64 SIMD/assembly, low-level GPU compute, and hardware-aware scheduling to make these fixed inference workloads run as fast as mature C/C++ implementations on commodity CPU + integrated-GPU systems, and where the fixed workload permits, exceed them.

The primary performance competitors are:

1. **OpenVINO** — Intel-oriented inference/runtime baseline.
2. **ggml / llama.cpp kernels** — highly specialized C/C++ inference and kernel baseline, especially for GEMM/attention-style workloads.

Secondary references:

- **oneDNN** — primitive/kernel gold standard for CPU and Intel GPU.
- **LibTorch / tch-rs** — correctness and general-framework baseline.
- **ORT + DirectML** — low-engineering-cost Windows GPU fallback.

A Rust implementation is not considered successful merely because it is faster than another Rust framework. The meaningful target is parity with, or superiority to, the mature C/C++ baselines above on the same hardware and workload.

## 2. Supported model set

The runtime only needs to support these seven checkpoints/workloads:

### VR Architecture

1. `5_HP-Karaoke-UVR`
2. `6_HP-Karaoke-UVR`
3. `UVR-DeEcho-DeReverb`

### BS-RoFormer

4. `model_bs_roformer_ep_368_sdr_12.9628`
5. `BS RoFormer` — Frazer + becruily lead/back-vocal model

### Mel-Band RoFormer

6. `MelBand Roformer-becruily_deux`

### SCNet

7. `SCNet XL IHF` — becruily lead/back-vocal model

Do not add general model compatibility unless it directly improves one of these seven targets.

## 3. Core design principle: specialization is a feature

Because the workload is fixed, prefer specialization over generality.

Allowed and encouraged optimizations include:

- hard-coded or compile-time-known tensor shapes where stable;
- per-model execution plans;
- per-shape convolution/GEMM kernels;
- pre-packed immutable weights;
- persistent scratch buffers and memory pools;
- operator fusion specific to the seven models;
- model-specific chunk/window sizes;
- model-specific FFT/STFT plans;
- specialized attention kernels for the RoFormer variants;
- CPU/iGPU overlap and asynchronous pipelining;
- startup-time autotuning followed by cached choices;
- separate code paths for AVX2/FMA, AVX-512, and other useful ISA features;
- device-specific GPU kernels when measurement justifies them.

Do **not** reject an optimization merely because it would be unsuitable for a general framework.

## 4. Hardware target

The principal deployment class is a normal x86-64 PC with:

- Intel/AMD x86-64 CPU;
- integrated GPU as an important accelerator target;
- shared system memory between CPU and iGPU on typical integrated systems;
- Linux and Windows as important environments.

The project should exploit the complete memory/compute hierarchy rather than treating an operator as an abstract mathematical function.

Relevant layers include, when present on the target architecture:

- registers and SIMD/vector register files;
- instruction decode/uop caches and execution ports;
- L1/L2/L3/LLC and platform-specific additional cache levels;
- DRAM bandwidth and memory-controller behavior;
- CPU ↔ iGPU shared-memory behavior;
- kernel launch/dispatch overhead;
- thread scheduling and synchronization;
- data layout, packing, tiling and prefetching.

Do not assume every processor has the same cache hierarchy. Query/detect hardware where necessary and benchmark actual machines.

## 5. CPU strategy

The CPU backend is allowed to be aggressively low-level.

Preferred progression for a hot kernel:

1. clear scalar Rust reference;
2. compiler-optimized Rust;
3. inspect generated code;
4. `std::arch::x86_64` intrinsics;
5. tiling, packing, prefetching and multithreading;
6. `asm!` only when measurements show a real advantage over compiler-generated code.

Hand-written assembly is a surgical optimization tool, not the default implementation language.

Important references:

- `rust-lang/stdarch` — Rust ISA intrinsics;
- `intelxed/xed` — x86 instruction encoding/decoding and ISA reference data;
- `oneDNN` — industrial CPU DNN kernels;
- `ggml` — compact specialized inference kernels.

For each optimized kernel, keep a simple correctness implementation when practical.

## 6. iGPU strategy

The primary experimental GPU path is:

`uvr-fast -> CubeCL -> Vulkan/WebGPU or other suitable backend -> GPU`

CubeCL is useful because it hides large parts of the platform API while still permitting kernel-level specialization, autotuning and hardware-aware implementation.

However, CubeCL is **not trusted by assumption**. It earns its place only through benchmarks.

Fallback/reference paths may include:

- oneDNN/SYCL or oneDNN GPU primitives for Intel hardware;
- ORT + DirectML on Windows;
- OpenVINO only as a baseline or optional fallback, not as the architectural center of this project.

x86-64 assembly applies to CPU execution. It does not directly optimize GPU shader/kernel execution.

## 7. Performance acceptance criteria

Every major optimization must be measured against a relevant mature baseline on the **same machine, dtype, tensor shape, batch/chunk configuration and model stage**.

Preferred hierarchy:

### Intel CPU

`uvr-fast` vs `oneDNN/OpenVINO CPU` vs `ggml` where applicable.

### Intel iGPU

`CubeCL` vs `OpenVINO GPU` vs `ggml SYCL/Vulkan` where applicable.

### Transformer/RoFormer kernels

Compare QKV projection, RoPE, attention/SDPA, softmax, FFN/GLU and normalization independently when possible.

### VR/SCNet kernels

Compare Conv2D/Conv1D, normalization, resampling and spectral pipeline stages independently when possible.

A result is not meaningful unless the benchmark records the exact configuration.

Do not celebrate a percentage improvement against a weak baseline while remaining far behind OpenVINO/oneDNN/ggml.

## 8. Optimization methodology

Performance work should proceed from measurement:

1. establish correctness;
2. establish a reproducible baseline;
3. profile end-to-end execution;
4. identify the dominant cost;
5. microbenchmark that cost in isolation;
6. optimize one hypothesis at a time;
7. inspect assembly/kernel output when relevant;
8. re-run end-to-end measurements;
9. record regressions and hardware-specific behavior.

Useful metrics include:

- wall-clock latency and throughput;
- CPU utilization and per-core utilization;
- cycles, instructions and IPC;
- SIMD/vector utilization;
- cache misses and memory bandwidth;
- allocation count and bytes copied;
- CPU↔GPU synchronization and transfer cost;
- GPU occupancy/workgroup behavior where accessible;
- kernel launch count;
- peak and steady-state memory usage.

## 9. Abstraction policy

Abstractions must justify their runtime cost.

Prefer:

- explicit tensor layouts;
- predictable ownership;
- contiguous buffers when beneficial;
- static dispatch in hot paths where practical;
- preallocation;
- small, transparent runtime layers;
- backend traits only at useful architectural boundaries.

Avoid introducing a general graph engine, generic operator zoo, plugin system, dynamic shape system, or framework-level abstraction merely because conventional ML frameworks contain them.

## 10. Correctness policy

Performance never excuses incorrect separation output.

For every backend/kernel:

- compare tensors against a known-good implementation;
- define numerical tolerances per dtype/operation;
- validate complete audio output, not only isolated tensors;
- distinguish acceptable floating-point drift from architecture/configuration mistakes.

Where possible, retain deterministic fixtures for known audio segments.

## 11. How AI contributors should work

When asked to implement or optimize something:

- first determine which of the seven model workloads it serves;
- find the actual hot path before introducing complexity;
- prefer project-specific solutions over framework-general solutions;
- explain relevant CPU/GPU architectural consequences;
- inspect existing reference implementations under `references/` before inventing behavior;
- never copy a reference design blindly if a simpler specialized implementation is possible;
- do not introduce large dependencies without a measured reason;
- keep benchmark code alongside optimized kernels;
- preserve a correctness path and tests;
- distinguish CPU intrinsics/assembly work from GPU kernel work;
- treat OpenVINO/oneDNN/ggml results as targets, not enemies to be rhetorically defeated.

The question is always:

> For these seven models on real CPU+iGPU hardware, what is the fastest correct implementation we can build while keeping the system understandable enough to profile and improve?

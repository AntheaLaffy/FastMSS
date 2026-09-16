# Performance Strategy

## Objective

The first-order objective is not "fast Rust". It is **competitive inference performance**.

For the seven supported model workloads, the project should aim to reach roughly the same performance class as mature C/C++ systems and exceed them where model-specific specialization creates an opportunity.

Primary baselines:

- OpenVINO on Intel CPU/iGPU;
- ggml/llama.cpp-style specialized kernels for GEMM/attention-class operations.

Primitive/reference baselines:

- oneDNN;
- LibTorch where useful.

## Optimization hierarchy

### 1. Algorithm and execution plan

The largest wins may come from doing less work:

- choose chunk/window sizes for the exact model;
- reuse STFT plans;
- eliminate redundant transforms/copies;
- keep immutable weights packed;
- fuse model-specific operations;
- overlap CPU preprocessing with iGPU inference;
- avoid synchronization between every operator;
- specialize execution graphs per checkpoint family.

### 2. Memory hierarchy

Treat memory traffic as a first-class cost.

Investigate:

- tensor layout and stride;
- NCHW/NHWC or model-specific blocked layouts;
- cache blocking and tiling;
- weight packing;
- alignment;
- scratch-buffer reuse;
- page faults and allocation behavior;
- prefetch distance;
- working-set fit in L1/L2/L3/LLC;
- CPU/iGPU shared-memory paths and unnecessary copies.

"L0-L4" should be interpreted as the actual hierarchy exposed by the target CPU/platform, not as an assumption that every processor has identically named cache levels.

### 3. CPU instruction-level optimization

Start with generated assembly before writing assembly by hand.

Possible targets:

- AVX2 + FMA;
- AVX-512 variants where present;
- vectorized complex arithmetic for spectral work;
- specialized GEMM/Conv microkernels;
- branch reduction in hot loops;
- unrolling and software pipelining;
- register blocking;
- prefetch and load/store scheduling.

Use `std::arch::x86_64` for most explicit SIMD work. Use `asm!` when it measurably improves a verified hot kernel.

### 4. Multicore scheduling

High CPU utilization is not itself the objective, but unexplained low utilization is a profiling signal.

Investigate:

- thread pool design;
- task granularity;
- work stealing vs static partitioning;
- false sharing;
- cache-affine partitioning;
- producer/consumer overlap between audio preprocessing and inference;
- oversubscription when a lower-level library also spawns threads.

### 5. iGPU kernels

Primary candidate: CubeCL.

Investigate per real model shape:

- workgroup dimensions;
- vector width;
- tiling;
- shared/local memory usage;
- fusion;
- kernel launch count;
- device-specific specialization;
- startup autotuning and persistent cache of chosen kernels.

Do not assume a kernel optimized for a discrete NVIDIA GPU is appropriate for an integrated Intel GPU.

## Benchmark tiers

### Tier A — microkernel

Examples:

- GEMM shape from a RoFormer projection;
- one real 3x3 convolution shape from a VR model;
- attention score/value product;
- RMSNorm;
- complex mask application;
- STFT window/FFT pipeline.

### Tier B — operator block

Examples:

- complete RoFormer attention block;
- complete VR convolution block;
- SCNet encoder/decoder stage.

### Tier C — model stage

Examples:

- preprocessing;
- neural network only;
- reconstruction/iSTFT only.

### Tier D — end-to-end

Input audio -> separated output audio.

All four tiers matter. A 2x faster microkernel is irrelevant if end-to-end runtime does not improve.

## Benchmark record

Every serious benchmark result should record at least:

- git commit;
- OS/kernel;
- CPU model;
- GPU model and driver;
- compiler/toolchain version;
- enabled CPU ISA features;
- backend;
- dtype;
- tensor shape;
- chunk/window size;
- thread count;
- warmup count;
- sample count;
- median and useful tail statistics;
- correctness tolerance/check result.

## Stop conditions

An optimization should be reconsidered when:

- it adds substantial complexity but provides no end-to-end gain;
- it wins only against a weak reference while remaining far behind the mature baseline;
- it causes unacceptable numerical or audio-output differences;
- it is so hardware-specific that maintenance cost exceeds its value for supported deployment machines.

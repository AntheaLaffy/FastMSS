# fast-mss Architecture Plan

## Proposed repository layout

```text
fast-mss/
├── AGENTS.md
├── README.md
├── Cargo.toml
│
├── crates/
│   ├── uvr-core/          # shared tensor/types, errors, model metadata
│   ├── uvr-audio/         # audio IO, STFT/iSTFT, overlap-add, resampling
│   ├── uvr-models/        # VR, RoFormer and SCNet model definitions
│   ├── uvr-runtime/       # execution plan, buffers, scheduling, backend dispatch
│   ├── uvr-kernels/       # CPU SIMD/asm + GPU/CubeCL kernels
│   ├── uvr-cli/           # command-line interface
│   └── uvr-bench/         # microbenchmarks and end-to-end benchmark harness
│
├── models/                # local checkpoints; normally gitignored
│   ├── vr/
│   │   ├── 5hp/
│   │   ├── 6hp/
│   │   └── deecho/
│   ├── roformer/
│   │   ├── bs-1296/
│   │   ├── melband-deux/
│   │   └── bs-karaoke/
│   └── scnet/
│       └── xl-ihf-becruily/
│
├── references/            # cloned upstream repos; reference material, not project code
│   ├── baselines/
│   │   ├── openvino/      # primary Intel inference performance baseline
│   │   └── ggml/          # specialized C/C++ kernel baseline
│   ├── kernels/
│   │   └── oneDNN/        # industrial CPU/Intel-GPU primitives
│   ├── runtimes/
│   │   ├── cubecl/        # primary low-level GPU compute candidate
│   │   ├── burn/          # higher-level CubeCL ecosystem reference
│   │   ├── tch-rs/        # LibTorch Rust binding/reference
│   │   ├── ort/           # ONNX Runtime Rust binding
│   │   └── DirectML/      # Windows GPU fallback/reference
│   ├── isa/
│   │   ├── stdarch/       # Rust x86/x86_64 intrinsics
│   │   └── xed/           # Intel x86 instruction encoder/decoder/reference data
│   ├── inference/
│   │   ├── ultimatevocalremovergui/
│   │   ├── msst/
│   │   ├── scnet/
│   │   └── bs-roformer/
│   └── papers/
│       └── README.md      # paper links and notes, not necessarily PDFs in git
│
├── benches/
│   ├── micro/             # Conv/GEMM/attention/STFT/etc.
│   ├── model/             # model-stage and end-to-end benches
│   └── results/           # machine-readable benchmark results
│
├── tools/
│   ├── model_downloader.py
│   ├── scan_tree.sh
│   └── profiling/
│
└── docs/
    ├── ARCHITECTURE.md
    ├── PERFORMANCE.md
    ├── MODELS.md
    └── BENCHMARKS.md
```

## Why rename `framework-friend` / `framework-enemy`

Those names are fun for local exploration but encode the wrong architectural relationship.

OpenVINO and ggml are not simply "enemies"; they are performance baselines and sources of implementation ideas. oneDNN is both a fallback candidate and a benchmark target. Burn/CubeCL may be dependencies, references, or both depending on the final backend design.

`references/{baselines,kernels,runtimes,isa,inference}` describes *why the repository is present* and gives an AI much better context.

## Runtime layering

```text
                         fast-mss
                            │
                  model-specific execution plan
                            │
            ┌───────────────┴────────────────┐
            │                                │
         CPU backend                     iGPU backend
            │                                │
 Rust + std::arch + asm!                 CubeCL kernels
            │                                │
 AVX2/FMA / AVX-512                    Vulkan/WebGPU/...
            │                                │
       optional oneDNN             optional fallback runtime
```

Model code should not directly depend on a concrete backend. The backend boundary should be narrow enough to permit comparison and replacement but not so generic that it recreates a full ML framework.

## Model families

```text
VR Architecture
├── 5_HP-Karaoke-UVR
├── 6_HP-Karaoke-UVR
└── UVR-DeEcho-DeReverb

RoFormer shared core
├── BS-RoFormer
│   ├── model_bs_roformer_ep_368_sdr_12.9628
│   └── Frazer + becruily BS-RoFormer
└── Mel-Band RoFormer
    └── becruily_deux

SCNet
└── SCNet XL IHF becruily
```

The code should share RoFormer attention/RoPE/norm/FFN machinery rather than duplicating complete BS and Mel-Band implementations.

## Kernel organization

A useful eventual structure inside `uvr-kernels` is:

```text
uvr-kernels/src/
├── cpu/
│   ├── scalar/
│   ├── x86_64/
│   │   ├── avx2/
│   │   ├── avx512/
│   │   └── asm/
│   └── dispatch.rs
├── gpu/
│   └── cubecl/
├── conv/
├── gemm/
├── attention/
├── norm/
├── fft/
└── tests/
```

Do not create every directory up front if it is empty. Add structure as real kernels appear.

## Reference repositories are not vendored dependencies

`references/` should normally be excluded from the main Git repository. They are cloned source trees used for reading, benchmarking and comparison.

Record their repository URL and tested commit hash in a small manifest instead of committing gigabytes of upstream history.

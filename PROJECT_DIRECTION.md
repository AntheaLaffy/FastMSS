# uvr-fast：项目目标与开发优先级

## 1. 项目定位

`uvr-fast` 不是一个通用 AI 推理框架。

它的目标是：

> 使用 Rust 作为主体语言，从较底层的执行框架和硬件接口出发，针对固定的 7 个音频分离模型，打造一个专用的高性能推理环境，并尽可能利用 Intel 核显、CPU SIMD、汇编、缓存层次和 CPU↔iGPU 协同，将端到端推理性能逼近甚至超过成熟的 C/C++ 推理实现。

我们接受“为了固定模型而牺牲通用性”。

只要能提升这 7 个模型的实际推理性能，就允许使用：

- 固定 shape specialization
- 模型专用 execution plan
- 权重预打包
- 长生命周期 scratch buffer
- 自定义内存布局
- 算子融合
- 固定 tile / workgroup
- 针对具体硬件的 autotune
- AVX2 / AVX-512
- 必要时的 x86-64 汇编
- CubeCL 自定义 GPU kernel
- CPU 与 iGPU 的流水线并行

项目的价值不在于“支持更多模型”，而在于把很小的任务集合做得足够快。

---

## 2. 当前只支持的模型

### VR Architecture

1. `5_HP-Karaoke-UVR`
2. `6_HP-Karaoke-UVR`
3. `UVR-DeEcho-DeReverb`

### RoFormer

4. `model_bs_roformer_ep_368_sdr_12.9628`
5. `MelBand Roformer - becruily_deux`
6. `BS Roformer - frazer + becruily`

### SCNet

7. `SCNet XL IHF - becruily`

因此，我们只需要围绕少数固定网络家族构建执行环境：

- VR Architecture
- BS-RoFormer
- Mel-Band RoFormer
- SCNet XL IHF

---

## 3. 第一原则：GPU First

项目当前的第一优先级是：

> **Intel 核显 / 通用 iGPU 推理性能。**

原因很简单：

此前另一个基于 Burn 的项目已经证明，CPU 推理性能虽然仍有优化空间，但已经达到“勉强可以接受”的水平。

因此当前最高价值的问题不再是：

> “CPU 还能不能再快 20%？”

而是：

> “我们能不能让固定的音频分离模型，在 Intel 核显上以接近成熟 C/C++ 推理框架的效率运行？”

所以开发顺序必须是：

```text
模型正确性
    ↓
CubeCL GPU backend
    ↓
Intel iGPU 跑通
    ↓
Vulkan / WebGPU 对比
    ↓
真实模型 profiling
    ↓
热点 kernel 定位
    ↓
Conv / GEMM / Attention / Norm 专用优化
    ↓
fusion / tiling / workgroup / memory layout
    ↓
CPU↔iGPU pipeline
    ↓
与 OpenVINO / ggml 等成熟实现比较
```

CPU 极限优化放在第二阶段。

---

## 4. GPU 主路线

当前 GPU 主路线：

```text
Rust
 ↓
CubeCL
 ↓
Vulkan / WebGPU
 ↓
Intel iGPU
```

CubeCL 的价值在于：

- 可以屏蔽大量平台 API 差异；
- 仍然允许我们进入 kernel 层；
- 可以针对具体 shape 做 specialization；
- 可以研究 workgroup、tile、fusion、autotune；
- 不需要自己维护完整 Vulkan / D3D12 / Metal 计算栈。

但不能默认认为 CubeCL 已经足够快。

CubeCL 必须通过真实 benchmark 证明自己。

---

## 5. GPU 性能竞争对象

Rust 框架之间的比较不是项目目标。

例如：

```text
Burn 比 Candle 快 2x
```

本身没有足够价值。

真正重要的是：

```text
uvr-fast / CubeCL
        vs
OpenVINO GPU
        vs
ggml Vulkan / SYCL
```

对于 Intel iGPU，OpenVINO 是最重要的性能标尺。

对于 RoFormer 的 Attention / GEMM / RoPE 等算子，ggml/llama.cpp 的 kernel 也是重要参考。

### GPU 成功标准

所有比较必须满足：

- 相同硬件
- 相同 dtype
- 相同模型
- 相同输入长度
- 相同 chunk / overlap
- 相同精度要求
- 相同 warm-up 规则
- 尽可能一致的端到端边界

理想目标：

```text
OpenVINO = 100%

uvr-fast ≥ 95%
    → 非常优秀

90% ~ 95%
    → 可以接受，继续优化

80% ~ 90%
    → 明显存在性能缺口

< 80%
    → 不满足“性能优先”的目标
```

如果 CubeCL 最终无法接近成熟实现，则保留 fallback：

- oneDNN
- ggml
- ORT / DirectML
- LibTorch / tch-rs

但 fallback 不能代替对 CubeCL 路线的性能验证。

---

## 6. CPU 路线：第二阶段

CPU 不是放弃，而是延后。

目标路线：

```text
Rust scalar baseline
        ↓
LLVM optimized Rust
        ↓
std::arch::x86_64
        ↓
AVX2 + FMA
        ↓
AVX-512
        ↓
packing / tiling / register blocking
        ↓
必要时 asm!
        ↓
oneDNN / ggml benchmark
```

原则：

> 不为了“会写汇编”而写汇编。

只有在 profiling 和反汇编证明 LLVM / intrinsics 生成的代码存在明显问题时，才进入 `asm!`。

CPU 优化目标包括：

- SIMD
- register blocking
- cache locality
- loop unrolling
- software prefetch
- branch reduction
- packing
- tiling
- NUMA / thread placement
- thread pool
- memory reuse
- operator fusion

---

## 7. 从体系结构层面优化

项目优化范围不是“调用更快的 Conv2D”。

我们要关注整个计算机体系结构：

```text
寄存器
 ↓
指令 / μop / pipeline
 ↓
L1 Cache
 ↓
L2 Cache
 ↓
L3 / LLC
 ↓
平台可能存在的额外缓存层
 ↓
DRAM
 ↓
CPU ↔ iGPU shared memory
 ↓
GPU local execution resources
```

因此优化对象包括：

- 数据布局
- cache blocking
- Tensor layout
- 权重布局
- SIMD vector width
- 内存带宽
- 中间 Tensor 生命周期
- buffer reuse
- CPU↔GPU copy
- unified/shared memory
- GPU occupancy
- workgroup size
- subgroup
- shader specialization
- kernel fusion
- CPU/GPU pipeline overlap

最终关注的是：

> **整台机器完成一次模型推理所需的最短时间。**

---

## 8. 专用化优先于通用化

我们明确不做：

- 通用动态图框架
- autograd
- 任意模型加载器
- 任意 dtype 体系
- 万能 operator registry
- 任意 shape 的最佳性能保证
- 为了 API 优雅牺牲性能
- 为了抽象统一阻止模型特化

我们允许：

```text
BS-RoFormer 1296 的专用执行路径

MelBand Deux 的专用 band layout

VR 5HP 的专用 Conv shape kernel

SCNet XL IHF 的专用内存计划
```

如果两个模型的最优实现不同，可以有两个执行计划。

---

## 9. Runtime 的职责

`uvr-runtime` 不应该发展成通用 graph runtime。

它应该主要负责：

- 固定模型 execution plan
- backend dispatch
- memory pool
- scratch buffer
- weight packing
- CPU/GPU task scheduling
- chunk pipeline
- buffer lifetime
- autotune result cache
- model-specific specialization

理想状态：

```text
模型
 ↓
静态 / 半静态 ExecutionPlan
 ↓
已知 shape
 ↓
已知 kernel
 ↓
已知 buffer
 ↓
直接执行
```

尽可能减少运行时动态决策。

---

## 10. Benchmark 层级

任何性能优化都必须有 benchmark 证明。

### Tier A — Microbenchmark

例如：

- FMA throughput
- GEMM microkernel
- GPU tile
- memory copy
- softmax kernel

### Tier B — Operator

例如：

- Conv2D
- MatMul
- Attention
- RMSNorm
- FFT / STFT

### Tier C — Model Stage

例如：

- STFT
- band split
- transformer block
- mask estimator
- reconstruction

### Tier D — End-to-End

```text
audio
 ↓
完整模型
 ↓
separated stems
```

最终 Tier D 才是决定性指标。

一个 microkernel 快 2 倍，但端到端只快 1%，不能被视作重要突破。

---

## 11. 当前开发顺序

### Phase 1 — 最小 GPU 基础

目标：

- 最小 Tensor metadata
- 权重读取
- CubeCL 接入
- Intel GPU 枚举
- 第一个 GPU buffer
- 第一个 kernel
- correctness test

### Phase 2 — VR Architecture

优先从 `5_HP-Karaoke-UVR` 开始。

原因：

- 网络相对直接；
- 主要热点更接近经典 Conv workload；
- 适合验证 GPU runtime；
- 能较快建立 OpenVINO 对照。

目标：

```text
Python / UVR reference
        ≈
uvr-fast CubeCL output
```

然后 benchmark：

```text
OpenVINO GPU
vs
CubeCL Vulkan
vs
CubeCL WebGPU
```

### Phase 3 — RoFormer

重点进入：

- QKV projection
- GEMM
- RoPE
- Attention
- Softmax
- RMSNorm
- FFN / GLU
- mask estimation

这里重点研究：

- ggml attention kernel
- CubeCL specialization
- fusion
- memory layout
- Flash-Attention 类算法是否适配当前 shape

### Phase 4 — SCNet

在 GPU runtime 和主要 primitive 稳定以后加入 SCNet。

### Phase 5 — CPU 极限优化

只有 GPU 主线已经稳定后，再系统投入：

- AVX2
- AVX-512
- handwritten asm
- oneDNN 对比
- ggml CPU 对比

---

## 12. AI / Codex 开发约束

AI 在修改本项目时必须遵守：

1. 不要把项目设计成通用推理框架。
2. 当前优先解决 iGPU，而不是 CPU。
3. 不要为了架构“漂亮”增加没有实际用途的抽象层。
4. 不要提前实现没有被 7 个模型使用的算子。
5. 所有性能改动必须有 benchmark。
6. 优先 profiling，再优化。
7. 优先真实模型 shape，不优先玩具 shape。
8. 对热点允许模型专用实现。
9. CPU 汇编必须建立在 profiling / disassembly 证据上。
10. GPU 优化必须与 OpenVINO/ggml 等成熟实现比较。
11. correctness 优先于性能。
12. microbenchmark 胜利不等于项目胜利。
13. 最终评价标准是端到端音频分离速度与结果正确性。

---

## 13. 一句话目标

> **uvr-fast 是一个 GPU-first、模型专用、性能优先的 Rust 音频分离推理项目。它利用固定 7 个模型这一强先验，从模型执行计划、内存布局、GPU kernel、CPU SIMD/汇编、缓存层次一直优化到 CPU↔iGPU 流水线，目标是在 Intel 核显环境下逼近甚至超过 OpenVINO、ggml 等成熟 C/C++ 推理实现。**

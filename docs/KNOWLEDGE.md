对，这样分类更准确。你的这些模型应该分成 **“算法原始来源”** 和 **“成熟工程实现”** 两条线来看：前者用来搞懂网络为什么这么设计，后者用来保证 checkpoint、预处理、chunk、STFT、推理行为都对得上。

## ① 原始算法 / 论文来源

| 你要支持的模型                        | 原始算法              | 原始论文 / 第一来源                                                       |
| ------------------------------ | ----------------- | ----------------------------------------------------------------- |
| 5_HP-Karaoke-UVR               | VR Architecture   | **没有找到正式论文**；第一来源是 tsurumeso 的 `vocal-remover`                    |
| 6_HP-Karaoke-UVR               | VR Architecture   | 同上                                                                |
| UVR-DeEcho-DeReverb            | VR Architecture   | 同上                                                                |
| `model_bs_roformer_ep_368...`  | BS-RoFormer       | **Music Source Separation with Band-Split RoPE Transformer**      |
| BS RoFormer frazer/becruily    | BS-RoFormer       | 同一篇论文                                                             |
| MelBand Roformer becruily_deux | Mel-Band RoFormer | **Mel-Band RoFormer for Music Source Separation**                 |
| SCNet XL IHF                   | SCNet             | **SCNet: Sparse Compression Network for Music Source Separation** |

### VR Architecture

这个比较特殊。我没有查到 tsurumeso 给 VR Architecture 写过正式论文，所以它的**原始算法第一手资料实际上就是源代码**：

[tsurumeso/vocal-remover](https://github.com/tsurumeso/vocal-remover?utm_source=chatgpt.com)

你现在用的 `5_HP-Karaoke-UVR` 和 `6_HP-Karaoke-UVR` 都明确属于 **VR Arch Single Model v5**。([GitHub][1])

所以这里应该理解成：

```text
论文：无

原始算法：
tsurumeso/vocal-remover
        ↓
后来 UVR 扩展/修改
        ↓
VR Architecture v5
        ↓
5_HP / 6_HP / DeEcho
```

对于这三只模型，**tsurumeso 的源码本身就是“论文级参考资料”**。

---

### BS-RoFormer

原论文：

**Music Source Separation with Band-Split RoPE Transformer**

Wei-Tsung Lu, Ju-Chiang Wang, Qiuqiang Kong, Yun-Ning Hung。

2023 年先发 arXiv，之后正式发表于 **ICASSP 2024，pp.481–485**。([arXiv][2])

[BS-RoFormer 原论文 arXiv](https://arxiv.org/abs/2309.02612?utm_source=chatgpt.com)

这篇就是：

```text
model_bs_roformer_ep_368_sdr_12.9628
BS RoFormer frazer/becruily
```

背后的核心算法。

`ep_368` 只是后来训练出来的 checkpoint，不是另一种网络。

---

### Mel-Band RoFormer

原论文：

**Mel-Band RoFormer for Music Source Separation**

Ju-Chiang Wang, Wei-Tsung Lu, Minz Won。

2023 年发表，并在 ISMIR 2023 展示。它是在 BS-RoFormer 基础上，把人为设计的 non-overlapping band split 换成基于 Mel scale 的重叠频带划分。([arXiv][3])

[Mel-Band RoFormer 原论文](https://arxiv.org/abs/2310.01809?utm_source=chatgpt.com)

你的：

```text
MelBand Roformer-becruily_deux
```

就是这一架构的后续训练模型。

因此 `becruily_deux` **不是一篇新论文，也不是新算法**，而是 Mel-Band RoFormer 的具体 checkpoint。

---

### SCNet

论文：

**SCNet: Sparse Compression Network for Music Source Separation**

Weinan Tong 等，2024，ICASSP。

核心思路就是针对不同频段的信息密度不同，做不同程度的 sparse compression。论文报告其 CPU inference time 约为 HT Demucs 的 48%。([arXiv][4])

[SCNet 原论文](https://arxiv.org/abs/2401.13276?utm_source=chatgpt.com)

你的：

```text
SCNet XL IHF
```

不是新的基础算法，而是 **SCNet 架构上的更大型/改进变体**。MSST 当前明确列有 SCNet Large、XL、XL IHF 等多个工程版本。([GitHub][5])

---

# ② 成熟实现 / 实际推理参考

这一类的评价标准完全不同：

> 不要求它是作者最早写的，而要求 **checkpoint 能直接跑、配置完整、推理逻辑经过大量用户验证、模型变体覆盖充分**。

### VR Architecture → Ultimate Vocal Remover

成熟实现毫无疑问看：

[Anjok07/ultimatevocalremovergui](https://github.com/Anjok07/ultimatevocalremovergui?utm_source=chatgpt.com)

核心位置：

```text
lib_v5/
└── vr_network/
    ├── nets.py
    ├── nets_new.py
    ├── layers.py
    ├── model_param_init.py
    └── modelparams/
```

UVR 当前实际推理就是从 `lib_v5.vr_network` 加载网络，同时配合自己的 `spec_utils` 和 model parameters。([GitHub][6])

因此：

```text
理解 VR 网络结构
→ tsurumeso/vocal-remover

保证 5_HP / 6_HP / DeEcho 完全兼容
→ Ultimate Vocal Remover
```

这两者职责完全不同。

---

### BS-RoFormer / Mel-Band RoFormer → ZFTurbo MSST

对你这些现有模型，我仍然首推：

[ZFTurbo/Music-Source-Separation-Training](https://github.com/ZFTurbo/Music-Source-Separation-Training?utm_source=chatgpt.com)

因为它不是简单的论文 demo，而已经成为这一批音乐分离 RoFormer 模型事实上的训练/推理生态之一。

它同时维护：

```text
bs_roformer
mel_band_roformer
scnet
...
```

并明确说明 BS/Mel RoFormer 实现是基于论文复现的，感谢 lucidrains 根据论文重建模型。([GitHub][7])

尤其你的：

```text
model_bs_roformer_ep_368_sdr_12.9628.ckpt
```

本身就广泛以 `Music-Source-Separation-Training` 模型格式传播；公开模型配置也直接把它标为 `model_type: bs_roformer`。([GitHub][8])

---

### RoFormer 的“干净算法实现” → lucidrains

这里再保留一个非常有价值的中间参考：

[lucidrains / BS-RoFormer](https://github.com/lucidrains/BS-RoFormer?utm_source=chatgpt.com)

它不是论文作者的官方 repo，而是**根据论文复现的简洁 PyTorch 实现**；ZFTurbo 自己也明确感谢 lucidrains 做了这两个 RoFormer 的论文复现。([GitExtract][9])

所以实际上：

```text
论文
 ↓
lucidrains
 ↓
ZFTurbo / 各种实际 checkpoint
```

非常适合我们做 Rust 移植时交叉检查。

论文告诉我们公式；

lucidrains 告诉我们：

```text
公式怎么翻译成 Tensor 操作
```

ZFTurbo 告诉我们：

```text
真实 checkpoint 到底怎么跑
```

---

### SCNet → 官方实现 + ZFTurbo

SCNet 是这里最舒服的一个，因为**有真正的官方实现**：

[starrytong/SCNet 官方实现](https://github.com/starrytong/SCNet?utm_source=chatgpt.com)

仓库明确声明自己是：

> official implementation of SCNet

而且包含训练和 inference。([GitHub][10])

但对于你的 **SCNet XL IHF**，成熟参考还是需要同时看：

[ZFTurbo/Music-Source-Separation-Training](https://github.com/ZFTurbo/Music-Source-Separation-Training?utm_source=chatgpt.com)

因为论文官方仓库主要对应基础 SCNet/large，而 **XL IHF 是后续 MSST 生态扩展的 variant**；MSST 当前明确提供 SCNet XL IHF 的配置和 checkpoint。([GitHub][5])

所以：

```text
理解 SCNet：
论文 + starrytong/SCNet

实现 SCNet XL IHF：
starrytong/SCNet
       +
ZFTurbo/MSST
```

---

## 最后压缩成你真正需要收藏的东西

**原始算法资料：**

1. VR → `tsurumeso/vocal-remover`，无正式论文
2. BS-RoFormer → arXiv `2309.02612`
3. Mel-Band RoFormer → arXiv `2310.01809`
4. SCNet → arXiv `2401.13276`

**成熟工程实现：**

1. VR → `Anjok07/ultimatevocalremovergui`
2. BS/Mel RoFormer → `ZFTurbo/Music-Source-Separation-Training`
3. RoFormer 简洁参考 → `lucidrains/BS-RoFormer`
4. SCNet → `starrytong/SCNet` + ZFTurbo MSST

因此从 `uvr-fast` 的角度，你其实应该采用一种“三角校验”方式：

```text
论文
 ↓
确定数学结构

原始/简洁实现
 ↓
确认 Tensor 运算

成熟实现
 ↓
确认 checkpoint、STFT、chunk、
overlap、padding、输出行为

        ↓
     Rust 实现
```

这样比直接照着 UVR/MSST 一行一行翻译可靠得多。

[1]: https://github.com/upseem/uvr5-cli-no-ui/blob/main/models.txt?utm_source=chatgpt.com "uvr5-cli-no-ui/models.txt at main · upseem/uvr5-cli-no-ui · GitHub"
[2]: https://arxiv.org/abs/2309.02612?utm_source=chatgpt.com "Music Source Separation with Band-Split RoPE Transformer"
[3]: https://arxiv.org/abs/2310.01809?utm_source=chatgpt.com "Mel-Band RoFormer for Music Source Separation"
[4]: https://arxiv.org/abs/2401.13276?utm_source=chatgpt.com "SCNet: Sparse Compression Network for Music Source Separation"
[5]: https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/docs/pretrained_models.md?utm_source=chatgpt.com "Music-Source-Separation-Training/docs/pretrained_models.md at main · ZFTurbo/Music-Source-Separation-Training · GitHub"
[6]: https://github.com/Anjok07/ultimatevocalremovergui/blob/master/separate.py?utm_source=chatgpt.com "ultimatevocalremovergui/separate.py at master · Anjok07/ultimatevocalremovergui · GitHub"
[7]: https://github.com/ZFTurbo/Music-Source-Separation-Training?utm_source=chatgpt.com "GitHub - ZFTurbo/Music-Source-Separation-Training: Repository for training models for music source separation. · GitHub"
[8]: https://github.com/Recordtini/MusicSepGUI/blob/main/models.json?utm_source=chatgpt.com "MusicSepGUI/models.json at main · Recordtini/MusicSepGUI · GitHub"
[9]: https://gitextract.com/ZFTurbo/Music-Source-Separation-Training?utm_source=chatgpt.com "Full Code of ZFTurbo/Music-Source-Separation-Training for AI - Complete Repository Source | GitExtract"
[10]: https://github.com/starrytong/SCNet/blob/main/README.md?utm_source=chatgpt.com "SCNet/README.md at main · starrytong/SCNet · GitHub"


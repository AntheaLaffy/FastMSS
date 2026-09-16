#!/usr/bin/env bash
set -euo pipefail

# FastMSS reference index initializer.
#
# Run from the FastMSS repository root:
#   chmod +x scripts/setup_references_index.sh
#   ./scripts/setup_references_index.sh
#
# What it does:
#   1. Stops ignoring the whole references/ directory.
#   2. Keeps large local checkouts and local paper files ignored.
#   3. Creates references/README.md.
#   4. Creates references/manifest.toml with upstream URLs and current local commit SHAs.
#   5. Prints the final git status.
#
# It does NOT run git add/commit/push automatically.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "${ROOT}" ]]; then
    echo "error: current directory is not inside a Git repository." >&2
    exit 1
fi

cd "${ROOT}"

if [[ ! -f "Cargo.toml" ]] || [[ ! -d "crates" ]]; then
    echo "warning: ${ROOT} does not look like the FastMSS repository root." >&2
    echo "continuing anyway..." >&2
fi

mkdir -p references

GITIGNORE=".gitignore"
touch "${GITIGNORE}"

# Remove common forms that ignore the entire references directory.
tmp_gitignore="$(mktemp)"
awk '
    $0 == "/references/" { next }
    $0 == "references/"  { next }
    $0 == "/references"  { next }
    $0 == "references"   { next }
    { print }
' "${GITIGNORE}" > "${tmp_gitignore}"
mv "${tmp_gitignore}" "${GITIGNORE}"

BEGIN_MARKER="# >>> FastMSS local references >>>"
END_MARKER="# <<< FastMSS local references <<<"

# Remove our previous managed block so this script is idempotent.
tmp_gitignore="$(mktemp)"
awk -v begin="${BEGIN_MARKER}" -v end="${END_MARKER}" '
    $0 == begin { skipping = 1; next }
    $0 == end   { skipping = 0; next }
    !skipping   { print }
' "${GITIGNORE}" > "${tmp_gitignore}"
mv "${tmp_gitignore}" "${GITIGNORE}"

cat >> "${GITIGNORE}" <<'EOF'

# >>> FastMSS local references >>>
# Local source checkouts are research material, not vendored dependencies.
/references/baselines/ggml/
/references/baselines/openvino/

/references/inference/bs-roformer/
/references/inference/msst/
/references/inference/scnet/
/references/inference/ultimatevocalremovergui/
/references/inference/vocal-remover-original/

/references/isa/stdarch/
/references/isa/xed/

/references/kernels/oneDNN/

/references/runtimes/cubecl/
/references/runtimes/DirectML/
/references/runtimes/ort/
/references/runtimes/tch-rs/

# Local copies of papers.
/references/papers/**/*.pdf
/references/papers/**/paper
# <<< FastMSS local references <<<
EOF

cat > references/README.md <<'EOF'
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
EOF

MANIFEST="references/manifest.toml"

cat > "${MANIFEST}" <<'EOF'
# FastMSS external reference manifest
#
# Local source trees are intentionally excluded from Git.
# This file records what they are, why they matter, and which revision
# was inspected locally.
#
# Re-run scripts/setup_references_index.sh after updating local reference
# repositories to refresh the recorded commit SHAs.

EOF

toml_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    printf '%s' "${s}"
}

add_ref() {
    local name="$1"
    local category="$2"
    local path="$3"
    local fallback_url="$4"
    local purpose="$5"

    local url="${fallback_url}"
    local commit=""

    if git -C "${path}" rev-parse --git-dir >/dev/null 2>&1; then
        commit="$(git -C "${path}" rev-parse HEAD 2>/dev/null || true)"
        local discovered_url
        discovered_url="$(git -C "${path}" remote get-url origin 2>/dev/null || true)"
        if [[ -n "${discovered_url}" ]]; then
            url="${discovered_url}"
        fi
    fi

    {
        echo '[[reference]]'
        printf 'name = "%s"\n' "$(toml_escape "${name}")"
        printf 'category = "%s"\n' "$(toml_escape "${category}")"
        printf 'path = "%s"\n' "$(toml_escape "${path}")"
        printf 'url = "%s"\n' "$(toml_escape "${url}")"
        printf 'commit = "%s"\n' "$(toml_escape "${commit}")"
        printf 'purpose = "%s"\n\n' "$(toml_escape "${purpose}")"
    } >> "${MANIFEST}"
}

add_ref \
    "ggml" \
    "baseline" \
    "references/baselines/ggml" \
    "https://github.com/ggml-org/ggml" \
    "C/C++ inference and kernel performance reference, especially GEMM and transformer primitives"

add_ref \
    "OpenVINO" \
    "baseline" \
    "references/baselines/openvino" \
    "https://github.com/openvinotoolkit/openvino" \
    "Primary Intel CPU/iGPU end-to-end performance baseline"

add_ref \
    "BS-RoFormer" \
    "inference" \
    "references/inference/bs-roformer" \
    "https://github.com/lucidrains/BS-RoFormer" \
    "Clean BS-RoFormer and Mel-Band RoFormer implementation reference"

add_ref \
    "Music-Source-Separation-Training" \
    "inference" \
    "references/inference/msst" \
    "https://github.com/ZFTurbo/Music-Source-Separation-Training" \
    "Mature checkpoint-compatible implementation for BS-RoFormer, Mel-Band RoFormer and SCNet variants"

add_ref \
    "SCNet" \
    "inference" \
    "references/inference/scnet" \
    "https://github.com/starrytong/SCNet" \
    "Official/reference implementation of SCNet"

add_ref \
    "Ultimate Vocal Remover GUI" \
    "inference" \
    "references/inference/ultimatevocalremovergui" \
    "https://github.com/Anjok07/ultimatevocalremovergui" \
    "Production reference for UVR VR Architecture v5 inference and checkpoint behavior"

add_ref \
    "vocal-remover" \
    "inference" \
    "references/inference/vocal-remover-original" \
    "https://github.com/tsurumeso/vocal-remover" \
    "Original VR Architecture implementation"

add_ref \
    "stdarch" \
    "isa" \
    "references/isa/stdarch" \
    "https://github.com/rust-lang/stdarch" \
    "Rust architecture intrinsics reference, especially x86_64 SIMD"

add_ref \
    "Intel XED" \
    "isa" \
    "references/isa/xed" \
    "https://github.com/intelxed/xed" \
    "Intel x86/x86-64 instruction encoding and ISA reference"

add_ref \
    "oneDNN" \
    "kernel" \
    "references/kernels/oneDNN" \
    "https://github.com/uxlfoundation/oneDNN" \
    "Industrial CPU and Intel GPU kernel reference for convolution, GEMM and related primitives"

add_ref \
    "CubeCL" \
    "runtime" \
    "references/runtimes/cubecl" \
    "https://github.com/tracel-ai/cubecl" \
    "Primary FastMSS GPU compute/runtime candidate"

add_ref \
    "DirectML" \
    "runtime" \
    "references/runtimes/DirectML" \
    "https://github.com/microsoft/DirectML" \
    "Windows GPU fallback and runtime reference"

add_ref \
    "ort" \
    "runtime" \
    "references/runtimes/ort" \
    "https://github.com/pykeio/ort" \
    "Rust ONNX Runtime binding and possible fallback execution path"

add_ref \
    "tch-rs" \
    "runtime" \
    "references/runtimes/tch-rs" \
    "https://github.com/LaurentMazare/tch-rs" \
    "Rust LibTorch binding and general inference/correctness baseline"

cat >> "${MANIFEST}" <<'EOF'
[[paper]]
name = "Music Source Separation with Band-Split RoPE Transformer"
architecture = "BS-RoFormer"
url = "https://arxiv.org/abs/2309.02612"
local_path = "references/papers/bs-roformer/paper"

[[paper]]
name = "Mel-Band RoFormer for Music Source Separation"
architecture = "Mel-Band RoFormer"
url = "https://arxiv.org/abs/2310.01809"
local_path = "references/papers/mel-band-roformer/paper.pdf"

[[paper]]
name = "SCNet: Sparse Compression Network for Music Source Separation"
architecture = "SCNet"
url = "https://arxiv.org/abs/2401.13276"
local_path = "references/papers/scnet/paper.pdf"

[[paper]]
name = "VR Architecture"
architecture = "VR Architecture"
url = "https://github.com/tsurumeso/vocal-remover"
note = "No formal paper identified; the original implementation is the primary algorithm reference."
EOF

echo
echo "FastMSS reference index updated."
echo
echo "Tracked metadata:"
echo "  references/README.md"
echo "  references/manifest.toml"
echo
echo "Local reference source trees remain ignored."
echo
echo "Current status:"
git status --ignored --short -- \
    .gitignore \
    references/README.md \
    references/manifest.toml \
    references

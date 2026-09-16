#!/usr/bin/env bash
set -euo pipefail

# Run from the uvr-fast repository root.
# The script only moves known top-level reference/model directories when they exist.
# It intentionally does not modify Rust source layout.

move_if_exists() {
    local src="$1"
    local dst="$2"
    if [[ -e "$src" ]]; then
        mkdir -p "$(dirname "$dst")"
        if [[ -e "$dst" ]]; then
            echo "skip: destination already exists: $dst"
        else
            echo "move: $src -> $dst"
            mv "$src" "$dst"
        fi
    fi
}

mkdir -p \
    references/{baselines,kernels,runtimes,isa,inference,papers} \
    models/{vr,roformer,scnet} \
    benches/{micro,model,results} \
    tools/profiling \
    docs

# Existing comparison/runtime repositories.
move_if_exists framework-enemy/openvino references/baselines/openvino
move_if_exists framework-enemy/ggml references/baselines/ggml

move_if_exists framework-friend/oneDNN references/kernels/oneDNN
move_if_exists framework-friend/tch-rs references/runtimes/tch-rs
move_if_exists framework-friend/DirectML references/runtimes/DirectML
move_if_exists framework-friend/stdarch references/isa/stdarch

# These may exist even if they were below the scan threshold.
move_if_exists framework-friend/cubecl references/runtimes/cubecl
move_if_exists framework-friend/burn references/runtimes/burn
move_if_exists framework-friend/ort references/runtimes/ort
move_if_exists framework-friend/xed references/isa/xed
move_if_exists framework-enemy/llama.cpp references/baselines/llama.cpp

# Inference/reference implementations.
move_if_exists inference-reference/ultimatevocalremovergui references/inference/ultimatevocalremovergui
move_if_exists inference-reference/Music-Source-Separation-Training references/inference/msst
move_if_exists inference-reference/msst references/inference/msst
move_if_exists inference-reference/SCNet references/inference/scnet
move_if_exists inference-reference/scnet references/inference/scnet
move_if_exists inference-reference/BS-RoFormer references/inference/bs-roformer
move_if_exists inference-reference/bs-roformer references/inference/bs-roformer

# Model checkpoints.
move_if_exists models/5hp models/vr/5hp
move_if_exists models/6hp models/vr/6hp
move_if_exists models/deecho models/vr/deecho
move_if_exists models/bs1296 models/roformer/bs-1296
move_if_exists models/deux models/roformer/melband-deux
move_if_exists models/bs-karaoke models/roformer/bs-karaoke
move_if_exists models/scnet-xl-ihf-becruily models/scnet/xl-ihf-becruily

# Remove old containers only when empty.
rmdir framework-enemy 2>/dev/null || true
rmdir framework-friend 2>/dev/null || true
rmdir inference-reference 2>/dev/null || true

echo
echo "Done. Review the tree before committing anything."
echo "Recommendation: keep models/ and references/ out of the main Git history."

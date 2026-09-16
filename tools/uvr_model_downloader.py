#!/usr/bin/env python3
"""
uvr_model_downloader.py

Small dependency-light downloader for the exact UVR/RoFormer models used by uvr-fast.

Features
--------
- Built-in manifest for the requested models.
- Hugging Face, ModelScope and GitHub/direct HTTP sources.
- Resume via HTTP Range, .part files, atomic rename.
- HTTP/HTTPS/SOCKS proxy profiles.
- Generic `fetch` command for arbitrary HF / ModelScope / GitHub assets.
- Optional SHA-256 verification when a trusted hash is known.

Dependency:
    pip install requests
For SOCKS proxies:
    pip install 'requests[socks]'

Examples:
    python uvr_model_downloader.py list
    python uvr_model_downloader.py download all -o ./models
    python uvr_model_downloader.py download 5hp 6hp deecho bs1296 deux bs-karaoke

    python uvr_model_downloader.py proxy add clash http://127.0.0.1:7890
    python uvr_model_downloader.py proxy use clash
    python uvr_model_downloader.py proxy show
    python uvr_model_downloader.py proxy off

    python uvr_model_downloader.py download all --proxy socks5h://127.0.0.1:7890
    python uvr_model_downloader.py download all --no-proxy

    # Arbitrary Hugging Face file
    python uvr_model_downloader.py fetch hf becruily/mel-band-roformer-deux becruily_deux.ckpt -o ./tmp

    # Arbitrary ModelScope file
    python uvr_model_downloader.py fetch modelscope AI-ModelScope/gpt2 config.json -o ./tmp

    # Arbitrary GitHub/direct URL
    python uvr_model_downloader.py fetch github \
      https://github.com/owner/repo/releases/download/tag/model.bin -o ./tmp/model.bin
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import quote, quote_plus, urlparse

try:
    import requests
except ImportError as exc:
    raise SystemExit(
        "缺少 requests。请先运行:  python -m pip install requests\n"
        "如果要用 SOCKS 代理: python -m pip install 'requests[socks]'"
    ) from exc


APP_NAME = "uvr-fast-model-downloader"
DEFAULT_TIMEOUT = 30
CHUNK_SIZE = 1024 * 1024
USER_AGENT = f"{APP_NAME}/1.0"


def config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "uvr-fast" / "model-downloader.json"


@dataclass(frozen=True)
class Source:
    kind: str  # github | hf | modelscope | url
    url: Optional[str] = None
    repo: Optional[str] = None
    file: Optional[str] = None
    revision: str = "main"

    def resolved_url(self) -> str:
        if self.kind in {"github", "url"}:
            if not self.url:
                raise ValueError(f"{self.kind} source 缺少 url")
            return self.url
        if self.kind == "hf":
            if not self.repo or not self.file:
                raise ValueError("hf source 缺少 repo/file")
            # Preserve path separators in repo file path.
            file_path = quote(self.file, safe="/")
            rev = quote(self.revision, safe="")
            return f"https://huggingface.co/{self.repo}/resolve/{rev}/{file_path}?download=true"
        if self.kind == "modelscope":
            if not self.repo or not self.file:
                raise ValueError("modelscope source 缺少 repo/file")
            # This is the public single-file endpoint used by the ModelScope SDK.
            return (
                f"https://modelscope.cn/api/v1/models/{self.repo}/repo"
                f"?Revision={quote_plus(self.revision)}&FilePath={quote_plus(self.file)}"
            )
        raise ValueError(f"未知 source kind: {self.kind}")


@dataclass(frozen=True)
class Artifact:
    filename: str
    sources: tuple[Source, ...]
    sha256: Optional[str] = None
    note: str = ""


@dataclass(frozen=True)
class Model:
    key: str
    name: str
    family: str
    artifacts: tuple[Artifact, ...] = field(default_factory=tuple)
    aliases: tuple[str, ...] = field(default_factory=tuple)
    unavailable_reason: Optional[str] = None
    include_in_all: bool = True


GH_AUDIO_SEPARATOR = "https://github.com/nomadkaraoke/python-audio-separator/releases/download/model-configs"
GH_TRVLVR = "https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models"


MODELS: tuple[Model, ...] = (
    Model(
        key="5hp",
        name="5_HP-Karaoke-UVR",
        family="VR Architecture v5",
        aliases=("5_hp", "5-hp", "5_HP-Karaoke-UVR"),
        artifacts=(
            Artifact(
                "5_HP-Karaoke-UVR.pth",
                (Source("github", url=f"{GH_AUDIO_SEPARATOR}/5_HP-Karaoke-UVR.pth"),),
            ),
        ),
    ),
    Model(
        key="6hp",
        name="6_HP-Karaoke-UVR",
        family="VR Architecture v5",
        aliases=("6_hp", "6-hp", "6_HP-Karaoke-UVR"),
        artifacts=(
            Artifact(
                "6_HP-Karaoke-UVR.pth",
                (Source("github", url=f"{GH_AUDIO_SEPARATOR}/6_HP-Karaoke-UVR.pth"),),
            ),
        ),
    ),
    Model(
        key="deecho",
        name="UVR-DeEcho-DeReverb",
        family="VR Architecture v5",
        aliases=("dereverb", "UVR-DeEcho-DeReverb"),
        artifacts=(
            Artifact(
                "UVR-DeEcho-DeReverb.pth",
                (Source("github", url=f"{GH_AUDIO_SEPARATOR}/UVR-DeEcho-DeReverb.pth"),),
            ),
        ),
    ),
    Model(
        key="bs1296",
        name="model_bs_roformer_ep_368_sdr_12.9628",
        family="BS-RoFormer",
        aliases=("1296", "bs-1296", "model_bs_roformer_ep_368_sdr_12.9628"),
        artifacts=(
            Artifact(
                "model_bs_roformer_ep_368_sdr_12.9628.ckpt",
                (
                    Source("github", url=f"{GH_TRVLVR}/model_bs_roformer_ep_368_sdr_12.9628.ckpt"),
                    Source(
                        "hf",
                        repo="Pragmaticl/music-source-separation-training-model",
                        file="model_bs_roformer_ep_368_sdr_12.9628.ckpt",
                    ),
                ),
                sha256="f6c94864adfb73bbb0ca58ec14d58dd0b364549e9fb61433ae51916f3e2f8d0b",
            ),
            Artifact(
                "model_bs_roformer_ep_368_sdr_12.9628.yaml",
                (
                    Source("github", url=f"{GH_AUDIO_SEPARATOR}/model_bs_roformer_ep_368_sdr_12.9628.yaml"),
                    Source(
                        "github",
                        url=(
                            "https://raw.githubusercontent.com/TRvlvr/application_data/main/"
                            "mdx_model_data/mdx_c_configs/model_bs_roformer_ep_368_sdr_12.9628.yaml"
                        ),
                    ),
                ),
            ),
        ),
    ),
    Model(
        key="deux",
        name="MelBand Roformer - becruily_deux",
        family="Mel-Band RoFormer",
        aliases=("becruily-deux", "mel-deux", "becruily_deux"),
        artifacts=(
            Artifact(
                "becruily_deux.ckpt",
                (
                    Source(
                        "hf",
                        repo="becruily/mel-band-roformer-deux",
                        file="becruily_deux.ckpt",
                    ),
                ),
            ),
            Artifact(
                "config_deux_becruily.yaml",
                (
                    Source(
                        "hf",
                        repo="becruily/mel-band-roformer-deux",
                        file="config_deux_becruily.yaml",
                    ),
                ),
            ),
        ),
    ),
    Model(
        key="scnet-becruily",
        name="SCNet XL IHF (@becruily) - lead/back vocal separation",
        family="SCNet XL IHF",
        aliases=("scnet", "scnet-xl-ihf-becruily"),
        unavailable_reason=(
            "已确认 MVSep 使用该 @becruily Karaoke/lead-back 版本，但截至脚本生成时未找到作者或 MVSep "
            "公开发布的 checkpoint URL。为避免下错模型，本项不会用普通 ZFTurbo SCNet XL IHF 冒充。"
        ),
    ),
    Model(
        key="bs-karaoke",
        name="BS Roformer Karaoke (@frazer + @becruily)",
        family="BS-RoFormer",
        aliases=("frazer-becruily", "bs-becruily", "bs_roformer_karaoke_frazer_becruily"),
        artifacts=(
            Artifact(
                "bs_roformer_karaoke_frazer_becruily.ckpt",
                (
                    Source(
                        "hf",
                        repo="becruily/bs-roformer-karaoke",
                        file="bs_roformer_karaoke_frazer_becruily.ckpt",
                    ),
                ),
                sha256="eb90ee24c1154d83fbcfd27e96182f19e061557cc6e4746953125e08c29389f9",
            ),
            Artifact(
                "config_karaoke_frazer_becruily.yaml",
                (
                    Source(
                        "hf",
                        repo="becruily/bs-roformer-karaoke",
                        file="config_karaoke_frazer_becruily.yaml",
                    ),
                ),
            ),
        ),
    ),
    # Not part of `all`: useful only as an architecture/performance reference.
    Model(
        key="scnet-xl-ihf-zfturbo",
        name="SCNet XL IHF 4-stem (ZFTurbo, reference only)",
        family="SCNet XL IHF",
        aliases=("scnet-zfturbo",),
        include_in_all=False,
        artifacts=(
            Artifact(
                "model_scnet_ep_36_sdr_10.0891.ckpt",
                (
                    Source(
                        "github",
                        url=(
                            "https://github.com/ZFTurbo/Music-Source-Separation-Training/"
                            "releases/download/v1.0.15/model_scnet_ep_36_sdr_10.0891.ckpt"
                        ),
                    ),
                ),
                note="这不是 @becruily 的和声分离模型，只是同架构公开参考权重。",
            ),
            Artifact(
                "config_musdb18_scnet_xl_more_wide_v5.yaml",
                (
                    Source(
                        "github",
                        url=(
                            "https://github.com/ZFTurbo/Music-Source-Separation-Training/"
                            "releases/download/v1.0.15/config_musdb18_scnet_xl_more_wide_v5.yaml"
                        ),
                    ),
                ),
            ),
        ),
    ),
)


MODEL_INDEX: dict[str, Model] = {}
for _m in MODELS:
    for _key in (_m.key, _m.name, *_m.aliases):
        MODEL_INDEX[_key.lower()] = _m


def human_bytes(n: float) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TiB"


def load_config() -> dict:
    path = config_path()
    if not path.exists():
        return {"active_proxy": None, "proxies": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"代理配置损坏: {path}\n{exc}") from exc
    data.setdefault("active_proxy", None)
    data.setdefault("proxies", {})
    return data


def save_config(cfg: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def validate_proxy_url(proxy: str) -> None:
    scheme = urlparse(proxy).scheme.lower()
    if scheme not in {"http", "https", "socks5", "socks5h", "socks4"}:
        raise SystemExit("代理必须以 http://, https://, socks5://, socks5h:// 或 socks4:// 开头")
    if scheme.startswith("socks"):
        try:
            import socks  # type: ignore  # noqa: F401
        except ImportError as exc:
            raise SystemExit(
                "检测到 SOCKS 代理，但缺少 PySocks。请运行: python -m pip install 'requests[socks]'"
            ) from exc


def configured_proxy(explicit_proxy: Optional[str], no_proxy: bool) -> tuple[Optional[str], bool]:
    """Return (proxy, trust_env)."""
    if no_proxy:
        return None, False
    if explicit_proxy:
        validate_proxy_url(explicit_proxy)
        return explicit_proxy, False
    cfg = load_config()
    active = cfg.get("active_proxy")
    if active:
        proxy = cfg.get("proxies", {}).get(active)
        if proxy:
            validate_proxy_url(proxy)
            return proxy, False
    # Inherit HTTP_PROXY / HTTPS_PROXY / ALL_PROXY from the shell.
    return None, True


def make_session(proxy: Optional[str], trust_env: bool) -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    session.trust_env = trust_env
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})
    return session


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_hash(path: Path, expected: Optional[str]) -> bool:
    if not expected:
        return True
    print(f"    校验 SHA-256: {path.name}")
    actual = sha256_file(path)
    if actual.lower() != expected.lower():
        print(f"    [!] SHA-256 不匹配\n        expected: {expected}\n        actual:   {actual}")
        return False
    print("    SHA-256 OK")
    return True


def auth_headers_for(source: Source) -> dict[str, str]:
    headers: dict[str, str] = {}
    if source.kind == "hf":
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


def download_http(
    session: requests.Session,
    source: Source,
    dest: Path,
    *,
    timeout: int,
    force: bool,
    dry_run: bool,
) -> None:
    url = source.resolved_url()
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")

    if dry_run:
        print(f"    [dry-run] {source.kind}: {url}\n              -> {dest}")
        return

    if dest.exists() and not force:
        print(f"    已存在，跳过: {dest}")
        return
    if force:
        dest.unlink(missing_ok=True)
        part.unlink(missing_ok=True)

    resume_from = part.stat().st_size if part.exists() else 0
    headers = auth_headers_for(source)
    if resume_from:
        headers["Range"] = f"bytes={resume_from}-"
        print(f"    发现断点: {human_bytes(resume_from)}")

    with session.get(url, headers=headers, stream=True, allow_redirects=True, timeout=timeout) as r:
        # Some servers ignore Range and return 200. Restart rather than appending duplicate bytes.
        if r.status_code == 416 and part.exists():
            # Requested range may already equal remote length. Try finalize; hash check happens later.
            part.replace(dest)
            return
        r.raise_for_status()

        append = resume_from > 0 and r.status_code == 206
        if resume_from and not append:
            print("    服务器未接受 Range，重新下载")
            resume_from = 0

        content_len = int(r.headers.get("Content-Length", "0") or 0)
        total = resume_from + content_len if content_len else 0
        mode = "ab" if append else "wb"
        downloaded = resume_from
        t0 = time.monotonic()
        last_print = 0.0

        with part.open(mode) as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)
                now = time.monotonic()
                if now - last_print >= 0.25:
                    elapsed = max(now - t0, 1e-6)
                    new_bytes = max(downloaded - resume_from, 0)
                    speed = new_bytes / elapsed
                    if total:
                        pct = downloaded * 100.0 / total
                        msg = (
                            f"\r    {pct:6.2f}%  {human_bytes(downloaded)} / {human_bytes(total)}"
                            f"  {human_bytes(speed)}/s"
                        )
                    else:
                        msg = f"\r    {human_bytes(downloaded)}  {human_bytes(speed)}/s"
                    print(msg, end="", flush=True)
                    last_print = now
        print()

    part.replace(dest)


def filtered_sources(artifact: Artifact, source_filter: str) -> tuple[Source, ...]:
    if source_filter == "auto":
        return artifact.sources
    return tuple(s for s in artifact.sources if s.kind == source_filter)


def download_artifact(
    session: requests.Session,
    artifact: Artifact,
    dest_dir: Path,
    *,
    source_filter: str,
    timeout: int,
    force: bool,
    dry_run: bool,
) -> bool:
    dest = dest_dir / artifact.filename
    if dest.exists() and not force:
        if artifact.sha256 and not dry_run:
            if verify_hash(dest, artifact.sha256):
                print(f"    已存在且校验通过: {dest}")
                return True
            print("    已有文件校验失败，将重新下载")
            dest.unlink(missing_ok=True)
        else:
            print(f"    已存在，跳过: {dest}")
            return True

    sources = filtered_sources(artifact, source_filter)
    if not sources:
        print(f"    [!] {artifact.filename}: 没有 {source_filter} 来源")
        return False

    errors: list[str] = []
    for i, source in enumerate(sources, 1):
        try:
            print(f"    来源 {i}/{len(sources)} [{source.kind}] {source.resolved_url()}")
            download_http(
                session,
                source,
                dest,
                timeout=timeout,
                force=force,
                dry_run=dry_run,
            )
            if dry_run:
                return True
            if not verify_hash(dest, artifact.sha256):
                dest.unlink(missing_ok=True)
                errors.append(f"{source.kind}: SHA-256 mismatch")
                continue
            return True
        except (requests.RequestException, OSError, ValueError) as exc:
            errors.append(f"{source.kind}: {exc}")
            print(f"    [!] 此来源失败: {exc}")
            # Preserve .part for the next retry/source when URLs serve identical bytes.

    print(f"    [X] {artifact.filename} 下载失败:")
    for err in errors:
        print(f"        - {err}")
    return False


def resolve_models(names: Iterable[str]) -> list[Model]:
    names = list(names)
    if len(names) == 1 and names[0].lower() == "all":
        return [m for m in MODELS if m.include_in_all]
    resolved: list[Model] = []
    seen: set[str] = set()
    for name in names:
        model = MODEL_INDEX.get(name.lower())
        if not model:
            raise SystemExit(f"未知模型: {name}\n运行 `list` 查看可用 key。")
        if model.key not in seen:
            resolved.append(model)
            seen.add(model.key)
    return resolved


def cmd_list(args: argparse.Namespace) -> int:
    out = Path(args.output).expanduser() if args.output else None
    print("内置模型清单:\n")
    for m in MODELS:
        marker = "*" if m.include_in_all else " "
        print(f"{marker} {m.key:24} {m.family:20} {m.name}")
        if m.unavailable_reason:
            print(f"    [未公开] {m.unavailable_reason}")
        for a in m.artifacts:
            status = ""
            if out:
                p = out / m.key / a.filename
                status = " [已存在]" if p.exists() else " [缺失]"
            kinds = "/".join(dict.fromkeys(s.kind for s in a.sources))
            print(f"    - {a.filename}  ({kinds}){status}")
            if a.note:
                print(f"      注意: {a.note}")
    print("\n* = `download all` 会包含。reference-only 模型默认不包含。")
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    models = resolve_models(args.models)
    root = Path(args.output).expanduser().resolve()
    proxy, trust_env = configured_proxy(args.proxy, args.no_proxy)
    session = make_session(proxy, trust_env)

    if proxy:
        print(f"代理: {proxy}")
    elif trust_env:
        env_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or os.environ.get("ALL_PROXY")
        print(f"代理: {'继承环境变量 ' + env_proxy if env_proxy else '直连（未配置）'}")
    else:
        print("代理: 强制直连")
    print(f"目录: {root}\n")

    failures = 0
    unavailable = 0
    for m in models:
        print(f"==> {m.key}: {m.name} [{m.family}]")
        if m.unavailable_reason:
            print(f"    [跳过：权重未公开] {m.unavailable_reason}\n")
            unavailable += 1
            continue
        model_dir = root / m.key
        for artifact in m.artifacts:
            ok = download_artifact(
                session,
                artifact,
                model_dir,
                source_filter=args.source,
                timeout=args.timeout,
                force=args.force,
                dry_run=args.dry_run,
            )
            if not ok:
                failures += 1
        print()

    if unavailable:
        print(f"提示: {unavailable} 个模型因未找到公开的精确 checkpoint 而跳过。")
    if failures:
        print(f"失败: {failures} 个文件。")
        return 2
    print("完成。")
    return 0


def cmd_proxy(args: argparse.Namespace) -> int:
    cfg = load_config()
    action = args.proxy_action
    if action == "add":
        validate_proxy_url(args.url)
        cfg["proxies"][args.name] = args.url
        save_config(cfg)
        print(f"已保存代理 {args.name} = {args.url}")
    elif action == "remove":
        if args.name not in cfg["proxies"]:
            raise SystemExit(f"代理不存在: {args.name}")
        del cfg["proxies"][args.name]
        if cfg.get("active_proxy") == args.name:
            cfg["active_proxy"] = None
        save_config(cfg)
        print(f"已删除代理: {args.name}")
    elif action == "use":
        if args.name not in cfg["proxies"]:
            raise SystemExit(f"代理不存在: {args.name}")
        cfg["active_proxy"] = args.name
        save_config(cfg)
        print(f"当前代理: {args.name} = {cfg['proxies'][args.name]}")
    elif action == "off":
        cfg["active_proxy"] = None
        save_config(cfg)
        print("已关闭脚本内置代理。注意：下载时仍会继承 shell 的 HTTP(S)_PROXY/ALL_PROXY；要强制直连请用 --no-proxy。")
    elif action in {"list", "show"}:
        active = cfg.get("active_proxy")
        if not cfg["proxies"]:
            print("没有保存的代理配置。")
        else:
            for name, url in cfg["proxies"].items():
                mark = "*" if name == active else " "
                print(f"{mark} {name:16} {url}")
        if action == "show":
            print(f"配置文件: {config_path()}")
            print(f"活动代理: {active or '(无；继承环境变量)'}")
            for env in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
                if os.environ.get(env):
                    print(f"{env}={os.environ[env]}")
    return 0


def infer_filename_from_url(url: str) -> str:
    name = Path(urlparse(url).path).name
    return name or "download.bin"


def cmd_fetch(args: argparse.Namespace) -> int:
    proxy, trust_env = configured_proxy(args.proxy, args.no_proxy)
    session = make_session(proxy, trust_env)
    kind = args.backend

    if kind == "hf":
        source = Source("hf", repo=args.arg1, file=args.arg2, revision=args.revision or "main")
        filename = Path(args.arg2).name
    elif kind == "modelscope":
        # ModelScope defaults to master in its public download examples/API.
        source = Source("modelscope", repo=args.arg1, file=args.arg2, revision=args.revision or "master")
        filename = Path(args.arg2).name
    elif kind in {"github", "url"}:
        source = Source(kind, url=args.arg1)
        filename = infer_filename_from_url(args.arg1)
    else:
        raise SystemExit(f"未知 backend: {kind}")

    out = Path(args.output).expanduser()
    if out.exists() and out.is_dir():
        dest = out / filename
    elif str(args.output).endswith(("/", os.sep)):
        dest = out / filename
    elif out.suffix and kind in {"github", "url"}:
        dest = out
    else:
        # For repo backends `-o` is naturally a directory; for URL, absent suffix is treated as dir.
        dest = out / filename

    print(f"[{kind}] {source.resolved_url()}\n -> {dest}")
    try:
        download_http(
            session,
            source,
            dest,
            timeout=args.timeout,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (requests.RequestException, OSError, ValueError) as exc:
        print(f"下载失败: {exc}", file=sys.stderr)
        return 2
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="uvr-fast 模型下载器：GitHub / Hugging Face / ModelScope + 代理管理 + 断点续传"
    )
    sub = p.add_subparsers(dest="command", required=True)

    lp = sub.add_parser("list", help="列出内置模型")
    lp.add_argument("-o", "--output", help="顺便检查该目录下的下载状态")
    lp.set_defaults(func=cmd_list)

    dp = sub.add_parser("download", help="下载内置模型")
    dp.add_argument("models", nargs="+", help="模型 key；使用 all 下载所有公开的精确目标模型")
    dp.add_argument("-o", "--output", default="./models", help="模型根目录，默认 ./models")
    dp.add_argument(
        "--source",
        choices=("auto", "github", "hf", "modelscope"),
        default="auto",
        help="限制来源；auto 会按 manifest 顺序自动 fallback",
    )
    dp.add_argument("--proxy", help="临时代理 URL，例如 http://127.0.0.1:7890")
    dp.add_argument("--no-proxy", action="store_true", help="本次强制直连，忽略脚本配置和环境代理")
    dp.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="单次网络读超时秒数")
    dp.add_argument("--force", action="store_true", help="忽略已有完成文件并重新下载")
    dp.add_argument("--dry-run", action="store_true", help="只打印将要下载的 URL")
    dp.set_defaults(func=cmd_download)

    pp = sub.add_parser("proxy", help="管理代理 profile")
    psub = pp.add_subparsers(dest="proxy_action", required=True)
    pa = psub.add_parser("add", help="保存代理")
    pa.add_argument("name")
    pa.add_argument("url")
    pa.set_defaults(func=cmd_proxy)
    pr = psub.add_parser("remove", help="删除代理")
    pr.add_argument("name")
    pr.set_defaults(func=cmd_proxy)
    pu = psub.add_parser("use", help="启用已保存代理")
    pu.add_argument("name")
    pu.set_defaults(func=cmd_proxy)
    po = psub.add_parser("off", help="禁用脚本内置代理")
    po.set_defaults(func=cmd_proxy)
    pl = psub.add_parser("list", help="列出保存的代理")
    pl.set_defaults(func=cmd_proxy)
    ps = psub.add_parser("show", help="显示当前代理和环境变量")
    ps.set_defaults(func=cmd_proxy)

    fp = sub.add_parser("fetch", help="从 HF / ModelScope / GitHub 下载任意单文件")
    fp.add_argument("backend", choices=("hf", "modelscope", "github", "url"))
    fp.add_argument("arg1", help="hf/modelscope: repo/model id；github/url: 直接 URL")
    fp.add_argument("arg2", nargs="?", help="hf/modelscope: repo 内文件路径")
    fp.add_argument("-o", "--output", default="./downloads", help="目标目录或 URL 模式下的目标文件")
    fp.add_argument("--revision", help="HF revision，或 ModelScope revision")
    fp.add_argument("--proxy", help="临时代理 URL")
    fp.add_argument("--no-proxy", action="store_true")
    fp.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    fp.add_argument("--force", action="store_true")
    fp.add_argument("--dry-run", action="store_true")
    fp.set_defaults(func=cmd_fetch)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "fetch" and args.backend in {"hf", "modelscope"} and not args.arg2:
        parser.error("fetch hf/modelscope 需要两个位置参数: REPO_ID FILE")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

"""
工具脚本：从当前 AstrBot 插件列表生成自定义插件源 JSON 与 MD5 文件。

功能说明：
- 扫描 AstrBot 的插件目录（data/plugins），读取每个插件的 metadata.yaml。
- 将插件元数据转换为兼容官方插件市场格式的 JSON 注册表：
    {
        "plugin_name": {
            "name": "...",
            "desc": "...",
            "version": "...",
            "author": "...",
            "repo": "...",
            "display_name": "...",
            "tags": [...],
            ...
        },
        ...
    }
- 计算该 JSON 内容的 MD5，并生成配套的 MD5 JSON 文件：
    {"md5": "<hex_md5>"}

使用方式示例：
1. 在 AstrBot 根目录执行（自动使用 data/plugins）：
    python tools/generate_plugin_registry.py

2. 指定输出文件路径：
    python tools/generate_plugin_registry.py \
        --output plugins_custom.json \
        --md5-output plugins_custom-md5.json

3. 指定插件目录（如果你有单独的插件集合）：
    python tools/generate_plugin_registry.py \
        --plugin-dir /path/to/your/plugins
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

import httpx
import yaml

from astrbot.cli.utils.plugin import load_yaml_metadata
from astrbot.core.utils.astrbot_path import get_astrbot_plugin_path

# 默认配置变量，便于根据实际环境调整
# 生成的插件市场 JSON 默认输出到 App-Store/admin/plugins.json
DEFAULT_REGISTRY_OUTPUT: str = "App-Store/admin/plugins.json"
# 对应的 MD5 文件默认输出到同一目录下
DEFAULT_MD5_OUTPUT: str = "App-Store/admin/plugins_md5.json"

# GitHub 相关配置
GITHUB_API_BASE: str = "https://api.github.com"
GITHUB_RAW_BASE: str = "https://raw.githubusercontent.com"
GITHUB_HTTP_TIMEOUT: float = 20.0

# GitHub 访问令牌配置：
# 1. 优先使用此变量配置的令牌（如不需要可保持为空字符串）
# 2. 若此变量为空，则依次从环境变量中读取 GITHUB_TOKEN、GH_TOKEN
GITHUB_ACCESS_TOKEN: str = ""
GITHUB_TOKEN_ENV_KEYS: tuple[str, ...] = ("GITHUB_TOKEN", "GH_TOKEN")


def create_github_client() -> httpx.Client:
    """
    创建访问 GitHub 所需的 HTTP 客户端。

    优先使用 GITHUB_ACCESS_TOKEN，其次尝试从环境变量中读取令牌。
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AstrBot-Plugin-Registry-Generator",
    }

    token = GITHUB_ACCESS_TOKEN
    if not token:
        for env_key in GITHUB_TOKEN_ENV_KEYS:
            env_val = os.environ.get(env_key)
            if env_val:
                token = env_val
                break

    if token:
        headers["Authorization"] = f"Bearer {token}"

    client = httpx.Client(
        headers=headers,
        follow_redirects=True,
        timeout=GITHUB_HTTP_TIMEOUT,
    )
    return client


def collect_installed_plugins(plugin_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    收集指定插件目录下的插件元数据，并构建插件注册表字典。

    插件目录结构要求：
    - plugin_dir/
        - plugin_a/
            - metadata.yaml
        - plugin_b/
            - metadata.yaml
        - ...

    元数据读取规则：
    - 使用 AstrBot 已有的 load_yaml_metadata 读取 metadata.yaml。
    - 只处理包含 name、desc/description、version、author 的插件。
    - 如果存在 repo 字段，则写入注册表，以支持在线更新。
    - display_name、tags 等扩展字段会尽量从 metadata.yaml 中读取，
      不存在则使用合理默认值。

    Args:
        plugin_dir: 插件根目录路径（一般为 data/plugins）。

    Returns:
        Dict[str, Dict[str, Any]]: 插件注册表字典，键为插件 name，值为插件信息。
    """
    registry: Dict[str, Dict[str, Any]] = {}

    if not plugin_dir.exists():
        # 如果插件目录不存在，则返回空字典，交由调用方处理
        return registry

    # 遍历插件目录中的所有子目录，每个子目录视为一个插件
    for sub in plugin_dir.iterdir():
        if not sub.is_dir():
            # 非目录（文件等）跳过
            continue

        # 使用 AstrBot 内置工具函数读取 metadata.yaml
        metadata = load_yaml_metadata(sub)

        if not metadata:
            # 没有 metadata，跳过该插件
            continue

        # 兼容旧字段名 description -> desc
        if "desc" not in metadata and "description" in metadata:
            metadata["desc"] = metadata["description"]

        # 必要字段检查：name / desc / version / author
        name = str(metadata.get("name", "")).strip()
        desc = str(metadata.get("desc", "")).strip()
        version = str(metadata.get("version", "")).strip()
        author = str(metadata.get("author", "")).strip()

        if not name or not desc or not version or not author:
            # 元数据不完整，不纳入注册表
            continue

        # 仓库地址，用于后续在线更新
        repo = str(metadata.get("repo", "") or "").strip()

        # 展示名称，缺省时前端会使用 name
        display_name = str(metadata.get("display_name", "") or "").strip()

        # 标签列表，如果 metadata 中没有 tags，则使用空列表
        tags = metadata.get("tags") or []
        if not isinstance(tags, list):
            # 如果 tags 字段存在但不是列表，则强制转换为空列表，避免前端报错
            tags = []

        # 额外可选字段：social_link、logo、pinned、stars、updated_at
        social_link = str(metadata.get("social_link", "") or "").strip()
        logo = str(metadata.get("logo", "") or "").strip()
        pinned = bool(metadata.get("pinned", False))
        # stars 建议使用整数，如果 metadata 中有值尝试转换
        raw_stars = metadata.get("stars", 0)
        try:
            stars = int(raw_stars)
        except (TypeError, ValueError):
            stars = 0
        updated_at = str(metadata.get("updated_at", "") or "").strip()

        # 构建单个插件的注册表条目
        plugin_entry: Dict[str, Any] = {
            "name": name,
            "desc": desc,
            "version": version,
            "author": author,
            "repo": repo,
            # 扩展字段
            "display_name": display_name,
            "social_link": social_link,
            "tags": tags,
            "logo": logo,
            "pinned": pinned,
            "stars": stars,
            "updated_at": updated_at,
        }

        # 顶层键使用插件 name，保持与官方格式一致
        registry[name] = plugin_entry

    return registry


def parse_github_repo(repo_url: str) -> Tuple[str, str] | None:
    """
    从仓库 URL 解析出 GitHub 仓库所有者与名称。

    支持的 URL 形式示例：
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/xxx

    Args:
        repo_url: 仓库地址。

    Returns:
        Tuple[str, str] | None: (owner, repo) 元组，解析失败返回 None。
    """
    parsed = urlparse(repo_url)
    if "github.com" not in parsed.netloc:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    owner = parts[0]
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _fetch_metadata_for_branch(
    client: httpx.Client,
    owner: str,
    repo: str,
    branch: str,
) -> Dict[str, Any] | None:
    """
    从指定分支读取仓库根目录下的 metadata.yaml 文件。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。
        branch: 分支名称。

    Returns:
        dict | None: 解析后的元数据字典，失败返回 None。
    """
    url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/metadata.yaml"
    try:
        resp = client.get(url, timeout=15.0)
    except Exception:
        return None
    if resp.status_code != 200:
        return None
    try:
        data = yaml.safe_load(resp.text) or {}
    except Exception:
        return None
    if isinstance(data, dict):
        return data
    return None


def fetch_remote_metadata(
    client: httpx.Client,
    owner: str,
    repo: str,
) -> Dict[str, Any] | None:
    """
    获取远程仓库中的 metadata.yaml 元数据。

    优先尝试使用 GitHub 仓库的 default_branch，其次回退到 main、master。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。

    Returns:
        dict | None: 元数据字典，若无法获取则返回 None。
    """
    default_branch: str | None = None

    try:
        api_resp = client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
        if api_resp.status_code == 200:
            repo_info = api_resp.json()
            default_branch = str(repo_info.get("default_branch", "") or "").strip()
    except Exception:
        default_branch = None

    tried_branches: set[str] = set()

    if default_branch:
        tried_branches.add(default_branch)
        data = _fetch_metadata_for_branch(client, owner, repo, default_branch)
        if data:
            return data

    for branch in ("main", "master"):
        if branch in tried_branches:
            continue
        data = _fetch_metadata_for_branch(client, owner, repo, branch)
        if data:
            return data

    return None


def update_registry_from_github(registry: Dict[str, Dict[str, Any]]) -> None:
    """
    使用 GitHub 仓库中的 metadata.yaml 刷新注册表中的插件元数据。

    只处理带有 GitHub 仓库地址的插件：
    - 解析 repo 字段得到 owner/repo。
    - 读取远程 metadata.yaml，更新 version/desc/author 等字段。

    Args:
        registry: 插件注册表字典。
    """
    if not registry:
        return
    client = create_github_client()
    try:
        for plugin_name, entry in registry.items():
            repo_url = str(entry.get("repo", "") or "").strip()
            if not repo_url:
                continue
            parsed = parse_github_repo(repo_url)
            if not parsed:
                continue
            owner, repo = parsed
            remote_metadata = fetch_remote_metadata(client, owner, repo)
            if not remote_metadata:
                continue
            remote_version = str(remote_metadata.get("version", "") or "").strip()
            if not remote_version:
                continue
            entry["version"] = remote_version
            remote_desc = remote_metadata.get("desc") or remote_metadata.get(
                "description",
            )
            if remote_desc:
                entry["desc"] = str(remote_desc)
            remote_author = remote_metadata.get("author")
            if remote_author:
                entry["author"] = str(remote_author)
    finally:
        client.close()


def compute_registry_md5(registry: Dict[str, Dict[str, Any]]) -> str:
    """
    计算插件注册表字典内容的 MD5 值。

    为了确保不同环境下 MD5 一致性：
    - 使用 json.dumps 时指定 sort_keys=True 和 separators 选项，
      保证键的顺序和缩进一致。
    - 使用 UTF-8 编码将字符串转换为字节，再计算 MD5。

    Args:
        registry: 插件注册表字典。

    Returns:
        str: 32 位十六进制 MD5 字符串。
    """
    # 将字典序列化为稳定的 JSON 字符串
    registry_json = json.dumps(
        registry,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    md5 = hashlib.md5()
    md5.update(registry_json.encode("utf-8"))
    return md5.hexdigest()


def save_json(data: Any, output_path: Path) -> None:
    """
    将任意数据以 JSON 格式保存到指定路径。

    会自动创建父目录，并使用 UTF-8 编码写入文件。

    Args:
        data: 任意可 JSON 序列化的数据。
        output_path: 输出文件路径。
    """
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        # 为了便于人工查看，这里使用缩进格式
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_existing_registry(output_path: Path) -> Dict[str, Dict[str, Any]]:
    if not output_path.exists():
        return {}
    try:
        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    existing: Dict[str, Dict[str, Any]] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            existing[str(key)] = value
    return existing


def diff_registries(
    old: Dict[str, Dict[str, Any]],
    new: Dict[str, Dict[str, Any]],
) -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Tuple[Any, Any]]],
]:
    added: Dict[str, Dict[str, Any]] = {}
    removed: Dict[str, Dict[str, Any]] = {}
    updated: Dict[str, Dict[str, Tuple[Any, Any]]] = {}

    for name, entry in new.items():
        if name not in old:
            added[name] = entry
            continue
        old_entry = old[name]
        if old_entry == entry:
            continue
        field_changes: Dict[str, Tuple[Any, Any]] = {}
        keys = set(old_entry.keys()) | set(entry.keys())
        for key in keys:
            old_value = old_entry.get(key)
            new_value = entry.get(key)
            if old_value != new_value:
                field_changes[key] = (old_value, new_value)
        if field_changes:
            updated[name] = field_changes

    for name, entry in old.items():
        if name not in new:
            removed[name] = entry

    return added, removed, updated


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。

    支持：
    - --plugin-dir：插件目录，默认使用 AstrBot 的 data/plugins。
    - --output：注册表 JSON 输出路径，默认 plugins_custom.json。
    - --md5-output：MD5 JSON 输出路径，默认 plugins_custom-md5.json。

    Returns:
        argparse.Namespace: 解析后的参数对象。
    """
    parser = argparse.ArgumentParser(
        description="从当前 AstrBot 插件列表生成自定义插件源 JSON 与 MD5 文件。",
    )
    parser.add_argument(
        "--plugin-dir",
        type=str,
        default="",
        help="插件目录路径，默认使用 AstrBot 内置的 data/plugins 目录。",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_REGISTRY_OUTPUT,
        help="插件注册表 JSON 输出路径，默认为 ./plugins_custom.json。",
    )
    parser.add_argument(
        "--md5-output",
        type=str,
        default=DEFAULT_MD5_OUTPUT,
        help="插件注册表 MD5 JSON 输出路径，默认为 ./plugins_custom-md5.json。",
    )
    return parser.parse_args()


def resolve_plugin_dir(plugin_dir_arg: str) -> Path:
    """
    根据命令行参数解析最终使用的插件目录路径。

    优先级：
    1. 如果 --plugin-dir 参数非空，则使用该路径。
    2. 否则，使用 AstrBot 内置的 get_astrbot_plugin_path() 路径。

    Args:
        plugin_dir_arg: 命令行传入的插件目录路径字符串。

    Returns:
        Path: 最终使用的插件目录路径。
    """
    if plugin_dir_arg:
        # 用户显式指定路径时，使用用户配置
        return Path(plugin_dir_arg).expanduser().resolve()

    # 默认使用 AstrBot 的插件目录 data/plugins
    return Path(get_astrbot_plugin_path()).resolve()


def main() -> None:
    """
    脚本入口函数。

    步骤：
    1. 解析命令行参数，确定插件目录与输出路径。
    2. 收集插件元数据，生成注册表字典。
    3. 将注册表写入 JSON 文件。
    4. 计算注册表的 MD5，并写入 MD5 JSON 文件。
    5. 在控制台打印简单的执行结果，方便确认。
    """
    args = parse_args()

    plugin_dir = resolve_plugin_dir(args.plugin_dir)
    output_path = Path(args.output).expanduser().resolve()
    md5_output_path = Path(args.md5_output).expanduser().resolve()

    print(f"使用插件目录: {plugin_dir}")
    print(f"注册表输出文件: {output_path}")
    print(f"MD5 输出文件: {md5_output_path}")

    existing_registry = load_existing_registry(output_path)

    registry = collect_installed_plugins(plugin_dir)

    if not registry:
        print("警告：未在指定目录中发现有效的插件元数据，未生成任何条目。")

    update_registry_from_github(registry)

    added, removed, updated = diff_registries(existing_registry, registry)

    save_json(registry, output_path)
    print(f"已生成插件注册表 JSON，包含 {len(registry)} 个插件。")

    if not existing_registry:
        print("未检测到已有注册表文件，视为首次生成。")
    else:
        if not added and not removed and not updated:
            print("本次生成与已有注册表内容一致，未检测到插件变更。")
        else:
            print("插件变更详情：")
            for name, entry in added.items():
                version = entry.get("version", "")
                print(f"  [新增] {name} 版本 {version}")
            for name, entry in removed.items():
                version = entry.get("version", "")
                print(f"  [移除] {name} 原版本 {version}")
            for name, fields in updated.items():
                version_old, version_new = fields.get("version", ("", ""))
                if version_old != version_new:
                    print(
                        f"  [更新] {name} 版本 {version_old} -> {version_new}",
                    )
                else:
                    print(f"  [变更] {name} 元数据发生更新")

    # 计算并保存 MD5 JSON
    md5_value = compute_registry_md5(registry)
    md5_data = {"md5": md5_value}
    save_json(md5_data, md5_output_path)
    print(f"已生成 MD5 JSON，MD5 = {md5_value}")


if __name__ == "__main__":
    main()

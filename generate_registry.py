"""
插件注册表生成器：从多个 GitHub 仓库自动收集 AstrBot 插件元数据并生成插件源 JSON。

功能说明：
- 从 sources.yaml 配置的多个 GitHub 仓库读取插件元数据
- 支持单插件仓库和插件集合仓库（collection 类型）
- 记录每个仓库的 commit SHA，只处理有更新的仓库
- 生成兼容官方插件市场格式的 JSON 注册表
- 支持通过 GitHub Actions 自动定时运行

使用方式：
1. 手动运行：
    python generate_registry.py

2. 指定配置文件：
    python generate_registry.py --config config.yaml --sources sources.yaml

3. 强制更新所有仓库（忽略 commit SHA 检查）：
    python generate_registry.py --force
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
import yaml

# 自动发现插件仓库的默认 GitHub 用户名
DEFAULT_GITHUB_USER: str = "1592363624"
# 插件仓库名前缀
PLUGIN_REPO_PREFIX: str = "astrbot_plugin"

# GitHub API 配置
GITHUB_API_BASE: str = "https://api.github.com"
GITHUB_RAW_BASE: str = "https://raw.githubusercontent.com"
GITHUB_HTTP_TIMEOUT: float = 20.0

# 默认配置文件路径
DEFAULT_CONFIG_PATH: str = "config.yaml"
DEFAULT_SOURCES_PATH: str = "sources.yaml"

# commit SHA 记录文件路径
COMMIT_STATE_FILE: str = ".commit_state.json"


def create_github_client() -> httpx.Client:
    """
    创建访问 GitHub 所需的 HTTP 客户端。

    优先从环境变量中读取 GitHub Token（GitHub Actions 环境会自动提供）。

    Returns:
        httpx.Client: 配置好的 HTTP 客户端实例。
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AstrBot-Plugin-Registry-Generator",
    }

    # 尝试从环境变量中读取 Token
    token = ""
    for env_key in ("GITHUB_TOKEN", "GH_TOKEN"):
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


def parse_github_repo(repo_url: str) -> Optional[Tuple[str, str]]:
    """
    从仓库 URL 解析出 GitHub 仓库所有者与名称。

    支持的 URL 形式示例：
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo/xxx

    Args:
        repo_url: 仓库地址。

    Returns:
        Optional[Tuple[str, str]]: (owner, repo) 元组，解析失败返回 None。
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


def get_repo_default_branch(client: httpx.Client, owner: str, repo: str) -> str:
    """
    获取 GitHub 仓库的默认分支名称。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。

    Returns:
        str: 默认分支名称，失败时返回 "main"。
    """
    try:
        api_resp = client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}")
        if api_resp.status_code == 200:
            repo_info = api_resp.json()
            return str(repo_info.get("default_branch", "main") or "main").strip()
    except Exception:
        pass
    return "main"


def get_repo_latest_commit_sha(client: httpx.Client, owner: str, repo: str, branch: str) -> Optional[str]:
    """
    获取仓库指定分支的最新 commit SHA。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。
        branch: 分支名称。

    Returns:
        Optional[str]: commit SHA，失败返回 None。
    """
    try:
        api_resp = client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits/{branch}")
        if api_resp.status_code == 200:
            commit_info = api_resp.json()
            return str(commit_info.get("sha", "") or "").strip()
    except Exception:
        pass
    return None


def fetch_file_from_repo(
    client: httpx.Client,
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
) -> Optional[str]:
    """
    从 GitHub 仓库读取指定文件的内容。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。
        branch: 分支名称。
        file_path: 文件在仓库中的路径。

    Returns:
        Optional[str]: 文件内容，失败返回 None。
    """
    url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{file_path}"
    try:
        resp = client.get(url, timeout=15.0)
    except Exception:
        return None
    if resp.status_code != 200:
        return None
    return resp.text


def fetch_metadata_from_repo(
    client: httpx.Client,
    owner: str,
    repo: str,
    branch: str,
    sub_dir: str = "",
) -> Optional[Dict[str, Any]]:
    """
    从 GitHub 仓库读取 metadata.yaml 文件。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。
        branch: 分支名称。
        sub_dir: 子目录路径（用于 collection 类型仓库）。

    Returns:
        Optional[Dict[str, Any]]: 解析后的元数据字典，失败返回 None。
    """
    file_path = f"{sub_dir}/metadata.yaml" if sub_dir else "metadata.yaml"
    content = fetch_file_from_repo(client, owner, repo, branch, file_path)
    if not content:
        return None
    try:
        data = yaml.safe_load(content) or {}
    except Exception:
        return None
    if isinstance(data, dict):
        return data
    return None


def list_subdirectories_in_repo(
    client: httpx.Client,
    owner: str,
    repo: str,
    branch: str,
) -> List[str]:
    """
    列出 GitHub 仓库根目录下的所有子目录（用于 collection 类型仓库）。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。
        branch: 分支名称。

    Returns:
        List[str]: 子目录名称列表。
    """
    try:
        api_resp = client.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents?ref={branch}")
        if api_resp.status_code != 200:
            return []
        contents = api_resp.json()
        if not isinstance(contents, list):
            return []
        # 只返回目录类型的条目
        return [
            item["name"]
            for item in contents
            if isinstance(item, dict) and item.get("type") == "dir"
        ]
    except Exception:
        return []


def build_plugin_entry(metadata: Dict[str, Any], repo_url: str) -> Optional[Dict[str, Any]]:
    """
    从元数据构建插件注册表条目。

    Args:
        metadata: 从 metadata.yaml 读取的元数据字典。
        repo_url: 插件仓库地址。

    Returns:
        Optional[Dict[str, Any]]: 插件注册表条目，元数据不完整时返回 None。
    """
    # 兼容旧字段名 description -> desc
    if "desc" not in metadata and "description" in metadata:
        metadata["desc"] = metadata["description"]

    # 必要字段检查
    name = str(metadata.get("name", "")).strip()
    desc = str(metadata.get("desc", "")).strip()
    version = str(metadata.get("version", "")).strip()
    author = str(metadata.get("author", "")).strip()

    if not name or not desc or not version or not author:
        return None

    # 扩展字段
    display_name = str(metadata.get("display_name", "") or "").strip()
    social_link = str(metadata.get("social_link", "") or "").strip()
    logo = str(metadata.get("logo", "") or "").strip()
    pinned = bool(metadata.get("pinned", False))

    # 标签列表
    tags = metadata.get("tags") or []
    if not isinstance(tags, list):
        tags = []

    # stars 字段
    raw_stars = metadata.get("stars", 0)
    try:
        stars = int(raw_stars)
    except (TypeError, ValueError):
        stars = 0

    updated_at = str(metadata.get("updated_at", "") or "").strip()

    return {
        "name": name,
        "desc": desc,
        "version": version,
        "author": author,
        "repo": repo_url,
        "display_name": display_name,
        "social_link": social_link,
        "tags": tags,
        "logo": logo,
        "pinned": pinned,
        "stars": stars,
        "updated_at": updated_at,
    }


def load_sources(sources_path: Path) -> List[Dict[str, Any]]:
    """
    加载插件源列表配置。

    Args:
        sources_path: sources.yaml 文件路径。

    Returns:
        List[Dict[str, Any]]: 插件源列表。
    """
    if not sources_path.exists():
        return []
    try:
        with sources_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    sources = data.get("sources") or []
    if not isinstance(sources, list):
        return []
    return sources


def fetch_astrbot_plugin_repos(
    client: httpx.Client,
    github_user: str = DEFAULT_GITHUB_USER,
) -> List[str]:
    """
    通过 GitHub API 自动发现指定用户下所有以 astrbot_plugin 开头的公开仓库。

    使用分页接口遍历全部仓库，避免截断。

    Args:
        client: HTTP 客户端实例。
        github_user: GitHub 用户名。

    Returns:
        List[str]: 仓库 URL 列表，按字母升序排列。
    """
    repos: List[str] = []
    page = 1
    per_page = 100

    while True:
        try:
            resp = client.get(
                f"{GITHUB_API_BASE}/users/{github_user}/repos",
                params={"per_page": per_page, "page": page},
            )
            if resp.status_code != 200:
                print(f"警告：GitHub API 请求失败 (状态码 {resp.status_code})，停止分页")
                break
            data = resp.json()
            if not isinstance(data, list) or not data:
                break
            for item in data:
                name = str(item.get("name", "") or "")
                if name.startswith(PLUGIN_REPO_PREFIX):
                    html_url = str(item.get("html_url", "") or "")
                    if html_url:
                        repos.append(html_url)
            if len(data) < per_page:
                break
            page += 1
        except Exception as e:
            print(f"警告：自动发现插件仓库时发生异常 ({e})，停止分页")
            break

    # 排序以保证输出稳定
    repos.sort()
    return repos


def generate_sources_yaml(
    sources_path: Path,
    client: httpx.Client,
    github_user: str = DEFAULT_GITHUB_USER,
) -> None:
    """
    自动发现指定用户下的 astrbot_plugin* 仓库，并写入 sources.yaml。

    保留仓库描述作为注释，便于人工识别插件用途。

    Args:
        sources_path: sources.yaml 文件路径。
        client: HTTP 客户端实例。
        github_user: GitHub 用户名。
    """
    # 先收集仓库及其描述（需要额外请求一次 API）
    repo_desc: List[Tuple[str, str]] = []
    page = 1
    per_page = 100

    while True:
        try:
            resp = client.get(
                f"{GITHUB_API_BASE}/users/{github_user}/repos",
                params={"per_page": per_page, "page": page},
            )
            if resp.status_code != 200:
                break
            data = resp.json()
            if not isinstance(data, list) or not data:
                break
            for item in data:
                name = str(item.get("name", "") or "")
                if name.startswith(PLUGIN_REPO_PREFIX):
                    html_url = str(item.get("html_url", "") or "")
                    desc = str(item.get("description", "") or "").strip()
                    fork = bool(item.get("fork", False))
                    if html_url:
                        repo_desc.append((html_url, desc, fork))  # type: ignore[arg-type]
            if len(data) < per_page:
                break
            page += 1
        except Exception:
            break

    # 按仓库名排序
    repo_desc.sort(key=lambda x: x[0])

    lines: List[str] = [
        "# 插件源列表配置文件",
        "# 由 GitHub Actions 自动生成，请勿手动编辑",
        "",
        "sources:",
    ]

    for url, desc, fork in repo_desc:
        repo_name = url.rstrip("/").split("/")[-1]
        # 生成注释：优先使用描述，fork 仓库会标注 (fork)
        if desc:
            comment = f"  # {desc}"
            if fork:
                comment += " (fork)"
        else:
            comment = f"  # {repo_name}" + (" (fork)" if fork else "")
        lines.append(comment)
        lines.append(f"  - repo: {url}")
        lines.append("    type: single")
        lines.append("")

    sources_path.parent.mkdir(parents=True, exist_ok=True)
    with sources_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"已自动生成 {sources_path}，包含 {len(repo_desc)} 个插件源。")


def load_commit_state(state_file: Path) -> Dict[str, str]:
    """
    加载仓库 commit SHA 状态记录。

    Args:
        state_file: 状态文件路径。

    Returns:
        Dict[str, str]: 仓库 URL 到 commit SHA 的映射。
    """
    if not state_file.exists():
        return {}
    try:
        with state_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def save_commit_state(state_file: Path, state: Dict[str, str]) -> None:
    """
    保存仓库 commit SHA 状态记录。

    Args:
        state_file: 状态文件路径。
        state: 仓库 URL 到 commit SHA 的映射。
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def process_single_plugin_repo(
    client: httpx.Client,
    owner: str,
    repo: str,
    branch: str,
    repo_url: str,
) -> Optional[Dict[str, Any]]:
    """
    处理单个插件仓库，读取 metadata.yaml 并构建注册表条目。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。
        branch: 分支名称。
        repo_url: 仓库 URL。

    Returns:
        Optional[Dict[str, Any]]: 插件注册表条目，失败返回 None。
    """
    metadata = fetch_metadata_from_repo(client, owner, repo, branch)
    if not metadata:
        return None
    return build_plugin_entry(metadata, repo_url)


def process_collection_repo(
    client: httpx.Client,
    owner: str,
    repo: str,
    branch: str,
    repo_url: str,
) -> Dict[str, Dict[str, Any]]:
    """
    处理插件集合仓库，遍历子目录读取多个插件的 metadata.yaml。

    Args:
        client: HTTP 客户端实例。
        owner: 仓库所有者。
        repo: 仓库名称。
        branch: 分支名称。
        repo_url: 仓库 URL。

    Returns:
        Dict[str, Dict[str, Any]]: 插件注册表字典，键为插件 name。
    """
    registry: Dict[str, Dict[str, Any]] = {}
    subdirs = list_subdirectories_in_repo(client, owner, repo, branch)

    for subdir in subdirs:
        metadata = fetch_metadata_from_repo(client, owner, repo, branch, subdir)
        if not metadata:
            continue
        entry = build_plugin_entry(metadata, repo_url)
        if entry:
            registry[entry["name"]] = entry

    return registry


def load_existing_registry(output_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    加载已有的插件注册表 JSON 文件。

    Args:
        output_path: JSON 文件路径。

    Returns:
        Dict[str, Dict[str, Any]]: 插件注册表字典。
    """
    if not output_path.exists():
        return {}
    try:
        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): v for k, v in data.items() if isinstance(v, dict)}


def diff_registries(
    old: Dict[str, Dict[str, Any]],
    new: Dict[str, Dict[str, Any]],
) -> Tuple[
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Any]],
    Dict[str, Dict[str, Tuple[Any, Any]]],
]:
    """
    对比新旧注册表的差异。

    Args:
        old: 旧注册表。
        new: 新注册表。

    Returns:
        Tuple: (新增插件, 移除插件, 更新插件) 三元组。
    """
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


def save_json(data: Any, output_path: Path) -> None:
    """
    将数据以 JSON 格式保存到文件。

    Args:
        data: 可 JSON 序列化的数据。
        output_path: 输出文件路径。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 变更记录分隔符
CHANGELOG_SEPARATOR: str = "---"
# 保留的最大变更记录数
MAX_CHANGELOG_ENTRIES: int = 10


def update_readme_changelog(
    readme_path: Path,
    added: Dict[str, Dict[str, Any]],
    removed: Dict[str, Dict[str, Any]],
    updated: Dict[str, Dict[str, Tuple[Any, Any]]],
) -> None:
    """
    更新 README.md 变更日志，保留最新的 10 条记录。

    Args:
        readme_path: README.md 文件路径。
        added: 新增插件字典。
        removed: 移除插件字典。
        updated: 更新插件字典，值为字段变更映射。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建本次变更条目
    changes: List[str] = []
    for name, entry in added.items():
        version = entry.get("version", "")
        changes.append(f"  - **[新增]** `{name}` v{version}")
    for name, entry in removed.items():
        version = entry.get("version", "")
        changes.append(f"  - **[移除]** `{name}` (原版本: {version})")
    for name, fields in updated.items():
        version_old, version_new = fields.get("version", ("", ""))
        if version_old != version_new:
            changes.append(f"  - **[更新]** `{name}` v{version_old} -> v{version_new}")
        else:
            changes.append(f"  - **[变更]** `{name}` 元数据发生更新")

    if not changes:
        return

    entry_text = f"### {now}\n\n" + "\n".join(changes) + "\n"

    # 读取现有 README 内容
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
    else:
        content = ""

    # 查找分隔线位置，将变更记录插入到分隔线后面
    lines = content.split("\n")
    separator_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == CHANGELOG_SEPARATOR:
            separator_idx = i
            break

    if separator_idx == -1:
        header = f"# AstrBot Plugin Registry\n\n插件注册表自动更新日志，记录最近 {MAX_CHANGELOG_ENTRIES} 次变更。\n\n---\n"
        existing_entries = ""
    else:
        header = "\n".join(lines[: separator_idx + 1]) + "\n"
        existing_entries = "\n".join(lines[separator_idx + 1 :])

    # 合并新旧条目
    all_entries = entry_text + "\n" + existing_entries if existing_entries.strip() else entry_text

    # 只保留最新的 MAX_CHANGELOG_ENTRIES 条记录
    entries_list: List[str] = []
    current_entry_lines: List[str] = []
    for line in all_entries.split("\n"):
        if line.startswith("### "):
            if current_entry_lines:
                entries_list.append("\n".join(current_entry_lines))
            current_entry_lines = [line]
        else:
            current_entry_lines.append(line)
    if current_entry_lines:
        entries_list.append("\n".join(current_entry_lines))

    entries_list = entries_list[:MAX_CHANGELOG_ENTRIES]
    final_content = header + "\n" + "\n\n".join(entries_list) + "\n"

    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(final_content, encoding="utf-8")
    print(f"已更新 README.md 变更日志。")


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。

    Returns:
        argparse.Namespace: 解析后的参数对象。
    """
    parser = argparse.ArgumentParser(
        description="从多个 GitHub 仓库自动收集 AstrBot 插件元数据并生成插件源 JSON。",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="配置文件路径，默认为 config.yaml。",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default=DEFAULT_SOURCES_PATH,
        help="插件源列表文件路径，默认为 sources.yaml。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制更新所有仓库，忽略 commit SHA 检查。",
    )
    parser.add_argument(
        "--generate-sources",
        action="store_true",
        help="自动从 GitHub 发现 astrbot_plugin* 仓库并生成 sources.yaml。",
    )
    parser.add_argument(
        "--github-user",
        type=str,
        default=DEFAULT_GITHUB_USER,
        help=f"GitHub 用户名，用于自动发现插件仓库，默认为 {DEFAULT_GITHUB_USER}。",
    )
    return parser.parse_args()


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    加载配置文件。

    Args:
        config_path: 配置文件路径。

    Returns:
        Dict[str, Any]: 配置字典。
    """
    default_config = {
        "output": "plugins.json",
        "check_interval": 300,  # 秒
    }
    if not config_path.exists():
        return default_config
    try:
        with config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception:
        return default_config
    if not isinstance(data, dict):
        return default_config
    # 合并默认配置
    for key, value in default_config.items():
        if key not in data:
            data[key] = value
    return data


def main() -> None:
    """
    脚本入口函数。

    步骤：
    1. 加载配置文件和插件源列表
    2. 检查每个仓库的 commit SHA，只处理有更新的仓库
    3. 从 GitHub 读取插件元数据，生成注册表
    4. 对比新旧注册表，输出变更日志
    5. 保存注册表和 commit 状态
    """
    args = parse_args()

    config_path = Path(args.config).expanduser().resolve()
    sources_path = Path(args.sources).expanduser().resolve()

    # 加载配置
    config = load_config(config_path)
    output_path = Path(config["output"]).expanduser().resolve()
    state_file = config_path.parent / COMMIT_STATE_FILE

    print(f"配置文件: {config_path}")
    print(f"插件源列表: {sources_path}")
    print(f"注册表输出: {output_path}")

    # 如果指定了 --generate-sources，则自动生成 sources.yaml
    if args.generate_sources:
        client = create_github_client()
        try:
            generate_sources_yaml(sources_path, client, args.github_user)
        finally:
            client.close()
        # 生成 sources.yaml 后，继续执行后续的注册表生成逻辑

    # 加载插件源列表
    sources = load_sources(sources_path)
    if not sources:
        print("警告：未配置任何插件源，请检查 sources.yaml")
        return

    # 加载 commit 状态
    commit_state = load_commit_state(state_file)
    new_commit_state = commit_state.copy()

    # 加载已有注册表
    existing_registry = load_existing_registry(output_path)
    registry: Dict[str, Dict[str, Any]] = {}

    client = create_github_client()
    try:
        for source in sources:
            repo_url = str(source.get("repo", "")).strip()
            if not repo_url:
                continue

            parsed = parse_github_repo(repo_url)
            if not parsed:
                print(f"跳过无效仓库: {repo_url}")
                continue

            owner, repo = parsed
            branch = str(source.get("branch", "")).strip()
            if not branch:
                branch = get_repo_default_branch(client, owner, repo)

            source_type = str(source.get("type", "single")).strip().lower()

            # 检查 commit SHA 是否有更新
            latest_sha = get_repo_latest_commit_sha(client, owner, repo, branch)
            old_sha = commit_state.get(repo_url, "")

            if not args.force and latest_sha and latest_sha == old_sha:
                print(f"仓库 {repo_url} 无更新，跳过")
                # 无更新时，保留原有注册表中的插件
                for name, entry in existing_registry.items():
                    if str(entry.get("repo", "")).strip() == repo_url:
                        registry[name] = entry
                continue

            print(f"处理仓库: {repo_url} (分支: {branch}, 类型: {source_type})")

            if source_type == "collection":
                # 插件集合仓库
                sub_registry = process_collection_repo(client, owner, repo, branch, repo_url)
                registry.update(sub_registry)
                print(f"  发现 {len(sub_registry)} 个插件")
            else:
                # 单插件仓库
                entry = process_single_plugin_repo(client, owner, repo, branch, repo_url)
                if entry:
                    registry[entry["name"]] = entry
                    print(f"  发现插件: {entry['name']}")
                else:
                    print(f"  未发现有效插件元数据")

            # 更新 commit SHA
            if latest_sha:
                new_commit_state[repo_url] = latest_sha

    finally:
        client.close()

    # 对比差异
    added, removed, updated = diff_registries(existing_registry, registry)

    # 保存注册表
    save_json(registry, output_path)
    print(f"\n已生成插件注册表，包含 {len(registry)} 个插件。")

    # 保存 commit 状态
    save_commit_state(state_file, new_commit_state)

    # 输出变更日志
    if not existing_registry:
        print("首次生成注册表。")
    elif not added and not removed and not updated:
        print("注册表内容无变化。")
    else:
        print("\n变更详情：")
        for name, entry in added.items():
            print(f"  [新增] {name} 版本 {entry.get('version', '')}")
        for name, entry in removed.items():
            print(f"  [移除] {name} 原版本 {entry.get('version', '')}")
        for name, fields in updated.items():
            version_old, version_new = fields.get("version", ("", ""))
            if version_old != version_new:
                print(f"  [更新] {name} 版本 {version_old} -> {version_new}")
            else:
                print(f"  [变更] {name} 元数据发生更新")

        # 更新 README.md 变更日志
        readme_path = config_path.parent / "README.md"
        update_readme_changelog(readme_path, added, removed, updated)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"JSON 파일을 찾을 수 없습니다: {path}")
    text = path.read_text(encoding="utf-8")
    return json.loads(text, strict=False)


def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def extract_servers(config: dict[str, Any]) -> list[dict[str, Any]]:
    servers = config.get("servers") or config.get("mcpServers")
    if isinstance(servers, dict):
        normalized: list[dict[str, Any]] = []
        for name, payload in servers.items():
            if not isinstance(payload, dict):
                raise ValueError("서버 항목 형식이 잘못되었습니다.")
            normalized.append({"name": name, **payload})
        return normalized
    if isinstance(servers, list):
        return servers
    raise ValueError("windsurf 설정에서 서버 목록을 찾을 수 없습니다.")


def update_workspace(workspaces: dict[str, Any], workspace_path: str, servers: list[dict[str, Any]]) -> None:
    workspace_entry = workspaces.setdefault(workspace_path, {})
    workspace_entry["mcpServers"] = servers


def sync_servers(
    windsurf_config_path: Path,
    claude_config_path: Path,
    workspace_path: str,
    backup: bool,
) -> None:
    windsurf_config = load_json(windsurf_config_path)
    original_text = claude_config_path.read_text(encoding="utf-8")
    claude_config = load_json(claude_config_path)

    servers = extract_servers(windsurf_config)

    workspaces = claude_config.setdefault("workspaces", {})
    update_workspace(workspaces, workspace_path, servers)

    if backup:
        backup_path = claude_config_path.with_suffix(claude_config_path.suffix + ".bak")
        backup_path.write_text(original_text, encoding="utf-8")

    save_json(claude_config_path, claude_config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Windsurf MCP 서버 구성을 .claude.json에 동기화")
    parser.add_argument("windsurf_config", help="windsurf mcp_config.json 경로")
    parser.add_argument("claude_config", help=".claude.json 경로")
    parser.add_argument(
        "workspace",
        help="mcpServers를 적용할 워크스페이스 경로 (예: g:/projects/foo)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="백업 파일(.bak) 생성을 생략",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sync_servers(
        Path(args.windsurf_config),
        Path(args.claude_config),
        args.workspace,
        backup=not args.no_backup,
    )


if __name__ == "__main__":
    main()

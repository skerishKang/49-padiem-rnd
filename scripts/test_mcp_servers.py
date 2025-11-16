from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

SUCCESS = "success"
ERROR = "error"
TIMEOUT = "timeout"


def load_json(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    return json.loads(text, strict=False)


def extract_servers(config: dict[str, Any]) -> list[dict[str, Any]]:
    servers = config.get("mcpServers") or config.get("servers")
    if isinstance(servers, dict):
        normalized: list[dict[str, Any]] = []
        for name, payload in servers.items():
            payload = payload or {}
            if not isinstance(payload, dict):
                raise ValueError("서버 항목 형식이 올바르지 않습니다.")
            normalized.append({"name": name, **payload})
        return normalized
    if isinstance(servers, list):
        return servers
    raise ValueError("서버 목록을 찾을 수 없습니다.")


def load_servers(config_path: Path, workspace: str | None) -> list[dict[str, Any]]:
    data = load_json(config_path)
    if "workspaces" in data:
        if not workspace:
            raise ValueError("워크스페이스 경로를 지정해야 합니다.")
        workspaces = data.get("workspaces", {})
        entry = workspaces.get(workspace)
        if not entry:
            raise ValueError(f"워크스페이스 항목을 찾을 수 없습니다: {workspace}")
        return extract_servers(entry)
    return extract_servers(data)


def build_command(server: dict[str, Any]) -> list[str]:
    command = [server["command"]]
    args = server.get("args", [])
    if args:
        command.extend(args)

    extra_flag = server.get("testFlag")
    if extra_flag:
        command.append(extra_flag)
    else:
        command.append("--help")

    return command


def run_server_check(server: dict[str, Any], timeout: float, mode: str) -> dict[str, Any]:
    env = os.environ.copy()
    env.update(server.get("env", {}))

    command = build_command(server)

    if mode == "which":
        executable = command[0]
        resolved = shutil.which(executable, path=env.get("PATH"))
        if resolved:
            return {
                "name": server.get("name"),
                "status": SUCCESS,
                "detail": f"명령 위치: {resolved}",
                "command": executable,
            }
        return {
            "name": server.get("name"),
            "status": ERROR,
            "detail": "명령을 PATH에서 찾을 수 없습니다.",
            "command": executable,
        }

    try:
        completed = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "name": server.get("name"),
            "status": ERROR,
            "detail": f"명령을 찾을 수 없습니다: {exc}",
            "command": shlex.join(command),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": server.get("name"),
            "status": TIMEOUT,
            "detail": f"{timeout}s 제한을 초과했습니다.",
            "command": shlex.join(command),
            "stdout": exc.stdout,
            "stderr": exc.stderr,
        }

    status = SUCCESS if completed.returncode == 0 else ERROR
    return {
        "name": server.get("name"),
        "status": status,
        "returncode": completed.returncode,
        "command": shlex.join(command),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MCP 서버 실행 가능 여부 점검")
    parser.add_argument("config", help="mcp 설정 파일(.claude.json 또는 mcp_config.json) 경로")
    parser.add_argument("--workspace", help=".claude.json 사용 시 대상 워크스페이스 경로")
    parser.add_argument("--timeout", type=float, default=15.0, help="각 명령 타임아웃(초)")
    parser.add_argument(
        "--mode",
        choices=["run", "which"],
        default="run",
        help="검사 방식: run은 --help 실행, which는 명령 존재 여부만 확인",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        help="테스트할 서버 이름 목록(미지정 시 전체)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    servers = load_servers(Path(args.config), args.workspace)

    if args.include:
        allow = set(args.include)
        filtered = [server for server in servers if server.get("name") in allow]
        missing = allow - {server.get("name") for server in filtered}
        if missing:
            raise ValueError(f"존재하지 않는 서버 이름: {', '.join(sorted(missing))}")
        servers = filtered

    results = [run_server_check(server, args.timeout, args.mode) for server in servers]

    summary = {SUCCESS: 0, ERROR: 0, TIMEOUT: 0}
    for result in results:
        summary[result["status"]] = summary.get(result["status"], 0) + 1

    print("=== 테스트 요약 ===")
    for key in (SUCCESS, ERROR, TIMEOUT):
        print(f"{key}: {summary.get(key, 0)}")

    print("\n=== 상세 결과 ===")
    for result in results:
        name = result.get("name", "<unknown>")
        status = result.get("status")
        print(f"[{status}] {name}")
        print(f"  command: {result.get('command')}")
        detail = result.get("detail")
        if detail:
            print(f"  detail: {detail}")
        rc = result.get("returncode")
        if rc is not None and status != TIMEOUT:
            print(f"  returncode: {rc}")
        stdout = result.get("stdout")
        stderr = result.get("stderr")
        if stdout:
            print("  stdout:")
            print("    " + stdout.replace("\n", "\n    "))
        if stderr:
            print("  stderr:")
            print("    " + stderr.replace("\n", "\n    "))
        print()


if __name__ == "__main__":
    main()

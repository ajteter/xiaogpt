#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="/config/xiao_config.yaml",
        help="path to xiaogpt config file",
    )
    parser.add_argument(
        "--allow-template",
        action="store_true",
        help="allow example/template configs with placeholder empty values",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"missing config file: {config_path}", file=sys.stderr)
        return 1

    try:
        with config_path.open("rb") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"failed to read config: {e}", file=sys.stderr)
        return 1

    required_common = ["hardware", "bot", "tts"]
    missing = [key for key in required_common if not data.get(key)]
    if missing:
        print(f"missing required config fields: {', '.join(missing)}", file=sys.stderr)
        return 1

    if args.allow_template:
        print("ok")
        return 0

    if not data.get("mi_did"):
        print("missing required config fields: mi_did", file=sys.stderr)
        return 1

    bot = data.get("bot")
    if bot == "gemini" and not data.get("gemini_key"):
        print("missing gemini_key", file=sys.stderr)
        return 1
    if bot == "chatgptapi" and not data.get("openai_key"):
        print("missing openai_key", file=sys.stderr)
        return 1

    login_methods = 0
    if data.get("cookie"):
        login_methods += 1
    if data.get("pass_token"):
        login_methods += 1
    if data.get("account") or data.get("password"):
        login_methods += 1
    if login_methods != 1:
        print("exactly one Xiaomi login method must be configured", file=sys.stderr)
        return 1

    if data.get("pass_token") and (
        not data.get("mi_user_id") or not data.get("mi_device_id")
    ):
        print("pass_token requires mi_user_id and mi_device_id", file=sys.stderr)
        return 1

    if data.get("cookie"):
        cookie = str(data["cookie"])
        for token in ("deviceId=", "userId=", "serviceToken="):
            if token not in cookie:
                print(f"cookie missing token: {token}", file=sys.stderr)
                return 1

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

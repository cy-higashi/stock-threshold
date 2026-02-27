# -*- coding: utf-8 -*-
"""
複数ポータルをシリアルに処理するランナー。
引数で与えたディレクトリ配下のポータル名ディレクトリを、
setting.json の min_stock_base_path が空でないものに限りアルファベット順で処理する。

引数なしの場合: デフォルトで G:\\共有ドライブ\\★OD\\99_Ops\\アーカイブ(Stock) を対象とし、
その配下の日付ディレクトリ（yyyy-MM-dd）のうち直近のものを使用する。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_ARCHIVE_ROOT = r"G:\共有ドライブ\★OD\99_Ops\アーカイブ(Stock)"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _resolve_base_dir() -> Path:
    """引数で指定されたベースディレクトリ、または未指定時は直近日付ディレクトリを返す。"""
    if len(sys.argv) >= 2:
        return Path(sys.argv[1]).resolve()

    archive_root = Path(DEFAULT_ARCHIVE_ROOT)
    if not archive_root.is_dir():
        print(f"エラー: デフォルトのアーカイブディレクトリが見つかりません: {archive_root}", file=sys.stderr)
        sys.exit(1)

    date_dirs = [d for d in archive_root.iterdir() if d.is_dir() and DATE_PATTERN.match(d.name)]
    if not date_dirs:
        print(f"エラー: 日付ディレクトリ（yyyy-MM-dd）が見つかりません: {archive_root}", file=sys.stderr)
        sys.exit(1)

    latest = max(date_dirs, key=lambda p: p.name)
    return latest


def main() -> None:
    base_dir = _resolve_base_dir()
    if not base_dir.is_dir():
        print(f"エラー: ディレクトリが見つかりません: {base_dir}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print(f"引数なし: 直近日付ディレクトリを対象にします: {base_dir}", flush=True)

    settings_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / "setting.json"
    if not settings_path.exists():
        print(f"エラー: 設定ファイルが見つかりません: {settings_path}", file=sys.stderr)
        sys.exit(1)

    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    portals = settings.get("portals") or {}

    # min_stock_base_path が空でないポータル名を抽出（小文字で照合用）
    target_portals_lower = {
        name.lower(): name for name, cfg in portals.items()
        if (cfg or {}).get("min_stock_base_path", "").strip()
    }

    # ベースディレクトリ配下のサブディレクトリで対象ポータルに一致するものを収集
    to_process: list[Path] = []
    for sub in base_dir.iterdir():
        if sub.is_dir() and sub.name.lower() in target_portals_lower:
            to_process.append(sub)
    to_process.sort(key=lambda p: p.name.lower())

    main_py = Path(__file__).resolve().parent / "main.py"
    for portal_dir in to_process:
        portal_name = portal_dir.name
        print(f"--- ポータル: {portal_name} ---", flush=True)
        ret = subprocess.run(
            [sys.executable, str(main_py), str(portal_dir), str(settings_path)],
            cwd=str(Path(__file__).resolve().parent),
        )
        if ret.returncode != 0:
            print(f"警告: ポータル「{portal_name}」でエラー (exit {ret.returncode})", file=sys.stderr)

    print("全ポータル処理完了。", flush=True)


if __name__ == "__main__":
    main()

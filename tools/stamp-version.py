#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проставить версию во всех местах лендинга, где она зашита.

Мест три, и все три раньше забывались по отдельности: баннер уехал на 2.2,
бейдж и статусная рамка жили на 2.4. Теперь версия меняется одной командой:

    python3 tools/stamp-version.py 2.5-beta8

Скрипт правит:
  - assets/banner.svg   — текст с id="version";
  - README.md           — бейдж CORE-vX (дефисы для shields.io удваиваются);
  - README.md           — строку "● vX — ..." в статусной рамке.

Автор: Dmitry Prokofev (XAKER) · GPL-3.0
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ver = sys.argv[1].lstrip("v")
    released = "-beta" not in ver
    status = "RELEASED" if released else "BETA"

    banner = ROOT / "assets" / "banner.svg"
    s = banner.read_text(encoding="utf-8")
    s2 = re.sub(r'(<text id="version"[^>]*>)[^<]*(</text>)',
                rf"\g<1>v{ver}\g<2>", s)
    if s2 == s:
        print("! в баннере нет <text id=\"version\"> — не проставил")
        return 1
    banner.write_text(s2, encoding="utf-8")

    readme = ROOT / "README.md"
    s = readme.read_text(encoding="utf-8")
    shields = ver.replace("-", "--")     # дефис в shields.io экранируется
    s = re.sub(r"badge/CORE-v[0-9][^-]*(?:--[a-z0-9]+)?-",
               f"badge/CORE-v{shields}-", s)
    s = re.sub(r"●\s*v[\w.\-]+\s*—\s*\w+",
               f"● v{ver} — {status}", s)
    readme.write_text(s, encoding="utf-8")

    print(f"Проставлено: v{ver} ({status}) — баннер, бейдж, статусная рамка")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

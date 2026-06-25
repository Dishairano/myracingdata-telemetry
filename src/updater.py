"""
In-app auto-updater.

Checks the project's GitHub Releases for a newer version and, if the user opts
in, downloads the new executable and swaps it in via a tiny batch script that
runs after this process exits (a running .exe can't overwrite itself). Only acts
when frozen (a real installed .exe); a no-op in dev.
"""

import os
import subprocess
import sys

import requests

REPO = "Dishairano/myracingdata-telemetry"
LATEST_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

# Remember the asset URL from the last successful check so apply doesn't refetch.
_pending = {"url": None, "version": None}


def _ver_tuple(v):
    parts = []
    for p in str(v).lstrip("vV").split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)


def check_for_update(current_version):
    """Return {available, version, url} — available True only if a newer release exists."""
    try:
        r = requests.get(LATEST_URL, timeout=8, headers={"Accept": "application/vnd.github+json"})
        if r.status_code != 200:
            return {"available": False}
        rel = r.json()
        tag = (rel.get("tag_name") or "").lstrip("vV")
        if not tag:
            return {"available": False}

        if _ver_tuple(tag) > _ver_tuple(current_version):
            asset = next(
                (a for a in rel.get("assets", []) if a.get("name", "").lower().endswith(".exe")),
                None,
            )
            url = asset["browser_download_url"] if asset else None
            _pending.update(url=url, version=tag)
            return {"available": bool(url), "version": tag, "url": url}
        return {"available": False, "version": current_version}
    except Exception as e:
        return {"available": False, "error": str(e)}


def download_and_apply(url=None):
    """Download the new exe and schedule a swap + relaunch after we exit."""
    url = url or _pending.get("url")
    if not url:
        return {"ok": False, "error": "No update available"}
    if not getattr(sys, "frozen", False):
        return {"ok": False, "error": "Updates only apply to the installed app"}

    try:
        current = sys.executable  # the running .exe when frozen
        folder = os.path.dirname(current)
        new_exe = os.path.join(folder, "MyRacingData-Telemetry.new.exe")

        with requests.get(url, timeout=180, stream=True) as r:
            r.raise_for_status()
            with open(new_exe, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

        # After this process exits: wait, replace the exe, relaunch, delete self.
        bat = os.path.join(folder, "_mrd_update.bat")
        with open(bat, "w", encoding="ascii") as b:
            b.write(
                "@echo off\r\n"
                "ping 127.0.0.1 -n 3 >nul\r\n"
                f'move /y "{new_exe}" "{current}" >nul\r\n'
                f'start "" "{current}"\r\n'
                'del "%~f0"\r\n'
            )
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(["cmd", "/c", bat], creationflags=CREATE_NO_WINDOW)
        os._exit(0)
    except Exception as e:
        return {"ok": False, "error": str(e)}

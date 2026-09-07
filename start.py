"""
Milliy Sertifikat Bot - Avtomatik Starter
Ishlatish: python start.py
"""

import subprocess
import sys
import signal
import re
import time
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"
CLOUDFLARED = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
BOT_PORT = 8000

processes = []

def log(msg):
    print(msg, flush=True)

def update_env(key: str, value: str):
    content = ENV_FILE.read_text(encoding="utf-8") if ENV_FILE.exists() else ""
    lines = content.splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

def cleanup(signum=None, frame=None):
    log("[STOP] Botva tunnel to'xtatilmoqda...")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    sys.exit(0)

def start_tunnel():
    if not Path(CLOUDFLARED).exists():
        log("[WARN] cloudflared topilmadi, tunnelsiz davom etilmoqda.")
        return None

    cf_log = Path("cf_tunnel.log")
    cf_log.write_text("", encoding="utf-8")

    log("[TUNNEL] Cloudflare tunnel ishga tushirilmoqda...")
    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{BOT_PORT}",
         "--logfile", str(cf_log)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(proc)

    # URL chiqishini kutish (max 30 sek)
    for _ in range(30):
        time.sleep(1)
        try:
            content = cf_log.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"https://[\w\-]+\.trycloudflare\.com", content)
            if match:
                return match.group(0)
        except Exception:
            pass

    log("[WARN] Tunnel URL olinmadi.")
    return None

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("=" * 55, flush=True)
    print("  Milliy Sertifikat Bot - Auto Starter", flush=True)
    print("=" * 55, flush=True)

    # 1. Tunnel ishga tushirish
    tunnel_url = start_tunnel()

    # 2. .env yangilash
    if tunnel_url:
        update_env("API_SERVER_URL", tunnel_url)
        log(f"[OK] Tunnel: {tunnel_url}")
        log("[OK] .env yangilandi")
    else:
        log("[INFO] Tunnelsiz davom etilmoqda...")

    # 3. Bot ishga tushirish
    log("[BOT] Bot ishga tushirilmoqda...")
    bot_proc = subprocess.Popen(
        [sys.executable, "-m", "bot.main"],
        cwd=Path(__file__).parent,
    )
    processes.append(bot_proc)

    print("=" * 55, flush=True)
    print("  Admin: https://azamqulov.github.io/ms-bot/web/admin.html", flush=True)
    if tunnel_url:
        print(f"  API  : {tunnel_url}", flush=True)
    print("  Chiqish: Ctrl+C", flush=True)
    print("=" * 55, flush=True)

    try:
        bot_proc.wait()
    except KeyboardInterrupt:
        cleanup()

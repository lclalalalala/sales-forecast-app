"""
桌面应用入口 - desktop.py
=========================
将 Flask 后端（同时托管前端 app/dist）以后台线程启动，并用 pywebview 打开一个原生窗口
加载本地服务，实现"双击即用"的桌面体验。

运行：
    conda activate dev
    python desktop.py

打包（见 desktop.spec / build_mac.sh / build_win.bat）后，本文件为可执行程序入口。
"""

import os
import socket
import sys
import threading
import time
import urllib.request

# 确保 api/ 在导入路径上（开发态与打包态一致）。
# 打包态下 __file__ 位于解包目录，api/ 与本文件同级一并打入。
_BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
_API_DIR = os.path.join(_BASE_DIR, "api")
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

from app import app as flask_app  # noqa: E402  （依赖上面的 sys.path 设置）

WINDOW_TITLE = "零售门店库存与需求预测系统"
HOST = "127.0.0.1"


def _pick_free_port() -> int:
    """向操作系统申请一个空闲端口，避免固定端口被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, 0))
        return s.getsockname()[1]


def _run_server(port: int) -> None:
    """在后台线程启动 Flask。关闭 reloader/调试，避免多进程与信号问题。"""
    flask_app.run(host=HOST, port=port, debug=False, use_reloader=False, threaded=True)


def _wait_until_ready(port: int, timeout: float = 30.0) -> bool:
    """轮询 /api/health，直到服务就绪或超时。"""
    url = f"http://{HOST}:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def main() -> int:
    port = _pick_free_port()

    server_thread = threading.Thread(target=_run_server, args=(port,), daemon=True)
    server_thread.start()

    if not _wait_until_ready(port):
        sys.stderr.write("后端服务启动超时，请检查数据文件是否完整。\n")
        return 1

    # 无头自检：仅验证服务与数据加载，不弹窗。用于打包产物的冒烟测试（CI / 本地）。
    if os.environ.get("DESKTOP_SELFTEST") == "1":
        import json
        import urllib.request

        with urllib.request.urlopen(f"http://{HOST}:{port}/api/health") as resp:
            payload = json.loads(resp.read())
        data = payload.get("data", {})
        ok = data.get("data_loaded") is True

        # 同时验证 GUI 后端可用（打包易漏收集 webview.platforms.* 及 pyobjc）
        gui_ok = False
        gui_msg = ""
        try:
            import platform

            import webview  # noqa: F401

            system = platform.system()
            if system == "Darwin":
                import webview.platforms.cocoa  # noqa: F401
            elif system == "Windows":
                import webview.platforms.edgechromium  # noqa: F401
            else:
                import webview.platforms.gtk  # noqa: F401
            gui_ok = True
        except Exception as exc:  # noqa: BLE001
            gui_msg = repr(exc)

        sys.stdout.write(
            f"[selftest] health={data.get('status')} data_loaded={data.get('data_loaded')} "
            f"stores={data.get('stores_count')} products={data.get('products_count')} "
            f"gui_backend={'ok' if gui_ok else 'FAIL ' + gui_msg}\n"
        )
        return 0 if (ok and gui_ok) else 1

    url = f"http://{HOST}:{port}/"

    # 优先使用 pywebview 原生窗口；若后端不可用则退回系统浏览器，保证仍能使用。
    try:
        import webview
    except Exception as exc:  # noqa: BLE001  （含 ImportError 及后端加载失败）
        import traceback
        import webbrowser

        sys.stderr.write(f"pywebview 不可用（{exc!r}），改用系统浏览器打开。\n")
        traceback.print_exc()
        webbrowser.open(url)
        server_thread.join()
        return 0

    webview.create_window(WINDOW_TITLE, url, width=1440, height=900, min_size=(1024, 720))
    webview.start()  # 阻塞直至窗口关闭
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

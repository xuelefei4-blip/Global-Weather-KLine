import http.server
import os
import subprocess
import sys
import urllib.parse
import webbrowser
import threading

PORT = 5500
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT_MAP = {
    "1": "step1_detect_align.py",
    "2": "step2_history_sync.py",
    "3": "step3_realtime_sync.py",
    "4": "step4_scaffold_city.py",
    "5": "step5_export_report.py",
    "6": "step6_audit_repair.py"
}

class MeteoOpsServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/run":
            query = urllib.parse.parse_qs(parsed.query)
            step = query.get("step", [""])[0]

            if step not in SCRIPT_MAP:
                self.send_error(400, "Unknown Step")
                return

            script_file = os.path.join(BASE_DIR, SCRIPT_MAP[step])
            if not os.path.exists(script_file):
                self.send_error(404, "Script Not Found")
                return

            # 建立实时传输通道
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUNBUFFERED"] = "1"

            # 实时逐行读写子进程输出
            proc = subprocess.Popen(
                [sys.executable, "-u", script_file],
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                bufsize=1
            )

            try:
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        self.wfile.write(line.encode("utf-8"))
                        self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError):
                pass
            finally:
                proc.stdout.close()
                proc.wait()
            return

        super().do_GET()

def open_browser():
    webbrowser.open(f"http://127.0.0.1:{PORT}/coverage.html")

if __name__ == "__main__":
    os.chdir(BASE_DIR)
    threading.Timer(0.8, open_browser).start()
    print(f"🚀 MeteoOps 服务启动: http://127.0.0.1:{PORT}/coverage.html")
    server = http.server.ThreadingHTTPServer(("", PORT), MeteoOpsServer)
    server.serve_forever()
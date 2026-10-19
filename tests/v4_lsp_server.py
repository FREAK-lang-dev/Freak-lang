#!/usr/bin/env python3
"""End-to-end JSON-RPC contracts for freak-lsp, the Maverick language server.

Usage:
    python tests/v4_lsp_server.py [path/to/freak-lsp] [--compiler path/to/freak]

Without a server path it is built first with src/compiler/v4/build_lsp.py.
With --compiler, `freak check` diagnostics are exercised too.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URI = "file:///workspace/lsp_demo.fk"

SOURCE = """shape Pilot {
    name: word
    power: int
}

task greet(who: word) -> word {
    give back "hi " + who
}

task main() -> int {
    pilot callsign = greet("Takeru")
    give back 0
}
"""


class Client:
    def __init__(self, command: list[str], env: dict | None = None) -> None:
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, env=env)
        self.next_id = 1
        self.notifications: list[dict] = []
        self.stderr = b""
        threading.Thread(target=self._drain_stderr, daemon=True).start()

    def _drain_stderr(self) -> None:
        self.stderr = self.proc.stderr.read()

    def send(self, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
        self.proc.stdin.flush()

    def read(self) -> dict:
        length = None
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise AssertionError(f"server closed stdout; stderr={self.stderr!r}")
            if line in (b"\r\n", b"\n"):
                break
            name, _, value = line.decode("ascii").partition(":")
            if name.strip().lower() == "content-length":
                length = int(value.strip())
        assert length is not None, "missing Content-Length"
        return json.loads(self.proc.stdout.read(length).decode("utf-8"))

    def request(self, method: str, params: dict | None = None) -> dict:
        msg_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": msg_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)
        while True:
            message = self.read()
            if message.get("id") == msg_id and "method" not in message:
                return message
            self.notifications.append(message)

    def notify(self, method: str, params: dict | None = None) -> None:
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)

    def wait_notification(self, method: str) -> dict:
        for index, message in enumerate(self.notifications):
            if message.get("method") == method:
                return self.notifications.pop(index)
        while True:
            message = self.read()
            if message.get("method") == method:
                return message
            self.notifications.append(message)


def position_of(text: str, needle: str, occurrence: int = 0, delta: int = 0) -> dict:
    index = -1
    for _ in range(occurrence + 1):
        index = text.index(needle, index + 1)
    index += delta
    line = text.count("\n", 0, index)
    column = index - (text.rfind("\n", 0, index) + 1)
    return {"line": line, "character": column}


def check(condition: bool, label: str, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"{label}: {detail}")
    print(f"ok - {label}")


def run(server: Path) -> None:
    client = Client([str(server)])
    doc = {"uri": URI}

    early = client.request("textDocument/hover", {"textDocument": doc, "position": {"line": 0, "character": 0}})
    check(early.get("error", {}).get("code") == -32002, "requests before initialize are refused", early)

    init = client.request("initialize", {
        "processId": None, "rootUri": None, "capabilities": {},
        "initializationOptions": {"compilerDiagnostics": False, "maverickDiagnostics": True},
    })
    caps = init["result"]["capabilities"]
    check(caps["hoverProvider"] and caps["definitionProvider"] and caps["documentSymbolProvider"],
          "initialize advertises hover, definition and symbols", caps)
    check(caps["textDocumentSync"]["change"] == 1, "full document sync", caps)
    check(init["result"]["serverInfo"]["name"] == "freak-lsp", "serverInfo names freak-lsp")
    client.notify("initialized", {})

    client.notify("textDocument/didOpen", {"textDocument": {**doc, "languageId": "freak", "version": 1, "text": SOURCE}})
    published = client.wait_notification("textDocument/publishDiagnostics")["params"]
    check(published["uri"] == URI, "didOpen publishes diagnostics for the document", published)
    check(published["diagnostics"] == [], "valid program has no diagnostics", published["diagnostics"])

    hover = client.request("textDocument/hover", {"textDocument": doc, "position": position_of(SOURCE, "greet", 1, 1)})
    value = (hover.get("result") or {}).get("contents", {}).get("value", "")
    check("greet" in value and "Task" in value, "hover on a call shows the task", hover)

    definition = client.request("textDocument/definition", {"textDocument": doc, "position": position_of(SOURCE, "greet", 1, 1)})
    target = definition.get("result") or {}
    check(target.get("uri") == URI and target["range"]["start"]["line"] == 5,
          "go-to-definition jumps to the task declaration", definition)

    symbols = client.request("textDocument/documentSymbol", {"textDocument": doc})["result"]
    names = {symbol["name"]: symbol for symbol in symbols}
    check({"Pilot", "greet", "main"} <= set(names), "document symbols list shapes and tasks", symbols)
    check(names["Pilot"]["kind"] == 23 and names["greet"]["kind"] == 12, "symbol kinds map to Struct/Function", names)
    check(names["greet"]["selectionRange"]["start"] == {"line": 5, "character": 5},
          "selection range points at the symbol name", names["greet"])

    completion = client.request("textDocument/completion", {"textDocument": doc, "position": position_of(SOURCE, "give back 0")})
    labels = {item["label"] for item in completion["result"]["items"]}
    check({"greet", "Pilot", "pilot", "word"} <= labels, "completion offers declarations, keywords and types", sorted(labels))

    broken = SOURCE.replace("give back 0", 'give back "zero"')
    client.notify("textDocument/didChange", {"textDocument": {**doc, "version": 2}, "contentChanges": [{"text": broken}]})
    published = client.wait_notification("textDocument/publishDiagnostics")["params"]
    check(len(published["diagnostics"]) >= 1 and published["diagnostics"][0]["severity"] == 1,
          "didChange re-checks live and reports the type error", published)
    first = published["diagnostics"][0]
    check(first["source"] == "maverick" and first["message"], "diagnostics carry source and message", first)

    unicode_text = 'task main() -> word {\n    pilot s = "ねこ"; pilot x = 1\n    give back s\n}\n'
    client.notify("textDocument/didChange", {"textDocument": {**doc, "version": 3}, "contentChanges": [{"text": unicode_text}]})
    client.wait_notification("textDocument/publishDiagnostics")
    hover = client.request("textDocument/hover", {"textDocument": doc, "position": {"line": 1, "character": 21}})
    check("result" in hover, "hover after multi-byte text answers without error", hover)

    unknown = client.request("freak/doesNotExist", {})
    check(unknown.get("error", {}).get("code") == -32601, "unknown requests get MethodNotFound", unknown)

    client.notify("textDocument/didClose", {"textDocument": doc})
    closed = client.wait_notification("textDocument/publishDiagnostics")["params"]
    check(closed["diagnostics"] == [], "didClose clears diagnostics", closed)

    started = time.monotonic()
    for version in range(4, 54):
        edited = SOURCE.replace("Takeru", "Takeru" + str(version))
        client.notify("textDocument/didChange", {"textDocument": {**doc, "version": version}, "contentChanges": [{"text": edited}]})
        client.wait_notification("textDocument/publishDiagnostics")
        client.request("textDocument/hover", {"textDocument": doc, "position": position_of(edited, "greet", 1, 1)})
    elapsed = time.monotonic() - started
    check(elapsed < 30, "50 edit+hover rounds stay responsive", f"{elapsed:.2f}s")

    shutdown = client.request("shutdown")
    check("result" in shutdown and shutdown["result"] is None, "shutdown answers null", shutdown)
    client.notify("exit")
    code = client.proc.wait(timeout=10)
    check(code == 0, "exit after shutdown returns 0", code)


def initialized(server: Path, options: dict, env: dict | None = None) -> Client:
    client = Client([str(server)], env)
    client.request("initialize", {"processId": None, "capabilities": {}, "initializationOptions": options})
    client.notify("initialized", {})
    return client


def close(client: Client) -> None:
    client.request("shutdown")
    client.notify("exit")
    client.proc.wait(timeout=10)


def run_worker_recycling(server: Path) -> None:
    # A 1 MB budget replaces the analysis worker after every message, so each
    # answer below comes from a worker rebuilt by replaying initialize/didOpen.
    env = {**os.environ, "FREAK_LSP_WORKER_MB": "1"}
    client = initialized(server, {"compilerDiagnostics": False, "maverickDiagnostics": True}, env)
    doc = {"uri": URI}
    client.notify("textDocument/didOpen", {"textDocument": {**doc, "languageId": "freak", "version": 1, "text": SOURCE}})
    client.wait_notification("textDocument/publishDiagnostics")
    for version in range(2, 6):
        edited = SOURCE.replace("Takeru", "Sumika" * version)
        client.notify("textDocument/didChange", {"textDocument": {**doc, "version": version}, "contentChanges": [{"text": edited}]})
        client.wait_notification("textDocument/publishDiagnostics")
        hover = client.request("textDocument/hover", {"textDocument": doc, "position": position_of(edited, "greet", 1, 1)})
        check("greet" in ((hover.get("result") or {}).get("contents", {}).get("value", "")),
              f"hover survives worker replacement (edit {version})", hover)
    symbols = client.request("textDocument/documentSymbol", {"textDocument": doc})["result"]
    check({"Pilot", "greet", "main"} <= {item["name"] for item in symbols}, "replayed worker keeps the latest text", symbols)
    client.request("shutdown")
    client.notify("exit")
    check(client.proc.wait(timeout=10) == 0, "supervisor exits cleanly after recycling")

    if sys.platform != "win32":
        import signal
        client = initialized(server, {"compilerDiagnostics": False})
        client.notify("textDocument/didOpen", {"textDocument": {**doc, "languageId": "freak", "version": 1, "text": SOURCE}})
        client.wait_notification("textDocument/publishDiagnostics")
        client.request("textDocument/documentSymbol", {"textDocument": doc})
        children = subprocess.run(["pgrep", "-P", str(client.proc.pid)], capture_output=True, text=True).stdout.split()
        os.kill(int(children[0]), signal.SIGKILL)
        time.sleep(0.2)
        crashed = client.request("textDocument/documentSymbol", {"textDocument": doc})
        check(crashed.get("error", {}).get("code") == -32603, "a crashed worker turns the request into an error", crashed)
        again = client.request("textDocument/documentSymbol", {"textDocument": doc})
        check(len(again.get("result") or []) >= 3, "the server recovers after a worker crash", again)
        close(client)


def run_compiler_checks(server: Path, compiler: Path) -> None:
    bad = 'task main() {\n    pilot x: int = "nope"\n    say undefined_thing\n}\n'
    with tempfile.TemporaryDirectory(prefix="freak lsp ") as folder:
        path = Path(folder) / "bad file.fk"
        path.write_text(bad, encoding="utf-8")
        uri = path.resolve().as_uri()
        client = initialized(server, {"compilerPath": str(compiler)})
        client.notify("textDocument/didOpen", {"textDocument": {"uri": uri, "languageId": "freak", "version": 1, "text": bad}})
        found = client.wait_notification("textDocument/publishDiagnostics")["params"]["diagnostics"]
        messages = [item["message"] for item in found]
        check(len(found) == 2 and all(item["source"] == "freak check" for item in found),
              "didOpen runs freak check on the saved file (path with spaces)", found)
        check(messages[1] == "unknown binding 'undefined_thing'", "checker messages drop the (line N) suffix", messages)
        check(found[1]["range"]["start"] == {"line": 2, "character": 4}, "checker range underlines the statement", found[1])

        fixed = bad.replace("    say undefined_thing\n", "")
        path.write_text(fixed, encoding="utf-8")
        client.notify("textDocument/didChange", {"textDocument": {"uri": uri, "version": 2}, "contentChanges": [{"text": fixed}]})
        client.wait_notification("textDocument/publishDiagnostics")
        client.notify("textDocument/didSave", {"textDocument": {"uri": uri}})
        found = client.wait_notification("textDocument/publishDiagnostics")["params"]["diagnostics"]
        check(len(found) == 1, "didSave re-runs freak check", found)
        close(client)

    client = initialized(server, {"compilerPath": str(Path(tempfile.gettempdir()) / "no-such-freak")})
    client.notify("textDocument/didOpen", {"textDocument": {"uri": URI, "languageId": "freak", "version": 1, "text": SOURCE}})
    logged = client.wait_notification("window/logMessage")["params"]["message"]
    check("not found" in logged, "a missing compiler is reported once in the log", logged)
    close(client)


def main() -> int:
    args = sys.argv[1:]
    compiler = None
    if "--compiler" in args:
        at = args.index("--compiler")
        compiler = Path(args[at + 1])
        del args[at:at + 2]
    if args:
        server = Path(args[0])
    else:
        subprocess.run([sys.executable, str(ROOT / "src" / "compiler" / "v4" / "build_lsp.py")], check=True)
        server = ROOT / "build" / ("freak-lsp.exe" if sys.platform.startswith("win") else "freak-lsp")
    run(server)
    run_worker_recycling(server)
    if compiler is not None:
        run_compiler_checks(server, compiler)
    print("freak-lsp contracts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""A minimal client of the Agent Client Protocol (ACP) for `kiro-cli acp`, used as a rater by relation_unlabelled.py. It is generic: it
sends a text prompt and returns the text of the answer, and knows nothing of word pairs.

Protocol (JSON-RPC 2.0, one message per line on the stdin and stdout of the agent): `initialize`, then for each question a new session
(`session/new`), the model set and checked with `session/set_config_option` (under the v3 engine of kiro-cli the flag --model is refused),
the autopilot set to off (so that any tool call becomes a permission request, which this client refuses), and `session/prompt`. The text
of the answer arrives as `session/update` notifications of kind `agent_message_chunk`, and the turn ends with the response to the prompt
and its stop reason. A model fallback reported by the agent, a model that the session does not confirm, a stop reason other than
`end_turn` and a timeout are errors: the rater is pinned, and a silent change of model would mix two raters.

Run as a script with a prompt as argument, it asks the real agent (`python acp_client.py "say hi"`); with no argument it only prints its
usage, so that `make test-code` does not call a language model.
"""
from __future__ import annotations

import json
import queue
import subprocess
import sys
import tempfile
import threading
import time

MODEL = "claude-opus-5.5"
COMMAND = ["kiro-cli", "acp"]


class AcpError(RuntimeError):
    pass


class AcpRater:
    """One agent process; every call of `ask` is a fresh session, so that no question sees another."""

    def __init__(self, model: str = MODEL, command: list[str] | None = None, timeout: float = 600.0, cwd: str | None = None):
        self.model, self.command, self.timeout = model, command or COMMAND, timeout
        self.cwd = cwd or tempfile.mkdtemp(prefix="acp_rater_")  # an empty directory: the rater has no files to look at
        self.process: subprocess.Popen | None = None
        self.lines: queue.Queue = queue.Queue()
        self.next_id = 0

    # --- transport
    def start(self) -> "AcpRater":
        self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                        text=True, bufsize=1, cwd=self.cwd)
        threading.Thread(target=self._reader, daemon=True).start()
        self._request("initialize", {"protocolVersion": 1, "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False},
                                                                                   "terminal": False}})
        return self

    def _reader(self) -> None:
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _send(self, message: dict) -> None:
        try:
            self.process.stdin.write(json.dumps(message) + "\n")
            self.process.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise AcpError(f"the agent closed its input: {e}") from e

    def _request(self, method: str, params: dict, on_message=None) -> dict:
        """Send a request and wait for its response; every other message on the way goes to `on_message` (or to the default handler)."""
        self.next_id += 1
        ident = self.next_id
        self._send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                line = self.lines.get(timeout=max(0.0, deadline - time.monotonic()))
            except queue.Empty:
                raise AcpError(f"no response to {method} within {self.timeout:.0f} s") from None
            if line is None:
                raise AcpError(f"the agent exited while waiting for {method}")
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue  # not a protocol message
            if message.get("id") == ident and "method" not in message:
                if "error" in message:
                    raise AcpError(f"{method}: {message['error']}")
                return message.get("result", {})
            self._handle(message, on_message)

    def _handle(self, message: dict, on_message) -> None:
        if message.get("method") == "session/request_permission":  # a tool call: always refused
            options = message.get("params", {}).get("options", [])
            reject = next((o["optionId"] for o in options if str(o.get("kind", "")).startswith("reject")), None)
            outcome = {"outcome": "selected", "optionId": reject} if reject else {"outcome": "cancelled"}
            self._send({"jsonrpc": "2.0", "id": message["id"], "result": {"outcome": outcome}})
            return
        if "method" in message and "id" in message:  # any other request from the agent: not supported
            self._send({"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32601, "message": "not supported by this client"}})
            return
        if "fallback" in json.dumps(message.get("params", {}).get("update", {}).get("_meta", {})).lower():
            raise AcpError(f"the agent reported a model fallback: {json.dumps(message)[:300]}")
        if on_message:
            on_message(message)

    # --- sessions
    def _set_option(self, session: str, option: str, value: str) -> None:
        result = self._request("session/set_config_option", {"sessionId": session, "configId": option, "value": value})
        current = {o.get("id"): o.get("currentValue") for o in result.get("configOptions", [])}
        if current.get(option) != value:
            raise AcpError(f"the session did not confirm {option} = {value} (it reports {current.get(option)!r})")

    def ask(self, text: str) -> str:
        """The text of the answer to `text`, in a new session with the pinned model."""
        if self.process is None:
            self.start()
        session = self._request("session/new", {"cwd": self.cwd, "mcpServers": []})["sessionId"]
        self._set_option(session, "model", self.model)
        self._set_option(session, "autopilot", "off")
        chunks: list[str] = []

        def collect(message: dict) -> None:
            update = message.get("params", {}).get("update", {})
            if message.get("params", {}).get("sessionId") == session and update.get("sessionUpdate") == "agent_message_chunk":
                content = update.get("content", {})
                if content.get("type") == "text":
                    chunks.append(content.get("text", ""))

        result = self._request("session/prompt", {"sessionId": session, "prompt": [{"type": "text", "text": text}]}, collect)
        if result.get("stopReason") != "end_turn":
            raise AcpError(f"the turn ended with {result.get('stopReason')!r}")
        return "".join(chunks)

    def close(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def __enter__(self) -> "AcpRater":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.close()


def main(argv: list[str]) -> None:
    if not argv:
        print(f"usage: python acp_client.py PROMPT  (asks {MODEL} through {' '.join(COMMAND)})")
        return
    with AcpRater() as rater:
        print(rater.ask(" ".join(argv)))


if __name__ == "__main__":
    main(sys.argv[1:])

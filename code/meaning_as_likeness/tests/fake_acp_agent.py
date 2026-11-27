"""A fake ACP agent for the tests of acp_client.py and relation_unlabelled.py. Behaviour is set by environment variables:
FAKE_REPLY (the text of every answer; "ECHO_IDS" answers each "pNNNN: a / b" line with {"id": ..., "relations": ["r-<a>"]}, and
"MAP" maps every "- name" line to "c-<name>"), FAKE_MODEL_IGNORED (the session keeps "auto"), FAKE_PERMISSION (ask a permission first),
FAKE_FALLBACK (report a model fallback), FAKE_HANG (never answer the prompt), FAKE_LOG (file to append the prompts to)."""
import json
import os
import re
import sys


def send(message):
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def update(session, kind, **fields):
    send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": session, "update": {"sessionUpdate": kind, **fields}}})


def reply_to(text):
    mode = os.environ.get("FAKE_REPLY", "hello world")
    if mode == "ECHO_IDS":
        return "\n".join(json.dumps({"id": m[0], "relations": [f"r-{m[1]}"]}) for m in re.findall(r"^(p\d+): (\S+) / \S+$", text, re.M))
    if mode == "MAP":
        return "Here:\n" + json.dumps({n: f"c-{n}" for n in re.findall(r"^- ([^:\n]+)", text, re.M)})
    return mode


options, sessions = {}, 0
for line in sys.stdin:
    msg = json.loads(line)
    method, ident, params = msg.get("method"), msg.get("id"), msg.get("params", {})
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": ident, "result": {"protocolVersion": 1}})
    elif method == "session/new":
        sessions += 1
        sid = f"s{sessions}"
        options[sid] = {"model": "auto", "autopilot": "on"}
        send({"jsonrpc": "2.0", "id": ident, "result": {"sessionId": sid}})
    elif method == "session/set_config_option":
        sid = params["sessionId"]
        if not (params["configId"] == "model" and os.environ.get("FAKE_MODEL_IGNORED")):
            options[sid][params["configId"]] = params["value"]
        send({"jsonrpc": "2.0", "id": ident, "result": {"configOptions": [{"id": k, "currentValue": v} for k, v in options[sid].items()]}})
    elif method == "session/prompt":
        sid, text = params["sessionId"], params["prompt"][0]["text"]
        if os.environ.get("FAKE_LOG"):
            with open(os.environ["FAKE_LOG"], "a") as f:
                f.write(json.dumps(text) + "\n")
        if os.environ.get("FAKE_HANG"):
            continue
        if os.environ.get("FAKE_PERMISSION"):
            send({"jsonrpc": "2.0", "id": "perm1", "method": "session/request_permission",
                  "params": {"sessionId": sid, "options": [{"optionId": "yes", "kind": "allow_once"}, {"optionId": "no", "kind": "reject_once"}]}})
            answer = json.loads(sys.stdin.readline())
            with open(os.environ["FAKE_PERMISSION"], "w") as f:
                f.write(json.dumps(answer))
        if os.environ.get("FAKE_FALLBACK"):
            update(sid, "session_info_update", _meta={"kiro": {"kind": "model_fallback", "from": "claude-opus-5.5"}})
        update(sid, "session_info_update", title="ignored")
        reply = reply_to(text)
        for k in range(0, len(reply), 7):  # in pieces, as the real agent does
            update(sid, "agent_message_chunk", content={"type": "text", "text": reply[k: k + 7]})
        send({"jsonrpc": "2.0", "id": ident, "result": {"stopReason": "end_turn"}})

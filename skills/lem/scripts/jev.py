#!/usr/bin/env python3
"""lem-jev: ask TypeSafe's Jev decision model one or more choice questions, through OpenRouter or another provider.

  lem-jev SPEC.json | lem-jev - < spec.json     ask, print the answers as JSON
  lem-jev check SPEC.json | lem-jev check -     validate the spec and its size, send nothing

Lem's own copy. The plugin puts it on the Bash tool's PATH as `lem-jev` (`bin/lem-jev`), named so
that it does not shadow a developer's own `jev`, and the correction hook runs it by its path.

A spec is {"state": "<the facts to decide on>", "questions": {NAME: QUESTION, ...}} and
optionally "model". A question is {"instructions": "<what to decide>", "choices": {ID: "<what
this choice means>", ...}}; it is sent as Jev's "choice" type, with the choices as its criteria.

The reply on stdout: {"model", "answers": {NAME: {"choice", "confidence", "probabilities"}},
"cost"}. Jev returns probabilities per choice; read them, a confidence near 0.5 is a coin toss.

Jev reads text best under about 32,000 bytes. Past that it runs in a long-context mode its docs
call slower and less accurate, so a spec whose state and questions together pass LIMIT_BYTES is
refused with exit 3 and nothing is sent. Nothing here truncates: a caller with a longer input
sends it to a big model instead.

The key is JEV_API_KEY from the environment, and the address JEV_API_URL, OpenRouter's by default
(the owner, 2026-11-18: "jev lib only care about API url and API token - we can use any
provider"). JEV_API_KEY is the one name of the key: with no JEV_API_KEY nothing is sent, and the
refusal says so. The key is in no settings file: a settings file is in the repository's folder,
and no secret goes into a file. A process keeps the values it started with, so a key
changed later reaches only processes started after the change.

The request and the reply are Jev's own form, the same at every provider: a POST of state, model
and questions with the key as a Bearer token, and answers with choice, confidence and
probabilities. Three parts are OpenRouter's: its address (`URL`), its name of the model
(`typesafe/jev-1.14`, where TypeSafe's own API says `jev-latest`), and the reply's `usage.cost`,
which another provider may not give (`cost` is then null). With another JEV_API_URL, set JEV_MODEL
to that provider's name of the model.

Exit codes: 0 answered; 1 a bad spec, no key, or a failed request (the error names which);
3 the input is over LIMIT_BYTES.
Environment: JEV_API_KEY (required), JEV_API_URL (the
address of the decisions endpoint, default URL), JEV_MODEL (default model), JEV_TIMEOUT (seconds).
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

# OpenRouter's address of Jev's decisions, the default of JEV_API_URL
URL = "https://openrouter.ai/api/alpha/decisions"
# The one variable of the key
KEY = "JEV_API_KEY"
DEFAULT_MODEL = os.environ.get("JEV_MODEL", "typesafe/jev-1.14")
LIMIT_BYTES = 32_000
# the default of JEV_TIMEOUT; main() reads the variable, so a wrong value is a message, not a traceback at import
TIMEOUT_SECONDS = 120.0
# macOS keeps its root certificates here. A python.org interpreter that never ran its
# "Install Certificates" step has none of its own and fails every TLS handshake without this.
MACOS_CA_BUNDLE = Path("/etc/ssl/cert.pem")


class SpecError(Exception):
    pass


def timeout_seconds() -> float:
    """JEV_TIMEOUT, the seconds one request may take: a number above 0, or TIMEOUT_SECONDS when it is unset."""
    raw = os.environ.get("JEV_TIMEOUT")
    if raw is None:
        return TIMEOUT_SECONDS
    try:
        seconds = float(raw)
    except ValueError:
        seconds = 0.0
    if not 0 < seconds < float("inf"):
        raise SpecError(f"JEV_TIMEOUT={raw!r} is not a number of seconds above 0; set it as JEV_TIMEOUT=120, or unset it for {TIMEOUT_SECONDS:g}")
    return seconds


def load(arg: str) -> dict:
    try:
        text = (sys.stdin.buffer.read() if arg == "-" else Path(arg).read_bytes()).decode("utf-8")
    except UnicodeDecodeError as error:
        raise SpecError(f"the spec ({'stdin' if arg == '-' else arg}) is not UTF-8 text (byte {error.start} does not read)") from error
    try:
        spec = json.loads(text)
    except ValueError as error:
        raise SpecError(f"the spec is not JSON: {error}") from error
    if not isinstance(spec, dict):
        raise SpecError("the spec must be a JSON object")
    return spec


def build(spec: dict) -> dict:
    """The decisions request body, after checking the spec's shape and size."""
    unknown = set(spec) - {"state", "questions", "model"}
    if unknown:
        raise SpecError(f"unknown spec keys: {sorted(unknown)}")
    state = spec.get("state")
    if not isinstance(state, str) or not state.strip():
        raise SpecError("state must be a non-empty string")
    questions = spec.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise SpecError("questions must be a non-empty object")
    body_questions = {}
    for name, question in questions.items():
        if not isinstance(question, dict) or set(question) - {"instructions", "choices"}:
            raise SpecError(f"question {name!r} takes only instructions and choices")
        instructions = question.get("instructions")
        choices = question.get("choices")
        if not isinstance(instructions, str) or not instructions.strip():
            raise SpecError(f"question {name!r} needs instructions")
        if not isinstance(choices, dict) or len(choices) < 2 or not all(
            isinstance(k, str) and isinstance(v, str) and v.strip() for k, v in choices.items()
        ):
            raise SpecError(f"question {name!r} needs at least two choices, each with a meaning")
        body_questions[name] = {"type": "choice", "instructions": instructions, "criteria": choices}
    body = {"model": spec.get("model") or DEFAULT_MODEL, "state": state, "questions": body_questions}
    size = len(state.encode()) + len(json.dumps(body_questions).encode())
    if size > LIMIT_BYTES:
        raise OverflowError(f"the input is {size} bytes, over Jev's {LIMIT_BYTES}; send it to a big model, never a cut-down copy")
    return body


def key() -> str:
    """The key: JEV_API_KEY, the one name Lem reads for it."""
    found = os.environ.get(KEY, "")
    if not found:
        raise RuntimeError(f"{KEY} is not set in this process's environment, and it is the one name Lem reads for the key; put the key of the Jev model's provider there")
    return found


def address() -> str:
    """JEV_API_URL, or OpenRouter's address when it is not set."""
    found = os.environ.get("JEV_API_URL", "").strip() or URL
    if not found.startswith(("https://", "http://")):
        raise SpecError(f"JEV_API_URL={found!r} is not an address; set it as the provider's decisions endpoint, as JEV_API_URL={URL}, or unset it for OpenRouter")
    return found


def ask(body: dict, timeout: float) -> dict:
    secret = key()
    url = address()
    where = "OpenRouter" if url == URL else url
    context = ssl.create_default_context(cafile=str(MACOS_CA_BUNDLE)) if MACOS_CA_BUNDLE.is_file() else ssl.create_default_context()
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            reply = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"{where} answered HTTP {error.code}: {error.read().decode(errors='replace')[:400]}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"{where} could not be reached: {error.reason}") from error
    answers = reply.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(body["questions"]):
        raise RuntimeError(f"the reply does not answer every question: {json.dumps(reply)[:400]}")
    return {
        "model": reply.get("model"),
        "answers": {
            name: {k: a.get(k) for k in ("choice", "confidence", "probabilities")}
            for name, a in answers.items()
        },
        "cost": (reply.get("usage") or {}).get("cost"),
    }


def main(argv: list[str]) -> int:
    check = bool(argv) and argv[0] == "check"
    args = argv[1:] if check else argv
    if len(args) != 1:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 1
    try:
        timeout = timeout_seconds()
        body = build(load(args[0]))
        if check:
            # what a request would use, and no key's value: the address, and which variable gives the key
            given = KEY if os.environ.get(KEY) else None
            print(json.dumps({"ok": True, "model": body["model"], "questions": sorted(body["questions"]), "url": address(), "key_from": given}))
            return 0
        print(json.dumps(ask(body, timeout)))
        return 0
    except OverflowError as error:
        print(f"lem-jev: {error}", file=sys.stderr)
        return 3
    except (SpecError, OSError, RuntimeError) as error:
        print(f"lem-jev: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

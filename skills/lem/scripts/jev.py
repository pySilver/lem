#!/usr/bin/env python3
"""lem-jev: ask TypeSafe's Jev decision model one or more choice or yes/no questions, through OpenRouter or another provider.

  lem-jev SPEC.json | lem-jev - < spec.json     ask, print the answers as JSON
  lem-jev check SPEC.json | lem-jev check -     validate the spec and its size, send nothing

Lem's own copy. The plugin puts it on the Bash tool's PATH as `lem-jev` (`bin/lem-jev`), named so
that it does not shadow a developer's own `jev`, and the correction hook runs it by its path.

A spec is {"state": STATE, "questions": {NAME: QUESTION, ...}} and optionally "model". STATE is
the facts to decide on: a non-empty string, or a non-empty JSON object or array (Jev's docs
recommend an object with named fields). Every question names its type, one of Jev's two that Lem
sends, and there is no default:

  {"type": "choice", "instructions": "<what to decide>", "choices": {ID: "<what this choice means>", ...}}
      at least two choices, each with a meaning; the choices are sent as its criteria.
  {"type": "noul", "instructions": "<the yes/no question>", "yes": "<what a yes means>", "no": "<what a no means>"}
      one question, answered with the probability of yes; "yes" and "no" are optional, both or
      neither, and are sent as its criteria "true" and "false".

The reply on stdout: {"model", "answers": {NAME: ANSWER}, "cost"}. A choice's ANSWER is {"type":
"choice", "choice", "confidence", "probabilities"}: Jev returns probabilities per choice; read
them, a confidence near 0.5 is a coin toss. A noul's is {"type": "noul", "noul"}, the probability
of yes, from 0 to 1. A reply whose answer lacks what its type must have is a failed request, never
a null passed on.

LIMIT_BYTES is OpenRouter's line: through it, a request with more than about 32,000 bytes of text
runs in a long-context mode, on its own, which TypeSafe calls slower and less accurate; the hard
limit is 262,144 tokens (OpenRouter's guide, read 2026-11-23). So a spec whose state and questions
together pass LIMIT_BYTES is refused with exit 3 and nothing is sent. A state object or array
counts the bytes of its JSON text. Nothing here truncates: a caller with a longer input sends it to
a big model instead.

The key is JEV_API_KEY from the environment, and the address JEV_API_URL, OpenRouter's by default
(the owner, 2026-11-18: "jev lib only care about API url and API token - we can use any
provider"). JEV_API_KEY is the one name of the key: with no JEV_API_KEY nothing is sent, and the
refusal says so. The key is in no settings file: a settings file is in the repository's folder,
and no secret goes into a file. A process keeps the values it started with, so a key
changed later reaches only processes started after the change.

The request and the reply are Jev's own form, the same at every provider: a POST of state, model
and questions with the key as a Bearer token, and answers with a choice's choice, confidence and
probabilities, or a noul's probability of yes. Three parts are OpenRouter's: its address (`URL`),
its name of the model (`typesafe/jev-1.14`, where TypeSafe's own API says `jev-latest`), and the
reply's `usage.cost`, which another provider may not give (`cost` is then null). With another
JEV_API_URL, set JEV_MODEL to that provider's name of the model.

Exit codes: 0 answered; 1 a bad spec, no key, or a failed request (the error names which);
3 the input is over LIMIT_BYTES.
Environment: JEV_API_KEY (required), JEV_API_URL (the
address of the decisions endpoint, default URL), JEV_MODEL (default model), JEV_TIMEOUT (seconds).
"""  # noqa: E501 - `main` prints its third line as the usage line, so its lines stay as they are

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
# the types of Jev's questions that Lem sends
TYPES = ("choice", "noul")
# the default of JEV_TIMEOUT; main() reads the variable, so a wrong value is a message,
# not a traceback at import
TIMEOUT_SECONDS = 120.0
# macOS keeps its root certificates here. A python.org interpreter that never ran its
# "Install Certificates" step has none of its own and fails every TLS handshake
# without this.
MACOS_CA_BUNDLE = Path("/etc/ssl/cert.pem")


class SpecError(Exception):
    pass


def timeout_seconds() -> float:
    """JEV_TIMEOUT, the seconds one request may take: a number above 0, or
    TIMEOUT_SECONDS when it is unset."""
    raw = os.environ.get("JEV_TIMEOUT")
    if raw is None:
        return TIMEOUT_SECONDS
    try:
        seconds = float(raw)
    except ValueError:
        seconds = 0.0
    if not 0 < seconds < float("inf"):
        raise SpecError(
            f"JEV_TIMEOUT={raw!r} is not a number of seconds above 0; "
            f"set it as JEV_TIMEOUT=120, or unset it for {TIMEOUT_SECONDS:g}"
        )
    return seconds


def load(arg: str) -> dict:
    try:
        text = (
            sys.stdin.buffer.read() if arg == "-" else Path(arg).read_bytes()
        ).decode("utf-8")
    except UnicodeDecodeError as error:
        raise SpecError(
            f"the spec ({'stdin' if arg == '-' else arg}) is not UTF-8 text (byte "
            f"{error.start} does not read)"
        ) from error
    try:
        spec = json.loads(text)
    except ValueError as error:
        raise SpecError(f"the spec is not JSON: {error}") from error
    if not isinstance(spec, dict):
        raise SpecError("the spec must be a JSON object")
    return spec


def filled(text: object) -> bool:
    return isinstance(text, str) and bool(text.strip())


def number(value: object) -> bool:
    """A number from 0 to 1, as Jev gives a probability or a confidence; a JSON true is
    not one."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 0 <= value <= 1
    )


def question_body(name: str, question: object) -> dict:
    """One question of the request, in Jev's form, after checking its shape."""
    if not isinstance(question, dict) or question.get("type") not in TYPES:
        given = question.get("type") if isinstance(question, dict) else None
        named = f"has type {given!r}" if given is not None else "names no type"
        raise SpecError(
            f'question {name!r} {named}; give it "type": "choice" (with choices) or '
            '"type": "noul" (a yes/no question)'
        )
    kind = question["type"]
    instructions = question.get("instructions")
    if kind == "choice":
        if set(question) - {"type", "instructions", "choices"}:
            raise SpecError(
                f"question {name!r} is a choice and takes only type, instructions and "
                "choices; yes and no belong to a noul"
            )
        if not filled(instructions):
            raise SpecError(f"question {name!r} needs instructions")
        choices = question.get("choices")
        if (
            not isinstance(choices, dict)
            or len(choices) <= 1
            or not all(filled(v) for v in choices.values())
        ):
            raise SpecError(
                f"question {name!r} needs at least two choices, each with a meaning"
            )
        return {"type": "choice", "instructions": instructions, "criteria": choices}
    if set(question) - {"type", "instructions", "yes", "no"}:
        raise SpecError(
            f"question {name!r} is a noul and takes only type, instructions, yes and "
            "no; choices belong to a choice"
        )
    if not filled(instructions):
        raise SpecError(f"question {name!r} needs instructions")
    body = {"type": "noul", "instructions": instructions}
    said = [key for key in ("yes", "no") if key in question]
    if said:
        if len(said) == 1 or not (filled(question["yes"]) and filled(question["no"])):
            raise SpecError(
                f"question {name!r} needs both yes and no, each a text that says what "
                "that answer means, or neither"
            )
        body["criteria"] = {"true": question["yes"], "false": question["no"]}
    return body


def build(spec: dict) -> dict:
    """The decisions request body, after checking the spec's shape and size."""
    unknown = set(spec) - {"state", "questions", "model"}
    if unknown:
        raise SpecError(f"unknown spec keys: {sorted(unknown)}")
    state = spec.get("state")
    if isinstance(state, str) and state.strip():
        state_text = state
    elif isinstance(state, (dict, list)) and state:
        state_text = json.dumps(state, ensure_ascii=False)
    else:
        raise SpecError(
            "state must be a non-empty string, or a non-empty JSON object or array"
        )
    questions = spec.get("questions")
    if not isinstance(questions, dict) or not questions:
        raise SpecError("questions must be a non-empty object")
    body_questions = {
        name: question_body(name, question) for name, question in questions.items()
    }
    body = {
        "model": spec.get("model") or DEFAULT_MODEL,
        "state": state,
        "questions": body_questions,
    }
    size = len(state_text.encode()) + len(json.dumps(body_questions).encode())
    if size > LIMIT_BYTES:
        raise OverflowError(
            f"the input is {size} bytes, over the {LIMIT_BYTES} past which OpenRouter "
            "runs Jev in its slower, less accurate long-context mode; send it to a big "
            "model, never a cut-down copy"
        )
    return body


def answer(name: str, kind: str, given: object) -> dict:
    """One answer of the printed reply, for a question of type KIND, or a RuntimeError
    that names the question."""
    if isinstance(given, dict) and given.get("type", kind) == kind:
        if kind == "noul" and number(given.get("noul")):
            return {"type": "noul", "noul": given["noul"]}
        probabilities = given.get("probabilities")
        if (
            kind == "choice"
            and isinstance(given.get("choice"), str)
            and number(given.get("confidence"))
            and isinstance(probabilities, dict)
            and probabilities
            and all(number(p) for p in probabilities.values())
        ):
            return {
                "type": "choice",
                "choice": given["choice"],
                "confidence": given["confidence"],
                "probabilities": probabilities,
            }
    must = (
        "a noul, a number from 0 to 1"
        if kind == "noul"
        else "a choice, a confidence and probabilities"
    )
    raise RuntimeError(
        f"the reply's answer to question {name!r}, a {kind}, "
        f"lacks {must}: {json.dumps(given)[:400]}"
    )


def read(reply: object, questions: dict) -> dict:
    """The printed reply from Jev's: each question's answer by its type, the model and
    the cost. QUESTIONS is the request's, which says each question's type."""
    answers = reply.get("answers") if isinstance(reply, dict) else None
    if (
        not isinstance(reply, dict)
        or not isinstance(answers, dict)
        or set(answers) != set(questions)
    ):
        raise RuntimeError(
            f"the reply does not answer every question: {json.dumps(reply)[:400]}"
        )
    usage = reply.get("usage")
    return {
        "model": reply.get("model"),
        "answers": {
            name: answer(name, questions[name]["type"], answers[name])
            for name in questions
        },
        "cost": usage.get("cost") if isinstance(usage, dict) else None,
    }


def key() -> str:
    """The key: JEV_API_KEY, the one name Lem reads for it."""
    found = os.environ.get(KEY, "")
    if not found:
        raise RuntimeError(
            f"{KEY} is not set in this process's environment, and it is the one name "
            "Lem reads for the key; put the key of the Jev model's provider there"
        )
    return found


def address() -> str:
    """JEV_API_URL, or OpenRouter's address when it is not set."""
    found = os.environ.get("JEV_API_URL", "").strip() or URL
    if not found.startswith(("https://", "http://")):
        raise SpecError(
            f"JEV_API_URL={found!r} is not an address; set it as the provider's "
            f"decisions endpoint, as JEV_API_URL={URL}, or unset it for OpenRouter"
        )
    return found


def ask(body: dict, timeout: float) -> dict:
    secret = key()
    url = address()
    where = "OpenRouter" if url == URL else url
    context = (
        ssl.create_default_context(cafile=str(MACOS_CA_BUNDLE))
        if MACOS_CA_BUNDLE.is_file()
        else ssl.create_default_context()
    )
    request = urllib.request.Request(  # noqa: S310 - address() takes only http and https
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(  # noqa: S310 - address() takes only http and https
            request, timeout=timeout, context=context
        ) as response:
            reply = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"{where} answered HTTP {error.code}: "
            f"{error.read().decode(errors='replace')[:400]}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"{where} could not be reached: {error.reason}") from error
    except ValueError as error:
        raise RuntimeError(
            f"{where} answered with a reply that is not JSON: {error}"
        ) from error
    return read(reply, body["questions"])


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
            # what a request would use, and no key's value: the address, and which
            # variable gives the key
            given = KEY if os.environ.get(KEY) else None
            print(
                json.dumps(
                    {
                        "ok": True,
                        "model": body["model"],
                        "questions": sorted(body["questions"]),
                        "url": address(),
                        "key_from": given,
                    }
                )
            )
            return 0
        print(json.dumps(ask(body, timeout)))
    except OverflowError as error:
        print(f"lem-jev: {error}", file=sys.stderr)
        return 3
    except (SpecError, OSError, RuntimeError) as error:
        print(f"lem-jev: {error}", file=sys.stderr)
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

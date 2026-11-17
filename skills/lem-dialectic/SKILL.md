---
name: lem-dialectic
description: "Lem's proof and counter-proof of one claim, by two agents. Lem's plan stage loads it; the owner calls it as `/lem dialectic`."
disable-model-invocation: true
argument-hint: '<statement to analyze>'
allowed-tools: Bash, Read, Grep, Glob, Task, AskUserQuestion
---

# Dialectic Analysis

Objective analysis of a statement by running two agents with opposing goals in parallel, then synthesizing findings.

## Process

### Step 1: Launch Parallel Agents

**CRITICAL: Both Task tool calls MUST be in a single message for true parallel execution.** Do NOT use run_in_background. Do NOT launch sequentially. Foreground agents in the same message run in parallel and block until both complete.

**Agent 1 (Thesis)** — find all POSITIVE evidence:
- what works well, improvements, correct patterns
- supporting facts, proof the statement is TRUE
- benefits, strengths, successful outcomes

**Agent 2 (Antithesis)** — find all NEGATIVE evidence:
- what's problematic, issues, risks, anti-patterns
- edge cases, proof the statement is FALSE
- weaknesses, failure modes, hidden costs

Both agents must provide specific file paths and line numbers when analyzing code.

### Step 2: Synthesize

After both agents complete, synthesize findings into an objective conclusion:
- weigh evidence from both sides
- identify where thesis and antithesis agree (strongest signal)
- note unresolved tensions

### Step 3: Verify

**CRITICAL** — after presenting the synthesis, verify it against actual implementation:
- read the specific files and line numbers referenced by both agents
- confirm the evidence cited actually exists in the codebase
- check the implementation flow matches the claims made
- verify the synthesis accurately reflects the actual code context
- identify any misinterpretations or missing context from agent reports
- revise synthesis if verification reveals inaccuracies

## Use Cases

**Architecture decisions:**
```
/lem dialectic this microservice split improves maintainability
```

**Bug analysis:**
```
/lem dialectic the connection pool fixes the timeout issue
```

**Performance claims:**
```
/lem dialectic caching reduced database load by 80%
```

**Refactoring safety:**
```
/lem dialectic extracting this interface simplifies testing
```

**Code review:**
```
/lem dialectic this implementation is thread-safe
```

**Review changes:**
```
/lem dialectic review the changes in server.go
```

## Key Principles

- **Eliminate confirmation bias** — examining both sides simultaneously prevents anchoring on the first conclusion
- **Evidence-based** — agents must cite specific files, lines, and facts, not general claims
- **Verification required** — synthesis must be checked against actual code before presenting
- **Objective conclusion** — the goal is truth, not winning either side

# Tail Tales — Decisions

Why the package is shaped the way it is. Each entry records the decision, the reason, and where it
came from — including the ones that were reversed.

## The size cap — the contract, and the two weeks the record got it wrong

**THE LIVE CONTRACT. This is settled, not open:**

- **One file.** `SESSION_TALE.md` is the only copy. Nothing injects it; the agent reads it directly.
- **30,000 characters**, enforced **on the write path** — the only place a limit can live when
  there is one file and no second copy.
- **Truncation from the top.** Oldest turns go first; the material nearest the seam is last to go.
- **The header always survives**, and the trim announces itself inside the tale.
- **No commit-gate enforcement.** The tale is rewritten every compaction, so gating a commit on it
  would be ceremony around a file the mechanism itself regenerates.

Owner rulings, 2026-08-15, verbatim: *"There is only ONE source of truth — the session tail itself.
The agent MANUALLY reads it. There IS NO INJECTED COPY. So any rule that relies on the idea of an
injected copy is FALSE."* · *"The enforcement comes from the write-path."* · *"truncation is from
the **top** of the file, not the bottom."* · *"No git enforcement on Tail Tales."*

### Why this section is longer than the contract needs

The cap was ruled on 2026-07-29 and **went unenforced for over two weeks — because this file
explained its absence, and the explanation was false.**

It said the cap had been scoped to an *injected copy*, and credited that scoping to the owner.
Both halves were wrong. The primary log shows her ruling (*"Hard cap the limit at 30k"*), then a
remark of hers on an unrelated matter, then **the packager identifying the flaw himself and
inventing the two-copy split.** No statement of hers authors it. The design decision was his,
recorded under her name.

**That misattribution is what made it durable.** A reviewer read the emission path correctly, saw
`HARD_CAP` defined and never read, and proposed enforcing it — and was overruled by this file
citing an owner ruling that did not exist. **A false premise in a design record outranks a correct
reading of the code, because the record claims an authority the code cannot argue with.**

Two failure shapes worth carrying out of it:

1. **A design record can go stale in a direction that protects the bug.** The prose explained the
   absence so plausibly that the absence stopped looking like a defect.
2. **When the architecture changes, re-derive the conclusions that rested on it.** "Capping the
   file is destructive" was true while a fallback copy existed. Injection was removed 2026-07-31;
   the premise died and the conclusion was carried forward anyway. **A conclusion is only as live
   as its premise, and neither announces its own death.**

**The code was the honest source. The prose was not.**

## An instruction that is load-bearing on install is load-bearing on uninstall

**Decision:** the uninstall section undoes *every* install step, step 3 included, and makes no
claim that removing the hook alone is sufficient.

**Reason, and it is a scope slip worth recognising by shape.** The uninstall section used to say
*"Nothing else is touched… removing the hook entry is a complete rollback on its own."* Every word
of that is true **about the package** — it writes no config, caches no state, installs no
dependencies. But a rollback section is not making a claim about the software. It is making a
claim about the **installation**, and this installation *requires* the user to create config: step
3 says arrange the read, and without it the package writes a file nobody opens.

So the sentence read as reassurance while being false for every real install. A fresh installer,
following the docs end to end with no prior context, uninstalled cleanly and left behind an
operating document still instructing an agent to read a tale inside a deleted package.

**⚠️ The same instruction has now failed in both directions in this package's short history:**

- **2026-07-29 / 07-31** — the install guide told installers to **retire** the read instruction,
  on the belief that injection covered it. It did not; that instruction was the delivery path.
- **2026-08-15** — the uninstall guide **left it standing**, aimed at nothing.

Removed when it was needed, kept when it was dead. Both silent, both because the read step sat in
an unclaimed space just outside the package boundary: the docs never decided whether it was part
of the thing.

**The rule, stated so it travels past this package:** *anything an install requires the user to
create belongs to the installation, and the uninstall owes it a step.* Whether the module's own
code writes that thing is irrelevant.

**The tell:** a rollback section describing what the *software* touches rather than what the
*installation* changed. Walk the install steps and check each has an inverse. A step without one
is residue nobody will ever clean, precisely because the docs promised there was nothing to clean.

**Why neither half looked wrong from inside:** both sections were written hours apart in the same
file, and each was accurate on its own. The contradiction existed only in the relationship between
them, and nothing in the test suite or the gate reads two sections at once. It surfaced only when
someone performed the whole lifecycle, in order, without knowing what was supposed to happen.

## The package writes; it does not inject

**Decision, 2026-07-31, owner ruling.** One program owns the file end to end. Delivery to the
agent's context is arranged separately.

**Reason:** the hook transport truncates payloads far below the size of a real tale, so injecting
one was never reliable. A short pointer fits; a tale does not, and never did. Every measured tale
exceeded the cap it was being squeezed through, and trimming ran from the end — silently removing
the turns closest to the seam, which is the entire content the tale exists to carry.

**Consequence, stated plainly because it is easy to miss:** installing this package does not, by
itself, give an agent its continuity back. See `!DEPENDENCIES.md`.

## Reasoning and tool calls are discarded; the user's words are kept

**Decision, 2026-07-29.**

Reasoning was capped at 300 characters, so it arrived as fragments — anxiety without resolution.
It is also the most *reconstructable* material in the file: the same agent, in the same situation,
can regenerate its own reasoning. **The user's exact words cannot be regenerated at all.** When
budget is scarce, keep the irreplaceable half.

Tool calls turned out never to have been captured — the code only ever read `thinking` and `text`
blocks. Removing them changed nothing. Recorded anyway, because otherwise the belief that a fix
had occurred would have persisted.

## Identity comes from the runtime payload, never from source constants

**Decision, 2026-06-10**, after four per-agent copies of the script each carried a hardcoded path.
When the workspace moved they silently captured week-old transcripts. Nothing failed; the output
was present, well-formed, and drawn from the wrong source.

**Reason:** a hardcoded path is a claim about the world that stops being true without telling
anyone. Reading `cwd` and `transcript_path` at fire time means the claim is re-checked every run.
Adding an agent needs no source edit.

**This is also why the verification step is a read and not a `stat`.** The failure mode this
package was built against produces a file that exists, has a fresh mtime, and is wrong.

## Failures never reach the agent, and never crash the runtime

**Decision:** every error path exits 0, writes nothing, and logs to a file.

A continuity hook that breaks the session it protects has failed worse than one that produces
nothing. The cost is that failure is invisible from inside the agent — accepted, and documented as
open issue #2 rather than hidden.

**Corollary that took a live incident to learn:** when no turns extract, the module returns *before*
the write. An empty transcript therefore cannot replace a good tale with an empty one. This is
asserted first in the test suite, as bait, because it is the property most worth proving and the
easiest to break by accident.

## Unrecognised arguments are tolerated rather than rejected

**Decision:** keep `parse_known_args()`.

Tightening to `parse_args()` would make the hook exit non-zero whenever a config carried a stale
flag — converting a silent degradation into a hard failure at session start, for a package whose
first duty is not to break the runtime.

**The cost is real and is recorded as open issue #1:** a removed flag keeps being accepted, so a
stale registration is indistinguishable from a live one. That cost fell due on 2026-08-15, when a
registration for a flag deleted six weeks earlier was found still live and still silent.

## Packaging decisions, 2026-08-15

- **Names became roles.** `the builder`, `the maintainer`, `a reviewer`, `the owner`. Measurements
  were kept and attributions dropped — *the scar travels, the names don't.* The failures are the
  useful part; whose console they appeared on is not.
- **Paths became `<PACKAGE_ROOT>` and `<WORKSPACE>`**, matching the precedent already set by the
  sibling packages in this repository rather than a scheme invented here.
- **The changelog was found incomplete, not stale.** Its newest entry predated the injection
  removal, so the top of the file still presented injection as the live design. The fix was the
  missing entry, not a banner over the old ones — **stale and missing look identical from the top
  of a file and take opposite repairs.**
- **License: Apache-2.0**, per the repository default, chosen by the rights holder. Loop Doctor's
  MIT is a framework-specific exception, not an author preference — a distinction worth writing
  down because the surface pattern invites the wrong inference.

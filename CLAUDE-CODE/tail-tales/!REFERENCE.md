# Tail Tales — Reference

## Companion packages (this repository)

| package | relationship |
|---|---|
| **Selfhook** | The usual answer to this package's hard dependency. Selfhook emits a short pointer telling the agent which files to open after a session break; naming the tale among them is what makes the tale get read. The two are independent — either works without the other, and this package has no knowledge of it. |
| **Freestyle Beats** | Unrelated at runtime. Shares the substrate and the hook-registration pattern. |
| **Loop Doctor** | Unrelated. Cross-substrate, MIT-licensed as a framework exception. |

**Nothing here is required.** This package has no dependency on any other package in this
repository. It needs a runtime, a Python, and somewhere to write.

## Concepts referenced

**The seam.** The compaction boundary. The point where a context window ends and a summary of it
begins. This package exists because a summary is a paraphrase, and paraphrase is lossy in one
direction: it keeps decisions and drops wording.

**The tale.** The written artifact. Conversational turns nearest the seam, reproduced verbatim
rather than condensed.

**Written-but-never-read.** The characteristic failure of this package: the hook fires, exits
clean, the file appears on disk with correct content, and the agent receives nothing. There is no
error and no observable difference from success. Named in `!DEPENDENCIES.md` because it is the
single most likely way for a correct install to deliver nothing.

**Stale versus missing.** Two document defects that look identical from the top of a file and take
opposite repairs. A stale document says something that stopped being true; an incomplete one never
said the newest thing at all. Annotating the second as though it were the first papers over an
absence. Both were present in this package's docs and were fixed differently.

**Bait-first testing.** Plant a case the instrument must catch, confirm it catches it, and only
then trust a clean result. `tests/smoke_test.py` runs its bait first and aborts the suite on
failure. **A green light from an instrument that cannot go red is not information.**

## Prior art / provenance

The mechanism is not novel — reading a transcript and writing a tail is a small amount of code.
What is carried forward here is the set of failures found by running it:

- hardcoded paths producing correct-looking output from the wrong source (2026-06-10)
- a schema validator silently dropping output rather than rejecting it (2026-06-03)
- two registrations racing on one event, failing by staleness so nothing warned (2026-07-29)
- an injection budget every real payload exceeded, trimming from the end (2026-07-29)
- a turn count inflated by counting reasoning as conversation (2026-07-29)
- documentation outliving the code it described, twice, in the same direction (2026-08-15)

Every one produced a working-looking system. That is the through-line, and the reason this
package's verification steps ask you to read output rather than confirm it exists.

## Feedback

Issues and corrections belong wherever this repository directs them. Corrections to the *factual*
claims in these docs are especially welcome — several were wrong until something checked, and the
checks that found them were mechanical, not clever.

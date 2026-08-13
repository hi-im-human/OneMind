# Freestyle Beats — Known Issues

## Open

**One bad comma in `settings.json` kills every hook, silently.**
Status: documented, not fixable from inside the package. The runtime disables the whole
hooks block on malformed JSON without surfacing an error to the agent. `!INSTALL.md`'s
verification section is the mitigation: check that the session-start reminder actually
appears after install.

**Hook failure is invisible to the agent.**
Status: inherent. If Python is missing from PATH or the hook path is wrong, the reminder
just never arrives — the agent doesn't know it's flying without a net until a schedule
silently dies. Mitigation is the same verification step, repeated after any environment
change.

**Cron survival across session breaks is unpredictable.**
Status: upstream behavior, worked around. Both survival and loss observed on the same
runtime in one day. The package's stance is check-don't-assume (`CronList` first); this
entry exists so nobody "fixes" the soft wording back into a confident claim in either
direction.

## Resolved (in ancestry)

**PostCompact `additionalContext` silently dropped** — resolved 2026-05-31 by emitting
`hookEventName: "SessionStart"` from the PostCompact registration. See `!DECISIONS.md`.

**"Compaction wipes your crons" asserted as fact** — falsified in live use; corrected
2026-08-13 to check-first wording. A hook speaks with the authority of infrastructure
and doesn't get to guess.

**Skill invocations as beat prompts** — ~78k chars/day of duplicate context, measured;
resolved 2026-08-01 in ancestry by registering literal prompt text, and forbidden in
this package's `SKILL.md`.

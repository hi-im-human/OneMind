# Decisions

## 2026-08-21 — preserve the official access gate

The local patch changes only the early blanket bot filter. Bot messages that pass still enter `handleInbound` and the official plugin's normal access and mention checks.

## 2026-08-21 — block self-messages unconditionally

The receiving Discord bot's own messages are dropped before allowlist evaluation. This prevents an accidental self-ID allowlist entry from reopening direct self-echo.

## 2026-08-21 — bind group authorization to the current channel

An allowlist entry in one group does not clear the early bot filter in another group. Threads check their own channel ID and their parent channel ID; plain text channels do not inherit authorization from their category.

## 2026-08-21 — exact source-state recognition

The patcher recognizes stock, Hearthwell v1, and current blocks exactly. It refuses mixed, duplicate, and unfamiliar variants instead of composing a patch from partial markers.

## 2026-08-21 — refusal is nonzero

An unfamiliar source shape is operationally different from a successful no-op. A nonzero exit makes that distinction available to manual and SessionStart callers.

## 2026-08-21 — fixture scans can exclude home roots

The default command scans `~/.claude*` for operational use. Tests and bounded-root inspections use `--no-home-scan`; unknown options fail before discovery so a misspelled isolation flag cannot fall back to live home scanning.

## 2026-08-21 — plugin refresh is the rollback mechanism

The package does not write backup files into plugin caches. Removing the hook and refreshing/reinstalling the official plugin restores vendor source without leaving package-specific backups in versioned cache directories.

## 2026-08-21 — Apache License 2.0

The copyright holders selected Apache-2.0 for public distribution. Attribution is recorded in `NOTICE`.

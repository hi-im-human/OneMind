# Known Issues and Limitations

## Open

### POSIX runtime is unverified

The implementation uses `pathlib` and platform-neutral text I/O, but this release has only been executed on Windows. POSIX support is not claimed until a runtime receipt exists.

### Upstream source changes require a package update

The patcher intentionally refuses unknown, mixed, or duplicated handler shapes. A new official plugin version may require a reviewed recognition block before the package can patch it.

### Plugin refreshes replace local modifications

Reinstalling or refreshing the Discord plugin may restore stock source. The included SessionStart entry rechecks installed copies; it does not prevent upstream files from changing.

### No automatic backup

The patcher writes the recognized replacement directly. Rollback uses an official plugin reinstall/refresh rather than a package-created backup.

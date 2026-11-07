# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project does not have released versions yet, so changes are listed under
`Unreleased`.

## [Unreleased]

### Added

- Scripted integration tests (`tests/test_atm.py`) covering sign-in, balance,
  deposits, withdrawals, insufficient funds, the three-attempt sign-in limit,
  admin account creation, invalid input, and end-of-input handling.
- GitHub Actions CI for Ubuntu (GCC), Windows (MinGW-w64), and macOS (Clang).
- `--fast` command-line flag to skip animation delays in tests and automation.
- Real screenshots, an animated demo, and a social preview generated from the
  application's recorded ANSI output.
- Reproducible capture and rendering scripts in `demo-assets/tools/`.
- Contribution, security, changelog, and issue/PR templates.

### Changed

- README rewritten around verified behavior, with accurate build commands,
  demo credentials, limitations, and testing instructions.
- Startup banner now says "single-file demo | in-memory session" instead of the
  unverified "v2.4 | secure session" text.
- Replaced the previous screenshots, which did not match the application's
  interface, with captures from the real program.

### Fixed

- Amounts that are not finite (for example `inf` or `nan`) are rejected.
- Non-numeric account IDs are re-prompted instead of leaving the input stream in
  a failed state.
- End of input now exits cleanly instead of looping or crashing.
- PIN validation now uses an unsigned-safe `isdigit` check.

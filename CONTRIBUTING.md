# Contributing

Thanks for taking a look at Simple ATM Simulation. This is a small educational
project, so the contribution process is intentionally lightweight.

## Before you start

- Small fixes, documentation improvements, and test additions can go straight
  to a pull request.
- For larger changes (new screens, persistence, refactors), please open an
  issue first so we can agree on scope.
- The repository does not have an open-source license yet. Please open an issue
  before contributing substantial code so we can agree on terms. See the
  License section of the README.

## Development setup

Requirements: a C++17 compiler and, for the tests, Python 3.8+.

```bash
git clone https://github.com/ShahabAhmed01/Simple-ATM-Simulation.git
cd Simple-ATM-Simulation
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror -O2 -o atm "Atm Simulation.cpp"
./atm
```

On Windows (PowerShell with MinGW-w64):

```powershell
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror -O2 -o atm.exe "Atm Simulation.cpp"
.\atm.exe
```

Use Windows Terminal for the ANSI color UI.

## Tests

```bash
python -m unittest discover -s tests -v
```

Set `CXX` to test with a different compiler:

```bash
CXX=clang++ python -m unittest discover -s tests -v
```

The suite compiles the app into a temporary directory and drives it with
scripted input, so no manual interaction is needed. Add or update a test for
every behavior change.

## Code style

- Keep the application in one source file. The single-file design is deliberate.
- Match the existing style: 4-space indentation, `static` helpers, and the ANSI
  color constants in `namespace C`.
- The build must be clean with `-Wall -Wextra -Wpedantic -Werror`.
- Do not add third-party runtime dependencies.
- Keep changes narrow. This is a demo, not a production banking system.

## Pull requests

- Describe what changed and why.
- Include the commands you ran to build and test.
- Update the README or CHANGELOG when behavior or setup changes.
- Do not include real personal data, credentials, or build artifacts.
- Keep commits focused; one logical change per commit is ideal.

By submitting a pull request you confirm that you wrote the change, or that you
have the right to submit it.

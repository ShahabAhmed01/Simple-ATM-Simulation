# Demo assets

All images here are rendered from the real output of `Atm Simulation.cpp`.
Nothing is a mockup.

| File | What it shows |
|---|---|
| `screenshots/01-main-menu.png` | Main menu after the splash screen |
| `screenshots/02-sign-in.png` | Account list and account-ID prompt |
| `screenshots/03-dashboard.png` | Signed-in dashboard |
| `screenshots/04-history.png` | Transaction history after a deposit |
| `demo.gif` | Sign-in, $250 deposit, history, logout (about 9 seconds) |
| `social-preview.png` | 1280 x 640 social preview for the GitHub repository |

`tools/session.json` is the captured ANSI session. It includes timestamps, the
90 x 30 terminal size, and the moments used for each screenshot.

## How the assets were made

1. Compile the app:

   ```bash
   g++ -std=c++17 -O2 -o atm.exe "Atm Simulation.cpp"
   ```

2. Create a Python environment and install the asset tools:

   ```bash
   py -m venv .venv-assets
   .venv-assets\Scripts\python -m pip install -r demo-assets/tools/requirements.txt
   ```

3. Capture a real session (Windows only, because it uses ConPTY through
   `pywinpty`):

   ```bash
   .venv-assets\Scripts\python demo-assets/tools/capture_session.py
   ```

4. Re-render the images:

   ```bash
   .venv-assets\Scripts\python demo-assets/tools/render_assets.py
   ```

The recording is sped up by 1.2x in the GIF; the original session is about 10.9
seconds. The GIF is quantized to 64 colors to keep it small.

The previous screenshots (`01-landing-page.png`, `02-dashboard.png`,
`03-deposit-flow.png`, and `04-history.png`) were removed because they showed a
different interface, prompts, and starting balance than the source in this
repository. They could not be reproduced from the code.

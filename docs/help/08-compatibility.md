# 08 — OS compatibility (Windows, WSL2, VM)

Back to [index](index.md). The kit's author develops on Linux; macOS/Windows rows below are
researched from upstream releases and docs, not run by the author — corrections welcome.

## Matrix (native OS, no VM)

| Component | Linux | macOS | Windows |
|---|---|---|---|
| Python scripts (`install.py`, `doctor.py`, all `skills/*/scripts/`) | yes | yes | yes — pure-Python deps; invoke with `py -3` / `python` wherever docs say `python3` |
| `.sh` wrappers (`install.sh`, `doctor.sh`, `tests/run.sh`) | yes | yes | Git Bash or WSL only; otherwise call the `.py` entry points directly |
| `tectonic` | yes | yes | yes — official `-windows-msvc` / `-windows-gnu` zips ship every release |
| `pdflatex` fallback | TeX Live | MacTeX | MiKTeX / TeX Live |
| `pdfinfo` | `poppler-utils` | `brew install poppler` | conda-forge (`conda install poppler`) or Chocolatey (`choco install poppler`); without it, `doctor.sh` flags the gap and page counts fall back to reading the PDF directly |
| `pandoc` | distro package | Homebrew | official Windows installer |
| Node + `agent-browser` | yes | yes | yes — upstream ships Windows builds and documents Windows behavior; `npm install -g` sets PATH itself |
| Debug browser + CDP attach | yes | yes | yes — launch command in [Browser setup](03-browser-setup.md); close Chrome before reusing a locked profile |
| `gog` backend | yes | yes | yes — upstream ships `windows_amd64` / `windows_arm64` zips; file keyring backend works the same |
| Python OAuth backend | yes | yes | yes — browser-based loopback flow, no OS-specific parts |
| chrome-devtools MCP via `npx` | yes | yes | yes — needs Node only; point at the same debug port |
| `curl` port probe | yes | yes | built into Windows 10/11 (`curl.exe`) |

Net: tailor-only mode works natively on all three OSes. Full apply mode works natively on Windows
too, with the translations above (`py -3`, `.py` entry points, Windows install sources). Nothing in
the shipped scripts assumes a POSIX shell — no hardcoded `/tmp`, no `shell=True`, `~` expands per-OS.

## WSL2 (when native Windows friction appears)

If anything above misbehaves natively, WSL2 (Ubuntu) is the next step, and it is strictly lighter
than a VM (shared kernel, dynamic memory). Two things users ask about:

- **Browser access.** Keep Chrome on the Windows side with the debug flag, run the agent inside WSL2:
  from WSL2, `localhost:9222` reaches ports listening on Windows, so `agent-browser connect 9222`
  and the `curl` probe work unchanged. The reverse (agent on Windows, browser inside WSL2 Linux) is
  more fragile — prefer keeping both on the same side.
- **Files.** The WSL2 checkout sees Windows drives under `/mnt/c`; keep the kit checkout and the
  workspace on the Linux side for speed, templates and PDFs move across freely.

## Full VM (last resort)

Only if WSL2 is unavailable (e.g. Home edition restrictions in your environment, or policy blocks).
Budget honestly on an 8 GB machine: Windows itself (~3 GB) + a Linux guest given 3–4 GB + a
Chromium with a dozen tabs + the agent runtime leaves almost no headroom — expect swapping. Prefer
WSL2; prefer native Windows with the translations above over both.

## What to do when something OS-specific breaks

1. Run `./doctor.sh --mode all` (or `python doctor.py --mode all`) — paste the exact MISSING/WARN line.
2. Check `docs/EXTERNAL_TOOLS.md` §9, then the page above for your module.
3. Report OS version + the failing command verbatim; "works on my machine" is not a diagnosis.

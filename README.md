<div align="center">

# 🗂️ F5 XC Log Downloader

**Pull Access, Security/Firewall, and Audit logs from F5 Distributed Cloud straight to CSV — no API scripting required.**

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Built with Flask](https://img.shields.io/badge/backend-Flask-000000.svg)

[Quick Start](#-quick-start) • [Features](#-features) • [Screenshots](#-screenshots) • [How It Works](#%EF%B8%8F-how-it-works) • [Known Limitations](#-known-limitations)

</div>

<br>

A self-contained desktop tool for **F5 Distributed Cloud (F5 XC)** — formerly known as **Volterra** — that lets anyone pull Access logs, Security/Firewall (WAF) logs, or Audit logs and export them straight to CSV, without writing a single line of code or reading F5's API documentation.

Runs as a small local web app (Python/Flask backend, themed single-page UI) and ships as a standalone Windows `.exe` via PyInstaller — no Python install required for the end user.

<br>

## 💡 Why this exists

F5 Distributed Cloud exposes its log data through a REST API (`AccessLogQueryV2`, `FirewallLogQuery`, `AuditLogQueryV2`, and their `/scroll` variants), documented at [docs.cloud.f5.com](https://docs.cloud.f5.com/docs-v2/api/log). That's fine if you're comfortable writing authenticated POST requests, handling pagination tokens, and reading OpenAPI schemas — but most people who *need* F5 XC log data day to day (support engineers, managed-services teams, network/security engineers, SOC analysts doing an incident review) just want to pick a time range and get a CSV of their access logs, WAF/firewall events, or audit trail.

This log export tool is the bridge between "I need last week's WAF events for this app" and an actual spreadsheet — no API knowledge, scripting, or Postman collection required.

<br>

## 📸 Screenshots

<p float="left">
  <img src="docs/screenshot-light.png" width="49%" alt="F5 XC Log Downloader main screen in light mode, showing Configuration Backups and Log Type selection" />
  <img src="docs/screenshot-dark.png" width="49%" alt="F5 XC Log Downloader main screen in dark mode, showing Configuration Backups and Log Type selection" />
</p>

<details>
<summary><b>More screenshots</b> — connection &amp; time range, advanced query, download progress</summary>
<br>

![F5 XC connection fields and time range picker with quick-range dropdown](docs/screenshot-connection-timerange.png)
![Advanced query editor showing F5 XC's documented allowed query fields per log type](docs/screenshot-query.png)
![Download progress view with live stats and activity log](docs/screenshot-download.png)

</details>

<br>

## ✨ Features

| | |
|---|---|
| 🗃️ **All three log types** | Access, Security/Firewall (WAF), and Audit logs — each using F5 XC's confirmed, documented query syntax |
| 🔄 **No manual pagination** | Automatically pages through large result sets (Search After with an automatic fallback to Scroll continuation, since F5 XC's live behavior for Search After doesn't always match its own published docs) |
| 🔍 **Advanced filtering** | F5 XC's native `{field="value"}` query syntax, with the actual documented allowed fields shown inline per log type — not guessed |
| 📤 **CSV / full JSON export** | Plus an always-on activity/debug log for troubleshooting |
| 📊 **Live progress** | Pause / resume / stop, with count validation against F5's own reported `total_hits` |
| 💾 **Config backup/restore** | Export and share non-sensitive settings (never the API token) as a JSON file |
| 📁 **Native OS folder picker** | A real Windows folder dialog for the output directory, not a fake in-page one |
| ⚡ **"Check Range"** | One-click probe that instantly tells you whether F5 XC will accept a given time range and log type, and how many records are available — before committing to a full download |
| 📦 **Single `.exe`** | Recipients don't need Python, pip, or any dependencies installed |

<br>

## 🚀 Quick start

<details open>
<summary><b>Option A — run the prebuilt Windows EXE</b> (easiest)</summary>
<br>

Download the latest `.exe` from [Releases](../../releases), double-click it, then open `http://127.0.0.1:5000` in your browser.
</details>

<details>
<summary><b>Option B — run from source</b></summary>
<br>

```bash
pip install flask requests
python f5xc_log_downloader_v5.py
```
Then open `http://127.0.0.1:5000`.
</details>

<details>
<summary><b>Option C — build your own EXE (Windows)</b></summary>
<br>

```
build_windows_exe.bat
```
This installs Flask/Requests/PyInstaller if needed, builds a onefile EXE, and drops it in `release\F5XC-Log-Downloader.exe` — ready to hand to anyone, with no Python required on their end.
</details>

<br>

## ⚠️ A note on Windows security warnings

The prebuilt EXE is unsigned (no paid code-signing certificate), so you should expect two things the first time you or a recipient runs it:

> **"Windows protected your PC" (SmartScreen)** — this appears for any new, unsigned executable from an "unknown publisher," regardless of what the program actually does. Click **More info** → **Run anyway**.

> **A handful of antivirus engines may flag the EXE.** This build is packaged with PyInstaller, which bundles a Python interpreter and your code into a single file. That extraction-at-startup pattern happens to resemble how some real malware packers behave, so a small number of heuristic-based antivirus engines flag PyInstaller executables as a false positive — this is a long-standing, widely documented issue with PyInstaller itself, not something specific to this project (see the PyInstaller project's own [`antivirus-false-positives`](https://github.com/pyinstaller/pyinstaller/issues?q=is%3Aissue+label%3Aantivirus-false-positives) issue label, where this has been reported hundreds of times against completely unrelated, legitimate projects).

<details>
<summary><b>VirusTotal scan details for v5.8</b> — 6 of 71 engines flagged it, click to see why that's expected</summary>
<br>

A [VirusTotal scan](https://www.virustotal.com/gui/file/06e6bcae4c24df703cba8d2605d59e94546558541c7ec6050b91b8412a5395eb/detection) of the packaged v5.8 EXE shows **6 of 71** engines flagging it — and every one of those 6 flags is a heuristic or machine-learning guess, not a signature match on real malicious code:

| Vendor | Verdict | Why it's a heuristic flag, not a real detection |
|---|---|---|
| Microsoft | `Trojan:Win32/Wacatac.C!ml` | The `!ml` suffix = machine-learning heuristic. Wacatac is the textbook example cited in PyInstaller's own false-positive reports. |
| Elastic | "Malicious (moderate confidence)" | Elastic itself hedges the confidence — not a firm detection. |
| Skyhigh (SWG) | `BehavesLike.Win64.Injector.rc` | "BehavesLike" is explicitly a behavioral guess, not a match. |
| Zillya | `Trojan.Convagent.Win32...` | Generic family bucket, no specific indicator. |
| Bkav Pro | Generic hash-based label | A low-tier engine known for a high false-positive rate. |
| SecureAge | "Malicious," no detail | No named threat or family at all. |

Every engine that does deep static/dynamic/behavioral analysis reports it clean — **Kaspersky, Sophos, CrowdStrike Falcon, BitDefender, ESET-NOD32, Symantec, TrendMicro, Malwarebytes, SentinelOne, Palo Alto Networks, WithSecure, Google, Avast, AVG, McAfee**, and 50+ others.

If you'd rather not rely on a point-in-time scan of this build at all, the most reliable option is **Option C above: build the EXE yourself from the source in this repo.** A self-built binary from code you can read end-to-end sidesteps the question entirely.

</details>

<br>

## ⚙️ How it works

The tool is a single Python file running a local Flask server, with the entire UI (HTML/CSS/JS) served from one template — no separate frontend build step. All F5 XC API calls are made server-side using your namespace/token/time range, so your token is used for the request but never written to disk in any saved configuration.

<br>

## 🔬 A real debugging story

*(why this is more than a form wrapper)*

F5 XC enforces an **undocumented rolling time-window limit** on how far back a query's `start_time` can be — confirmed through direct testing, since it appears nowhere in F5's published API schema. Figuring this out (and ruling out several wrong theories along the way — first assuming it was a maximum *range width*, then confirming via a narrow 24-hour test window that it's actually about how *old* `start_time` is, regardless of window size) is documented in [CHANGELOG.md](CHANGELOG.md). The tool's "Check Range" feature exists specifically because of this finding — it lets you probe the real boundary in one click instead of waiting through a failed multi-minute download.

<br>

## 🤖 Development notes

This project was built with [Claude](https://www.anthropic.com/claude) (Anthropic) as an AI pair-programmer — code generation, debugging assistance, and documentation drafting were AI-assisted throughout. The requirements, feature direction, and validation were mine: every fix in this repo (including the debugging story above) came from hands-on testing against the F5 XC API and cross-checking behavior against F5's official API documentation, not from taking AI-generated output at face value.

I'm noting this openly rather than leaving it implicit — knowing how to direct AI tooling effectively, verify its output against real systems, and catch it when it's wrong is itself a skill I'd rather demonstrate than hide.

<br>

## 🧩 Known limitations

- F5 XC enforces a real but undocumented limit on how old a query's start time can be (varies by log type). The tool surfaces F5's exact rejection message and offers "Check Range" to probe it quickly, but cannot bypass it — this is an F5-side platform constraint, not something the client can safely work around.
- A `scroll_id` (used for large result sets) is only valid for ~2 minutes between requests per F5's own schema — pausing a large download for longer than that may require restarting it.
- Built and tested against F5 XC's Log Query V2 / Scroll API family; other F5 XC log APIs (e.g. Application Security Monitoring) are not currently used by this tool.

<br>

## 📄 License

MIT — see [LICENSE](LICENSE).

<div align="center">
<br>

If this saved you time, a ⭐ on the repo is appreciated.

</div>

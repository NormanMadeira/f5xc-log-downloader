# Changelog

## v1.1.0 (current)

### Added
- **Native Windows folder picker.** "Browse…" opens the standard Windows folder dialog on the machine running the app. The in-page folder list is removed.
- **Time presets for Last 7 days, Last 14 days and Last 30 days.** Relative presets are recalculated when you click Download or Check Range, so the start time does not drift past a limit while the form is open.
- **Range rules by log type**, shown as a notice under the time range and enforced on Download:
  - Ranges longer than 7 days show a warning: Access logs cannot be retrieved beyond 7 days, and only Security Events and Audit logs can be retrieved up to 30 days.
  - Ranges longer than 30 days are blocked for all log types.
  - Access logs are blocked when the start time is more than 7 days old. Security Events and Audit logs are blocked when the start time is more than 30 days old.

### Changed
- **WAF security events now use the Application Security Monitoring API** (`ves.io.schema.app_security.AppSecurityMonitoringAPI.SecurityEventsQuery` and `SecurityEventsScrollQuery`) instead of `FirewallLogQuery`. The Log type "Security / Firewall" is now "Security Events (WAF)". Security events are read from the `events` field of the response. Scroll requests use `GET` with `scroll_id` as a query parameter, as the API reference describes.
- Query help for Security Events lists the fields the API reference documents: `vh_name`, `sec_event_type`, `src_site`, `city`, `country`.

### Fixed
- **Security events beyond about 8 days.** The earlier restriction came from using `FirewallLogQuery`, not from F5 retention. F5 TAC confirmed that security events are queried through the Application Security Monitoring API. With that endpoint, requests are no longer limited to 8 days. Confirmed on a live tenant: Security Events return data across the full 30-day retention window.
- **Search After downloads failing on the first request.** An earlier build sent `scroll` and `search_after` in the same request. F5 rejects this with HTTP 400 (`scroll and search_after query at the same time is not possible`), so any download over 500 records failed. Both pagination options now use scroll continuation. The UI option is kept for compatibility.
- **Client-side block on valid Audit downloads.** A hardcoded rule rejected any `start_time` older than 8 days for every log type, even when F5 accepted the range. The rule is removed. F5's response is now the only check, the same one "Check Range" uses.

- The EXE file name includes the version (`F5XC-Log-Downloader-v1.1.0.exe`). The build script sets it, so every build is identifiable. The version also shows in the app header.

### Notes
- Security events are retained for 30 days per F5 retention documentation.
- The Security Events request path `/api/data/namespaces/{namespace}/app_security/events` was confirmed working on a live tenant.

## v1.0.0 — Initial public release

### Fixed
- **Root cause of downloads appearing to hang / "Stop" doing nothing.** Output-directory creation, time parsing, and log-type validation previously ran *outside* the main try/except block in the download worker. Any failure there (e.g. an invalid or inaccessible output path) silently killed the background thread with no status update — the job stayed "running" forever in the UI, and Stop had nothing left to signal. The entire worker is now wrapped so any failure reports a clean, specific error within about a second.
- **Search After pagination silently stopping after the first batch** on large result sets. Confirmed through testing: F5 XC's Log Query V2 response does not reliably return `last_sort_values` even when `search_after` is requested — despite that field being part of F5's documented schema. The tool now also requests `scroll: true` up front and automatically falls back to scroll-token continuation whenever `last_sort_values` is absent, instead of giving up.
- **Permanent API errors (bad auth, invalid time range, etc.) wasting ~30 seconds on useless retries.** Retry-with-backoff now only applies to genuinely transient conditions (HTTP 429/500/502/503/504, or a network-level error). Permanent 4xx errors fail immediately and surface F5's own error message directly.
- Negative/garbage progress percentage when F5's response didn't include a usable `total_hits` mid-download.
- A duplicate, dead option in the Sort Order dropdown.
- Stale hardcoded version numbers in the UI that didn't match the running app version.

### Changed
- **Query Builder removed.** Its Firewall/Security fields were based on fields present in a *returned* log record, not F5's actual documented *queryable* fields — which is a different, shorter list per F5's own schema (`site`, `src_ip`, `dst_ip`, `policy_hits.policy`, `policy_hits.policy_rule`, `policy_hits.result` for Firewall; different lists for Access and Audit). Advanced Query is now the single filtering mechanism, with F5's actual documented allowed fields shown inline per log type, plus working examples sourced directly from F5's schema text.
- Default sort order changed to Ascending (oldest first).
- All dropdowns re-themed to match the app's light/dark UI instead of the browser's native style.
- Date/time range fields are now native date-and-time pickers instead of free-text RFC3339 entry.
- Time range presets consolidated into a single dropdown (with a Custom option) instead of a row of buttons.
- Output directory now has a native OS folder-browser button, in addition to manual typing/pasting.
- Progress bar made visually heavier (18px → 32px).
- Renamed the app from "F5 XC Access Log Tool" to "F5 XC Log Downloader" to reflect that it handles all three log types, not just Access.
- "Create JSON backup" renamed to "Save full JSON copy," with a note clarifying that a separate `.debug.log` activity log is *always* written regardless of that checkbox — this was previously a common point of confusion.
- Configuration Backups card moved to the top of the page (it was already labeled "1" but rendered second).
- CSV "Common fields" preset updated to use field names that match F5's actual Firewall/Security log schema (`action`, `sec_event_type`, `waf_mode`, `app_firewall_name`, etc.) rather than an assumed set that didn't align with the real schema.

### Added
- **"Check Range"** — a one-click probe (single-record query) that reports F5 XC's matching record count or exact rejection reason for the current Host/Namespace/Token/Time Range/Query, without running a full download.
- A note next to the Pagination option about F5's confirmed 2-minute `scroll_id` expiry window, since a long pause could otherwise silently break a large download.
- Display of which configuration file/source is currently loaded, under Configuration Backups.
- Client-side warning when the selected time range's start time is likely too old for F5 XC to accept, based on empirically-confirmed behavior (see "Notes on an undocumented API limit" below).

This release consolidates a series of fixes and UI changes made during iterative development prior to the first public release — see the sections below for the most notable technical finding along the way.

---

## Notes on the 8-day start_time restriction

While testing WAF security events, the app's `FirewallLogQuery` requests were rejected when `start_time` was more than about 8 days in the past. Narrowing the window did not help, so the limit was not about range width. Comparing failing and succeeding requests against the current time showed a rolling boundary on the age of `start_time`.

The XC Console showed up to 30 days of the same events, so the next question was whether the console used a different API. F5 TAC confirmed that security events must be queried with the Application Security Monitoring API (`SecurityEventsQuery` / `SecurityEventsScrollQuery`). Version 1.1.0 uses that API. The `FirewallLogQuery` restriction is not part of this API.

The **"Check Range"** feature is still useful for checking any log type and time range with a single-record request before a full download.


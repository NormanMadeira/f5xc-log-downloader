# Changelog

## v1.0.0 (current) — Initial public release

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

## Notes on an undocumented F5 XC API limit

While debugging a large download that stopped after exactly one batch, testing surfaced a real but **undocumented** constraint: F5 XC's Log Query V2 API rejects requests where the query's `start_time` is more than a certain number of days in the past — independent of how wide the requested time window is.

This was initially misdiagnosed twice before being correctly identified:

1. **First theory:** the total *range width* (`end_time - start_time`) was capped. This fit the first failing request (a wide, multi-day range).
2. **Disproven by a second test:** a request with a narrow 24-hour window, but with `start_time` still several days old, was *also* rejected with the identical error message — ruling out "width" as the cause.
3. **Correct theory, confirmed:** the constraint is a rolling window on how old `start_time` is allowed to be *relative to the time of the request*, not the width of the window. Comparing failing vs. succeeding requests' `start_time` ages against "now" confirmed this cleanly.

A full export of F5's own rendered API documentation was checked directly for any mention of "retention," "days," or "maximum supported" in the relevant operation schemas — zero matches. So this limit is real (confirmed through direct testing) but is not part of F5's published API contract for these operations. It also does not appear to be a single universal number across all three log types — in testing, Audit logs successfully returned data further back than Firewall logs did under the same conditions.

The **"Check Range"** feature exists specifically to make probing this boundary fast — a single-record request instead of a full, multi-minute download attempt.

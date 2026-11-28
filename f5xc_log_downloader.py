import sys

# Native folder-picker helper mode: when run as "<this> --_browse_dialog_helper [initial_dir]"
# it opens the Windows folder dialog, prints the chosen folder, and exits without starting Flask.
_BROWSE_HELPER_FLAG = '--_browse_dialog_helper'
if len(sys.argv) >= 2 and sys.argv[1] == _BROWSE_HELPER_FLAG:
    try:
        import tkinter as tk
        from tkinter import filedialog
        initial = sys.argv[2] if len(sys.argv) > 2 else ''
        root = tk.Tk(); root.withdraw()
        try:
            root.attributes('-topmost', True)
        except Exception:
            pass
        chosen = filedialog.askdirectory(initialdir=initial or None, title="Select output folder", mustexist=True)
        root.destroy()
        sys.stdout.write(chosen or '')
    except Exception as e:
        sys.stderr.write(f"Could not open the folder picker: {e}\n")
    sys.exit(0)

from flask import Flask, render_template_string, request, jsonify
from pathlib import Path
import csv, json, os, re, subprocess, sys, threading, time, traceback
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
import requests

APP_VERSION = "2.0.0"
INDEX_HTML = r'''<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>F5 XC Log Downloader V{{ version }}</title>
<style>
:root{
 --bg:#f5f7fb;--surface:#fff;--surface-soft:#f8fafc;--surface-blue:#eef5ff;
 --text:#182230;--muted:#667085;--line:#dfe5ee;--accent:#2563eb;--accent-hover:#1d4ed8;
 --good:#15803d;--warn:#b45309;--bad:#dc2626;--code:#0a1020;--code-text:#d8e0ec;
 --shadow:0 8px 28px rgba(16,24,40,.055);--shadow-hover:0 12px 34px rgba(16,24,40,.09);
 color-scheme:light
}
html[data-theme=dark]{
 --bg:#0b1120;--surface:#111a2c;--surface-soft:#172237;--surface-blue:#132746;
 --text:#edf2f7;--muted:#9aa9bf;--line:#293850;--accent:#60a5fa;--accent-hover:#93c5fd;
 --good:#4ade80;--warn:#fbbf24;--bad:#f87171;--code:#070b14;--code-text:#dbe5f2;
 --shadow:0 10px 32px rgba(0,0,0,.22);--shadow-hover:0 15px 40px rgba(0,0,0,.3);
 color-scheme:dark
}
*{box-sizing:border-box}
body{
 margin:0;background:var(--bg);color:var(--text);
 font:14px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial;
 transition:background .2s,color .2s
}
body:before{content:"";position:fixed;inset:0;pointer-events:none;background:radial-gradient(circle at 85% 0%,#dbeafe55,transparent 30%)}
html[data-theme=dark] body:before{background:radial-gradient(circle at 85% 0%,#1e3a8a33,transparent 30%)}
.header{
 position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--surface) 93%,transparent);
 backdrop-filter:blur(14px);border-bottom:1px solid var(--line)
}
.header-inner{max-width:1240px;margin:auto;padding:15px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}
.brand{display:flex;align-items:center;gap:12px}.brand-icon{
 width:42px;height:42px;border-radius:12px;display:grid;place-items:center;color:#fff;font-weight:850;
 background:linear-gradient(135deg,#2563eb,#7c3aed);box-shadow:0 8px 18px #2563eb2b
}
.brand h1{margin:0;font-size:18px;letter-spacing:-.2px}.brand small{color:var(--muted);font-size:11px}
.top-actions{display:flex;align-items:center;gap:10px}
.theme{display:flex;border:1px solid var(--line);border-radius:10px;overflow:hidden;background:var(--surface)}
.theme button{border:0;background:transparent;color:var(--muted);padding:8px 11px;cursor:pointer}.theme button.active{background:var(--accent);color:#fff}
main{max-width:1240px;margin:26px auto;padding:0 20px 55px;position:relative}
.hero{margin:0 0 20px}.hero h2{font-size:28px;line-height:1.2;margin:0 0 5px;letter-spacing:-.5px}.hero p{margin:0;color:var(--muted)}
.card{
 background:var(--surface);border:1px solid var(--line);border-radius:15px;padding:21px 22px;
 margin-bottom:15px;box-shadow:var(--shadow)
}
.card{border-left:4px solid var(--accent)}
.card:hover{box-shadow:var(--shadow-hover)}
.section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:17px}
.section-title{display:flex;align-items:flex-start;gap:11px}.num{flex:0 0 auto;width:36px;height:36px;border-radius:11px;background:linear-gradient(135deg,var(--accent),#7c3aed);color:#fff;display:grid;place-items:center;font-weight:800;font-size:16px;box-shadow:0 6px 16px #2563eb33}
.title-text h3{margin:2px 0 4px;font-size:20px;font-weight:750;letter-spacing:-.3px;color:var(--text)}.hint{font-size:12px;color:var(--muted);font-weight:450;max-width:760px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}.full{grid-column:1/-1}
label.field{display:block;font-weight:650;margin-bottom:6px}
input[type=text],input[type=password],input[type=datetime-local],input:not([type]),textarea{
 width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--surface);
 color:var(--text);outline:0;transition:border .15s,box-shadow .15s;font-family:inherit;font-size:14px
}
input:focus,textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px #2563eb18}
textarea{min-height:96px;resize:vertical;font:12px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.help{color:var(--muted);font-size:12px;margin-top:6px}
.choice-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.choice-grid.two{grid-template-columns:repeat(2,1fr)}
.choice{position:relative}.choice input{position:absolute;opacity:0;pointer-events:none}.choice label{
 display:block;border:1px solid var(--line);border-radius:11px;background:var(--surface-soft);padding:11px 13px;cursor:pointer;
 transition:.15s
}.choice label strong{display:block;font-size:13px}.choice label span{display:block;color:var(--muted);font-size:11px;margin-top:2px}
.choice input:checked+label{border-color:var(--accent);background:#2563eb12;box-shadow:inset 0 0 0 1px var(--accent);color:var(--accent)}
.choice input:checked+label span{color:var(--muted)}
.query-preview{font:12px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--surface-soft);border:1px solid var(--line);border-radius:9px;padding:11px;white-space:pre-wrap;word-break:break-all}
.inline-checks{display:flex;gap:20px;flex-wrap:wrap}.inline-check{display:flex;align-items:center;gap:7px;font-weight:550}.inline-check input{accent-color:var(--accent)}
.btn{
 border:1px solid var(--line);background:var(--surface);color:var(--text);padding:9px 12px;border-radius:9px;cursor:pointer;font-weight:600
}.btn:hover{border-color:var(--accent)}.btn.primary{
 background:linear-gradient(135deg,var(--accent),var(--accent-hover));color:#fff;border-color:transparent;
 padding:12px 19px;font-weight:750;box-shadow:0 7px 17px #2563eb2b
}.btn.danger{color:var(--bad)}
.backup-layout{display:grid;grid-template-columns:1.2fr 1fr;gap:14px}.backup-box{
 border:1px solid var(--line);border-radius:12px;padding:15px;background:var(--surface-soft)
}.backup-box h4{margin:0 0 3px}.backup-box p{margin:0 0 11px;color:var(--muted);font-size:12px}
.file-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.file-row input[type=file]{display:none}
.status{padding:11px 13px;border-radius:10px;background:var(--surface-soft);border:1px solid var(--line)}
.success{color:var(--good)}.warning{color:var(--warn)}.error{color:var(--bad)}
.action-row{display:flex;gap:9px;flex-wrap:wrap}.action-row .hidden{display:none!important}
.cond-row{display:grid;grid-template-columns:1.6fr 1fr 1.6fr 1fr auto;gap:8px;align-items:start;margin-bottom:8px}
.cond-row input[type=text]{margin:0}
.progress-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;font-size:12px;color:var(--muted)}.progress-head strong{font-size:18px;color:var(--text)}
.modern-progress{height:32px;border-radius:99px;padding:3px;background:var(--surface-soft);box-shadow:inset 0 1px 3px rgba(0,0,0,.08)}.modern-progress .bar{height:100%;border-radius:99px;position:relative;overflow:hidden;background:linear-gradient(90deg,var(--accent),#7c3aed);display:flex;align-items:center;justify-content:flex-end;min-width:0;transition:width .25s}
.modern-progress .bar:after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 25%,rgba(255,255,255,.28) 50%,transparent 75%);animation:shine 1.4s linear infinite}
@keyframes shine{from{transform:translateX(-100%)}to{transform:translateX(100%)}}
.progress-sub{display:flex;justify-content:space-between;margin-top:7px;font-size:11px;color:var(--muted)}
code{font:11px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--surface-soft);border:1px solid var(--line);padding:2px 4px;border-radius:4px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:13px}.stat{background:var(--surface-soft);border:1px solid var(--line);border-radius:11px;padding:12px}.stat span{font-size:11px;color:var(--muted)}.stat b{display:block;font-size:18px;margin-top:2px}
.result-file{padding:10px 12px;background:var(--surface-soft);border:1px solid var(--line);border-radius:9px;margin-top:7px;font:12px ui-monospace,SFMono-Regular,Menlo,monospace;word-break:break-all}
.log{background:var(--code);color:var(--code-text);border-radius:11px;padding:12px;height:310px;overflow:auto;font:12px/1.65 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.log-line{display:block;min-height:20px;padding:1px 0;border-bottom:1px solid #ffffff0c;white-space:pre-wrap}
.hidden{display:none!important}
/* Themed dropdown (replaces native <select> rendering) */
select.xdd-native{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;border:0!important;white-space:nowrap!important}
.xdd{position:relative}
.xdd-btn{width:100%;text-align:left;padding:10px 34px 10px 12px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--text);cursor:pointer;font:inherit;position:relative}
.xdd-btn:after{content:"";position:absolute;right:13px;top:50%;width:8px;height:8px;border-right:2px solid var(--muted);border-bottom:2px solid var(--muted);transform:translateY(-65%) rotate(45deg);pointer-events:none}
.xdd-btn:hover{border-color:var(--accent)}
.xdd.open .xdd-btn{border-color:var(--accent);box-shadow:0 0 0 3px #2563eb18}
.xdd-panel{display:none;position:absolute;left:0;right:0;top:calc(100% + 6px);background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow-hover);z-index:40;max-height:280px;overflow:auto;padding:6px}
.xdd.open .xdd-panel{display:block}
.xdd-opt{padding:9px 11px;border-radius:8px;cursor:pointer;font-size:13.5px}
.xdd-search{position:sticky;top:0;z-index:1;width:100%;margin-bottom:6px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--text);font:inherit;font-size:13px}
.xdd-opt:hover{background:var(--surface-soft)}
.xdd-opt.sel{background:#2563eb12;color:var(--accent);font-weight:650}
.modal-backdrop{position:fixed;inset:0;background:#0008;z-index:60;display:grid;place-items:center;padding:20px}.modal{
 width:min(650px,100%);max-height:86vh;overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:15px;padding:22px;box-shadow:0 25px 70px #0006
}.modal section{padding:12px 0;border-bottom:1px solid var(--line)}.modal section:last-child{border-bottom:0}.modal p{color:var(--muted);margin:5px 0 0}
@media(max-width:850px){.grid,.backup-layout{grid-template-columns:1fr}.choice-grid,.choice-grid.two{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}}
</style>
</head>
<body>
<header class="header"><div class="header-inner">
 <div class="brand"><div class="brand-icon">F5</div><div><h1>F5 XC Log Downloader</h1><small>Version {{ version }}</small></div></div>
 <div class="top-actions"><div class="theme">
  <button id="lightBtn" onclick="setTheme('light')">☀ Light</button><button id="darkBtn" onclick="setTheme('dark')">☾ Dark</button><button id="systemBtn" onclick="setTheme('system')">⚙ System</button>
 </div></div>
</div></header>

<main>
<div class="hero"><h2>F5 XC Log Downloader</h2><p>Download Access, Security Events (WAF), or Audit logs from F5 Distributed Cloud and export them to CSV.</p></div>

<form id="form">

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">1</div><div class="title-text"><h3>Configuration Backups</h3><div class="hint">Save or share non-sensitive settings so another user can reproduce the same query quickly. API tokens are never included.</div></div></div></div>
 <div class="backup-layout">
  <div class="backup-box"><h4>Share this configuration</h4><p>Exports tenant, namespace, query, pagination, CSV preferences, output path, and logging preferences. Credentials are excluded.</p><button type="button" class="btn" onclick="exportConfig()">↓ Download Config</button></div>
  <div class="backup-box"><h4>Restore a configuration</h4><p>Select a previously exported JSON file. Your API token will remain blank and must be entered separately.</p><div class="file-row"><input type="file" id="configFile" accept=".json"><button type="button" class="btn" onclick="$('configFile').click()">↑ Restore Config</button><button type="button" class="btn danger" onclick="clearConfig()">Clear Saved</button></div></div>
 </div>
 <div id="backupStatus" class="help"></div>
 <div id="activeConfigSource" class="help">{% if config %}Currently loaded from: {{ config_path }}{% endif %}</div>
</div>

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">2</div><div class="title-text"><h3>Log Type</h3><div class="hint">Choose which F5 XC log API to query. Access logs cover application traffic, Security Events contain WAF security events, and Audit logs record configuration/API activity.</div></div></div></div>
 <div class="choice-grid">
  <div class="choice"><input type="radio" id="typeAccess" name="log_type" value="access" checked><label for="typeAccess"><strong>Access Logs</strong><span>Application requests and responses</span></label></div>
  <div class="choice"><input type="radio" id="typeSecurity" name="log_type" value="security"><label for="typeSecurity"><strong>Security Events (WAF)</strong><span>WAF security events (Security Events API)</span></label></div>
  <div class="choice"><input type="radio" id="typeAudit" name="log_type" value="audit"><label for="typeAudit"><strong>Audit Logs</strong><span>Configuration and API activity</span></label></div>
 </div>
</div>

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">3</div><div class="title-text"><h3>F5 XC Connection</h3><div class="hint">Enter the tenant and namespace you want to query. Your API token is used only for the current download and is never stored.</div></div></div></div>
 <div class="grid">
  <div><label class="field">Tenant hostname</label><input id="host" required value="{{ config.get('host','') }}" placeholder="<tenantname>.console.ves.volterra.io"></div>
  <div><label class="field">Namespace</label><input id="namespace" required value="{{ config.get('namespace','default') }}"></div>
  <div class="full"><label class="field">API token</label><input id="token" type="password" required placeholder="Enter API token"><div class="help">Credential is sent to the local backend for the API request and is not written to configuration backups.</div></div>
 </div>
</div>

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">4</div><div class="title-text"><h3>Time Range</h3><div class="hint">Pick a quick range or choose Custom and set the exact start/end date and time. A smaller window is recommended for your first test.</div></div></div></div>
 <div class="grid">
  <div class="full">
   <label class="field">Quick range</label>
   <select id="range_preset" class="xdd-native">
    <option value="10">Last 10 minutes</option>
    <option value="30">Last 30 minutes</option>
    <option value="60">Last 1 hour</option>
    <option value="360">Last 6 hours</option>
    <option value="720">Last 12 hours</option>
    <option value="1440">Last 24 hours</option>
    <option value="10080">Last 7 days</option>
    <option value="20160">Last 14 days</option>
    <option value="43200">Last 30 days</option>
    <option value="today">Today</option>
    <option value="yesterday">Yesterday</option>
    <option value="custom">Custom</option>
   </select>
  </div>
  <div class="full"><label class="field">Time input</label>
    <div class="choice-grid two">
      <div class="choice"><input type="radio" id="tzIST" name="timeZone" value="IST" checked><label for="tzIST"><strong>IST (UTC+05:30)</strong><span>Recommended default</span></label></div>
      <div class="choice"><input type="radio" id="tzUTC" name="timeZone" value="UTC"><label for="tzUTC"><strong>UTC</strong><span>Enter timestamps directly in UTC</span></label></div>
    </div>
    <div class="help">Click a field to open the date &amp; time picker, or type the value directly. When IST is selected, the tool converts the entered time to UTC before calling F5 XC.</div>
  </div>
  <div><label class="field" id="start_label">Start (IST)</label><input type="datetime-local" step="1" id="start" required></div>
  <div><label class="field" id="end_label">End (IST)</label><input type="datetime-local" step="1" id="end" required></div>
  <div class="full"><div id="rangeNotice" class="hidden"></div><div class="help" id="utc_preview">API time preview: enter a start and end time to see the UTC values that will be sent to F5 XC.</div></div>
</div>
</div>

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">5</div><div class="title-text"><h3>Query</h3><div class="hint">All matching logs is the default. Use the Filter builder to add conditions without typing query syntax, or Advanced Query to type it yourself.</div></div></div></div>
 <div class="choice-grid">
  <div class="choice"><input type="radio" id="qall" name="qmode" value="all" checked><label for="qall"><strong>All matching logs</strong><span>No additional filter</span></label></div>
  <div class="choice"><input type="radio" id="qadvanced" name="qmode" value="advanced"><label for="qadvanced"><strong>Advanced Query</strong><span>Enter XC syntax directly</span></label></div>
  <div class="choice"><input type="radio" id="qbuilder" name="qmode" value="builder"><label for="qbuilder"><strong>Filter builder</strong><span>Add conditions with a few clicks</span></label></div>
 </div><br>
 <div id="advanced" class="hidden">
 <label class="field">Advanced F5 XC query</label>
 <textarea id="advanced_query" placeholder='{vh_name="uat-load-balancer-3"}'></textarea>
 <div class="help">
  <b>Syntax:</b> <code>{field="value"}</code>, comma-separated matchers are combined with logical <b>AND</b>. Operators: <code>=</code> equal, <code>!=</code> not equal.<br><br>
  <b>Only the fields below can be used in a query filter</b> for each log type (per F5's own API schema - this is the full allowed list, not just examples; it's a different, shorter list than the many fields present in a returned log record):<br>
  <b>Access:</b> app_type, vh_name, src_site, src, src_instance, dst_site, dst, dst_instance, method, req_path, rsp_code, browser_type, city, country, device_type<br>
  &nbsp;&nbsp;e.g. <code>{src="service1",dst="service2"}</code> &nbsp; <code>{vh_name="vh1",rsp_code!=P0"}</code><br>
  <b>Security Events (WAF):</b> vh_name, sec_event_type, src_site, city, country<br>
  &nbsp;&nbsp;e.g. <code>{vh_name="vh1",sec_event_type="waf_sec_event"}</code> &nbsp; <code>{country="United States",city="California"}</code><br>
  <b>Audit:</b> user, src_site, src, src_instance, dst_site, dst, dst_instance, method, req_path, rsp_code<br>
  &nbsp;&nbsp;e.g. <code>{user="abc",rsp_code="404"}</code><br><br>
  Full schema reference (requires your XC API Developer Portal login):
  <a href="https://docs.cloud.f5.com/docs-v2/api/log#operation/ves.io.schema.log.CustomAPI.AccessLogQueryV2" target="_blank" rel="noopener">Access Log Query V2</a> ·
  <a href="https://docs.cloud.f5.com/docs-v2/api/app-security#operation/ves.io.schema.app_security.AppSecurityMonitoringAPI.SecurityEventsQuery" target="_blank" rel="noopener">Security Events Query</a> ·
  <a href="https://docs.cloud.f5.com/docs-v2/api/log#operation/ves.io.schema.log.CustomAPI.AuditLogQueryV2" target="_blank" rel="noopener">Audit Log Query V2</a>
 </div>
</div>
 <div id="builder" class="hidden">
 <div class="help" style="margin-bottom:10px">Every condition must match (AND). Pick a field, a condition and a value. Start from a template to fill in common conditions.</div>
 <div style="display:flex;gap:8px;align-items:center;margin-bottom:12px"><select id="tpl_select" class="xdd-native"></select></div>
 <div id="cond_rows"></div>
 <button type="button" class="btn" id="add_cond" style="margin-top:4px">+ Add condition</button>
 <button type="button" class="btn" id="ref_btn" style="margin-top:4px;margin-left:8px" onclick="openRef()">Field reference</button>
</div>
<br><label class="field">Query that will be sent</label><div id="preview" class="query-preview">&lt;ALL MATCHING LOGS&gt;</div>
</div>
<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">6</div><div class="title-text"><h3>Download Options</h3><div class="hint">F5 XC returns up to 500 records per response. Pagination retrieves additional batches and combines them into one CSV file. Search After is recommended for current F5 XC deployments; Scroll is retained as a legacy compatibility option.</div></div></div></div>
 <div class="grid">
  <div><label class="field">Sort order</label>
   <select id="sort" class="xdd-native">
    <option value="DESCENDING">Newest first (Descending)</option>
    <option value="ASCENDING" selected>Oldest first (Ascending)</option>
   </select>
   <div class="help">Controls the order of returned logs. Newest first is recommended for investigations.</div>
  </div>
  <div><label class="field">Pagination</label>
   <div class="choice-grid two">
    <div class="choice"><input type="radio" id="pSearch" name="paginationChoice" value="search_after" checked><label for="pSearch"><strong>Search After</strong><span>Recommended default</span></label></div>
    <div class="choice"><input type="radio" id="pScroll" name="paginationChoice" value="scroll"><label for="pScroll"><strong>Scroll</strong><span>Legacy / compatibility</span></label></div>
   </div>
   <div class="help">Per F5's API schema, a <code>scroll_id</code> is only valid for 2 minutes between requests. If Search After falls back to scroll continuation (see log), pausing for longer than ~2 minutes may cause the download to fail and need restarting.</div>
  </div>
  <div><label class="field">CSV fields</label>
   <select id="csv_mode" class="xdd-native">
    <option value="1">All fields</option>
    <option value="2">Common fields</option>
    <option value="3">Custom fields</option>
   </select>
   <div class="help">All fields is best for investigation; Common fields creates a smaller operational CSV.</div>
  </div>
  <div id="custom_wrap" class="full hidden"><label class="field">Custom CSV fields</label><input id="custom_fields" placeholder="time,vh_name,method,req_path,rsp_code"></div>
  <div><label class="field">Output directory</label><div style="display:flex;gap:8px"><input id="output_dir" required value="{{ config.get('output_dir','') }}" placeholder="<output-directory>" style="flex:1"><button type="button" class="btn" id="browseBtn" onclick="browseFolder()">Browse…</button></div><div class="help">The tool removes common invisible Unicode formatting characters from pasted paths.</div></div>
  <div><label class="field">Logging detail</label>
   <select id="log_level" class="xdd-native">
    <option value="1">Normal</option>
    <option value="2">Extreme</option>
   </select>
   <div class="help">Extreme shows API requests, responses, batches, retries, and validation details.</div>
  </div>
  <div class="full inline-checks"><label class="inline-check"><input type="checkbox" id="keep_json" checked> Save full JSON copy (all fields, all records)</label><label class="inline-check"><input type="checkbox" id="open_after" checked> Open CSV when complete</label></div>
  <div class="full help">The CSV is always created. "Save full JSON copy" additionally writes a <code>.json</code> file with every field of every downloaded record. A separate <code>.debug.log</code> activity/troubleshooting log (API requests, retries, batch progress) is always saved automatically regardless of this setting.</div>
 </div>
</div>

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">7</div><div class="title-text"><h3>Download & Results</h3><div class="hint">Start the download and watch live progress. The tool validates the downloaded count against F5 XC total_hits when available.</div></div></div></div>
 <div class="action-row">
  <button class="btn primary" id="download" type="submit">DOWNLOAD LOGS</button>
  <button class="btn" id="checkRangeBtn" type="button" onclick="checkRange()">🔍 Check Range</button>
  <button class="btn hidden" id="pauseBtn" type="button" onclick="togglePause()">Ⅱ Pause</button>
  <button class="btn danger hidden" id="stopBtn" type="button" onclick="stopDownload()">■ Stop</button>
</div>
 <div id="status" class="status" style="margin-top:13px">Ready.</div>
 <div id="progress_wrap" class="hidden" style="margin-top:15px">
   <div class="progress-head"><span id="progress_label">Downloading</span><strong id="percent">0%</strong></div>
   <div class="modern-progress"><div class="bar" id="bar"></div></div>
   <div class="progress-sub"><span id="progress_received">0 of - records</span><span id="progress_state">Starting</span></div>
 </div>
 <div class="stats">
  <div class="stat"><span>Downloaded</span><b id="received">0</b></div><div class="stat"><span>F5 total_hits</span><b id="total">-</b></div>
  <div class="stat"><span>Batch</span><b id="batch">0</b></div><div class="stat"><span>Rate</span><b id="rate">-</b></div>
 </div>
 <div id="results" class="hidden" style="margin-top:16px"><h3>Output files</h3><div id="files"></div></div>
</div>

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">8</div><div class="title-text"><h3>Detailed Log</h3><div class="hint">Each event appears on its own line. Use Extreme logging when troubleshooting API, authentication, pagination, or count issues.</div></div></div><button type="button" class="btn" onclick="clearLog()">Clear</button></div>
 <div id="log" class="log"><span class="log-line">No activity yet.</span></div>
</div>
</form>

<div id="refModal" class="modal-backdrop hidden" onclick="if(event.target===this)closeRef()">
  <div class="modal" style="width:min(820px,100%)">
   <div style="display:flex;justify-content:space-between;align-items:center;gap:12px"><h3 style="margin:0">Field reference: <span id="refLt"></span></h3><button type="button" class="btn" onclick="closeRef()">Close</button></div>
   <input id="refSearch" placeholder="Search by name, field key or description" style="margin:12px 0;width:100%">
   <div id="refList" style="max-height:60vh;overflow:auto"></div>
  </div>
</div>
</main>

<script>
const $=id=>document.getElementById(id);
const CATALOG={{ catalog_json|safe }};
const TEMPLATES={{ templates_json|safe }};
const themeQuery=window.matchMedia('(prefers-color-scheme: dark)');
function resolveTheme(pref,prefersDark){return pref==='system'?(prefersDark?'dark':'light'):pref}
function applyTheme(){
 const pref=localStorage.getItem('f5xc_theme')||'system';
 document.documentElement.dataset.theme=resolveTheme(pref,themeQuery.matches);
 ['light','dark','system'].forEach(t=>$(t+'Btn').classList.toggle('active',t===pref));
}
function setTheme(t){localStorage.setItem('f5xc_theme',t);applyTheme()}
themeQuery.addEventListener('change',()=>{if((localStorage.getItem('f5xc_theme')||'system')==='system')applyTheme()});
applyTheme();

/* ---- Themed dropdown: wraps a hidden native <select> so existing .value / onchange code keeps working ---- */
function enhanceSelect(sel){
 const wrap=document.createElement('div');wrap.className='xdd';
 const btn=document.createElement('button');btn.type='button';btn.className='xdd-btn';
 const panel=document.createElement('div');panel.className='xdd-panel';
 let search=null;
 if(sel.options.length>=1){
  search=document.createElement('input');search.type='text';search.className='xdd-search';search.placeholder='Search…';
  search.onclick=e=>e.stopPropagation();
  search.oninput=()=>{const q=search.value.toLowerCase().trim(),u=q.replace(/ /g,'_');
   panel.querySelectorAll('.xdd-opt').forEach(d=>{const hit=!q||d.dataset.search.includes(q)||d.dataset.search.includes(u);d.style.display=hit?'':'none'})};
  panel.appendChild(search);
 }
 function sync(){
  const o=sel.options[sel.selectedIndex];
  btn.textContent=o?o.text:'';
  panel.querySelectorAll('.xdd-opt').forEach(d=>d.classList.toggle('sel',d.dataset.value===sel.value));
 }
 [...sel.options].forEach(o=>{
  const d=document.createElement('div');d.className='xdd-opt'+(o.selected?' sel':'');d.textContent=o.text;d.dataset.value=o.value;d.dataset.search=(o.dataset.search||(o.text+' '+o.value)).toLowerCase();
  d.onclick=()=>{sel.value=o.value;sync();sel.dispatchEvent(new Event('change',{bubbles:true}));wrap.classList.remove('open')};
  panel.appendChild(d);
 });
 btn.onclick=e=>{e.stopPropagation();document.querySelectorAll('.xdd.open').forEach(x=>{if(x!==wrap)x.classList.remove('open')});wrap.classList.toggle('open');
  if(search&&wrap.classList.contains('open')){search.value='';search.oninput();search.focus()}};
 wrap.appendChild(btn);wrap.appendChild(panel);
 sel.parentNode.insertBefore(wrap,sel.nextSibling);
 sync();
 sel._xddSync=sync;
 return wrap;
}
document.addEventListener('click',()=>document.querySelectorAll('.xdd.open').forEach(x=>x.classList.remove('open')));
document.addEventListener('keydown',e=>{if(e.key==='Escape'){document.querySelectorAll('.xdd.open').forEach(x=>x.classList.remove('open'));closeRef()}});
document.querySelectorAll('select.xdd-native').forEach(enhanceSelect);

/* ---- Time range ---- */
// Retention per log type: Access logs 7 days; Audit and Security Events 30 days. Maximum range is 30 days.
const RETENTION_DAYS={access:7,audit:30,security:30};
const MAX_RANGE_DAYS=30, TOL_MS=60000;
let activePresetMinutes=10, jobRunning=false;
function validateRange(){
 const lt=selectedType(), zone=document.querySelector('input[name=timeZone]:checked').value;
 const s=parseUserTime($('start').value,zone), e=parseUserTime($('end').value,zone);
 const errors=[], notes=[];
 if(!s||!e) return {errors:['Enter a start and end date/time.'],notes};
 const st=new Date(s).getTime(), en=new Date(e).getTime(), now=Date.now();
 if(en<=st) errors.push('The end time must be after the start time.');
 const spanDays=(en-st)/86400000;
 if(spanDays>MAX_RANGE_DAYS+1e-9) errors.push('A range longer than 30 days is not allowed. Choose a range of 30 days or less.');
 if(lt==='access'&&spanDays>7+1e-9) notes.push('Beyond 7 days, Access logs cannot be retrieved. Only Security Events and Audit logs can be retrieved up to 30 days.');
 const ret=RETENTION_DAYS[lt]||30;
 if(now-st>ret*86400000+TOL_MS){
   const name=lt==='access'?'Access logs':lt==='audit'?'Audit logs':'Security Events';
   errors.push(name+' can only be retrieved for the last '+ret+' days. Move the start time forward, or use the '+(ret===7?'Last 7 days':'Last 30 days')+' preset.');
 }
 return {errors,notes};
}
function updateRangeNotice(){
 const r=validateRange(), box=$('rangeNotice');
 const lines=[...r.errors.map(t=>({t,k:'error'})),...r.notes.map(t=>({t,k:'warning'}))];
 box.innerHTML='';
 lines.forEach(l=>{const d=document.createElement('div');d.className='status '+l.k;d.style.marginTop='6px';d.textContent=(l.k==='error'?'✕ ':'⚠ ')+l.t;box.appendChild(d)});
 box.classList.toggle('hidden',lines.length===0);
 if(!jobRunning)$('download').disabled=r.errors.length>0;
}
function refreshRelativeRange(){ if(activePresetMinutes) setRange(activePresetMinutes); }
function parseUserTime(v,zone){
 const s=(v||'').trim();if(!s)return null;
 let d;
 if(/[zZ]|[+-]\d\d:\d\d$/.test(s)) d=new Date(s);
 else d=new Date(s+(zone==='IST'?'+05:30':'Z'));
 if(isNaN(d.getTime()))return null;
 return d.toISOString().replace('.000Z','Z');
}
function updateTimeLabels(){
 const z=document.querySelector('input[name=timeZone]:checked').value;
 $('start_label').textContent='Start ('+z+')';$('end_label').textContent='End ('+z+')';
 updateTimePreview();
}
function updateTimePreview(){
 const z=document.querySelector('input[name=timeZone]:checked').value;
 const s=parseUserTime($('start').value,z),e=parseUserTime($('end').value,z);
 $('utc_preview').textContent=(s&&e)?'API time preview: F5 XC will receive Start='+s+' | End='+e:'API time preview: enter a start and end time to see the UTC values that will be sent to F5 XC.';
}
function formatInputTime(d,zone){
 const x=new Date(d.getTime()+(zone==='IST'?330:0)*60000);
 return x.toISOString().slice(0,19);
}
let settingRangeProgrammatically=false;
function setRange(minutes){
 const e=new Date(),s=new Date(e.getTime()-minutes*60000),zone=document.querySelector('input[name=timeZone]:checked').value;
 settingRangeProgrammatically=true;
 $('start').value=formatInputTime(s,zone);$('end').value=formatInputTime(e,zone);
 settingRangeProgrammatically=false;
 updatePreview();updateTimePreview();updateRangeNotice();
}
function todayRange(){
 const n=new Date(),z=document.querySelector('input[name=timeZone]:checked').value,offset=z==='IST'?330:0,local=new Date(n.getTime()+offset*60000),e=new Date(Date.UTC(local.getUTCFullYear(),local.getUTCMonth(),local.getUTCDate())-offset*60000);
 settingRangeProgrammatically=true;
 $('start').value=formatInputTime(e,z);$('end').value=formatInputTime(n,z);
 settingRangeProgrammatically=false;
 updatePreview();updateTimePreview();updateRangeNotice();
}
function yesterdayRange(){
 const n=new Date(),z=document.querySelector('input[name=timeZone]:checked').value,offset=z==='IST'?330:0,local=new Date(n.getTime()+offset*60000),mid=new Date(Date.UTC(local.getUTCFullYear(),local.getUTCMonth(),local.getUTCDate())-offset*60000),s=new Date(mid.getTime()-86400000);
 settingRangeProgrammatically=true;
 $('start').value=formatInputTime(s,z);$('end').value=formatInputTime(mid,z);
 settingRangeProgrammatically=false;
 updatePreview();updateTimePreview();updateRangeNotice();
}
$('range_preset').onchange=()=>{
 const v=$('range_preset').value;
 activePresetMinutes=(v==='today'||v==='yesterday'||v==='custom')?null:+v;
 if(v==='custom'){updateRangeNotice();return}
 if(v==='today')todayRange();else if(v==='yesterday')yesterdayRange();else setRange(+v);
};
document.querySelectorAll('input[name=timeZone]').forEach(x=>x.onchange=()=>{
 const v=$('range_preset').value;
 if(v==='today')todayRange();else if(v==='yesterday')yesterdayRange();else if(v!=='custom')setRange(+v);
 updateTimeLabels();updateRangeNotice();
});
['start','end'].forEach(id=>$(id).addEventListener('input',()=>{
 if(!settingRangeProgrammatically){activePresetMinutes=null;$('range_preset').value='custom';$('range_preset')._xddSync()}
 updateTimePreview();updatePreview();updateRangeNotice();
}));
setRange(10);

/* ---- Log type / query mode ---- */
function selectedType(){return document.querySelector('input[name=log_type]:checked').value}
function refreshQueryMode(){
 const m=document.querySelector('input[name=qmode]:checked').value;
 $('advanced').classList.toggle('hidden',m!=='advanced');
 $('builder').classList.toggle('hidden',m!=='builder');
 updatePreview();
}
document.querySelectorAll('input[name=log_type]').forEach(x=>x.onchange=()=>{onLogTypeChanged();updateRangeNotice()});
document.querySelectorAll('input[name=qmode]').forEach(x=>x.onchange=refreshQueryMode);
$('advanced_query').addEventListener('input',updatePreview);
$('csv_mode').addEventListener('change',()=>$('custom_wrap').classList.toggle('hidden',$('csv_mode').value!=='3'));
/* ---- Filter builder (AND only). Pure helpers come first so they can be tested. ---- */
function escQ(v){return String(v).replace(/\\/g,'\\\\').replace(/"/g,'\\"')}
function builderQuery(rows){
 const parts=rows.filter(r=>r.field&&String(r.value).trim()!=='').map(r=>r.field+r.op+'"'+escQ(String(r.value).trim())+'"');
 return parts.length?'{'+parts.join(',')+'}':'';
}
function fieldsFor(lt){return (CATALOG.log_types&&CATALOG.log_types[lt])||[]}
function findField(lt,name){return fieldsFor(lt).find(f=>f.name===name)}
function labelOf(name,lt){const f=findField(lt,name);return f?f.label:name}
function builderError(rows,lt){
 for(const r of rows){
  if(!r.field) return 'Choose a field for every condition, or remove the empty row.';
  if(!findField(lt,r.field)) return 'The field "'+r.field+'" is not available for this log type. Remove that condition.';
  if(String(r.value).trim()==='') return 'Enter a value for "'+labelOf(r.field,lt)+'", or remove the row.';
 }
 return '';
}
function templateRows(tpl){return tpl.conditions.map(c=>({field:c.field,op:c.op,value:c.value||'',placeholder:c.placeholder||''}))}
let rows=[];
function renderRows(){
 const box=$('cond_rows'); if(!box)return;
 box.innerHTML='';
 const lt=selectedType();
 rows.forEach((r,i)=>{
  const row=document.createElement('div'); row.className='cond-row';
  const fs=document.createElement('select'); fs.className='xdd-native';
  const fp=document.createElement('option'); fp.value=''; fp.textContent='Choose a field…'; fs.appendChild(fp);
  fieldsFor(lt).forEach(f=>{const o=document.createElement('option');o.value=f.name;o.textContent=f.group+' · '+f.label;o.dataset.search=(f.label+' '+f.name);fs.appendChild(o)});
  fs.value=r.field;
  fs.onchange=()=>{r.field=fs.value;r.value='';renderRows();updatePreview()};
  row.appendChild(fs);
  const os=document.createElement('select'); os.className='xdd-native';
  [['=','Equals'],['!=','Not equals']].forEach(([v,t])=>{const o=document.createElement('option');o.value=v;o.textContent=t;os.appendChild(o)});
  os.value=r.op;
  os.onchange=()=>{r.op=os.value;updatePreview()};
  row.appendChild(os);
  const vi=document.createElement('input'); vi.type='text'; vi.value=r.value; vi.placeholder=r.placeholder||'Value';
  vi.oninput=()=>{r.value=vi.value;updatePreview()};
  row.appendChild(vi);
  const fd=findField(lt,r.field);
  if(fd&&fd.value_suggestions&&fd.value_suggestions.length){
    const ss=document.createElement('select'); ss.className='xdd-native';
    const sp=document.createElement('option'); sp.value=''; sp.textContent='Suggestions…'; ss.appendChild(sp);
    fd.value_suggestions.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=v;ss.appendChild(o)});
    ss.onchange=()=>{if(ss.value){r.value=ss.value;vi.value=ss.value;updatePreview()}};
    row.appendChild(ss);
  } else { row.appendChild(document.createElement('div')) }
  const del=document.createElement('button'); del.type='button'; del.className='btn danger'; del.textContent='✕'; del.title='Remove condition';
  del.onclick=()=>{rows.splice(i,1);renderRows();updatePreview()};
  row.appendChild(del);
  box.appendChild(row);
 });
 box.querySelectorAll('select.xdd-native').forEach(enhanceSelect);
}
function refreshTemplates(){
 const sel=$('tpl_select'); if(!sel)return;
 const w=sel.nextElementSibling; if(w&&w.classList.contains('xdd')) w.remove();
 sel.innerHTML='';
 const p=document.createElement('option'); p.value=''; p.textContent='Start from a template…'; sel.appendChild(p);
 ((TEMPLATES.templates||{})[selectedType()]||[]).forEach((t,i)=>{const o=document.createElement('option');o.value=String(i);o.textContent=t.name;sel.appendChild(o)});
 sel.value='';
 enhanceSelect(sel);
}
function onLogTypeChanged(){
 const lt=selectedType(), before=rows.length;
 rows=rows.filter(r=>r.field&&findField(lt,r.field));
 if(rows.length!==before) $('status').textContent='Some conditions were removed because those fields do not apply to this log type.';
 refreshTemplates(); renderRows(); updatePreview();
}
$('tpl_select').addEventListener('change',()=>{
 const v=$('tpl_select').value; if(v==='')return;
 const tpl=((TEMPLATES.templates||{})[selectedType()]||[])[+v];
 if(tpl){rows=rows.filter(r=>r.field||String(r.value).trim()!=='').concat(templateRows(tpl)); renderRows(); updatePreview()}
 $('tpl_select').value=''; if($('tpl_select')._xddSync)$('tpl_select')._xddSync();
});
$('add_cond').onclick=()=>{rows.push({field:'',op:'=',value:'',placeholder:''});renderRows();updatePreview()};
function openRef(){
 const lt=selectedType();
 $('refLt').textContent=lt==='access'?'Access logs':lt==='audit'?'Audit logs':'Security Events';
 $('refSearch').value=''; renderRef(); $('refModal').classList.remove('hidden'); $('refSearch').focus();
}
function closeRef(){const m=$('refModal'); if(m)m.classList.add('hidden')}
function renderRef(){
 const q=$('refSearch').value.toLowerCase().trim(), u=q.replace(/ /g,'_'), box=$('refList'); box.innerHTML='';
 fieldsFor(selectedType()).filter(f=>!q||(f.label+' '+f.name).toLowerCase().includes(q)||f.name.includes(u)).forEach(f=>{
  const d=document.createElement('div'); d.style.cssText='padding:10px 4px;border-bottom:1px solid var(--line)';
  const head=document.createElement('div');
  const b=document.createElement('b'); b.textContent=f.label;
  const c=document.createElement('code'); c.textContent=f.name; c.style.marginLeft='8px';
  const g=document.createElement('span'); g.className='help'; g.textContent='  '+f.group; g.style.marginLeft='8px';
  head.appendChild(b); head.appendChild(c); head.appendChild(g);
  const desc=document.createElement('div'); desc.className='help'; desc.textContent=f.description||'';
  d.appendChild(head); d.appendChild(desc); box.appendChild(d);
 });
 if(!box.children.length){box.innerHTML='<div class="help" style="padding:12px">No fields match that search.</div>'}
}
$('refSearch').addEventListener('input',renderRef);
function query(){
 const m=document.querySelector('input[name=qmode]:checked').value;
 if(m==='advanced') return $('advanced_query').value.trim();
 if(m==='builder') return builderQuery(rows);
 return '';
}
function updatePreview(){$('preview').textContent=query()||'<ALL MATCHING LOGS>'}
function collect(){return {log_type:selectedType(),host:$('host').value,namespace:$('namespace').value,token:$('token').value,start_time:parseUserTime($('start').value,document.querySelector('input[name=timeZone]:checked').value),end_time:parseUserTime($('end').value,document.querySelector('input[name=timeZone]:checked').value),query:query(),pagination:document.querySelector('input[name=paginationChoice]:checked').value,sort:$('sort').value,csv_mode:$('csv_mode').value,custom_fields:$('custom_fields').value,output_dir:$('output_dir').value,log_level:$('log_level').value,keep_json:$('keep_json').checked,open_after:$('open_after').checked,time_zone:document.querySelector('input[name=timeZone]:checked').value}}
let activeJob=null,paused=false;
$('form').onsubmit=async e=>{
 e.preventDefault();refreshRelativeRange();$('download').disabled=true;$('pauseBtn').classList.remove('hidden');$('stopBtn').classList.remove('hidden');$('pauseBtn').textContent='Ⅱ Pause';paused=false;
 $('progress_wrap').classList.remove('hidden');$('results').classList.add('hidden');$('status').textContent='Starting download...';$('status').className='status';clearLog();const payload=collect();
const be=(document.querySelector('input[name=qmode]:checked').value==='builder')?builderError(rows,selectedType()):'';
if(be){$('status').textContent=be;$('status').className='status error';$('download').disabled=false;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden');return}
const rv=validateRange();
if(rv.errors.length){$('status').textContent=rv.errors[0];$('status').className='status error';$('download').disabled=true;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden');updateRangeNotice();return}
jobRunning=true;
 if(!payload.start_time||!payload.end_time){$('status').textContent='Invalid time. Pick a valid start and end date/time.';$('status').className='status error';$('download').disabled=false;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden');return}
 try{const r=await fetch('/api/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();if(!r.ok)throw new Error(j.error||'Download failed');activeJob=j.job_id;poll(activeJob,payload)}
 catch(err){jobRunning=false;$('status').textContent=err.message;$('status').className='status error';$('download').disabled=false;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden')}
};
async function togglePause(){
 if(!activeJob)return;
 const url=paused?'/resume':'/pause';
 const r=await fetch('/api/job/'+activeJob+url,{method:'POST'});
 if(r.ok){paused=!paused;$('pauseBtn').textContent=paused?'▶ Resume':'Ⅱ Pause'}
}
async function stopDownload(){
 if(!activeJob)return;
 $('stopBtn').disabled=true;$('status').textContent='Stopping download...';
 await fetch('/api/job/'+activeJob+'/stop',{method:'POST'});
}
async function poll(id,payload){
 let j;
 try{const r=await fetch('/api/job/'+id);j=await r.json()}
 catch(err){setTimeout(()=>poll(id,payload),1200);return}
 $('received').textContent=(j.received||0).toLocaleString();$('total').textContent=j.total_hits??'-';$('batch').textContent=j.batch||0;
 const pct=Math.max(0,Math.min(100,Number(j.percent)||0));$('bar').style.width=pct.toFixed(2)+'%';$('percent').textContent=pct.toFixed(2)+'%';
 $('progress_received').textContent=(j.received||0).toLocaleString()+' of '+(j.total_hits??'-')+' records';$('progress_state').textContent=j.status==='paused'?'Paused':j.status==='stopping'?'Stopping':(j.message||'Working...');
 $('rate').textContent=j.rate?j.rate.toFixed(1)+' / sec':'-';$('status').textContent=j.message||'Working...';
 const el=$('log');el.innerHTML='';(j.log||[]).forEach(line=>{const sp=document.createElement('span');sp.className='log-line';sp.textContent=line;el.appendChild(sp)});el.scrollTop=el.scrollHeight;
 if(j.status==='complete'||j.status==='error'||j.status==='stopped'||j.status===undefined){
   jobRunning=false;updateRangeNotice();$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden');$('stopBtn').disabled=false;
   if(j.status==='complete'){$('status').className='status '+(j.complete?'success':'warning');$('results').classList.remove('hidden');$('files').innerHTML=`<div class="result-file">CSV: ${j.csv||''}</div>${j.json?`<div class="result-file">JSON: ${j.json}</div>`:''}<div class="result-file">Debug log: ${j.debug||''}</div>`;$('status').textContent=j.complete?'✓ Download complete — count validated.':'⚠ Download complete — count warning.';if(payload.open_after&&j.csv)fetch('/api/open',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:j.csv})})}
   else {$('status').className='status '+(j.status==='stopped'?'warning':'error');$('status').textContent=j.status==='stopped'?'Download stopped by user':'✕ '+(j.message||'The job could not be found. It may have failed to start — check the output directory and try again.')}
 }else setTimeout(()=>poll(id,payload),700)
};
function clearLog(){$('log').innerHTML='<span class="log-line">Log cleared.</span>'}
/* ---- Output folder browser (server-side, since this app and browser run on the same machine) ---- */
/* ---- Output folder: opens the native Windows folder picker on this machine ---- */
async function browseFolder(){
 const btn=$('browseBtn'); btn.disabled=true; const orig=btn.textContent; btn.textContent='Opening…';
 $('status').textContent='Choose a folder in the Windows folder picker.';$('status').className='status';
 try{
  const r=await fetch('/api/browse_native',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:$('output_dir').value})});
  const j=await r.json();
  if(j.ok&&j.path){$('output_dir').value=j.path;$('status').textContent='Output folder set.';$('status').className='status success'}
  else if(j.cancelled){$('status').textContent='Ready.';$('status').className='status'}
  else{$('status').textContent='Could not open the folder picker: '+(j.error||'unknown error')+'. You can still paste a path into the field.';$('status').className='status error'}
 }catch(e){$('status').textContent='Could not reach the local server: '+e.message;$('status').className='status error'}
 finally{btn.disabled=false;btn.textContent=orig}
}
/* ---- Check Range: quick single-record probe against F5 XC, without running a full download ---- */
async function checkRange(){
 refreshRelativeRange();const payload=collect();
 if(!payload.start_time||!payload.end_time){$('status').textContent='Pick a valid start and end date/time first.';$('status').className='status error';return}
 $('status').textContent='Checking range against F5 XC…';$('status').className='status';
 try{
  const r=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const j=await r.json();
  if(j.ok){$('status').textContent='✓ Range accepted — F5 XC reports '+(j.total_hits!=null?j.total_hits.toLocaleString():'an unknown number of')+' matching records available.';$('status').className='status success'}
  else{$('status').textContent='✕ F5 XC rejected this range: '+(j.error||'Unknown error');$('status').className='status error'}
 }catch(e){$('status').textContent='Could not reach the local server: '+e.message;$('status').className='status error'}
}
async function exportConfig(){
 const settings=collectConfigForBackup();
 try{
  const r=await fetch('/api/config/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({settings})});
  const j=await r.json();if(!r.ok)throw new Error(j.error||'Export failed');
  const blob=new Blob([JSON.stringify(j,null,2)],{type:'application/json'});
  const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='f5xc_log_tool_config.json';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
  $('backupStatus').textContent='Configuration downloaded successfully. API token was excluded.';
 }catch(err){$('backupStatus').textContent='Export failed: '+err.message}
}
function collectConfigForBackup(){
 return {host:$('host').value,namespace:$('namespace').value,query:query(),output_dir:$('output_dir').value,pagination:document.querySelector('input[name=paginationChoice]:checked')?.value||'search_after',sort:$('sort').value,csv_mode:$('csv_mode').value,custom_fields:$('custom_fields').value,open_after:$('open_after').checked,keep_json:$('keep_json').checked,log_level:$('log_level').value,log_type:selectedType(),time_zone:document.querySelector('input[name=timeZone]:checked')?.value||'IST'}
}
$('configFile').onchange=async e=>{
 const file=e.target.files[0];if(!file)return;
 try{
  const j=JSON.parse(await file.text());
  if(j.format!=='f5xc-log-tool-config'||!j.settings||typeof j.settings!=='object')throw new Error('This is not a valid F5 XC Log Downloader configuration backup.');
  const r=await fetch('/api/config/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(j)});
  const out=await r.json();if(!r.ok)throw new Error(out.error||'Import failed');
  applyConfig(out.settings);$('backupStatus').textContent='Configuration restored successfully. API token was not imported and must be entered separately.';$('activeConfigSource').textContent='Currently loaded from: '+file.name+' (restored just now — browsers only expose the file name, not its full folder path)';
 }catch(err){$('backupStatus').textContent='Restore failed: '+err.message}
 e.target.value='';
};
function applyConfig(c){
 if(c.host!=null)$('host').value=c.host;
 if(c.namespace!=null)$('namespace').value=c.namespace;
 if(c.output_dir!=null)$('output_dir').value=c.output_dir;
 if(c.log_type){const r=document.querySelector(`input[name=log_type][value="${c.log_type}"]`);if(r)r.checked=true}
 if(c.pagination){const r=document.querySelector(`input[name=paginationChoice][value="${c.pagination}"]`);if(r)r.checked=true}
 if(c.sort){$('sort').value=c.sort;$('sort')._xddSync&&$('sort')._xddSync()}
 if(c.csv_mode!=null){$('csv_mode').value=c.csv_mode;$('csv_mode')._xddSync&&$('csv_mode')._xddSync()}
 if(c.log_level!=null){$('log_level').value=c.log_level;$('log_level')._xddSync&&$('log_level')._xddSync()}
 if(c.keep_json!=null)$('keep_json').checked=!!c.keep_json;
 if(c.open_after!=null)$('open_after').checked=!!c.open_after;
 if(c.time_zone){const tz=document.querySelector(`input[name=timeZone][value="${c.time_zone}"]`);if(tz)tz.checked=true}
 if(c.query){document.querySelector('input[name=qmode][value="advanced"]').checked=true;$('advanced_query').value=c.query}
 refreshQueryMode();$('custom_wrap').classList.toggle('hidden',$('csv_mode').value!=='3');updatePreview();
}
async function clearConfig(){if(!confirm('Clear the saved configuration on this laptop?'))return;const r=await fetch('/api/config/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({settings:{}})});if(r.ok){$('backupStatus').textContent='Saved configuration cleared.';$('activeConfigSource').textContent=''}}
refreshTemplates();renderRows();refreshQueryMode();updatePreview();updateTimeLabels();updateTimePreview();updateRangeNotice();
</script>
</body>
</html>
'''
app = Flask(__name__)

HOME = Path.home()
CONFIG_FILE = HOME / ".f5xc_log_downloader_config.json"
jobs = {}
jobs_lock = threading.Lock()
job_controls = {}

def control_wait(job_id):
    c = job_controls.get(job_id)
    if not c:
        return
    while c["paused"].is_set() and not c["stop"].is_set():
        with jobs_lock:
            jobs[job_id].update(status="paused",message="Download paused")
        c["resume"].wait(0.25)
    if c["stop"].is_set():
        raise RuntimeError("Download stopped by user")

def control_sleep(job_id, seconds):
    c = job_controls.get(job_id)
    if not c:
        time.sleep(seconds)
        return
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        control_wait(job_id)
        if c["stop"].wait(min(0.25, max(0, end-time.monotonic()))):
            raise RuntimeError("Download stopped by user")

# Common CSV field set, chosen from real Access/Audit/Security Events field names.
COMMON_FIELDS = ["time","@timestamp","vh_name","method","req_path","rsp_code","user","src","src_ip","dst","dst_ip","site","domain","action","sec_event_type","waf_mode","app_firewall_name"]

def clean_path(v):
    if v is None:return ""
    v=str(v).replace("\u202a","").replace("\u202b","").replace("\u202c","").replace("\u202d","").replace("\u202e","").replace("\u2066","").replace("\u2067","").replace("\u2068","").replace("\u2069","").replace("\ufeff","").strip()
    return v

def normalize_host(host):
    host=clean_path(host).strip()
    host=re.sub(r'^https?://','',host,flags=re.I).rstrip('/')
    return host

def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
    except Exception:return {}

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data,indent=2),encoding="utf-8")

def rfc3339(v):
    s=str(v).strip()
    if s.endswith('Z'): return s
    dt=datetime.fromisoformat(s)
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00','Z')

def scalar(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    return json.dumps(v,ensure_ascii=False,separators=(",",":"))

def flatten(v,parent="",sep="."):
    out={}
    if isinstance(v,dict):
        for k,val in v.items():
            key=f"{parent}{sep}{k}" if parent else str(k)
            out.update(flatten(val,key,sep))
    elif isinstance(v,list): out[parent]=json.dumps(v,ensure_ascii=False,separators=(",",":"))
    else: out[parent]=scalar(v)
    return out

def parse_record(raw):
    if isinstance(raw,dict): return flatten(raw)
    try:
        obj=json.loads(raw) if isinstance(raw,str) else raw
        return flatten(obj) if isinstance(obj,dict) else {"raw_log":scalar(obj)}
    except Exception:return {"raw_log":raw}

# Security Events uses the app_security API (not FirewallLogQuery). Confirmed with F5 TAC:
# FirewallLogQuery was the wrong endpoint for security events, which caused the earlier
# ~8-day start_time restriction. The path below follows F5's /api/data/namespaces/{ns}/<resource>
# convention; the reference page gives the operation, not the literal REST path, so verify it
# with Check Range on first use.
# Filter builder data (generated from the F5 reference pages; see catalog/ in the repo).
CATALOG_JSON = r'''{"version":"2.0.0","note":"status: api_listed = in F5's query schema; tested = confirmed on tenant; reference = listed on the F5 reference pages (accepted by F5 per project owner; nested keys may need checking). suggestion_source: valid_values = reference says 'Valid values'; examples = reference uses 'and so on' or a partial list.","log_types":{"access":[{"name":"time","group":"Client","label":"Event time","status":"reference","input":"text","description":"When the log record was generated."},{"name":"user","group":"Client","label":"User","status":"reference","input":"text","description":"User from the user identification policy, or the client IP if none is set."},{"name":"src_ip","group":"Client","label":"Client IP address","status":"reference","input":"text","description":"IP address of the client."},{"name":"asn","group":"Client","label":"Client network (ASN)","status":"reference","input":"text","description":"Autonomous system (network) of the client, as name and number."},{"name":"as_org","group":"Client","label":"Client network name","status":"reference","input":"text","description":"Name of the client's autonomous system (network)."},{"name":"as_number","group":"Client","label":"AS number","status":"tested","input":"text","description":"Number of the client's autonomous system."},{"name":"country","group":"Client","label":"Client country","status":"api_listed","input":"text","description":"Client's country, as a two-letter ISO code."},{"name":"region","group":"Client","label":"Client region","status":"reference","input":"text","description":"Client's region or state, as an ISO subdivision code."},{"name":"city","group":"Client","label":"Client city","status":"api_listed","input":"text","description":"Client's city."},{"name":"longitude","group":"Client","label":"Client longitude","status":"reference","input":"text","description":"Geographic longitude of the client."},{"name":"latitude","group":"Client","label":"Client latitude","status":"reference","input":"text","description":"Geographic latitude of the client."},{"name":"tls_fingerprint","group":"Client","label":"TLS fingerprint","status":"reference","input":"text","description":"TLS client fingerprint (JA3) used to identify the client."},{"name":"ja4_tls_fingerprint","group":"Client","label":"JA4 TLS fingerprint","status":"reference","input":"text","description":"Newer TLS client fingerprint (JA4), with fewer distinct values than JA3."},{"name":"src_port","group":"Client","label":"Client port","status":"reference","input":"text","description":"Port number of the client."},{"name":"browser_type","group":"Device","label":"Browser","status":"api_listed","input":"text","description":"Browser, taken from the User-Agent header (HTTP only)."},{"name":"device_type","group":"Device","label":"Device type","status":"api_listed","input":"text","description":"Device type, taken from the User-Agent header (HTTP only)."},{"name":"dst","group":"Destination","label":"Destination service","status":"api_listed","input":"text","description":"Destination service or origin server the request was sent to."},{"name":"dst_instance","group":"Destination","label":"Destination instance","status":"api_listed","input":"text","description":"Specific instance (for example a pod) that handled the request."},{"name":"dst_site","group":"Destination","label":"Destination site","status":"api_listed","input":"text","description":"Site that sent the traffic on to the destination."},{"name":"dst_port","group":"Destination","label":"Destination port","status":"reference","input":"text","description":"Destination port on the origin server."},{"name":"src","group":"Source","label":"Source service","status":"api_listed","input":"text","description":"Service that sent the request, or N:public for internet clients."},{"name":"src_instance","group":"Source","label":"Source instance","status":"api_listed","input":"text","description":"Specific instance that generated the traffic."},{"name":"src_site","group":"Source","label":"Receiving site","status":"api_listed","input":"text","description":"F5 site (regional or customer edge) that received the request."},{"name":"duration_with_no_data_tx_delay","group":"Timing","label":"Processing time (no data delay)","status":"reference","input":"text","description":"Processing time from the first byte sent to the client, until the response is complete."},{"name":"duration_with_data_tx_delay","group":"Timing","label":"Processing time (with data delay)","status":"reference","input":"text","description":"Time spent by the load balancer and origin processing the request and response."},{"name":"time_to_last_upstream_rx_byte","group":"Timing","label":"Time to last upstream byte","status":"reference","input":"text","description":"Seconds from the first client byte until the last origin byte was received."},{"name":"time_to_first_upstream_rx_byte","group":"Timing","label":"Time to first upstream byte","status":"reference","input":"text","description":"Seconds from the first client byte until the origin's first byte arrived."},{"name":"time_to_last_downstream_tx_byte","group":"Timing","label":"Time to last downstream byte","status":"reference","input":"text","description":"Seconds from the first client byte until the last byte was sent to the client."},{"name":"time_to_first_downstream_tx_byte","group":"Timing","label":"Time to first downstream byte","status":"reference","input":"text","description":"Seconds from the first client byte until the first byte was sent to the client."},{"name":"total_duration_seconds","group":"Timing","label":"Total request duration (s)","status":"reference","input":"text","description":"Total end-to-end processing time, in seconds."},{"name":"rtt_upstream_seconds","group":"Timing","label":"Upstream round-trip time (s)","status":"reference","input":"text","description":"Round-trip time to the origin server, in seconds."},{"name":"rtt_downstream_seconds","group":"Timing","label":"Client round-trip time (s)","status":"reference","input":"text","description":"Round-trip time to the client, in seconds."},{"name":"protocol","group":"Request","label":"HTTP protocol version","status":"tested","value_suggestions":["HTTP 1.0","HTTP 1.1","HTTP 2"],"suggestion_source":"examples","input":"text_with_suggestions","description":"HTTP version used, such as HTTP 1.1 or HTTP 2."},{"name":"scheme","group":"Request","label":"URL scheme","status":"reference","value_suggestions":["HTTP","HTTPS"],"suggestion_source":"examples","input":"text_with_suggestions","description":"URL scheme: HTTP or HTTPS."},{"name":"method","group":"Request","label":"HTTP method","status":"tested","value_suggestions":["HEAD","GET","POST","OPTIONS"],"suggestion_source":"examples","input":"text_with_suggestions","description":"HTTP method, such as GET or POST."},{"name":"authority","group":"Request","label":"Host (authority)","status":"reference","input":"text","description":"Host name in the request (the Host or :authority value)."},{"name":"original_authority","group":"Request","label":"Original host","status":"reference","input":"text","description":"Host header as the client sent it, before any change."},{"name":"domain","group":"Request","label":"Domain","status":"reference","input":"text","description":"Domain extracted from the host name."},{"name":"referer","group":"Request","label":"Referer","status":"reference","input":"text","description":"Referer header: the page that linked to this request."},{"name":"x_forwarded_for","group":"Request","label":"X-Forwarded-For","status":"reference","input":"text","description":"X-Forwarded-For header, with the address sanitized for privacy."},{"name":"user_agent","group":"Request","label":"User agent","status":"reference","input":"text","description":"User-Agent header identifying the client software."},{"name":"req_path","group":"Request","label":"Request path","status":"api_listed","input":"text","description":"Request path, without query parameters."},{"name":"req_params","group":"Request","label":"Query parameters","status":"reference","input":"text","description":"Query string parameters from the URL."},{"name":"req_headers","group":"Request","label":"Request headers","status":"reference","input":"text","description":"Request headers, logged only when API discovery is enabled and sampled."},{"name":"rsp_code","group":"Response","label":"Response code","status":"tested","value_suggestions":["0"],"suggestion_source":"examples","input":"text_with_suggestions","description":"HTTP response code. Shows 0 when the request was blocked."},{"name":"waf_action","group":"WAF","label":"WAF action","status":"reference","value_suggestions":["allow","block"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Action the WAF recommended: allow or block."},{"name":"bot_defense_js_injection","group":"Bot defense","label":"Bot defence JS injected","status":"reference","input":"text","description":"Whether the Bot Defense JavaScript was injected into the page."},{"name":"insight","group":"Bot defense","label":"Bot insight","status":"reference","value_suggestions":["HUMAN","GOODBOT","MALICIOUS","UNAVAILABLE"],"suggestion_source":"examples","input":"text_with_suggestions","description":"Bot classification from Bot Defense: HUMAN, GOODBOT, MALICIOUS or UNAVAILABLE."},{"name":"recommendation","group":"Bot defense","label":"Bot recommended action","status":"reference","value_suggestions":["Action_alert","Action_block","Action_redirect"],"suggestion_source":"examples","input":"text_with_suggestions","description":"Bot Defense recommended action, such as alert, block or redirect."},{"name":"automation_type","group":"Bot defense","label":"Bot automation type","status":"reference","input":"text","description":"Reason the client was flagged as a bot, such as Token Missing."},{"name":"policy_set","group":"Service policy","label":"Policy set","status":"reference","input":"text","description":"Last service policy set that ran."},{"name":"policy","group":"Service policy","label":"Policy","status":"reference","input":"text","description":"Last service policy that ran."},{"name":"policy_namespace","group":"Service policy","label":"Policy namespace","status":"reference","input":"text","description":"Namespace of the last service policy that ran."},{"name":"policy_rule","group":"Service policy","label":"Policy rule","status":"reference","input":"text","description":"Last service policy rule that ran."},{"name":"policy_rule_description","group":"Service policy","label":"Policy rule description","status":"reference","input":"text","description":"Description of that policy rule, as set in its configuration."},{"name":"result","group":"Service policy","label":"Policy result","status":"reference","value_suggestions":["allow","deny","default_allow","default_deny"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Service policy result: allow, deny, default_allow or default_deny."},{"name":"rate_limiter_action","group":"Service policy","label":"Rate limiter action","status":"reference","value_suggestions":["fail","pass","none"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Rate limiter result: fail, pass or none."},{"name":"malicious_user_mitigation_action","group":"Service policy","label":"Malicious user mitigation","status":"reference","value_suggestions":["MUM_NONE","MUM_BLOCK_TEMPORARILY","MUM_JAVASCRIPT_CHALLENGE","MUM_CAPTCHA_CHALLENGE"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Action taken for a malicious user: none, temporary block, or a challenge."},{"name":"ip_risk","group":"Service policy","label":"IP risk","status":"reference","value_suggestions":["LOW_RISK","MEDIUM_RISK","HIGH_RISK"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Risk of the client IP from the IP reputation database: LOW, MEDIUM or HIGH."},{"name":"ip_trustscore","group":"Service policy","label":"IP trust score","status":"reference","input":"text","description":"Client IP trust score, from 0 (low trust) to 100 (high trust)."},{"name":"ip_trustworthiness","group":"Service policy","label":"IP trustworthiness","status":"reference","value_suggestions":["LOW","MEDIUM","HIGH"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Client IP trustworthiness: LOW, MEDIUM or HIGH (the opposite of risk)."},{"name":"ip_threat_categories","group":"Service policy","label":"IP threat categories","status":"reference","input":"text","description":"Threat categories the client IP belongs to."},{"name":"oas_request_properties","group":"Service policy","label":"API spec request checks","status":"reference","input":"text","description":"Parts of the request checked against the API specification."},{"name":"oas_validation_action","group":"Service policy","label":"API spec validation action","status":"reference","value_suggestions":["OAS_REPORT_VIOLATION","OAS_BLOCK_VIOLATION"],"suggestion_source":"examples","input":"text_with_suggestions","description":"Action taken when a request fails API specification checks."},{"name":"connected_time","group":"Service policy","label":"Connection start time","status":"tested","input":"text","description":"When the connection started."},{"name":"app_type","group":"Metadata","label":"App type","status":"api_listed","input":"text","description":"Application profile name."},{"name":"cluster_name","group":"Metadata","label":"Cluster","status":"reference","input":"text","description":"F5 cluster that routed the request."},{"name":"has_sec_event","group":"Metadata","label":"Has security event","status":"reference","input":"text","description":"Whether a security event was generated for this request."},{"name":"hostname","group":"Metadata","label":"Node hostname","status":"reference","input":"text","description":"Machine that generated this log record."},{"name":"messaged","group":"Metadata","label":"Log type ID","status":"reference","input":"text","description":"Identifier of the log record type."},{"name":"namespace","group":"Metadata","label":"Namespace","status":"reference","input":"text","description":"Namespace the virtual host was created in."},{"name":"req_id","group":"Metadata","label":"Request ID","status":"reference","input":"text","description":"Unique ID of the request."},{"name":"tenant","group":"Metadata","label":"Tenant","status":"reference","input":"text","description":"Tenant (organization) the resource belongs to."},{"name":"vh_name","group":"Metadata","label":"Virtual host","status":"api_listed","input":"text","description":"Name of the virtual host (load balancer)."},{"name":"vh_type","group":"Metadata","label":"Virtual host type","status":"reference","value_suggestions":["VIRTUAL_SERVICE","HTTP_LOAD_BALANCER","API_GATEWAY","TCP_LOADBALANCER","PROXY","LOCAL_K8S_API_GATEWAY","CDN_LOADBALANCER"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Virtual host type, such as HTTP load balancer or API gateway."},{"name":"timeseries_enabled","group":"Metadata","label":"DDoS protection enabled","status":"reference","input":"text","description":"Whether DDoS protection is enabled on this load balancer."}],"security":[{"name":"asn","group":"Client","label":"Client network (ASN)","status":"reference","input":"text","description":"Autonomous system (network) of the client, as name and number."},{"name":"as_number","group":"Client","label":"AS number","status":"reference","input":"text","description":"Number of the client's autonomous system."},{"name":"as_org","group":"Client","label":"Client network name","status":"reference","input":"text","description":"Name of the client's autonomous system (network)."},{"name":"city","group":"Client","label":"Client city","status":"api_listed","input":"text","description":"Client's city."},{"name":"country","group":"Client","label":"Client country","status":"api_listed","input":"text","description":"Client's country, as a two-letter ISO code."},{"name":"latitude","group":"Client","label":"Client latitude","status":"reference","input":"text","description":"Geographic latitude of the client."},{"name":"longitude","group":"Client","label":"Client longitude","status":"reference","input":"text","description":"Geographic longitude of the client."},{"name":"region","group":"Client","label":"Client region","status":"reference","input":"text","description":"Client's region or state, as an ISO subdivision code."},{"name":"sni","group":"Client","label":"SNI (server name)","status":"reference","input":"text","description":"Server name (SNI) requested in the TLS handshake."},{"name":"src_ip","group":"Client","label":"Client IP address","status":"reference","input":"text","description":"IP address of the client."},{"name":"tls_fingerprint","group":"Client","label":"TLS fingerprint","status":"reference","input":"text","description":"TLS client fingerprint (JA3) used to identify the client."},{"name":"user","group":"Client","label":"User","status":"reference","input":"text","description":"User from the user identification policy, or the client IP if none is set."},{"name":"browser_type","group":"Device","label":"Browser","status":"reference","input":"text","description":"Browser, taken from the User-Agent header (HTTP only)."},{"name":"device_type","group":"Device","label":"Device type","status":"reference","input":"text","description":"Device type, taken from the User-Agent header (HTTP only)."},{"name":"authority","group":"HTTP","label":"Host (authority)","status":"reference","input":"text","description":"Host name in the request (the Host or :authority value)."},{"name":"domain","group":"HTTP","label":"Domain","status":"reference","input":"text","description":"Domain extracted from the host name."},{"name":"http_version","group":"HTTP","label":"HTTP version","status":"reference","input":"text","description":"HTTP version of the request."},{"name":"method","group":"HTTP","label":"HTTP method","status":"reference","value_suggestions":["HEAD","GET","POST","OPTIONS"],"suggestion_source":"examples","input":"text_with_suggestions","description":"HTTP method, such as GET or POST."},{"name":"original_path","group":"HTTP","label":"Original path","status":"reference","input":"text","description":"Request path as received, before decoding."},{"name":"req_headers","group":"HTTP","label":"Request headers","status":"reference","input":"text","description":"Request headers, logged only when API discovery is enabled and sampled."},{"name":"req_path","group":"HTTP","label":"Request path","status":"reference","input":"text","description":"Request path, without query parameters."},{"name":"req_params","group":"HTTP","label":"Query parameters","status":"reference","input":"text","description":"Query string parameters from the URL."},{"name":"user_agent","group":"HTTP","label":"User agent","status":"reference","input":"text","description":"User-Agent header identifying the client software."},{"name":"x_forwarded_for","group":"HTTP","label":"X-Forwarded-For","status":"reference","input":"text","description":"X-Forwarded-For header, with the address sanitized for privacy."},{"name":"dst_ip","group":"Request","label":"Destination IP","status":"reference","input":"text","description":"IP address of the upstream (origin) server."},{"name":"dst_port","group":"Request","label":"Destination port","status":"reference","input":"text","description":"Destination port on the origin server."},{"name":"req_headers_size","group":"Request","label":"Request headers size","status":"reference","input":"text","description":"Size of the request headers, in bytes."},{"name":"req_size","group":"Request","label":"Request size","status":"reference","input":"text","description":"Size of the request, in bytes."},{"name":"src_port","group":"Request","label":"Client port","status":"reference","input":"text","description":"Port number of the client."},{"name":"rsp_code","group":"Response","label":"Response code","status":"reference","value_suggestions":["0"],"suggestion_source":"examples","input":"text_with_suggestions","description":"HTTP response code. Shows 0 when the request was blocked."},{"name":"rsp_code_class","group":"Response","label":"Response code class","status":"reference","value_suggestions":["2xx","3xx","4xx","5xx"],"suggestion_source":"examples","input":"text_with_suggestions","description":"Response code class: 2xx, 3xx, 4xx or 5xx."},{"name":"rsp_size","group":"Response","label":"Response size","status":"reference","input":"text","description":"Size of the response, in bytes."},{"name":"calculated_action","group":"WAF","label":"Calculated WAF action","status":"reference","value_suggestions":["allow","report","block"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"WAF recommended action: allow, report or block."},{"name":"action","group":"WAF","label":"Action taken","status":"reference","input":"text","description":"Action actually taken on the request."},{"name":"waf_mode","group":"WAF","label":"WAF mode","status":"reference","value_suggestions":["allow","report","block"],"suggestion_source":"examples","input":"text_with_suggestions","description":"WAF mode: allow, report or block."},{"name":"bot_info.name","group":"WAF","label":"Bot name","status":"reference","input":"text","description":"Name of the detected bot."},{"name":"bot_info.type","group":"WAF","label":"Bot type","status":"reference","input":"text","description":"Type of the detected bot, such as Search Engine."},{"name":"bot_info.classification","group":"WAF","label":"Bot classification","status":"reference","value_suggestions":["Malicious","Suspicious","Benign"],"suggestion_source":"valid_values","input":"text_with_suggestions","description":"Bot classification: Malicious, Suspicious or Benign."},{"name":"bot_info.anomaly","group":"WAF","label":"Bot anomaly","status":"reference","input":"text","description":"How the WAF detected the bot, such as invalid HTTP headers."},{"name":"attack_types","group":"WAF","label":"Attack types","status":"reference","input":"text","description":"Attack types detected in the request."},{"name":"signatures","group":"WAF","label":"Signatures matched","status":"reference","input":"text","description":"Signatures (attack patterns) matched in the request."},{"name":"violations","group":"WAF","label":"Violations","status":"reference","input":"text","description":"Policy violations detected in the request."},{"name":"app_type","group":"Metadata","label":"App type","status":"reference","input":"text","description":"Application profile name."},{"name":"sec_event_type","group":"Metadata","label":"Security event type","status":"api_listed","value_suggestions":["waf_sec_event","bot_defense_sec_event","api_sec_event","svc_policy_sec_event"],"suggestion_source":"examples","input":"text_with_suggestions","description":"Security event type: waf_sec_event, bot_defense_sec_event, api_sec_event or svc_policy_sec_event."},{"name":"sec_event_name","group":"Metadata","label":"Security event name","status":"reference","input":"text","description":"Security event name, such as WAF."},{"name":"cluster_name","group":"Metadata","label":"Cluster","status":"reference","input":"text","description":"F5 cluster that routed the request."},{"name":"hostname","group":"Metadata","label":"Node hostname","status":"reference","input":"text","description":"Machine that generated this log record."},{"name":"messageid","group":"Metadata","label":"Message ID","status":"reference","input":"text","description":"Unique identifier of the log record type."},{"name":"namespace","group":"Metadata","label":"Namespace","status":"reference","input":"text","description":"Namespace the virtual host was created in."},{"name":"req_id","group":"Metadata","label":"Request ID","status":"reference","input":"text","description":"Unique ID of the request."},{"name":"tenant","group":"Metadata","label":"Tenant","status":"reference","input":"text","description":"Tenant (organization) the resource belongs to."},{"name":"vh_name","group":"Metadata","label":"Virtual host","status":"api_listed","input":"text","description":"Name of the virtual host (load balancer)."},{"name":"src","group":"Metadata","label":"Source service","status":"reference","input":"text","description":"Service that sent the request, or N:public for internet clients."},{"name":"src_instance","group":"Metadata","label":"Source instance","status":"reference","input":"text","description":"Specific instance that generated the traffic."},{"name":"src_site","group":"Metadata","label":"Receiving site","status":"api_listed","input":"text","description":"F5 site (regional or customer edge) that received the request."}],"audit":[{"name":"dst","group":"Destination","label":"Destination service","status":"api_listed","input":"text","description":"Destination service or origin server the request was sent to."},{"name":"dst_site","group":"Destination","label":"Destination site","status":"api_listed","input":"text","description":"Site that sent the traffic on to the destination."},{"name":"src","group":"Source","label":"Source service","status":"api_listed","input":"text","description":"Service that sent the request, or N:public for internet clients."},{"name":"src_site","group":"Source","label":"Receiving site","status":"api_listed","input":"text","description":"F5 site (regional or customer edge) that received the request."},{"name":"src_instance","group":"Source","label":"Source instance","status":"api_listed","input":"text","description":"Specific instance that generated the traffic."},{"name":"method","group":"Request","label":"HTTP method","status":"api_listed","value_suggestions":["HEAD","GET","POST","OPTIONS"],"suggestion_source":"examples","input":"text_with_suggestions","description":"HTTP method, such as GET or POST."},{"name":"req_path","group":"Request","label":"Request path","status":"api_listed","input":"text","description":"Request path, without query parameters."},{"name":"req_headers","group":"Request","label":"Request headers","status":"reference","input":"text","description":"Request headers, logged only when API discovery is enabled and sampled."},{"name":"req_body","group":"Request","label":"Request body","status":"reference","input":"text","description":"Request body submitted to the API."},{"name":"req_size","group":"Request","label":"Request size","status":"reference","input":"text","description":"Size of the request, in bytes."},{"name":"user_agent","group":"Request","label":"User agent","status":"reference","input":"text","description":"User-Agent header identifying the client software."},{"name":"req_error","group":"Request","label":"Request error","status":"reference","input":"text","description":"Error returned when request validation or processing failed."},{"name":"rsp_code","group":"Response","label":"Response code","status":"api_listed","value_suggestions":["0"],"suggestion_source":"examples","input":"text_with_suggestions","description":"HTTP response code. Shows 0 when the request was blocked."},{"name":"rsp_size","group":"Response","label":"Response size","status":"reference","input":"text","description":"Size of the response, in bytes."},{"name":"rsp_seconds","group":"Response","label":"Response time (s)","status":"reference","input":"text","description":"Seconds spent processing the request and creating the response."},{"name":"user","group":"Identity","label":"User","status":"api_listed","input":"text","description":"User from the user identification policy, or the client IP if none is set."},{"name":"ctx_creatorid","group":"Identity","label":"Created by (user ID)","status":"reference","input":"text","description":"User ID of the person who started the operation."},{"name":"ctx_creatorcls","group":"Identity","label":"Created by (client type)","status":"reference","input":"text","description":"Client type that sent the request, such as Prism."},{"name":"peer_CN","group":"Identity","label":"Peer certificate name","status":"reference","input":"text","description":"Common Name from the peer certificate."},{"name":"tenant","group":"Identity","label":"Tenant","status":"reference","input":"text","description":"Tenant (organization) the resource belongs to."},{"name":"original_tenant","group":"Identity","label":"Original tenant","status":"reference","input":"text","description":"Tenant the request originally belonged to."},{"name":"time","group":"Event","label":"Event time","status":"reference","input":"text","description":"When the log record was generated."},{"name":"time_start","group":"Event","label":"Start time","status":"reference","input":"text","description":"When request processing started."},{"name":"messageid","group":"Event","label":"Message ID","status":"reference","input":"text","description":"Unique identifier of the log record type."},{"name":"message","group":"Event","label":"Event message","status":"reference","input":"text","description":"Summary or type of the audit event."},{"name":"message_key","group":"Event","label":"Message key","status":"reference","input":"text","description":"Internal key used for indexing and correlation."},{"name":"severity","group":"Event","label":"Severity","status":"reference","input":"text","description":"Severity level of the audit event."},{"name":"trace_info","group":"Event","label":"Trace ID","status":"reference","input":"text","description":"Distributed tracing ID used to correlate requests across services."},{"name":"rpc","group":"Event","label":"API call","status":"reference","input":"text","description":"Internal API call that was made."},{"name":"transport","group":"Event","label":"Transport","status":"reference","input":"text","description":"Transport used by the API, such as REST or gRPC."},{"name":"stream","group":"Event","label":"Stream","status":"reference","input":"text","description":"Internal log stream name."},{"name":"server_id","group":"Event","label":"Server ID","status":"reference","input":"text","description":"ID of the service instance that generated the record."},{"name":"original_topic_name","group":"Event","label":"Original topic","status":"reference","input":"text","description":"Message topic the audit event was first published to."},{"name":"app","group":"Metadata","label":"App","status":"reference","input":"text","description":"Application name (internal)."},{"name":"cluster_name","group":"Metadata","label":"Cluster","status":"reference","input":"text","description":"F5 cluster that routed the request."},{"name":"hostname","group":"Metadata","label":"Node hostname","status":"reference","input":"text","description":"Machine that generated this log record."},{"name":"host","group":"Metadata","label":"Host IP","status":"reference","input":"text","description":"Host IP address the record came from."},{"name":"site","group":"Metadata","label":"Site","status":"reference","input":"text","description":"Site that handled the request."},{"name":"namespace","group":"Metadata","label":"Namespace","status":"reference","input":"text","description":"Namespace the virtual host was created in."},{"name":"kubernetes","group":"Metadata","label":"Kubernetes info","status":"reference","input":"text","description":"Internal Kubernetes details."}]},"input_rules":{"text":"Free text. Any value can be typed.","text_with_suggestions":"Free text, with a suggestion list from the reference. Suggestions are not a limit; the user can type any value.","conditions":["Equals","Not equals"]}}'''
TEMPLATES_JSON = r'''{"version":"2.0.0","rules":"Templates use only the fields in field_catalog.json and only the operators = and !=. Placeholders must be filled before running.","templates":{"access":[{"name":"Blocked requests","description":"Requests blocked by F5 (response code 0).","conditions":[{"field":"rsp_code","op":"=","value":"0"}]},{"name":"POST requests only","description":"Only HTTP POST requests.","conditions":[{"field":"method","op":"=","value":"POST"}]},{"name":"Exclude GET and HEAD","description":"Everything except GET and HEAD requests.","conditions":[{"field":"method","op":"!=","value":"GET"},{"field":"method","op":"!=","value":"HEAD"}]},{"name":"Traffic from one country","description":"Requests from one client country (ISO code, e.g. IN).","conditions":[{"field":"country","op":"=","value":"","placeholder":"Country code, e.g. IN"}]},{"name":"Traffic from one autonomous system","description":"Requests from one AS number.","conditions":[{"field":"as_number","op":"=","value":"","placeholder":"AS number, e.g. 15169"}]},{"name":"One virtual host","description":"Requests to one load balancer.","conditions":[{"field":"vh_name","op":"=","value":"","placeholder":"Virtual host name"}]},{"name":"Chrome browser only","description":"Requests from Chrome browsers.","conditions":[{"field":"browser_type","op":"=","value":"Chrome"}]},{"name":"Responses other than 200","description":"Requests whose response code is not 200 OK.","conditions":[{"field":"rsp_code","op":"!=","value":"200"}]},{"name":"Successful requests (200)","description":"Requests whose response code is 200 OK.","conditions":[{"field":"rsp_code","op":"=","value":"200"}]}],"security":[{"name":"All WAF events","description":"All WAF security events.","conditions":[{"field":"sec_event_type","op":"=","value":"waf_sec_event"}]},{"name":"WAF events for one virtual host","description":"WAF events on one load balancer.","conditions":[{"field":"sec_event_type","op":"=","value":"waf_sec_event"},{"field":"vh_name","op":"=","value":"","placeholder":"Virtual host name"}]},{"name":"WAF events from one country","description":"WAF events from one client country.","conditions":[{"field":"sec_event_type","op":"=","value":"waf_sec_event"},{"field":"country","op":"=","value":"","placeholder":"Country code, e.g. IN"}]},{"name":"Exclude one country","description":"Security events not from a given country.","conditions":[{"field":"country","op":"!=","value":"","placeholder":"Country code to exclude"}]},{"name":"Events from one city","description":"Security events from one client city.","conditions":[{"field":"city","op":"=","value":"","placeholder":"City name"}]},{"name":"Events from one source site","description":"Security events received at one F5 site.","conditions":[{"field":"src_site","op":"=","value":"","placeholder":"Site name"}]}],"audit":[{"name":"Changes by one user","description":"Audit records for one user.","conditions":[{"field":"user","op":"=","value":"","placeholder":"User name or email"}]},{"name":"Write operations only","description":"Everything except read requests (GET and HEAD excluded).","conditions":[{"field":"method","op":"!=","value":"GET"},{"field":"method","op":"!=","value":"HEAD"}]},{"name":"POST requests only","description":"Only POST requests (creates and some updates).","conditions":[{"field":"method","op":"=","value":"POST"}]},{"name":"Responses other than 200","description":"Audit records whose response code is not 200 OK.","conditions":[{"field":"rsp_code","op":"!=","value":"200"}]}]}}'''

LOG_ENDPOINTS={
    "access":  ("access_logs", "Access Log Query V2"),
    "audit":   ("audit_logs", "Audit Log Query V2"),
    "security":("app_security/events", "Security Events Query"),
}
def normalize_log_type(v):
    v=str(v or "access").strip().lower()
    return "security" if v in ("firewall","security") else v

def run_job(job_id,cfg):
    def update(**kw):
        with jobs_lock: jobs[job_id].update(kw)
    log_lines=[]
    def log(msg,level="INFO"):
        line=f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] [{level:7}] {msg}"; log_lines.append(line); update(log=log_lines[-500:],message=msg)
    # Everything below can fail (bad path, bad time, bad log type, network errors, etc).
    # The whole body is wrapped so a failure always reports a clean status instead of
    # silently killing the background thread and leaving the UI stuck on "running".
    csv_path=json_path=log_path=None
    total_hits=None; received=0; batch=1; complete=True; started=time.perf_counter()
    try:
        output_dir=Path(clean_path(cfg["output_dir"])).expanduser()
        try:
            output_dir.mkdir(parents=True,exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Cannot create or access output directory '{output_dir}': {e.strerror or e}. Check the path and your permissions, then try again.") from e
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); typ=normalize_log_type(cfg.get("log_type","access"))
        label={"access":"access","audit":"audit","security":"security_events"}.get(typ,typ)
        base=output_dir/f"f5xc_{label}_logs_{stamp}"; csv_path=base.with_suffix('.csv'); json_path=base.with_suffix('.json'); log_path=base.with_suffix('.debug.log'); jsonl_path=base.with_suffix('.jsonl')
        token=cfg["token"]; host=normalize_host(cfg["host"]); ns=cfg["namespace"].strip(); query=str(cfg.get("query","")).strip(); pagination=cfg.get("pagination","search_after"); sort=cfg.get("sort","ASCENDING")
        try:
            start=rfc3339(cfg["start_time"]); end=rfc3339(cfg["end_time"])
        except Exception as e:
            raise RuntimeError(f"Invalid start/end time: {e}") from e
        batch_size=500
        endpoints=LOG_ENDPOINTS
        if typ not in endpoints:
            raise RuntimeError(f"Unknown log type '{typ}'")
        resource,opname=endpoints[typ]; url=f"https://{host}/api/data/namespaces/{ns}/{resource}"; scroll_url=url+"/scroll"
        session=requests.Session(); session.headers.update({"Authorization":f"APIToken {token}","Content-Type":"application/json","Accept":"application/json","User-Agent":f"F5XC-Log-Tool/{APP_VERSION}"})
        def api(url,payload,op,method="POST"):
            for attempt in range(1,6):
                control_wait(job_id)
                t=time.perf_counter(); safe=dict(payload)
                if "scroll_id" in safe:safe["scroll_id"]=f"<MASKED length={len(str(payload['scroll_id']))}>"
                log(f"{op} | POST {url}"); log(f"Request: {json.dumps(safe,ensure_ascii=False)}","DEBUG")
                try:
                    resp=(session.get(url,params=payload,timeout=60) if method=="GET" else session.post(url,json=payload,timeout=60)); elapsed=time.perf_counter()-t; log(f"HTTP {resp.status_code} | {len(resp.content):,} bytes | {elapsed:.3f}s")
                    if resp.status_code in {429,500,502,503,504} and attempt<5:
                        delay=2**(attempt-1); log(f"Transient HTTP {resp.status_code}; retrying in {delay}s","WARN"); control_sleep(job_id,delay); continue
                    if not resp.ok:
                        log(f"Response: {resp.text[:8000]}","ERROR")
                        # 400/401/403/404 etc. won't change on retry with the same
                        # request - fail immediately instead of burning ~30s of
                        # exponential-backoff retries on something that can never succeed.
                        detail=resp.text[:500]
                        try:
                            j=resp.json(); detail=j.get("message") or detail
                        except Exception:pass
                        raise RuntimeError(f"F5 XC rejected the request (HTTP {resp.status_code}): {detail}")
                    return resp.json()
                except requests.RequestException as e:
                    if attempt>=5: raise
                    delay=2**(attempt-1); log(f"Request exception: {e!r}; retrying in {delay}s","WARN"); control_sleep(job_id,delay)
            raise RuntimeError("API request failed")
        payload={"namespace":ns,"start_time":start,"end_time":end,"limit":batch_size,"sort":sort}
        if query:payload["query"]=query
        # CONFIRMED through direct testing: F5 XC rejects any request that sets
        # BOTH "scroll" and "search_after" at once, with HTTP 400 ("scroll and
        # search_after query at the same time is not possible"). Separately, earlier
        # testing showed "search_after" alone does not reliably return a usable
        # last_sort_values continuation token either. scroll_id is the only mechanism
        # confirmed to work end-to-end, so both pagination options below use it - the
        # UI choice is kept for now since removing it isn't necessary to fix this bug.
        payload["scroll"]=True
        if pagination=="search_after":
            log("Search After pagination requested: using scroll-token continuation internally, since F5 XC does not allow combining scroll and search_after in one request, and search_after alone was not confirmed to return a usable continuation token")
        else:
            log("Scroll pagination enabled: initial query requests a scroll_id")
        with jsonl_path.open('w',encoding='utf-8') as jf:
            response=None
            while True:
                control_wait(job_id)
                if response is None:
                    response=api(url,payload,opname)
                if total_hits is None: total_hits=response.get("total_hits"); log(f"F5 total_hits: {total_hits}")
                logs=response.get("logs") or response.get("events") or []; log(f"Batch {batch}: {len(logs):,} records")
                if not logs: break
                control_wait(job_id)
                for raw in logs: jf.write(json.dumps(parse_record(raw),ensure_ascii=False,separators=(",",":"))+"\n")
                received+=len(logs); reported=int(total_hits) if str(total_hits).isdigit() else -1; pct=100 if reported<=0 else min(100,received/reported*100); update(received=received,total_hits=total_hits,batch=batch,percent=pct); log(f"Accumulated: {received:,} | Progress: {pct:.2f}%")
                if reported>=0 and received>=reported: break
                sid=response.get("scroll_id",""); log(f"scroll_id received: {'YES (masked)' if sid else 'NO'}","DEBUG")
                if not sid:
                    if len(logs)<batch_size: break
                    complete=False
                    raise RuntimeError(f"F5 XC did not return a scroll_id after {received:,} of {total_hits} records, so the remaining records can't be fetched. Try narrowing the time range and downloading in smaller batches.")
                control_wait(job_id)
                if typ=="security":
                    # Security Events Scroll is a GET with scroll_id as a query parameter.
                    response=api(scroll_url,{"scroll_id":sid},opname.replace('Query','Scroll'),method="GET")
                else:
                    response=api(scroll_url,{"namespace":ns,"scroll_id":sid},opname.replace('Query','Scroll'))
                batch+=1
        reported=int(total_hits) if str(total_hits).isdigit() else -1
        if reported>=0 and received!=reported:complete=False
        log(f"COUNT: F5={total_hits} | downloaded={received} | {'MATCH' if complete else 'MISMATCH'}","INFO" if complete else "WARN")
        fields=OrderedDict()
        with jsonl_path.open(encoding='utf-8') as jf:
            for line in jf:
                if line.strip():
                    for k in json.loads(line).keys(): fields.setdefault(k,None)
        all_fields=list(fields.keys()) or ["raw_log"]; mode=cfg.get('csv_mode','1')
        if mode=='2':selected=[x for x in all_fields if x in COMMON_FIELDS] or all_fields
        elif mode=='3':
            req=[x.strip() for x in cfg.get('custom_fields','').split(',') if x.strip()]; selected=[x for x in all_fields if x in req] or all_fields
        else:selected=all_fields
        with csv_path.open('w',newline='',encoding='utf-8-sig') as cf, jsonl_path.open(encoding='utf-8') as jf:
            writer=csv.DictWriter(cf,fieldnames=selected,extrasaction='ignore'); writer.writeheader()
            for line in jf:
                if line.strip(): writer.writerow(json.loads(line))
        if cfg.get('keep_json',True):
            # Stream JSON array to avoid holding all logs in memory.
            with json_path.open('w',encoding='utf-8') as out, jsonl_path.open(encoding='utf-8') as jf:
                out.write('[\n'); first=True
                for line in jf:
                    if line.strip():
                        if not first:out.write(',\n')
                        out.write(json.dumps(json.loads(line),ensure_ascii=False,indent=2)); first=False
                out.write('\n]\n')
        else:json_path=None
        try:jsonl_path.unlink()
        except Exception:pass
        elapsed=time.perf_counter()-started
        log_path.write_text('\n'.join(log_lines),encoding='utf-8')
        final_pct=100 if complete else (100 if reported<=0 else min(100,received/reported*100))
        update(status='complete',received=received,total_hits=total_hits,batch=batch,percent=final_pct,csv=str(csv_path),json=str(json_path) if json_path else None,debug=str(log_path),complete=complete,elapsed=elapsed,rate=(received/elapsed if elapsed else 0),message='Download complete' if complete else 'Download complete with count warning',log=log_lines[-500:])
        job_controls.pop(job_id,None)
    except Exception as e:
        try:
            if log_path: log_path.write_text('\n'.join(log_lines),encoding='utf-8')
        except Exception:pass
        msg=str(e)
        stopped = 'stopped by user' in msg.lower()
        update(status='stopped' if stopped else 'error',message=msg,error=traceback.format_exc(),debug=(str(log_path) if log_path else None),log=log_lines[-500:])
        job_controls.pop(job_id,None)

@app.after_request
def no_cache(response):
    response.headers['Cache-Control']='no-store, no-cache, must-revalidate, max-age=0'; response.headers['Pragma']='no-cache'; response.headers['Expires']='0'; return response

@app.route('/')
def index():return render_template_string(INDEX_HTML,config=load_config(),version=APP_VERSION,config_path=str(CONFIG_FILE),catalog_json=CATALOG_JSON,templates_json=TEMPLATES_JSON)
@app.route('/api/config',methods=['GET'])
def config_get():return jsonify(load_config())
@app.route('/api/download',methods=['POST'])
def download():
    data=request.get_json(force=True); required=['host','namespace','token','start_time','end_time','output_dir']
    missing=[x for x in required if not str(data.get(x,'' )).strip()]
    if missing:return jsonify({'error':'Missing required fields: '+', '.join(missing)}),400
    data['host']=normalize_host(data['host']); data['output_dir']=clean_path(data['output_dir']); data['log_type']=data.get('log_type','access'); data['pagination']=data.get('pagination','search_after'); data['sort']=data.get('sort','ASCENDING')
    data['log_type']=normalize_log_type(data['log_type'])
    if data['log_type'] not in LOG_ENDPOINTS:return jsonify({'error':'Invalid log type'}),400
    job_id=os.urandom(8).hex()
    with jobs_lock:jobs[job_id]={'status':'running','received':0,'total_hits':None,'batch':0,'percent':0,'log':[],'message':'Starting'}
    job_controls[job_id]={'paused':threading.Event(),'resume':threading.Event(),'stop':threading.Event()}
    job_controls[job_id]['resume'].set()
    t=threading.Thread(target=run_job,args=(job_id,data),daemon=True);t.start();return jsonify({'job_id':job_id})
@app.route('/api/preview',methods=['POST'])
def preview():
    data=request.get_json(force=True); required=['host','namespace','token','start_time','end_time']
    missing=[x for x in required if not str(data.get(x,'')).strip()]
    if missing:return jsonify({'ok':False,'error':'Missing required fields: '+', '.join(missing)})
    typ=normalize_log_type(data.get('log_type','access')); endpoints=LOG_ENDPOINTS
    if typ not in endpoints:return jsonify({'ok':False,'error':'Invalid log type'})
    try:
        start=rfc3339(data['start_time']); end=rfc3339(data['end_time'])
    except Exception as e:
        return jsonify({'ok':False,'error':f'Invalid start/end time: {e}'})
    host=normalize_host(data['host']); ns=str(data['namespace']).strip(); resource,_=endpoints[typ]
    url=f"https://{host}/api/data/namespaces/{ns}/{resource}"
    query=str(data.get('query','')).strip()
    payload={"namespace":ns,"start_time":start,"end_time":end,"limit":1,"sort":data.get('sort','ASCENDING')}
    if query:payload['query']=query
    try:
        session=requests.Session()
        session.headers.update({"Authorization":f"APIToken {data['token']}","Content-Type":"application/json","Accept":"application/json","User-Agent":f"F5XC-Log-Tool/{APP_VERSION}"})
        resp=session.post(url,json=payload,timeout=30)
        if not resp.ok:
            detail=resp.text[:500]
            try:
                j=resp.json(); detail=j.get('message') or detail
            except Exception:pass
            return jsonify({'ok':False,'status_code':resp.status_code,'error':detail})
        j=resp.json()
        return jsonify({'ok':True,'total_hits':j.get('total_hits')})
    except requests.RequestException as e:
        return jsonify({'ok':False,'error':str(e)})
@app.route('/api/browse_native',methods=['POST'])
def browse_native():
    # Runs this same script/exe with the helper flag, which opens the Windows folder dialog.
    data=request.get_json(silent=True) or {}
    initial=clean_path(data.get('path',''))
    try:
        if getattr(sys,'frozen',False): cmd=[sys.executable,_BROWSE_HELPER_FLAG,initial]
        else: cmd=[sys.executable,os.path.abspath(__file__),_BROWSE_HELPER_FLAG,initial]
        result=subprocess.run(cmd,capture_output=True,text=True,timeout=300)
        err=(result.stderr or '').strip()
        path=(result.stdout or '').strip()
        if err: return jsonify({'ok':False,'error':err})
        if not path: return jsonify({'ok':False,'cancelled':True})
        return jsonify({'ok':True,'path':path})
    except subprocess.TimeoutExpired:
        return jsonify({'ok':False,'error':'The folder picker timed out after 5 minutes.'})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})
@app.route('/api/job/<job_id>')
def job(job_id):
    with jobs_lock:return jsonify(jobs.get(job_id,{'status':'error','message':'Unknown job'}))
@app.route('/api/job/<job_id>/pause',methods=['POST'])
def pause_job(job_id):
    c=job_controls.get(job_id)
    if not c:return jsonify({'error':'Unknown job'}),404
    c['paused'].set();c['resume'].clear()
    with jobs_lock:jobs[job_id].update(status='paused',message='Download paused')
    return jsonify({'ok':True})
@app.route('/api/job/<job_id>/resume',methods=['POST'])
def resume_job(job_id):
    c=job_controls.get(job_id)
    if not c:return jsonify({'error':'Unknown job'}),404
    c['paused'].clear();c['resume'].set()
    with jobs_lock:jobs[job_id].update(status='running',message='Download resumed')
    return jsonify({'ok':True})
@app.route('/api/job/<job_id>/stop',methods=['POST'])
def stop_job(job_id):
    c=job_controls.get(job_id)
    if not c:
        # Job already finished (or crashed) and its controls were cleaned up.
        # Report success rather than 404 so the UI doesn't appear stuck.
        with jobs_lock:
            j=jobs.get(job_id)
            if j and j.get('status')=='running':j.update(status='error',message='Job is no longer active.')
        return jsonify({'ok':True,'already_finished':True})
    c['stop'].set();c['paused'].clear();c['resume'].set()
    with jobs_lock:jobs[job_id].update(status='stopping',message='Stopping download...')
    return jsonify({'ok':True})
@app.route('/api/open',methods=['POST'])
def open_path_route():
    p=clean_path(request.get_json(force=True).get('path',''))
    if os.name=='nt':os.startfile(p)
    elif os.name=='posix':
        import subprocess; subprocess.Popen(['open' if 'darwin' in sys.platform else 'xdg-open',p])
    return jsonify({'ok':True})
ALLOWED_CONFIG={'host','namespace','query','output_dir','pagination','sort','csv_mode','custom_fields','open_after','keep_json','log_level','log_type','time_zone'}
@app.route('/api/config/export',methods=['GET','POST'])
def config_export():
    if request.method=='POST':
        data=request.get_json(silent=True) or {}
        cfg=data.get('settings',{}) if isinstance(data,dict) else {}
        if not isinstance(cfg,dict): return jsonify({'error':'Invalid settings.'}),400
    else:
        cfg=load_config()
    safe={k:cfg.get(k) for k in ALLOWED_CONFIG if k in cfg}
    # Never export credentials, even if a caller supplies them.
    safe.pop('token',None); safe.pop('api_token',None); safe.pop('password',None)
    return jsonify({'format':'f5xc-log-tool-config','version':1,'application':'F5 XC Log Downloader','created':datetime.now(timezone.utc).isoformat(),'settings':safe})
@app.route('/api/config/import',methods=['POST'])
def config_import():
    data=request.get_json(force=True);settings=data.get('settings') if isinstance(data,dict) else None
    if not isinstance(settings,dict):return jsonify({'error':'Invalid configuration backup format.'}),400
    safe={k:settings.get(k) for k in ALLOWED_CONFIG if k in settings}
    safe['host']=normalize_host(safe.get('host',''))
    safe['output_dir']=clean_path(safe.get('output_dir',''))
    safe.pop('token',None);safe.pop('api_token',None);safe.pop('password',None)
    save_config(safe)
    return jsonify({'ok':True,'settings':safe})
if __name__=='__main__':
    print(f'\nF5 XC Log Downloader V{APP_VERSION}\nOpen http://127.0.0.1:5000 in your browser.')
    app.run(host='127.0.0.1',port=5000,debug=False,threaded=True)

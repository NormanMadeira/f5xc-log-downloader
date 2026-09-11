from flask import Flask, render_template_string, request, jsonify
from pathlib import Path
import csv, json, os, re, sys, threading, time, traceback
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
import requests

APP_VERSION = "5.8"
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
.card:hover{box-shadow:var(--shadow-hover)}
.section-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:17px}
.section-title{display:flex;align-items:flex-start;gap:11px}.num{
 flex:0 0 auto;width:29px;height:29px;border-radius:9px;background:#2563eb14;color:var(--accent);
 display:grid;place-items:center;font-weight:800
}
.title-text h3{margin:1px 0 2px;font-size:15px}.hint{font-size:12px;color:var(--muted);font-weight:450;max-width:760px}
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
  <button id="lightBtn" onclick="setTheme('light')">☀ Light</button><button id="darkBtn" onclick="setTheme('dark')">☾ Dark</button>
 </div></div>
</div></header>

<main>
<div class="hero"><h2>F5 XC Log Downloader</h2><p>Download Access, Security / Firewall, or Audit logs from F5 Distributed Cloud and export them to CSV.</p></div>

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
 <div class="section-head"><div class="section-title"><div class="num">2</div><div class="title-text"><h3>Log Type</h3><div class="hint">Choose which F5 XC log API to query. Access logs cover application traffic, Security / Firewall logs contain WAF/policy events, and Audit logs record configuration/API activity.</div></div></div></div>
 <div class="choice-grid">
  <div class="choice"><input type="radio" id="typeAccess" name="log_type" value="access" checked><label for="typeAccess"><strong>Access Logs</strong><span>Application requests and responses</span></label></div>
  <div class="choice"><input type="radio" id="typeFirewall" name="log_type" value="firewall"><label for="typeFirewall"><strong>Security / Firewall</strong><span>WAF events and policy hits</span></label></div>
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
  <div class="full"><div class="help" id="utc_preview">API time preview: enter a start and end time to see the UTC values that will be sent to F5 XC.</div></div>
</div>
</div>

<div class="card">
 <div class="section-head"><div class="section-title"><div class="num">5</div><div class="title-text"><h3>Query</h3><div class="hint">All matching logs is the default. Select Advanced Query to filter using the same <code>{field="value"}</code> syntax shown when you view a log as JSON in the XC portal.</div></div></div></div>
 <div class="choice-grid two">
  <div class="choice"><input type="radio" id="qall" name="qmode" value="all" checked><label for="qall"><strong>All matching logs</strong><span>No additional filter</span></label></div>
  <div class="choice"><input type="radio" id="qadvanced" name="qmode" value="advanced"><label for="qadvanced"><strong>Advanced Query</strong><span>Enter XC syntax directly</span></label></div>
 </div><br>
 <div id="advanced" class="hidden">
 <label class="field">Advanced F5 XC query</label>
 <textarea id="advanced_query" placeholder='{vh_name="uat-load-balancer-3"}'></textarea>
 <div class="help">
  <b>Syntax:</b> <code>{field="value"}</code>, comma-separated matchers are combined with logical <b>AND</b>. Operators: <code>=</code> equal, <code>!=</code> not equal, <code>=~</code> regex match, <code>!~</code> not-regex-match, e.g. <code>rsp_code=~"5.*"</code> for all 5xx codes.<br><br>
  <b>Only the fields below can be used in a query filter</b> for each log type (per F5's own API schema - this is the full allowed list, not just examples; it's a different, shorter list than the many fields present in a returned log record):<br>
  <b>Access:</b> app_type, vh_name, src_site, src, src_instance, dst_site, dst, dst_instance, method, req_path, rsp_code, browser_type, city, country, device_type<br>
  &nbsp;&nbsp;e.g. <code>{src="service1",dst="service2"}</code> &nbsp; <code>{vh_name="vh1",rsp_code=~"4.*"}</code><br>
  <b>Firewall / Security:</b> site, src_ip, dst_ip, policy_hits.policy, policy_hits.policy_rule, policy_hits.result (allow|deny|default_deny)<br>
  &nbsp;&nbsp;e.g. <code>{site="site-1"}</code> &nbsp; <code>{policy_hits.result="deny"}</code><br>
  <b>Audit:</b> user, src_site, src, src_instance, dst_site, dst, dst_instance, method, req_path, rsp_code<br>
  &nbsp;&nbsp;e.g. <code>{user="abc",rsp_code="404"}</code><br><br>
  Full schema reference (requires your XC API Developer Portal login):
  <a href="https://docs.cloud.f5.com/docs-v2/api/log#operation/ves.io.schema.log.CustomAPI.AccessLogQueryV2" target="_blank" rel="noopener">Access Log Query V2</a> ·
  <a href="https://docs.cloud.f5.com/docs-v2/api/log#operation/ves.io.schema.log.CustomAPI.FirewallLogQuery" target="_blank" rel="noopener">Firewall Log Query</a> ·
  <a href="https://docs.cloud.f5.com/docs-v2/api/log#operation/ves.io.schema.log.CustomAPI.AuditLogQueryV2" target="_blank" rel="noopener">Audit Log Query V2</a>
 </div>
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
  <div><label class="field">Output directory</label><div style="display:flex;gap:8px"><input id="output_dir" required value="{{ config.get('output_dir','') }}" placeholder="<output-directory>" style="flex:1"><button type="button" class="btn" onclick="openBrowseModal()">Browse…</button></div><div class="help">The tool removes common invisible Unicode formatting characters from pasted paths.</div></div>
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

<div id="browseModalBackdrop" class="modal-backdrop hidden" onclick="if(event.target===this)closeBrowseModal()">
  <div class="modal">
   <h3 style="margin-top:0">Select output folder</h3>
   <div style="display:flex;gap:8px;margin-bottom:11px"><input id="browsePath" style="flex:1" placeholder="Path"><button type="button" class="btn" onclick="browseGo($('browsePath').value,'')">Go</button></div>
   <div id="browseUp" class="help" style="cursor:pointer;margin-bottom:7px;min-height:15px"></div>
   <div id="browseList" style="max-height:300px;overflow:auto;border:1px solid var(--line);border-radius:10px"></div>
   <div style="display:flex;justify-content:flex-end;gap:9px;margin-top:15px"><button type="button" class="btn" onclick="closeBrowseModal()">Cancel</button><button type="button" class="btn primary" onclick="selectBrowseFolder()">Select This Folder</button></div>
  </div>
</div>
</main>

<script>
const $=id=>document.getElementById(id);
function setTheme(t){document.documentElement.dataset.theme=t;localStorage.setItem('f5xc_theme',t);$('lightBtn').classList.toggle('active',t==='light');$('darkBtn').classList.toggle('active',t==='dark')}
setTheme(localStorage.getItem('f5xc_theme')||'light');

/* ---- Themed dropdown: wraps a hidden native <select> so existing .value / onchange code keeps working ---- */
function enhanceSelect(sel){
 const wrap=document.createElement('div');wrap.className='xdd';
 const btn=document.createElement('button');btn.type='button';btn.className='xdd-btn';
 const panel=document.createElement('div');panel.className='xdd-panel';
 function sync(){
  const o=sel.options[sel.selectedIndex];
  btn.textContent=o?o.text:'';
  panel.querySelectorAll('.xdd-opt').forEach(d=>d.classList.toggle('sel',d.dataset.value===sel.value));
 }
 [...sel.options].forEach(o=>{
  const d=document.createElement('div');d.className='xdd-opt'+(o.selected?' sel':'');d.textContent=o.text;d.dataset.value=o.value;
  d.onclick=()=>{sel.value=o.value;sync();sel.dispatchEvent(new Event('change',{bubbles:true}));wrap.classList.remove('open')};
  panel.appendChild(d);
 });
 btn.onclick=e=>{e.stopPropagation();document.querySelectorAll('.xdd.open').forEach(x=>{if(x!==wrap)x.classList.remove('open')});wrap.classList.toggle('open')};
 wrap.appendChild(btn);wrap.appendChild(panel);
 sel.parentNode.insertBefore(wrap,sel.nextSibling);
 sync();
 sel._xddSync=sync;
 return wrap;
}
document.addEventListener('click',()=>document.querySelectorAll('.xdd.open').forEach(x=>x.classList.remove('open')));
document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.xdd.open').forEach(x=>x.classList.remove('open'))});
document.querySelectorAll('select.xdd-native').forEach(enhanceSelect);

/* ---- Time range ---- */
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
 updatePreview();updateTimePreview();
}
function todayRange(){
 const n=new Date(),z=document.querySelector('input[name=timeZone]:checked').value,offset=z==='IST'?330:0,local=new Date(n.getTime()+offset*60000),e=new Date(Date.UTC(local.getUTCFullYear(),local.getUTCMonth(),local.getUTCDate())-offset*60000);
 settingRangeProgrammatically=true;
 $('start').value=formatInputTime(e,z);$('end').value=formatInputTime(n,z);
 settingRangeProgrammatically=false;
 updatePreview();updateTimePreview();
}
function yesterdayRange(){
 const n=new Date(),z=document.querySelector('input[name=timeZone]:checked').value,offset=z==='IST'?330:0,local=new Date(n.getTime()+offset*60000),mid=new Date(Date.UTC(local.getUTCFullYear(),local.getUTCMonth(),local.getUTCDate())-offset*60000),s=new Date(mid.getTime()-86400000);
 settingRangeProgrammatically=true;
 $('start').value=formatInputTime(s,z);$('end').value=formatInputTime(mid,z);
 settingRangeProgrammatically=false;
 updatePreview();updateTimePreview();
}
$('range_preset').onchange=()=>{
 const v=$('range_preset').value;
 if(v==='custom')return;
 if(v==='today')todayRange();else if(v==='yesterday')yesterdayRange();else setRange(+v);
};
document.querySelectorAll('input[name=timeZone]').forEach(x=>x.onchange=()=>{
 const v=$('range_preset').value;
 if(v==='today')todayRange();else if(v==='yesterday')yesterdayRange();else if(v!=='custom')setRange(+v);
 updateTimeLabels();
});
['start','end'].forEach(id=>$(id).addEventListener('input',()=>{
 if(!settingRangeProgrammatically){$('range_preset').value='custom';$('range_preset')._xddSync()}
 updateTimePreview();updatePreview();
}));
setRange(10);

/* ---- Log type / query mode ---- */
function selectedType(){return document.querySelector('input[name=log_type]:checked').value}
function refreshQueryMode(){
 const m=document.querySelector('input[name=qmode]:checked').value;
 $('advanced').classList.toggle('hidden',m!=='advanced');
 updatePreview();
}
document.querySelectorAll('input[name=log_type]').forEach(x=>x.onchange=updatePreview);
document.querySelectorAll('input[name=qmode]').forEach(x=>x.onchange=refreshQueryMode);
$('advanced_query').addEventListener('input',updatePreview);
$('csv_mode').addEventListener('change',()=>$('custom_wrap').classList.toggle('hidden',$('csv_mode').value!=='3'));
function query(){
 const m=document.querySelector('input[name=qmode]:checked').value;
 return m==='advanced' ? $('advanced_query').value.trim() : '';
}
function updatePreview(){$('preview').textContent=query()||'<ALL MATCHING LOGS>'}
function collect(){return {log_type:selectedType(),host:$('host').value,namespace:$('namespace').value,token:$('token').value,start_time:parseUserTime($('start').value,document.querySelector('input[name=timeZone]:checked').value),end_time:parseUserTime($('end').value,document.querySelector('input[name=timeZone]:checked').value),query:query(),pagination:document.querySelector('input[name=paginationChoice]:checked').value,sort:$('sort').value,csv_mode:$('csv_mode').value,custom_fields:$('custom_fields').value,output_dir:$('output_dir').value,log_level:$('log_level').value,keep_json:$('keep_json').checked,open_after:$('open_after').checked,time_zone:document.querySelector('input[name=timeZone]:checked').value}}
let activeJob=null,paused=false;
$('form').onsubmit=async e=>{
 e.preventDefault();$('download').disabled=true;$('pauseBtn').classList.remove('hidden');$('stopBtn').classList.remove('hidden');$('pauseBtn').textContent='Ⅱ Pause';paused=false;
 $('progress_wrap').classList.remove('hidden');$('results').classList.add('hidden');$('status').textContent='Starting download...';$('status').className='status';clearLog();const payload=collect();
 if(!payload.start_time||!payload.end_time){$('status').textContent='Invalid time. Pick a valid start and end date/time.';$('status').className='status error';$('download').disabled=false;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden');return}
 if(Date.now()-new Date(payload.start_time)>8*24*60*60*1000){$('status').textContent="Start time is more than 8 days ago. This F5 XC log API appears to only accept requests where the start time is within the last 8 days (confirmed through testing — a 24-hour window starting 8+ days ago was still rejected). Move the start time closer to now and try again.";$('status').className='status error';$('download').disabled=false;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden');return}
 try{const r=await fetch('/api/download',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const j=await r.json();if(!r.ok)throw new Error(j.error||'Download failed');activeJob=j.job_id;poll(activeJob,payload)}
 catch(err){$('status').textContent=err.message;$('status').className='status error';$('download').disabled=false;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden')}
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
   $('download').disabled=false;$('pauseBtn').classList.add('hidden');$('stopBtn').classList.add('hidden');$('stopBtn').disabled=false;
   if(j.status==='complete'){$('status').className='status '+(j.complete?'success':'warning');$('results').classList.remove('hidden');$('files').innerHTML=`<div class="result-file">CSV: ${j.csv||''}</div>${j.json?`<div class="result-file">JSON: ${j.json}</div>`:''}<div class="result-file">Debug log: ${j.debug||''}</div>`;$('status').textContent=j.complete?'✓ Download complete — count validated.':'⚠ Download complete — count warning.';if(payload.open_after&&j.csv)fetch('/api/open',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:j.csv})})}
   else {$('status').className='status '+(j.status==='stopped'?'warning':'error');$('status').textContent=j.status==='stopped'?'Download stopped by user':'✕ '+(j.message||'The job could not be found. It may have failed to start — check the output directory and try again.')}
 }else setTimeout(()=>poll(id,payload),700)
};
function clearLog(){$('log').innerHTML='<span class="log-line">Log cleared.</span>'}
/* ---- Output folder browser (server-side, since this app and browser run on the same machine) ---- */
let browseCurrentPath='';
function openBrowseModal(){$('browseModalBackdrop').classList.remove('hidden');browseGo($('output_dir').value||'','')}
function closeBrowseModal(){$('browseModalBackdrop').classList.add('hidden')}
async function browseGo(path,child){
 const params=new URLSearchParams();if(path)params.set('path',path);if(child)params.set('child',child);
 $('browseList').innerHTML='<div style="padding:12px;color:var(--muted)">Loading…</div>';
 try{
  const r=await fetch('/api/browse?'+params.toString());const j=await r.json();
  if(!r.ok||j.error){$('browseList').innerHTML='<div style="padding:12px;color:var(--bad)">'+(j.error||'Could not browse this path.')+'</div>';return}
  browseCurrentPath=j.path;$('browsePath').value=j.path;
  $('browseUp').innerHTML=(j.parent!=null)?'⬆ Up one level':'';
  $('browseUp').onclick=(j.parent!=null)?(()=>browseGo(j.parent,'')):null;
  const list=$('browseList');list.innerHTML='';
  if(!j.dirs.length){list.innerHTML='<div style="padding:12px;color:var(--muted)">No subfolders here.</div>'}
  j.dirs.forEach(d=>{
   const row=document.createElement('div');row.style.cssText='padding:9px 13px;cursor:pointer;border-bottom:1px solid var(--line)';row.textContent='📁 '+d;
   row.onclick=()=>browseGo(j.is_root_list?d:j.path,j.is_root_list?'':d);
   row.onmouseenter=()=>row.style.background='var(--surface-soft)';row.onmouseleave=()=>row.style.background='';
   list.appendChild(row);
  });
 }catch(e){$('browseList').innerHTML='<div style="padding:12px;color:var(--bad)">Could not reach the local server: '+e.message+'</div>'}
}
function selectBrowseFolder(){$('output_dir').value=browseCurrentPath||$('browsePath').value;closeBrowseModal()}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeBrowseModal()});
/* ---- Check Range: quick single-record probe against F5 XC, without running a full download ---- */
async function checkRange(){
 const payload=collect();
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
refreshQueryMode();updatePreview();updateTimeLabels();updateTimePreview();
</script>
</body>
</html>
'''
app = Flask(__name__)

HOME = Path.home()
CONFIG_FILE = HOME / ".f5xc_access_log_tool_v5.json"
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

# Common CSV field set, chosen from real Access/Firewall/Audit log field names
# (Firewall/Security events use action / sec_event_type / waf_mode - not policy_hits.*).
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
    total_hits=None; received=0; batch=1; sort_values=None; complete=True; started=time.perf_counter()
    try:
        output_dir=Path(clean_path(cfg["output_dir"])).expanduser()
        try:
            output_dir.mkdir(parents=True,exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Cannot create or access output directory '{output_dir}': {e.strerror or e}. Check the path and your permissions, then try again.") from e
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); typ=cfg.get("log_type","access")
        label={"access":"access","audit":"audit","firewall":"security_firewall"}.get(typ,typ)
        base=output_dir/f"f5xc_{label}_logs_{stamp}"; csv_path=base.with_suffix('.csv'); json_path=base.with_suffix('.json'); log_path=base.with_suffix('.debug.log'); jsonl_path=base.with_suffix('.jsonl')
        token=cfg["token"]; host=normalize_host(cfg["host"]); ns=cfg["namespace"].strip(); query=str(cfg.get("query","")).strip(); pagination=cfg.get("pagination","search_after"); sort=cfg.get("sort","ASCENDING")
        try:
            start=rfc3339(cfg["start_time"]); end=rfc3339(cfg["end_time"])
        except Exception as e:
            raise RuntimeError(f"Invalid start/end time: {e}") from e
        batch_size=500
        endpoints={"access":("access_logs","Access Log Query V2"),"audit":("audit_logs","Audit Log Query V2"),"firewall":("firewall_logs","Firewall Log Query")}
        if typ not in endpoints:
            raise RuntimeError(f"Unknown log type '{typ}'")
        resource,opname=endpoints[typ]; url=f"https://{host}/api/data/namespaces/{ns}/{resource}"; scroll_url=url+"/scroll"
        session=requests.Session(); session.headers.update({"Authorization":f"APIToken {token}","Content-Type":"application/json","Accept":"application/json","User-Agent":f"F5XC-Log-Tool/{APP_VERSION}"})
        def api(url,payload,op):
            for attempt in range(1,6):
                control_wait(job_id)
                t=time.perf_counter(); safe=dict(payload)
                if "scroll_id" in safe:safe["scroll_id"]=f"<MASKED length={len(str(payload['scroll_id']))}>"
                log(f"{op} | POST {url}"); log(f"Request: {json.dumps(safe,ensure_ascii=False)}","DEBUG")
                try:
                    resp=session.post(url,json=payload,timeout=60); elapsed=time.perf_counter()-t; log(f"HTTP {resp.status_code} | {len(resp.content):,} bytes | {elapsed:.3f}s")
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
        if pagination=="search_after":
            # Confirmed through testing: F5 XC's Log Query V2 response does NOT
            # reliably include last_sort_values even when "search_after" is requested -
            # the field F5's own release notes tie search_after to is on the *Scroll*
            # endpoint, not this one. We still ask for it (harmless if ignored), but we
            # also request "scroll":true so the response includes a scroll_id we can
            # fall back to - that field IS confirmed to work for pagination.
            payload["search_after"]=True
            payload["scroll"]=True
            log("Search After pagination requested (with scroll_id fallback enabled, since F5 XC may not return last_sort_values directly)")
        else:
            # V2 scroll workflow: the initial query must explicitly enable scroll.
            # Without this flag F5 XC legitimately returns the first 500 records
            # without a scroll_id, so the downloader cannot request batch 2.
            payload["scroll"]=True
            log("Scroll pagination enabled: initial query requests a scroll_id")
        with jsonl_path.open('w',encoding='utf-8') as jf:
            response=None
            while True:
                control_wait(job_id)
                if response is None:
                    if pagination=="search_after" and sort_values is not None: payload["sort_values"]=sort_values
                    response=api(url,payload,opname)
                if total_hits is None: total_hits=response.get("total_hits"); log(f"F5 total_hits: {total_hits}")
                logs=response.get("logs") or []; log(f"Batch {batch}: {len(logs):,} records")
                if not logs: break
                control_wait(job_id)
                for raw in logs: jf.write(json.dumps(parse_record(raw),ensure_ascii=False,separators=(",",":"))+"\n")
                received+=len(logs); reported=int(total_hits) if str(total_hits).isdigit() else -1; pct=100 if reported<=0 else min(100,received/reported*100); update(received=received,total_hits=total_hits,batch=batch,percent=pct); log(f"Accumulated: {received:,} | Progress: {pct:.2f}%")
                if reported>=0 and received>=reported: break
                if pagination=="search_after":
                    sort_values=response.get("last_sort_values") or response.get("sort_values")
                    sid=response.get("scroll_id","")
                    if sort_values:
                        log("Continuing via last_sort_values.","DEBUG"); response=None; batch+=1
                    elif sid:
                        log("No last_sort_values in response; continuing via scroll_id instead.","WARN")
                        control_wait(job_id)
                        response=api(scroll_url,{"namespace":ns,"scroll_id":sid},opname.replace('Query','Scroll')); batch+=1
                    else:
                        if len(logs)<batch_size: break
                        complete=False
                        raise RuntimeError(f"F5 XC did not return a continuation token (last_sort_values or scroll_id) after {received:,} of {total_hits} records, so the remaining records can't be fetched. Try switching Pagination to 'Scroll', or narrow the time range and download in smaller chunks.")
                else:
                    sid=response.get("scroll_id",""); log(f"scroll_id received: {'YES (masked)' if sid else 'NO'}","DEBUG")
                    if not sid: break
                    control_wait(job_id)
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
def index():return render_template_string(INDEX_HTML,config=load_config(),version=APP_VERSION,config_path=str(CONFIG_FILE))
@app.route('/api/config',methods=['GET'])
def config_get():return jsonify(load_config())
@app.route('/api/download',methods=['POST'])
def download():
    data=request.get_json(force=True); required=['host','namespace','token','start_time','end_time','output_dir']
    missing=[x for x in required if not str(data.get(x,'' )).strip()]
    if missing:return jsonify({'error':'Missing required fields: '+', '.join(missing)}),400
    data['host']=normalize_host(data['host']); data['output_dir']=clean_path(data['output_dir']); data['log_type']=data.get('log_type','access'); data['pagination']=data.get('pagination','search_after'); data['sort']=data.get('sort','ASCENDING')
    if data['log_type'] not in {'access','audit','firewall'}:return jsonify({'error':'Invalid log type'}),400
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
    typ=data.get('log_type','access'); endpoints={"access":("access_logs","Access Log Query V2"),"audit":("audit_logs","Audit Log Query V2"),"firewall":("firewall_logs","Firewall Log Query")}
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
@app.route('/api/browse')
def browse():
    # Server and browser run on the same local machine, so this just lists real
    # folders on disk - the same trust boundary the app already has via the
    # freely-typed Output directory field and the Open-file button.
    p=clean_path(request.args.get('path','')); child=clean_path(request.args.get('child',''))
    try:
        if child: p=str(Path(p)/child) if p else child
        if not p:
            if os.name=='nt':
                import string
                drives=[f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
                return jsonify({'path':'','parent':None,'dirs':drives,'is_root_list':True})
            p='/'
        path=Path(p)
        if not path.exists() or not path.is_dir():
            return jsonify({'error':f"Path not found: {p}"}),400
        try:
            entries=sorted([e.name for e in path.iterdir() if e.is_dir()],key=str.lower)
        except PermissionError:
            return jsonify({'error':f"Permission denied: {p}"}),403
        is_drive_root=os.name=='nt' and str(path)==path.anchor
        parent='' if is_drive_root else (str(path.parent) if path.parent!=path else None)
        return jsonify({'path':str(path),'parent':parent,'dirs':entries,'is_root_list':False})
    except Exception as e:
        return jsonify({'error':str(e)}),400
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
    app.run(host='127.0.0.1',port=5000,debug=False)

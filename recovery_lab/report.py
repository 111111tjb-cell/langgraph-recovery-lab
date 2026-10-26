from __future__ import annotations

import html
import json
from pathlib import Path

VERDICT_TEXT = {
    "observed-fix": "Baseline lost completed work; candidate preserved it.",
    "same-implementation": "Both environments loaded the same implementation. No fix comparison is established.",
    "candidate-check-failed": "At least one candidate recovery check failed.",
    "baseline-bug-not-reproduced": "Candidate checks passed, but the baseline bug was not observed. No fix comparison is established.",
    "runtime-changed": "A loaded runtime changed between worker stages or runs. The comparison is inconclusive.",
}


def rows(report: dict):
    for label in ("baseline", "candidate"):
        for number, case in enumerate(report[label], start=1):
            yield label, number, case


def markdown_report(report: dict) -> str:
    lines = [
        "# Recovery experiment",
        "",
        VERDICT_TEXT[report["verdict"]],
        "",
        f"Generated: {report['generated_at']} (UTC).",
        "",
        "These are measured local observations of a synthetic failure, not a throughput benchmark or an exactly-once guarantee.",
        "",
        "| Environment | Case | Execution | Durability | Async policy | B completed before exit | B saved | B total calls | Observation |",
        "|---|---:|---|---|---|---|---|---:|---|",
    ]
    for label, number, case in rows(report):
        options = case["options"]
        assessment = case["assessment"]
        lines.append(
            f"| {label} | {number} | {options['mode']} | {options['durability']} | "
            f"{options['async_policy'] if options['mode'] == 'async' else '-'} | "
            f"{assessment['slow_completed_before_exit']} | {assessment['slow_result_saved']} | "
            f"{assessment['slow_total_calls']} | {assessment['observation']} |"
        )
    lines.extend(["", "## Loaded runtimes", ""])
    if "source_verification" in report:
        lines.extend(
            [
                "Expected source references are checked against loaded source fingerprints:",
                "",
                "```json",
                json.dumps(report["source_verification"], indent=2),
                "```",
                "",
            ]
        )
    for label in ("baseline", "candidate"):
        runtime = report[label][0]["stages"][0]["runtime"]
        lines.extend(
            [
                f"### {label}",
                "",
                f"Python {runtime['python']}, {runtime['platform']}",
                "",
                "```json",
                json.dumps(runtime, indent=2),
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "- A is `flaky`: it intentionally fails once and should have two total calls after recovery.",
            "- B is `slow`: if it completed during the failed attempt, its saved result should prevent a second call.",
            "- An async B that honors cancellation has no completed result to preserve; retrying it is expected.",
            "- The fail and resume stages use independent Python processes with the same SQLite files.",
            "- Inspect `comparison.json`, per-stage stderr and trace files for the underlying observations.",
            "- A missing reproduction is reported explicitly; it is not evidence of an improvement.",
            "",
        ]
    )
    return "\n".join(lines)


def svg_report(report: dict) -> str:
    baseline = report["baseline"][0]["assessment"]
    candidate = report["candidate"][0]["assessment"]
    success = report["verdict"] == "observed-fix"
    accent = "#34d399" if success else "#fbbf24"
    verdict = html.escape(VERDICT_TEXT[report["verdict"]])
    cards = []
    for label, assessment, x in (
        ("BASELINE", baseline, 36),
        ("CANDIDATE", candidate, 516),
    ):
        calls = html.escape(str(assessment["slow_total_calls"]))
        observation = html.escape(assessment["observation"])
        saved = "saved" if assessment["slow_result_saved"] else "not saved"
        cards.append(
            f'<g transform="translate({x},100)">'
            '<rect width="448" height="194" rx="18" fill="#172337" stroke="#2a3b51"/>'
            f'<text x="24" y="34" class="label">{label}</text>'
            f'<text x="24" y="103" class="count">{calls}</text>'
            '<text x="83" y="99" class="body">total calls to node B</text>'
            f'<text x="24" y="142" class="body">B result: {saved}</text>'
            f'<text x="24" y="173" class="small">{observation}</text></g>'
        )
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 392" role="img" '
        'aria-labelledby="title desc">'
        '<title id="title">Measured LangGraph recovery comparison</title>'
        f'<desc id="desc">{verdict} First recorded case from each environment.</desc>'
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#e8eef9}"
        ".title{font-size:25px;font-weight:700}.label{font-size:13px;letter-spacing:2px;fill:#9eb4cf}"
        ".count{font-size:64px;font-weight:700}.body{font-size:17px}.small{font-size:13px;fill:#a9bbd1}</style>"
        '<rect width="1000" height="392" rx="22" fill="#0c1524"/>'
        '<text x="36" y="50" class="title">Does completed work survive a parallel failure?</text>'
        '<text x="36" y="77" class="small">Actual local run · A fails once · B finishes later · SQLite · fresh-process resume</text>'
        + "".join(cards)
        + f'<text x="36" y="329" class="body" style="fill:{accent}">{verdict}</text>'
        '<text x="36" y="359" class="small">First case only. Full matrix and source fingerprints are in comparison.json. No exactly-once guarantee.</text>'
        "</svg>\n"
    )


def html_report(report: dict) -> str:
    payload = json.dumps(report, ensure_ascii=True).replace("<", "\\u003c")
    return (
        """<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LangGraph recovery lab — measured comparison</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#0c1524;color:#e8eef9}
*{box-sizing:border-box}body{max-width:1180px;margin:auto;padding:36px 24px}h1{font-size:clamp(25px,4vw,40px);line-height:1.15;margin:12px 0}
.muted{color:#a9bbd1;line-height:1.65}header{margin-bottom:30px}.eyebrow{font-size:12px;letter-spacing:2px;color:#74d7c2}
.verdict,.card{border:1px solid #2a3b51;border-radius:16px;padding:22px;background:#142135}.verdict{margin:24px 0}
.controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:20px 0}select,button{font:inherit;background:#1e3048;color:inherit;border:1px solid #47607d;border-radius:8px;padding:9px 12px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.metric{font-size:60px;font-weight:750;margin:5px 0}.badge{display:inline-block;background:#24364d;padding:5px 9px;border-radius:6px;font-size:12px}
.events{max-height:370px;overflow:auto;padding-left:22px}.events li{padding:7px 0;line-height:1.4}.events code{color:#74d7c2}small{color:#a9bbd1}details{margin-top:24px}pre{overflow:auto;padding:20px;background:#101c2c;border-radius:12px}a{color:#74d7c2}
table{width:100%;border-collapse:collapse;margin:24px 0}th,td{text-align:left;padding:10px;border-bottom:1px solid #2a3b51}.scroll{overflow:auto}.pass{color:#74d7c2}.warn{color:#fbbf24}
@media(max-width:720px){.grid{grid-template-columns:1fr}body{padding:22px 14px}}
</style>
<header><div class="eyebrow">LANGGRAPH RECOVERY LAB / LOCAL OBSERVATIONS</div>
<h1>Does completed work survive a parallel failure?</h1>
<p class="muted">A fails once. B finishes later. A new Python process resumes the graph from SQLite. Compare actual saved writes and call counts.</p>
</header><div class="verdict" id="verdict"></div>
<div class="controls"><label for="case">Recorded case</label><select id="case"></select><button id="replay">Replay recorded events</button><span class="muted" id="options"></span></div>
<div class="grid" id="cards"></div>
<h2>All observations</h2><div class="scroll"><table><thead><tr><th>Environment</th><th>Case</th><th>Execution / durability</th><th>B saved</th><th>B calls</th><th>Observation</th></tr></thead><tbody id="matrix"></tbody></table></div>
<p class="muted">The timeline uses recorded events from two processes. Replay advances by event, rather than reproducing measured timing. A cancelled node without a result should run again. This experiment does not establish exactly-once external effects or recovery after a hard kill.</p>
<details><summary>Exact runtime versions and source fingerprints</summary><pre id="runtime"></pre></details>
<p class="muted"><a href="comparison.json">Raw JSON</a> · <a href="comparison.md">Markdown report</a> · <a href="https://github.com/langchain-ai/langgraph/issues/9397">Upstream issue #9397</a></p>
<script id="data" type="application/json">"""
        + payload
        + """</script>
<script>
const data=JSON.parse(document.getElementById('data').textContent);
const verdicts={"observed-fix":"Baseline lost completed work; candidate preserved it.","same-implementation":"Same implementation loaded in both environments: no improvement established.","candidate-check-failed":"A candidate recovery check failed.","baseline-bug-not-reproduced":"Baseline bug was not observed: no improvement established.","runtime-changed":"A runtime changed during the experiment: comparison inconclusive."};
const el=id=>document.getElementById(id);let timer=null;
el('verdict').textContent=verdicts[data.verdict];el('verdict').classList.add(data.verdict==='observed-fix'?'pass':'warn');
data.baseline.forEach((c,i)=>{const option=document.createElement('option');option.value=i;option.textContent=`${i+1}. ${c.options.mode} / ${c.options.durability} / ${c.options.async_policy}`;el('case').append(option)});
function render(limit=Infinity){
 const i=Number(el('case').value);el('cards').replaceChildren();
 const options=data.baseline[i].options;el('options').textContent=`${options.delay_ms} ms injected delay; not a benchmark`;
 ['baseline','candidate'].forEach(label=>{
  const c=data[label][i],a=c.assessment,card=document.createElement('section');card.className='card';
  const title=document.createElement('h2');title.textContent=label==='baseline'?'Baseline':'Candidate';
  const metric=document.createElement('div');metric.className='metric';metric.textContent=a.slow_total_calls;
  const caption=document.createElement('p');caption.textContent='total calls to node B';
  const badge=document.createElement('span');badge.className='badge';badge.textContent=a.observation;
  const summary=document.createElement('p');summary.className='muted';summary.textContent=`B result saved: ${a.slow_result_saved}. Separate processes: ${a.different_processes}.`;
  const events=document.createElement('ol');events.className='events';
  c.trace.slice(0,limit).forEach(event=>{const li=document.createElement('li'),code=document.createElement('code');code.textContent=event.event;li.append(code,document.createTextNode(` ${event.node||''}`));const note=document.createElement('div');note.className='muted';note.textContent=`${event.stage} process ${event.pid}, +${event.elapsed_ms} ms${event.saved_channels?' · saved: '+event.saved_channels.join(', '):''}`;li.append(note);events.append(li)});
  card.append(title,metric,caption,badge,summary,events);el('cards').append(card);if(limit!==Infinity)events.scrollTop=events.scrollHeight
 });
 el('runtime').textContent=JSON.stringify({source_verification:data.source_verification,baseline:data.baseline[i].stages[0].runtime,candidate:data.candidate[i].stages[0].runtime},null,2)
}
['baseline','candidate'].forEach(label=>data[label].forEach((c,i)=>{const tr=document.createElement('tr');[label,i+1,c.options.mode+' / '+c.options.durability,c.assessment.slow_result_saved,c.assessment.slow_total_calls,c.assessment.observation].forEach(value=>{const td=document.createElement('td');td.textContent=String(value);tr.append(td)});el('matrix').append(tr)}));
el('case').addEventListener('change',()=>{clearInterval(timer);render()});
el('replay').addEventListener('click',()=>{clearInterval(timer);let count=0;const i=Number(el('case').value),maximum=Math.max(data.baseline[i].trace.length,data.candidate[i].trace.length);render(0);timer=setInterval(()=>{render(++count);if(count>=maximum)clearInterval(timer)},400)});
render();
</script></html>
"""
    )


def write_reports(directory: Path, report: dict) -> None:
    (directory / "comparison.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (directory / "comparison.md").write_text(markdown_report(report), encoding="utf-8")
    (directory / "comparison.svg").write_text(svg_report(report), encoding="utf-8")
    (directory / "index.html").write_text(html_report(report), encoding="utf-8")

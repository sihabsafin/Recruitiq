import streamlit as st
import streamlit.components.v1 as components
from utils.styles import inject_styles, page_header, section_title

st.set_page_config(page_title="Analytics · RecruitIQ", layout="wide")
inject_styles()
page_header("📈", "Hiring Analytics", "Score distributions · Funnel drop-off · Pipeline health")

candidates = st.session_state.get("screened_candidates", [])
pipeline   = st.session_state.get("pipeline", {})

if not candidates:
    st.warning("⚠️ No data yet. Complete **Resume Screening** to see analytics.")
    st.stop()

def safe_score(c):
    try: return float(str(c.get("ai_score",0)).replace("%",""))
    except: return 0

def safe_sem(c):
    try: return float(str(c.get("semantic_score",0)).replace("%",""))
    except: return 0

scores      = [safe_score(c) for c in candidates]
avg_score   = sum(scores)/len(scores) if scores else 0
max_score   = max(scores) if scores else 0
min_score   = min(scores) if scores else 0
shortlisted = sum(1 for c in candidates if "shortlist" in str(c.get("recommendation","")).lower())
rejected    = sum(1 for c in candidates if "reject"    in str(c.get("recommendation","")).lower())
on_hold     = len(candidates) - shortlisted - rejected

# ── KPI row ───────────────────────────────────────────────────────────────────
col1,col2,col3,col4,col5,col6 = st.columns(6)
col1.metric("Total Screened",  len(candidates))
col2.metric("Avg AI Score",    f"{avg_score:.0f}%")
col3.metric("Top Score",       f"{max_score:.0f}%")
col4.metric("Shortlisted",     shortlisted)
col5.metric("Rejected",        rejected)
col6.metric("Shortlist Rate",  f"{shortlisted/len(candidates)*100:.0f}%" if candidates else "0%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Score distribution — components.html to avoid raw HTML bug ───────────────
section_title("Score Distribution")

buckets = {"0–20":0,"21–40":0,"41–60":0,"61–80":0,"81–100":0}
for s in scores:
    if   s <= 20:  buckets["0–20"]   += 1
    elif s <= 40:  buckets["21–40"]  += 1
    elif s <= 60:  buckets["41–60"]  += 1
    elif s <= 80:  buckets["61–80"]  += 1
    else:          buckets["81–100"] += 1

max_b = max(buckets.values()) if max(buckets.values()) > 0 else 1
bar_colors = ["#ef4444","#f87171","#fbbf24","#a78bfa","#22c55e"]
total_c = len(candidates)

bars_html = ""
for (label, count), color in zip(buckets.items(), bar_colors):
    h   = max(count / max_b * 160, 4) if count > 0 else 0
    pct = count/total_c*100 if total_c else 0
    bars_html += f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:6px;flex:1;">
        <div style="font-size:14px;font-weight:700;color:{color};">{count}</div>
        <div style="width:70%;background:{color};border-radius:4px 4px 0 0;height:{h}px;min-height:{'4px' if count>0 else '0'};"></div>
        <div style="font-size:11px;color:rgba(232,230,240,0.5);text-align:center;">{label}</div>
        <div style="font-size:10px;color:rgba(232,230,240,0.3);">{pct:.0f}%</div>
    </div>"""

components.html(f"""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>* {{box-sizing:border-box;margin:0;padding:0;}} body {{background:transparent;}}</style>
</head><body>
<div style="background:#0d0d14;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px 32px;">
    <div style="display:flex;align-items:flex-end;gap:8px;height:200px;justify-content:space-around;
    border-bottom:1px solid rgba(255,255,255,0.08);padding-bottom:0;">
        {bars_html}
    </div>
    <div style="font-family:'DM Sans',sans-serif;font-size:11px;color:rgba(232,230,240,0.3);
    text-align:center;margin-top:12px;">AI Match Score Ranges</div>
</div>
</body></html>""", height=260)

st.markdown("<br>", unsafe_allow_html=True)

# ── Recommendation split + AI vs Semantic ────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    section_title("Recommendation Split")
    rec_data = [("Shortlisted",shortlisted,"#22c55e"),("On Hold",on_hold,"#fbbf24"),("Rejected",rejected,"#ef4444")]
    for label, count, color in rec_data:
        pct = count/total_c*100 if total_c else 0
        st.markdown(f"""
<div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>
    <div style='width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;'></div>
    <div style='font-family:DM Sans;font-size:13px;color:#e8e6f0;width:100px;'>{label}</div>
    <div style='flex:1;background:rgba(255,255,255,0.05);border-radius:99px;height:8px;overflow:hidden;'>
        <div style='background:{color};height:100%;width:{pct}%;border-radius:99px;'></div>
    </div>
    <div style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:{color};width:28px;text-align:right;'>{count}</div>
    <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.35);width:34px;'>{pct:.0f}%</div>
</div>""", unsafe_allow_html=True)

with col2:
    section_title("AI vs Semantic Score Comparison")
    for c in sorted(candidates, key=safe_score, reverse=True)[:8]:
        ai_s  = safe_score(c)
        sem_s = safe_sem(c)
        diff  = ai_s - sem_s
        diff_color = "#22c55e" if diff > 5 else ("#ef4444" if diff < -5 else "#fbbf24")
        st.markdown(f"""
<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;
padding:6px 10px;background:#13131f;border-radius:6px;'>
    <div style='font-family:DM Sans;font-size:12px;color:#e8e6f0;flex:1;
    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{c['name'][:20]}</div>
    <div style='font-family:Syne,sans-serif;font-size:12px;font-weight:700;color:#a78bfa;width:36px;text-align:right;'>{ai_s:.0f}%</div>
    <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.3);'>vs</div>
    <div style='font-family:Syne,sans-serif;font-size:12px;font-weight:700;color:#06b6d4;width:36px;text-align:right;'>{sem_s:.0f}%</div>
    <div style='font-family:DM Sans;font-size:11px;color:{diff_color};width:40px;text-align:right;'>{("+" if diff>=0 else "")}{diff:.0f}</div>
</div>""", unsafe_allow_html=True)
    st.markdown("<div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.3);margin-top:6px;'><span style='color:#a78bfa;'>■</span> AI &nbsp;<span style='color:#06b6d4;'>■</span> Semantic &nbsp;<span style='color:rgba(232,230,240,0.3);'>Δ = difference</span></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Pipeline funnel ───────────────────────────────────────────────────────────
section_title("Pipeline Funnel")

STAGES = ["Applied","Screened","Interview","Offer","Hired","Rejected"]
STAGE_COLORS = {"Applied":"#64748b","Screened":"#a78bfa","Interview":"#06b6d4",
                "Offer":"#f59e0b","Hired":"#22c55e","Rejected":"#ef4444"}
stage_counts = {s: len(pipeline.get(s,[])) for s in STAGES} if pipeline else {}
if stage_counts.get("Screened",0) == 0:
    stage_counts["Screened"] = len(candidates)
total_pipe = max(sum(stage_counts.values()), 1)
max_c      = max(stage_counts.values()) if max(stage_counts.values())>0 else 1

funnel_rows = ""
for stage in STAGES:
    count = stage_counts.get(stage,0)
    color = STAGE_COLORS[stage]
    pct   = count/total_pipe*100
    bar_w = count/max_c*100 if max_c else 0
    funnel_rows += f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:14px;">
        <div style="font-family:'DM Sans',sans-serif;font-size:12px;color:rgba(232,230,240,0.5);width:80px;text-align:right;flex-shrink:0;">{stage}</div>
        <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:99px;height:12px;overflow:hidden;">
            <div style="background:{color};height:100%;width:{bar_w}%;border-radius:99px;"></div>
        </div>
        <div style="font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;color:{color};width:28px;">{count}</div>
        <div style="font-family:'DM Sans',sans-serif;font-size:11px;color:rgba(232,230,240,0.3);width:36px;">{pct:.0f}%</div>
    </div>"""

components.html(f"""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;700&display=swap" rel="stylesheet">
<style>* {{box-sizing:border-box;margin:0;padding:0;}} body {{background:transparent;}}</style>
</head><body>
<div style="background:#0d0d14;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px 32px;">
    {funnel_rows}
</div>
</body></html>""", height=len(STAGES)*52 + 48)

st.markdown("<br>", unsafe_allow_html=True)

# ── Top candidates leaderboard ────────────────────────────────────────────────
section_title("Top Candidates Leaderboard")
medals = ["🥇","🥈","🥉","④","⑤"]
for i, cand in enumerate(sorted(candidates, key=safe_score, reverse=True)[:5]):
    s   = safe_score(cand)
    sc  = "#22c55e" if s>=75 else ("#fbbf24" if s>=55 else "#ef4444")
    rec = str(cand.get("recommendation","hold")).lower()
    rl  = "Shortlist" if "shortlist" in rec else ("Reject" if "reject" in rec else "Hold")
    rc  = "#22c55e" if "shortlist" in rec else ("#ef4444" if "reject" in rec else "#fbbf24")
    col1,col2,col3,col4 = st.columns([0.5,3,1,1])
    col1.markdown(f"<div style='font-size:20px;padding-top:8px;text-align:center;'>{medals[i]}</div>", unsafe_allow_html=True)
    col2.markdown(f"<div style='padding:8px 0;'><div style='font-family:DM Sans;font-size:13px;font-weight:500;color:#e8e6f0;'>{cand['name']}</div><div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.35);margin-top:2px;'>{cand.get('email','')}</div></div>", unsafe_allow_html=True)
    col3.markdown(f"<div style='font-family:Syne,sans-serif;font-size:18px;font-weight:800;color:{sc};padding-top:8px;'>{s:.0f}%</div>", unsafe_allow_html=True)
    col4.markdown(f"<div style='background:{rc}18;color:{rc};border:1px solid {rc}44;font-size:12px;padding:4px 12px;border-radius:99px;font-family:DM Sans;display:inline-block;margin-top:8px;'>{rl}</div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(139,92,246,0.07);margin:2px 0;'>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Insights ──────────────────────────────────────────────────────────────────
section_title("Pipeline Insights")
insights = []
if avg_score < 50:
    insights.append(("⚠️","Low average score",f"Average is {avg_score:.0f}%. Consider broadening search or revising JD requirements.","#fbbf24"))
if total_c > 0 and shortlisted/total_c > 0.5:
    insights.append(("✅","High shortlist rate",f"{shortlisted/total_c*100:.0f}% shortlisted — strong candidate pool for this role.","#22c55e"))
if shortlisted == 0:
    insights.append(("🚨","No shortlisted candidates","No candidates meet the bar. Consider relaxing requirements or re-evaluating must-haves.","#ef4444"))
if max_score - min_score > 40:
    insights.append(("📊","High score variance",f"Scores range {min_score:.0f}–{max_score:.0f}%. Clear separation between strong and weak candidates.","#a78bfa"))
if not insights:
    insights.append(("✅","Pipeline looks healthy",f"{len(candidates)} candidates screened, {shortlisted} shortlisted, avg {avg_score:.0f}%.","#22c55e"))

for icon, title, desc, color in insights:
    st.markdown(f"""
<div style='background:{color}08;border:1px solid {color}22;border-left:3px solid {color};
border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:10px;display:flex;gap:12px;'>
    <span style='font-size:18px;'>{icon}</span>
    <div>
        <div style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#e8e6f0;margin-bottom:4px;'>{title}</div>
        <div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.55);line-height:1.5;'>{desc}</div>
    </div>
</div>""", unsafe_allow_html=True)

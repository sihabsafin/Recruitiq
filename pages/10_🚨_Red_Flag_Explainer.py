import streamlit as st
import json
from utils.styles import inject_styles, page_header, section_title
from utils.execution_log import run_crew_with_log
from config import get_llm

st.set_page_config(page_title="Red Flag Explainer · RecruitIQ", layout="wide")
inject_styles()
page_header("🚨", "Red Flag Explainer", "AI deep-dives why a candidate scored low · Evidence-backed · Actionable")

candidates = st.session_state.get("screened_candidates", [])
jd_parsed  = st.session_state.get("current_jd_parsed", {}) or {}

if not candidates:
    st.markdown("""<div style='background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.2);
    border-radius:8px;padding:14px 18px;font-family:DM Sans;font-size:13px;color:#fbbf24;'>
    ⚠️ No screened candidates yet. Complete <strong>Resume Screening</strong> first.</div>""",
    unsafe_allow_html=True)
    st.stop()

# ── Selector ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 2])
name = col1.selectbox("Select Candidate to Analyze", ["— select —"] + [c["name"] for c in candidates])
mode = col2.selectbox("Analysis Mode", [
    "Full red flag deep-dive",
    "Score gap analysis (why low vs JD)",
    "Skills mismatch breakdown",
    "Credibility check (resume claims)",
])

cand = next((c for c in candidates if c["name"] == name), None)
if not cand:
    st.markdown("""<div style='background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.15);
    border-radius:8px;padding:12px 16px;font-family:DM Sans;font-size:13px;
    color:rgba(232,230,240,0.4);margin-top:12px;'>Select a candidate to begin analysis.</div>""",
    unsafe_allow_html=True)
    st.stop()

# ── Score overview ────────────────────────────────────────────────────────────
score = cand.get("ai_score", 0)
try:
    score_f = float(str(score).replace("%",""))
except:
    score_f = 0

score_color = "#22c55e" if score_f >= 75 else ("#fbbf24" if score_f >= 55 else "#ef4444")
screening = cand.get("screening", {}) or {}
red_flags = screening.get("red_flags", []) or []
rec = str(cand.get("recommendation","hold")).lower()

st.markdown(f"""
<div style='background:#0d0d14;border:1px solid rgba(255,255,255,0.07);
border-radius:12px;padding:20px 24px;margin:16px 0;display:flex;align-items:center;gap:24px;flex-wrap:wrap;'>
    <div>
        <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.4);
        text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>AI Match Score</div>
        <div style='font-family:Syne,sans-serif;font-size:36px;font-weight:800;color:{score_color};'>{score_f:.0f}%</div>
    </div>
    <div style='width:1px;height:50px;background:rgba(255,255,255,0.08);'></div>
    <div>
        <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.4);
        text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Quick Red Flags</div>
        {"".join(f"<div style='font-family:DM Sans;font-size:12px;color:#f87171;margin-bottom:3px;'>⚠ {f}</div>" for f in red_flags[:3]) if red_flags else "<div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.3);'>None flagged in initial screening</div>"}
    </div>
    <div style='margin-left:auto;'>
        <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.4);
        text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Recommendation</div>
        <div style='font-family:Syne,sans-serif;font-size:16px;font-weight:700;
        color:{"#22c55e" if "shortlist" in rec else "#ef4444" if "reject" in rec else "#fbbf24"};'>
        {"Shortlist" if "shortlist" in rec else "Reject" if "reject" in rec else "Hold"}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Run analysis ──────────────────────────────────────────────────────────────
if st.button("🔍 Run Deep Analysis", use_container_width=True, type="primary"):

    PROMPTS = {
        "Full red flag deep-dive": f"""You are a senior talent analyst. Do a thorough red flag analysis.

CANDIDATE: {name}
RESUME TEXT (first 2000 chars):
{str(cand.get('resume_text',''))[:2000]}

AI MATCH SCORE: {score_f:.0f}%
EXISTING RED FLAGS: {json.dumps(red_flags)}
SCREENING REPORT: {json.dumps(screening, indent=2)[:1500]}

JOB REQUIREMENTS:
{json.dumps(jd_parsed, indent=2)[:1000]}

Return JSON with:
- severity_rating: critical / high / medium / low
- overall_verdict: 2-3 sentence summary of why this candidate scored low
- red_flags: list of {{flag, evidence_from_resume, impact_on_score, severity}}
- green_flags_ignored: things screeners might overlook that are actually positives
- biggest_risk: the single most concerning issue
- is_worth_second_look: true/false with reason
- questions_to_ask: list of 3 interview questions that would clarify the red flags""",

        "Score gap analysis (why low vs JD)": f"""Analyze why this candidate's score is low relative to the JD requirements.

CANDIDATE: {name}, SCORE: {score_f:.0f}%
SKILLS MATCH: {json.dumps(cand.get('skills_match',{}), indent=2)[:1500]}
JD REQUIREMENTS: {json.dumps(jd_parsed, indent=2)[:1000]}

Return JSON with:
- score_breakdown_analysis: why each section scored what it did
- biggest_gap: the requirement furthest from candidate's profile
- closest_match: what the candidate does well vs JD
- gap_bridgeable: true/false — can gaps be closed with training?
- estimated_ramp_time: how long to get candidate to full productivity
- red_flags: list of {{flag, evidence_from_resume, impact_on_score, severity}}
- overall_verdict: honest 2-3 sentence assessment
- is_worth_second_look: true/false with reason
- questions_to_ask: list of 3 clarifying questions""",

        "Skills mismatch breakdown": f"""Deep dive into skills mismatch between candidate and role.

CANDIDATE: {name}
SKILLS MATCH DATA: {json.dumps(cand.get('skills_match',{}), indent=2)[:2000]}
JD SKILLS REQUIRED: {json.dumps(jd_parsed.get('qualifications_required',[]), indent=2)}

Return JSON with:
- critical_missing_skills: list of skills that are dealbreakers
- partially_met_skills: skills present but at insufficient level
- transferable_skills: candidate has adjacent skills that could substitute
- severity_rating: critical / high / medium / low
- red_flags: list of {{flag, evidence_from_resume, impact_on_score, severity}}
- overall_verdict: 2-3 sentence skills summary
- is_worth_second_look: true/false with reason
- questions_to_ask: list of 3 technical questions to probe weak areas""",

        "Credibility check (resume claims)": f"""Check the credibility and consistency of resume claims.

CANDIDATE: {name}
RESUME TEXT:
{str(cand.get('resume_text',''))[:2500]}

SCREENING REPORT: {json.dumps(screening, indent=2)[:1000]}

Return JSON with:
- credibility_score: 0-100
- suspicious_claims: list of {{claim, why_suspicious, verification_suggestion}}
- timeline_issues: any employment gaps or overlaps
- qualification_inflation: overstated skills or titles
- positive_signals: genuine strong claims
- severity_rating: critical / high / medium / low
- red_flags: list of {{flag, evidence_from_resume, impact_on_score, severity}}
- overall_verdict: 2-3 sentence credibility assessment
- is_worth_second_look: true/false with reason
- questions_to_ask: list of 3 verification questions""",
    }

    with st.spinner("AI is analyzing..."):
        try:
            llm = get_llm(temperature=0.2)
            prompt = PROMPTS[mode]
            response = llm.call([{"role":"user","content":prompt}]) if hasattr(llm,'call') else ""

            try:
                raw = str(response).strip().strip("```json").strip("```").strip()
                result = json.loads(raw)
            except:
                result = {
                    "severity_rating": "medium",
                    "overall_verdict": screening.get("summary","Analysis complete."),
                    "red_flags": [{"flag":f,"evidence_from_resume":"See screening report","impact_on_score":"Medium","severity":"medium"} for f in red_flags[:3]],
                    "is_worth_second_look": score_f >= 55,
                    "biggest_risk": red_flags[0] if red_flags else "No critical risks identified",
                    "questions_to_ask": ["Can you walk me through your most relevant project?","What's your experience with our tech stack?","How do you handle gaps in your knowledge?"],
                }

            st.session_state[f"redflag_{name}"] = result

        except Exception as e:
            st.error(f"Analysis error: {e}")
            st.stop()

# ── Display result ────────────────────────────────────────────────────────────
result = st.session_state.get(f"redflag_{name}")
if result:
    sev = str(result.get("severity_rating","medium")).lower()
    sev_color = {"critical":"#ef4444","high":"#f87171","medium":"#fbbf24","low":"#22c55e"}.get(sev,"#fbbf24")
    worth = result.get("is_worth_second_look", False)

    # Top banner
    st.markdown(f"""
    <div style='background:{sev_color}08;border:1px solid {sev_color}33;
    border-radius:12px;padding:20px 24px;margin:16px 0;'>
        <div style='display:flex;align-items:center;gap:16px;flex-wrap:wrap;'>
            <div>
                <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.4);
                text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Risk Severity</div>
                <div style='font-family:Syne,sans-serif;font-size:22px;font-weight:800;
                color:{sev_color};'>{sev.upper()}</div>
            </div>
            <div style='width:1px;height:44px;background:rgba(255,255,255,0.08);'></div>
            <div style='flex:1;'>
                <div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.7);
                line-height:1.6;'>{result.get("overall_verdict","")}</div>
            </div>
            <div style='background:{"rgba(34,197,94,0.1)" if worth else "rgba(248,113,113,0.1)"};
            border:1px solid {"rgba(34,197,94,0.3)" if worth else "rgba(248,113,113,0.3)"};
            border-radius:8px;padding:10px 16px;text-align:center;'>
                <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.4);
                text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Second Look?</div>
                <div style='font-family:Syne,sans-serif;font-size:16px;font-weight:700;
                color:{"#22c55e" if worth else "#ef4444"};'>{"YES" if worth else "NO"}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Red flags detail
    flags = result.get("red_flags", [])
    if flags:
        section_title(f"Red Flags Identified ({len(flags)})")
        for i, flag in enumerate(flags, 1):
            if not isinstance(flag, dict):
                continue
            fsev = str(flag.get("severity","medium")).lower()
            fc   = {"critical":"#ef4444","high":"#f87171","medium":"#fbbf24","low":"#22c55e"}.get(fsev,"#fbbf24")
            st.markdown(f"""
            <div style='background:#0d0d14;border:1px solid {fc}22;border-left:3px solid {fc};
            border-radius:0 8px 8px 0;padding:14px 16px;margin-bottom:10px;'>
                <div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>
                    <span style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;
                    color:#e8e6f0;'>#{i} · {flag.get("flag","")}</span>
                    <span style='background:{fc}18;color:{fc};font-size:10px;font-weight:600;
                    padding:1px 8px;border-radius:99px;font-family:DM Sans;
                    letter-spacing:0.5px;'>{fsev.upper()}</span>
                </div>
                <div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.5);
                margin-bottom:6px;'><strong style='color:rgba(167,139,250,0.7);'>Evidence:</strong> {flag.get("evidence_from_resume","N/A")}</div>
                <div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.45);'>
                <strong style='color:rgba(167,139,250,0.7);'>Score impact:</strong> {flag.get("impact_on_score","N/A")}</div>
            </div>
            """, unsafe_allow_html=True)

    # Questions to ask
    questions = result.get("questions_to_ask", [])
    if questions:
        section_title("Questions to Clarify Red Flags")
        for i, q in enumerate(questions, 1):
            st.markdown(f"""
            <div style='background:#13131f;border:1px solid rgba(139,92,246,0.12);
            border-radius:8px;padding:12px 16px;margin-bottom:8px;
            font-family:DM Sans;font-size:13px;color:#e8e6f0;line-height:1.6;'>
                <strong style='color:#a78bfa;'>{i}.</strong> {q}
            </div>""", unsafe_allow_html=True)

    # Extra fields
    for field, label in [
        ("biggest_risk","Biggest Risk"),("credibility_score","Credibility Score"),
        ("biggest_gap","Biggest Gap"),("gap_bridgeable","Gap Bridgeable?"),
        ("estimated_ramp_time","Ramp Time"),
    ]:
        val = result.get(field)
        if val is not None and val != "N/A":
            st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.6);padding:6px 0;'><strong style='color:#a78bfa;'>{label}:</strong> {val}</div>", unsafe_allow_html=True)

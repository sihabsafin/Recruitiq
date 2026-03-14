import json
import streamlit as st
from utils.styles import inject_styles, page_header, section_title
from utils.execution_log import run_crew_with_log
from crews.crews import run_screening_crew
from utils.resume_parser import parse_resume
from utils.vector_store import match_resume_to_jd, add_resume
from utils.database import save_candidate

st.set_page_config(page_title="Resume Screening · RecruitIQ", layout="wide")
inject_styles()
page_header("🔍", "Resume Screening", "Upload resumes · AI scores & ranks · Shortlist candidates")

if "current_jd_text" not in st.session_state:
    st.markdown("<div style='background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.2);border-radius:8px;padding:14px 18px;font-family:DM Sans;font-size:13px;color:#fbbf24;'>⚠️ No active JD — complete <strong>JD Intake</strong> first.</div>", unsafe_allow_html=True)
    st.stop()

jd_text   = st.session_state["current_jd_text"]
jd_parsed = st.session_state.get("current_jd_parsed", {})
skills    = st.session_state.get("current_skills", {})

with st.expander("Active JD", expanded=False):
    jd_info = jd_parsed if isinstance(jd_parsed, dict) else {}
    st.markdown(f"<span style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.6);'><strong style='color:#a78bfa;'>{jd_info.get('job_title','Job')}</strong> · {jd_info.get('experience_level','')} · {jd_info.get('location','')}</span>", unsafe_allow_html=True)

uploaded = st.file_uploader("Upload Resumes (PDF or DOCX)", type=["pdf","docx","doc"], accept_multiple_files=True)

if uploaded:
    if st.button("🚀 Screen All Resumes", use_container_width=True, type="primary"):
        if "screened_candidates" not in st.session_state:
            st.session_state["screened_candidates"] = []
        progress = st.progress(0, text="Starting...")
        total = len(uploaded)

        for i, file in enumerate(uploaded):
            progress.progress(i/total, text=f"Screening {file.name}...")
            resume_text = parse_resume(file.read(), file.name)
            semantic_score = match_resume_to_jd(resume_text, jd_text)

            try:
                result = run_crew_with_log(
                    run_screening_crew,
                    resume_text, jd_parsed, skills,
                    phase_name=f"Screening: {file.name[:30]}",
                    agents=["Resume Screener", "Skills Matcher"],
                )
                screening = result.get("screening_report", {})
                name  = screening.get("candidate_name", file.name.replace(".pdf","").replace(".docx",""))
                email = screening.get("candidate_email", "N/A")
                ai_score = screening.get("overall_match_score", semantic_score)
                recommendation = screening.get("recommendation", "hold")
                add_resume(f"resume_{i}_{name}", resume_text, {"name": name, "score": ai_score})
                jd_id = st.session_state.get("current_jd_id")
                if jd_id:
                    save_candidate(jd_id, name, email, resume_text, ai_score, screening)
                st.session_state["screened_candidates"].append({
                    "name": name, "email": email, "file": file.name,
                    "semantic_score": semantic_score, "ai_score": ai_score,
                    "recommendation": recommendation,
                    "screening": screening, "skills_match": result.get("skills_match",{}),
                    "resume_text": resume_text,
                })
            except Exception as e:
                st.error(f"Error screening {file.name}: {e}")
                st.session_state["screened_candidates"].append({
                    "name": file.name, "email":"N/A","file":file.name,
                    "semantic_score":semantic_score,"ai_score":semantic_score,
                    "recommendation":"error","screening":{},"skills_match":{},"resume_text":resume_text,
                })
            progress.progress((i+1)/total, text=f"Done: {file.name}")

        st.session_state["resumes_screened"] = st.session_state.get("resumes_screened",0) + total
        progress.progress(1.0, text="All done!")

candidates = st.session_state.get("screened_candidates", [])
if candidates:
    st.markdown("<br>", unsafe_allow_html=True)
    sorted_c = sorted(candidates, key=lambda x: x["ai_score"], reverse=True)
    shortlisted = sum(1 for c in candidates if "shortlist" in str(c["recommendation"]).lower())
    st.session_state["shortlisted"] = shortlisted

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Screened", len(candidates))
    col2.metric("Shortlisted", shortlisted)
    col3.metric("Avg AI Score", f"{sum(c['ai_score'] for c in candidates)/len(candidates):.0f}%")

    st.markdown("<br>", unsafe_allow_html=True)
    section_title("Candidate Rankings")

    for rank, c in enumerate(sorted_c, 1):
        rec = str(c["recommendation"]).lower()
        rec_label = "Shortlist" if "shortlist" in rec else ("Reject" if "reject" in rec else "Hold")
        rec_color = "#22c55e" if "shortlist" in rec else ("#ef4444" if "reject" in rec else "#fbbf24")
        with st.expander(f"#{rank}  {c['name']}   —   {c['ai_score']:.0f}%   ·   {rec_label}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("AI Match Score", f"{c['ai_score']:.0f}%")
            col2.metric("Semantic Score", f"{c['semantic_score']:.0f}%")
            col3.metric("Recommendation", rec_label)
            tab1, tab2, tab3 = st.tabs(["Screening Report","Skills Match","Resume Text"])
            with tab1:
                s = c.get("screening",{})
                if isinstance(s, dict):
                    if s.get("green_flags"):
                        section_title("Green Flags")
                        for f in s.get("green_flags",[]):
                            st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:#22c55e;padding:5px 10px 5px 12px;border-left:2px solid #22c55e;margin-bottom:5px;background:rgba(34,197,94,0.04);border-radius:0 4px 4px 0;'>✓ {f}</div>", unsafe_allow_html=True)
                    if s.get("red_flags"):
                        section_title("Red Flags")
                        for f in s.get("red_flags",[]):
                            st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:#f87171;padding:5px 10px 5px 12px;border-left:2px solid #f87171;margin-bottom:5px;background:rgba(248,113,113,0.04);border-radius:0 4px 4px 0;'>⚠ {f}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.6);margin-top:12px;line-height:1.6;'>{s.get('summary','')}</div>", unsafe_allow_html=True)
            with tab2:
                sm = c.get("skills_match",{})
                if isinstance(sm, dict):
                    col1, col2 = st.columns(2)
                    col1.metric("Must-Have Coverage", sm.get("must_have_coverage","N/A"))
                    col2.metric("Skills Score", sm.get("overall_skills_score","N/A"))
                    for sk in sm.get("skills_match_breakdown",[])[:10]:
                        if isinstance(sk, dict):
                            found = "✅" if sk.get("found_in_resume") else "❌"
                            st.markdown(f"<div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.6);padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);'>{found} <strong style='color:#e8e6f0;'>{sk.get('skill','')}</strong> — {sk.get('score_0_to_10','?')}/10</div>", unsafe_allow_html=True)
            with tab3:
                st.text_area("", c.get("resume_text",""), height=250, disabled=True, label_visibility="collapsed")
            if st.button(f"➡️ Send {c['name']} to Interview Prep", key=f"send_{rank}"):
                st.session_state["selected_candidate"] = c
                st.success(f"✓ {c['name']} queued for interview prep!")

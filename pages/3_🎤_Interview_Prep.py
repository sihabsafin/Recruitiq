import json
import streamlit as st
import streamlit.components.v1 as components
from utils.styles import inject_styles, page_header, section_title
from utils.execution_log import run_crew_with_log
from crews.crews import run_interview_prep_crew
from utils.database import save_interview_kit

st.set_page_config(page_title="Interview Prep · RecruitIQ", layout="wide")
inject_styles()
page_header("🎤", "Interview Prep", "Tailored question bank · Scoring rubric per candidate")

if "current_jd_parsed" not in st.session_state:
    st.warning("⚠️ Complete **JD Intake** first.")
    st.stop()

candidate = st.session_state.get("selected_candidate")
jd_parsed = st.session_state["current_jd_parsed"]

if candidate:
    st.markdown(f"<div style='background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.15);border-radius:8px;padding:12px 16px;font-family:DM Sans;font-size:13px;color:#22c55e;margin-bottom:16px;'>✓ Candidate: <strong>{candidate['name']}</strong> · AI Score: {candidate.get('ai_score',0):.0f}%</div>", unsafe_allow_html=True)
    screening_summary = candidate.get("screening", {})
else:
    st.markdown("<div style='background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.15);border-radius:8px;padding:12px 16px;font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.5);margin-bottom:16px;'>No candidate selected — generating generic kit.</div>", unsafe_allow_html=True)
    cand_name = st.text_input("Candidate Name")
    screening_summary = {"candidate_name": cand_name}
    candidate = {"name": cand_name, "screening": screening_summary, "resume_text": "", "ai_score": 0}

if st.button("🚀 Generate Interview Kit", use_container_width=True, type="primary"):
    try:
        result = run_crew_with_log(
            run_interview_prep_crew,
            candidate.get("screening", screening_summary),
            jd_parsed,
            phase_name="Interview Prep Crew",
            agents=["Question Generator", "Rubric Builder"],
        )
    except Exception as e:
        st.stop()
    save_interview_kit(None, st.session_state.get("current_jd_id"), result.get("questions",{}), result.get("rubric",{}))
    st.session_state["interview_kit"]    = result.get("questions", {})
    st.session_state["interview_rubric"] = result.get("rubric", {})
    st.rerun()

kit    = st.session_state.get("interview_kit", {})
rubric = st.session_state.get("interview_rubric", {})

if kit:
    st.markdown("<br>", unsafe_allow_html=True)
    tabs = st.tabs(["💻  Technical","🧠  Behavioral","🎭  Situational","💜  Culture Fit","🔎  Probing","📊  Rubric"])
    cats = [
        ("technical_questions",         tabs[0]),
        ("behavioral_questions",         tabs[1]),
        ("situational_questions",        tabs[2]),
        ("culture_fit_questions",        tabs[3]),
        ("red_flag_probing_questions",   tabs[4]),
    ]
    for key, tab in cats:
        with tab:
            questions = kit.get(key, [])
            if not questions:
                st.markdown("<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.3);padding:20px 0;'>No questions in this category.</div>", unsafe_allow_html=True)
                continue
            for i, q in enumerate(questions, 1):
                if isinstance(q, dict):
                    q_text  = str(q.get("question_text", ""))
                    purpose = str(q.get("purpose", ""))
                    probes  = q.get("follow_up_probes", [])
                else:
                    q_text  = str(q)
                    purpose = ""
                    probes  = []

                with st.expander(f"Q{i}:  {q_text[:90]}{'...' if len(q_text)>90 else ''}"):
                    st.markdown(f"<div style='font-family:DM Sans;font-size:14px;color:#e8e6f0;line-height:1.7;margin-bottom:12px;'>{q_text}</div>", unsafe_allow_html=True)
                    if purpose:
                        st.markdown(f"<div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.4);margin-bottom:8px;'><strong style='color:rgba(167,139,250,0.7);'>Purpose:</strong> {purpose}</div>", unsafe_allow_html=True)
                    for p in probes:
                        st.markdown(f"<div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.5);padding:3px 0 3px 12px;border-left:2px solid rgba(139,92,246,0.3);margin-bottom:4px;'>↳ {p}</div>", unsafe_allow_html=True)

    with tabs[5]:  # Rubric — render properly
        if rubric and isinstance(rubric, dict):
            raw = rubric.get("raw_output")
            if raw:
                # Parse raw_output which may contain JSON string
                try:
                    clean = str(raw).strip().strip("```json").strip("```").strip()
                    parsed = json.loads(clean)
                    rubric = parsed
                    st.session_state["interview_rubric"] = parsed
                except:
                    pass

            if "raw_output" not in rubric:
                rubric_items = rubric if isinstance(rubric, list) else rubric.get("rubric", [])
                if isinstance(rubric_items, list):
                    for item in rubric_items:
                        if isinstance(item, dict):
                            q_text = str(item.get("question", item.get("question_text", "Question")))
                            with st.expander(q_text[:80]):
                                col1, col2, col3 = st.columns(3)
                                col1.markdown(f"**⭐ Poor (1):**\n\n{str(item.get('score_1_response','N/A'))}")
                                col2.markdown(f"**⭐⭐⭐ Average (3):**\n\n{str(item.get('score_3_response','N/A'))}")
                                col3.markdown(f"**⭐⭐⭐⭐⭐ Excellent (5):**\n\n{str(item.get('score_5_response','N/A'))}")
                                indicators = item.get("key_indicators", [])
                                if indicators:
                                    st.markdown("**Key signals to listen for:**")
                                    for ind in indicators:
                                        st.markdown(f"- {ind}")
                else:
                    st.json(rubric)
            else:
                # Still raw_output — show parsed nicely
                st.markdown("<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.5);padding:12px;background:#13131f;border-radius:8px;line-height:1.7;'>Rubric generated. The AI returned it in raw format — questions are loaded in the question tabs above with embedded scoring guidance.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.3);'>Generate the kit first to see the rubric.</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("📥 Download Interview Kit (JSON)",
        data=json.dumps({"questions":kit,"rubric":rubric},indent=2),
        file_name=f"interview_kit_{candidate['name'].replace(' ','_')}.json",
        mime="application/json", use_container_width=True)

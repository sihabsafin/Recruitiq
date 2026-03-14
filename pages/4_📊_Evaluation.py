import json
import streamlit as st
from utils.styles import inject_styles, page_header, section_title
from utils.execution_log import run_crew_with_log
from crews.crews import run_evaluation_crew

st.set_page_config(page_title="Evaluation · RecruitIQ", layout="wide")
inject_styles()
page_header("📊", "Candidate Evaluation", "Interview analysis · Competency scores · Hire recommendation")

candidate   = st.session_state.get("selected_candidate", {})
rubric      = st.session_state.get("interview_rubric", {})
cand_name   = st.text_input("Candidate Name", value=candidate.get("name",""))
resume_text = candidate.get("resume_text","")
interview_notes = st.text_area("Interview Notes / Transcript", placeholder="Paste interview notes or transcript here...", height=280)

if st.button("🚀 Run Evaluation Crew", use_container_width=True, type="primary"):
    if not interview_notes.strip():
        st.error("Please paste interview notes.")
        st.stop()
    try:
        result = run_crew_with_log(
            run_evaluation_crew,
            interview_notes, rubric, cand_name, resume_text,
            phase_name="Evaluation Crew",
            agents=["Interview Analyst", "Reference Checker"],
        )
        st.session_state["evaluation_result"] = result
    except Exception as e:
        st.stop()

eval_result = st.session_state.get("evaluation_result")
if eval_result:
    evaluation = eval_result.get("evaluation", {})
    ref_guide  = eval_result.get("reference_guide", {})
    rec = evaluation.get("hire_recommendation","N/A")
    rec_colors = {"strong_yes":"#22c55e","yes":"#22c55e","maybe":"#fbbf24","no":"#ef4444","strong_no":"#ef4444"}
    rec_color = rec_colors.get(str(rec).lower().replace(" ","_"),"#a78bfa")

    st.markdown(f"<div style='background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.2);border-radius:10px;padding:20px 24px;margin:16px 0;'><div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.4);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;'>Hire Recommendation</div><div style='font-family:Syne,sans-serif;font-size:28px;font-weight:800;color:{rec_color};'>{str(rec).upper().replace('_',' ')}</div></div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊  Evaluation Report","📞  Reference Guide"])
    with tab1:
        if isinstance(evaluation, dict):
            overall = evaluation.get("overall_interview_score","N/A")
            st.metric("Overall Interview Score", f"{overall}/100")
            scores = evaluation.get("competency_scores",{})
            if scores and isinstance(scores, dict):
                cols = st.columns(min(len(scores),4))
                for col,(comp,score) in zip(cols,list(scores.items())[:4]):
                    col.metric(comp.replace("_"," ").title(), f"{score}/100")
            col1,col2 = st.columns(2)
            with col1:
                section_title("Strongest Areas")
                for s in evaluation.get("strongest_areas",[]):
                    st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:#22c55e;padding:5px 10px 5px 12px;border-left:2px solid #22c55e;margin-bottom:5px;background:rgba(34,197,94,0.04);border-radius:0 4px 4px 0;'>✓ {s}</div>", unsafe_allow_html=True)
            with col2:
                section_title("Areas of Concern")
                for s in evaluation.get("areas_of_concern",[]):
                    st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:#fbbf24;padding:5px 10px 5px 12px;border-left:2px solid #fbbf24;margin-bottom:5px;background:rgba(251,191,36,0.04);border-radius:0 4px 4px 0;'>⚠ {s}</div>", unsafe_allow_html=True)
            section_title("Justification")
            st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.6);line-height:1.7;'>{evaluation.get('hire_justification','')}</div>", unsafe_allow_html=True)
    with tab2:
        if isinstance(ref_guide, dict):
            section_title("Claims to Verify")
            for claim in ref_guide.get("claims_to_verify",[]):
                st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.6);padding:5px 0 5px 12px;border-left:2px solid rgba(139,92,246,0.3);margin-bottom:5px;'>• {claim}</div>", unsafe_allow_html=True)
            section_title("Reference Check Questions")
            for i,q in enumerate(ref_guide.get("suggested_reference_questions",[]),1):
                st.markdown(f"<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.65);padding:8px 12px;background:#13131f;border:1px solid rgba(139,92,246,0.1);border-radius:6px;margin-bottom:6px;'><strong style='color:#a78bfa;'>{i}.</strong> {q}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("📥 Download Evaluation Report (JSON)", data=json.dumps(eval_result,indent=2),
        file_name=f"evaluation_{cand_name.replace(' ','_')}.json", mime="application/json", use_container_width=True)

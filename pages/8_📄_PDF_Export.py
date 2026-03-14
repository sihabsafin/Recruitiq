import streamlit as st
from utils.styles import inject_styles, page_header, section_title
from utils.pdf_report import generate_candidate_pdf

st.set_page_config(page_title="PDF Export · RecruitIQ", layout="wide")
inject_styles()
page_header("📄", "Candidate Report Export", "Generate professional PDF reports · Share with hiring managers")

candidates = st.session_state.get("screened_candidates", [])
jd_parsed  = st.session_state.get("current_jd_parsed", {})

if not candidates:
    st.markdown("""
    <div style='background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.2);
    border-radius:8px;padding:14px 18px;font-family:DM Sans;font-size:13px;color:#fbbf24;'>
    ⚠️ No screened candidates found. Complete <strong>Resume Screening</strong> first.
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Export all button ─────────────────────────────────────────────────────────
st.markdown("""
<div style='background:rgba(139,92,246,0.06);border:1px solid rgba(139,92,246,0.15);
border-radius:10px;padding:16px 20px;margin-bottom:20px;font-family:DM Sans;font-size:13px;
color:rgba(232,230,240,0.6);'>
    Generate a professional PDF report for any screened candidate. Each report includes 
    AI match scores, skills breakdown, screening flags, keyword analysis, and hire recommendation — 
    ready to share with your hiring manager.
</div>""", unsafe_allow_html=True)

# ── Per-candidate export ──────────────────────────────────────────────────────
section_title(f"{len(candidates)} Candidates Ready for Export")

sorted_candidates = sorted(candidates, key=lambda x: x.get("ai_score", 0), reverse=True)

for i, cand in enumerate(sorted_candidates):
    score = cand.get("ai_score", 0)
    try:
        score_f = float(str(score).replace("%",""))
    except:
        score_f = 0

    score_color = "#22c55e" if score_f >= 75 else ("#fbbf24" if score_f >= 55 else "#ef4444")
    rec = str(cand.get("recommendation","hold")).lower()
    rec_label = "Shortlist" if "shortlist" in rec else ("Reject" if "reject" in rec else "Hold")
    rec_color = "#22c55e" if "shortlist" in rec else ("#ef4444" if "reject" in rec else "#fbbf24")

    col1, col2, col3, col4 = st.columns([3, 1, 1, 1.5])

    with col1:
        st.markdown(f"""
        <div style='padding:14px 0 8px;'>
            <div style='font-family:Syne,sans-serif;font-size:15px;font-weight:700;
            color:#f0eeff;margin-bottom:4px;'>#{i+1} · {cand['name']}</div>
            <div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.35);'>
                {cand.get('email','N/A')} · {cand.get('file','')}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='padding:14px 0 8px;text-align:center;'>
            <div style='font-family:DM Sans;font-size:10px;color:rgba(232,230,240,0.35);
            text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>AI Score</div>
            <div style='font-family:Syne,sans-serif;font-size:20px;font-weight:800;
            color:{score_color};'>{score_f:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style='padding:14px 0 8px;text-align:center;'>
            <div style='font-family:DM Sans;font-size:10px;color:rgba(232,230,240,0.35);
            text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Decision</div>
            <div style='
                background:{rec_color}18;color:{rec_color};
                border:1px solid {rec_color}44;
                font-family:DM Sans;font-size:12px;font-weight:500;
                padding:4px 12px;border-radius:99px;display:inline-block;
            '>{rec_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        try:
            with st.spinner(""):
                pdf_bytes = generate_candidate_pdf(cand, jd_parsed)
            fname = f"report_{cand['name'].replace(' ','_').lower()}.pdf"
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                use_container_width=True,
                key=f"dl_{i}_{cand['name']}",
            )
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("<hr style='border-color:rgba(139,92,246,0.08);margin:4px 0;'>", unsafe_allow_html=True)

# ── Bulk export all ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
section_title("Bulk Export")

col1, col2 = st.columns(2)

with col1:
    if st.button("📦 Export All Candidates (ZIP)", use_container_width=True, type="primary"):
        import zipfile, io
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for cand in sorted_candidates:
                try:
                    pdf_bytes = generate_candidate_pdf(cand, jd_parsed)
                    fname = f"report_{cand['name'].replace(' ','_').lower()}.pdf"
                    zf.writestr(fname, pdf_bytes)
                except Exception as e:
                    pass
        zip_buf.seek(0)
        st.download_button(
            "📥 Download ZIP",
            data=zip_buf.getvalue(),
            file_name="recruitiq_candidate_reports.zip",
            mime="application/zip",
            use_container_width=True,
        )

with col2:
    # Shortlisted only
    shortlisted = [c for c in sorted_candidates if "shortlist" in str(c.get("recommendation","")).lower()]
    if shortlisted:
        if st.button(f"⭐ Export Shortlisted Only ({len(shortlisted)})", use_container_width=True):
            import zipfile, io
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for cand in shortlisted:
                    try:
                        pdf_bytes = generate_candidate_pdf(cand, jd_parsed)
                        fname = f"shortlisted_{cand['name'].replace(' ','_').lower()}.pdf"
                        zf.writestr(fname, pdf_bytes)
                    except:
                        pass
            zip_buf.seek(0)
            st.download_button(
                "📥 Download Shortlisted ZIP",
                data=zip_buf.getvalue(),
                file_name="recruitiq_shortlisted.zip",
                mime="application/zip",
                use_container_width=True,
            )
    else:
        st.markdown("""
        <div style='background:#13131f;border:1px solid rgba(255,255,255,0.06);
        border-radius:8px;padding:12px 16px;font-family:DM Sans;font-size:13px;
        color:rgba(232,230,240,0.3);'>No shortlisted candidates yet.</div>
        """, unsafe_allow_html=True)

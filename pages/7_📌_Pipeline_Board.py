import streamlit as st
import streamlit.components.v1 as components
from utils.styles import inject_styles, page_header, section_title
from datetime import datetime

st.set_page_config(page_title="Pipeline Board · RecruitIQ", layout="wide")
inject_styles()
page_header("📌", "Pipeline Board", "Visual hiring pipeline · Drag candidates across stages · Track every hire")

# ── Init pipeline state ───────────────────────────────────────────────────────
STAGES = ["Applied", "Screened", "Interview", "Offer", "Hired", "Rejected"]
STAGE_COLORS = {
    "Applied":   "#64748b",
    "Screened":  "#a78bfa",
    "Interview": "#06b6d4",
    "Offer":     "#f59e0b",
    "Hired":     "#22c55e",
    "Rejected":  "#ef4444",
}

if "pipeline" not in st.session_state:
    st.session_state["pipeline"] = {s: [] for s in STAGES}

# Auto-populate from screened candidates
screened = st.session_state.get("screened_candidates", [])
pipeline = st.session_state["pipeline"]

# Add new screened candidates to Applied/Screened automatically
for cand in screened:
    name = cand["name"]
    already_placed = any(name in [c["name"] for c in pipeline[s]] for s in STAGES)
    if not already_placed:
        rec = str(cand.get("recommendation","hold")).lower()
        stage = "Screened" if "shortlist" in rec else ("Rejected" if "reject" in rec else "Applied")
        pipeline[stage].append({
            "name": name,
            "email": cand.get("email","N/A"),
            "score": cand.get("ai_score", 0),
            "file": cand.get("file",""),
            "added": datetime.now().strftime("%b %d"),
            "notes": "",
        })

# ── Stats bar ─────────────────────────────────────────────────────────────────
total = sum(len(pipeline[s]) for s in STAGES)
col1,col2,col3,col4,col5 = st.columns(5)
col1.metric("Total Candidates", total)
col2.metric("In Pipeline",      sum(len(pipeline[s]) for s in ["Applied","Screened","Interview","Offer"]))
col3.metric("Hired",            len(pipeline["Hired"]))
col4.metric("Rejected",         len(pipeline["Rejected"]))
col5.metric("Offer Stage",      len(pipeline["Offer"]))

st.markdown("<br>", unsafe_allow_html=True)

# ── Manual add ────────────────────────────────────────────────────────────────
with st.expander("➕ Add Candidate Manually"):
    c1,c2,c3,c4 = st.columns(4)
    new_name  = c1.text_input("Name")
    new_email = c2.text_input("Email")
    new_score = c3.number_input("Score", 0, 100, 70)
    new_stage = c4.selectbox("Stage", STAGES)
    if st.button("Add to Pipeline", use_container_width=True):
        if new_name:
            pipeline[new_stage].append({
                "name": new_name, "email": new_email,
                "score": new_score, "file": "",
                "added": datetime.now().strftime("%b %d"), "notes": "",
            })
            st.success(f"✓ {new_name} added to {new_stage}")
            st.rerun()

# ── Kanban board ──────────────────────────────────────────────────────────────
section_title("Hiring Pipeline")

cols = st.columns(len(STAGES))

for col, stage in zip(cols, STAGES):
    color = STAGE_COLORS[stage]
    cards = pipeline[stage]

    with col:
        # Column header
        st.markdown(f"""
        <div style='
            background:#13131f;
            border:1px solid {color}33;
            border-top:3px solid {color};
            border-radius:10px 10px 0 0;
            padding:12px 14px 10px;
            margin-bottom:2px;
        '>
            <div style='display:flex;align-items:center;justify-content:space-between;'>
                <span style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:#f0eeff;'>{stage}</span>
                <span style='
                    background:{color}22;color:{color};
                    font-size:11px;font-weight:700;
                    padding:1px 8px;border-radius:99px;
                    font-family:DM Sans;
                '>{len(cards)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Cards
        st.markdown(f"""
        <div style='
            background:#0d0d14;
            border:1px solid {color}22;
            border-top:none;
            border-radius:0 0 10px 10px;
            padding:8px;
            min-height:200px;
        '>
        """, unsafe_allow_html=True)

        if not cards:
            st.markdown(f"""
            <div style='
                padding:20px 10px;text-align:center;
                font-family:DM Sans;font-size:11px;
                color:rgba(232,230,240,0.2);
                border:1px dashed rgba(255,255,255,0.06);
                border-radius:6px;margin:4px;
            '>No candidates</div>
            """, unsafe_allow_html=True)

        for ci, card in enumerate(cards):
            score = card.get("score", 0)
            try:
                score_f = float(str(score).replace("%",""))
            except:
                score_f = 0

            score_color = "#22c55e" if score_f >= 75 else ("#fbbf24" if score_f >= 55 else "#ef4444")

            st.markdown(f"""
            <div style='
                background:#13131f;
                border:1px solid rgba(255,255,255,0.07);
                border-radius:8px;
                padding:12px;
                margin-bottom:8px;
            '>
                <div style='font-family:DM Sans;font-size:13px;font-weight:500;color:#e8e6f0;margin-bottom:4px;'>{card['name']}</div>
                <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.35);margin-bottom:8px;'>{card.get('email','')[:28]}</div>
                <div style='display:flex;align-items:center;justify-content:space-between;'>
                    <span style='
                        background:{score_color}18;color:{score_color};
                        font-family:Syne,sans-serif;font-size:12px;font-weight:700;
                        padding:2px 8px;border-radius:99px;
                    '>{score_f:.0f}%</span>
                    <span style='font-family:DM Sans;font-size:10px;color:rgba(232,230,240,0.25);'>{card.get('added','')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Move buttons
        st.markdown("<div style='margin-top:6px;'>", unsafe_allow_html=True)
        for ci, card in enumerate(list(cards)):
            other_stages = [s for s in STAGES if s != stage]
            move_to = st.selectbox(
                f"Move {card['name'][:15]}",
                ["— move to —"] + other_stages,
                key=f"move_{stage}_{ci}_{card['name']}",
                label_visibility="collapsed",
            )
            if move_to != "— move to —":
                pipeline[stage].remove(card)
                pipeline[move_to].append(card)
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ── Pipeline progress visualization ──────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
section_title("Funnel View")

if total > 0:
    stage_counts = {s: len(pipeline[s]) for s in STAGES}
    max_count = max(stage_counts.values()) if max(stage_counts.values()) > 0 else 1

    funnel_html = """<div style='background:#0d0d14;border:1px solid rgba(255,255,255,0.07);border-radius:12px;padding:24px 32px;'>"""
    for stage in STAGES:
        count = stage_counts[stage]
        pct = (count / total * 100) if total > 0 else 0
        bar_w = max(count / max_count * 100, 4) if count > 0 else 0
        color = STAGE_COLORS[stage]
        funnel_html += f"""
        <div style='display:flex;align-items:center;gap:16px;margin-bottom:14px;'>
            <div style='font-family:DM Sans;font-size:12px;color:rgba(232,230,240,0.5);
            width:80px;text-align:right;flex-shrink:0;'>{stage}</div>
            <div style='flex:1;background:rgba(255,255,255,0.05);border-radius:99px;height:10px;overflow:hidden;'>
                <div style='background:{color};height:100%;width:{bar_w}%;border-radius:99px;'></div>
            </div>
            <div style='font-family:Syne,sans-serif;font-size:13px;font-weight:700;color:{color};
            width:40px;flex-shrink:0;'>{count}</div>
            <div style='font-family:DM Sans;font-size:11px;color:rgba(232,230,240,0.3);
            width:36px;flex-shrink:0;'>{pct:.0f}%</div>
        </div>"""
    funnel_html += "</div>"
    st.markdown(funnel_html, unsafe_allow_html=True)
else:
    st.markdown("<div style='font-family:DM Sans;font-size:13px;color:rgba(232,230,240,0.3);'>No candidates in pipeline yet.</div>", unsafe_allow_html=True)

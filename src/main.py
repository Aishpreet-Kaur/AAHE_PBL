import streamlit as st
import os
from pdf_exporter import generate_pdf
from ai_engine import generate_hypotheses,temporal_update_engine
from db_manager import init_db, save_theories, load_theories,clear_history,get_hypothesis_by_id

# audio and video
video_url = "http://localhost:9000/background.mp4"
audio_url = "http://localhost:9000/background.mp3"

st.markdown(f"""
    <style>
    .stApp {{
        background: transparent !important;
    }}
    video#bgvid {{
        position: fixed;
        top: 0;
        left: 0;
        min-width: 100vw;
        min-height: 100vh;
        width: 100vw;
        height: 100vh;
        object-fit: cover;
        z-index: -1;
        opacity: 0.45;
        pointer-events: none;
    }}
    /* Center and constrain main content */
    .main .block-container {{
        max-width: 850px;
        margin-left: auto;
        margin-right: auto;
        background: rgba(17,17,17,0.88);
        border-radius: 24px;
        padding: 2.5rem 2.5rem 2rem 2.5rem;
        box-shadow: 0 8px 32px 0 rgba(0,0,0,0.27);
    }}
    .sidebar-content {{
        background: rgba(24,24,24,0.93);
        border-radius: 12px;
    }}
    @media (max-width: 900px) {{
        .main .block-container {{
            max-width: 98vw;
            padding: 1.5rem .75rem 1rem .75rem;
        }}
    }}
    </style>
    <video autoplay muted loop id="bgvid">
        <source src="{video_url}" type="video/mp4">
    </video>
""", unsafe_allow_html=True)

# Sidebar 

with st.sidebar:
    st.title("AI-AUGMENTED-HYPOTHESIS-EXPLORER")
    topic = st.text_area("Case Topic / Search")
    domain = st.selectbox("Domain", ["Business", "Finance", "Geopolitics", "Policy", "Multi"])
    custom_query = st.text_area("Custom Investigation Query (optional)")
    n_hypotheses = st.slider("Hypotheses To Generate", 3, 10, value=5)
    run = st.button("Analyze Case")
    st.markdown("---")
    st.markdown("Crime is the Blunt Instrument of Power\n "
    "Power is the art that makes it Legal.\n " 
    "Control Doesn't comes from force alone.\n " 
    "But from narratives.\n"
    "Its Not the truth that prevails.\n" 
    "But the Winners's Power\n"
    "Winner Writes the History\n" 
    "VEER BHOGYA VASUNDHARA")
    st.markdown("#### Ambient Audio")
    st.audio(audio_url, format='audio/mp3')

init_db()

# Main report content 
if run and topic:
    with st.spinner("Preparing elite forensic report..."):
        gemini_output = generate_hypotheses(topic, custom_query)
        save_theories(topic, [gemini_output])

    st.markdown("## 🔍 Detailed Investigative Report")

    st.markdown(
        f"<div style='background:#111111bb;padding:24px;border-radius:16px;'>{gemini_output}</div>",
        unsafe_allow_html=True
    )

    # Create a simple summary for PDF export
    summary = gemini_output[:500] + "..." if len(gemini_output) > 500 else gemini_output

    # PDF Export 
    st.markdown("### 📄 Export Report")

    pdf_buffer = generate_pdf(
        topic=topic,
        summary=summary,
        full_text=gemini_output
    )

    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"{topic.replace(' ', '_')}_report.pdf",
        mime="application/pdf"
    )

# Previous Investigations
st.markdown("### 📁 Previous Investigations")

col1, col2 = st.columns(2)

with col1:
    if st.button("Show All Saved Results"):
        df = load_theories()
        st.dataframe(df)

with col2:
    if st.button("🗑️ Clear History"):
        from db_manager import clear_history
        clear_history()
        st.success("History cleared successfully!")

def run_realtime_engine():
    hypothesis = get_hypothesis_by_id(1)  # pass valid id

    if not hypothesis:
        print("No hypothesis found")
        return

    new_conf = temporal_update_engine(
        hypothesis_id=hypothesis["id"],
        hypothesis_text=hypothesis["topic"],
        old_confidence=hypothesis["confidence"]
    )

    print("Updated confidence:", new_conf)



if __name__ == "__main__":
    run_realtime_engine()
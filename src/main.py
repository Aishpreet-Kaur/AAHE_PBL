import streamlit as st
import os
from pdf_exporter import generate_pdf_with_sources
from ai_engine import generate_hypotheses_with_evidence
from db_manager import (
    init_db, 
    save_theories_with_sources, 
    load_theories,
    clear_history,
    get_hypothesis_with_sources,
    get_statistics
)
import json

video_url = "http://localhost:9000/background.mp4"
audio_url = "http://localhost:9000/background.mp3"

st.set_page_config(
    page_title="AI-Augmented Hypothesis Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .main .block-container {{
        max-width: 1200px;
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
    .source-card {{
        background: rgba(40,40,40,0.9);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }}
    .source-card h4 {{
        color: #4CAF50;
        margin: 0 0 8px 0;
    }}
    .source-meta {{
        color: #999;
        font-size: 0.85em;
        margin: 5px 0;
    }}
    .credibility-badge {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    }}
    .credibility-high {{
        background: #4CAF50;
        color: white;
    }}
    .credibility-medium {{
        background: #FF9800;
        color: white;
    }}
    .credibility-low {{
        background: #f44336;
        color: white;
    }}
    /* Better aligned buttons */
    .stButton button {{
        width: 100%;
        border-radius: 8px;
        font-weight: 500;
    }}
    

    /* Custom color for primary button */
    .stButton button[kind="primary"] {{
        background-color: #6c757d !important;
        border-color: #6c757d !important;
        color: white !important;
    }}

    .stButton button[kind="primary"]:hover {{
        background-color: #E0E0E0;
        border-color: #E0E0E0;
    }}
    /* Statistics cards */
    .stat-card {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin: 10px 0;
    }}
    .stat-value {{
        font-size: 2em;
        font-weight: bold;
        margin: 5px 0;
    }}
    .stat-label {{
        font-size: 0.9em;
        opacity: 0.9;
    }}
    /* Investigation card styling */
    .investigation-card {{
        background: rgba(30,30,30,0.95);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    .investigation-card:hover {{
        border-color: #4CAF50;
        box-shadow: 0 4px 12px rgba(76,175,80,0.3);
        transform: translateY(-2px);
    }}
    .investigation-title {{
        color: #4CAF50;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }}
    .investigation-meta {{
        color: #999;
        font-size: 0.85em;
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

# Initialize database
init_db()

# Initialize session state for viewing investigations
if 'viewing_investigation' not in st.session_state:
    st.session_state.viewing_investigation = None
if 'show_history' not in st.session_state:
    st.session_state.show_history = False

# Sidebar Configuration
with st.sidebar:
    st.title("🔍 AI-AUGMENTED HYPOTHESIS EXPLORER")
    
    st.markdown("---")
    
    # Configuration
    st.markdown("### 📋 Investigation Setup")
    topic = st.text_area("Case Topic / Search Query", placeholder="Enter the topic you want to investigate...", height=100)
    domain = st.selectbox("Domain", ["Business", "Finance", "Geopolitics", "Policy", "Technology", "Health", "Science", "Multi-Domain"])
    custom_query = st.text_area("Custom Investigation Query (optional)", placeholder="Specific questions or angles to explore...", height=80)
    
    st.markdown("### ⚙️ Analysis Parameters")
    max_sources = st.slider("Maximum Web Sources", 3, 10, value=5, 
                            help="Number of web sources to search and analyze")
    
    run = st.button("🚀 Generate Evidence-Based Analysis", type="primary", use_container_width=True)
    
    st.markdown("---")
    
    # Statistics with better styling
    st.markdown("### 📊 Database Statistics")
    stats = get_statistics()
    
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{stats['total_hypotheses']}</div>
        <div class="stat-label">Total Analyses</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Sources", stats['total_sources'])
    with col2:
        st.metric("Avg Credibility", f"{stats['avg_credibility']}/10")
    
    st.markdown("---")
    
    # Philosophy quote
    st.markdown("""
    <div style='font-size:0.85em; font-style:italic; color:#aaa; padding:10px; border-left:2px solid #555;'>
    "Crime is the Blunt Instrument of Power<br>
    Power is the art that makes it Legal.<br>
    Control Doesn't come from force alone,<br>
    But from narratives.<br>
    It's Not the truth that prevails,<br>
    But the Winner's Power<br>
    Winner Writes the History<br>
    <strong>VEER BHOGYA VASUNDHARA</strong>"
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 🎵 Ambient Audio")
    st.audio(audio_url, format='audio/mp3')

# Main Content Area

# Check if we're viewing a specific investigation
if st.session_state.viewing_investigation is not None:
    # Show back button
    if st.button("⬅️ Back to New Analysis"):
        st.session_state.viewing_investigation = None
        st.rerun()
    
    # Display the investigation
    investigation = get_hypothesis_with_sources(st.session_state.viewing_investigation)
    
    if investigation:
        st.markdown("## 📊 Investigation Details")
        
        # Investigation info
        st.markdown(f"**Topic:** {investigation['topic']}")
        st.markdown(f"**Created:** {investigation['created_at']}")
        st.markdown(f"**Confidence:** {investigation['confidence']:.2%}")
        
        st.markdown("---")
        
        # Main Report
        st.markdown("### 📝 Analysis Report")
        st.markdown(
            f"<div style='background:#111111bb;padding:24px;border-radius:16px;'>{investigation['theory']}</div>",
            unsafe_allow_html=True
        )
        
        # Sources
        if investigation['sources']:
            st.markdown("---")
            st.markdown("### 📚 Evidence Sources")
            
            for source in investigation['sources']:
                credibility = source['credibility']
                
                if credibility >= 8.0:
                    badge_class = "credibility-high"
                    badge_text = "High Credibility"
                elif credibility >= 6.5:
                    badge_class = "credibility-medium"
                    badge_text = "Medium Credibility"
                else:
                    badge_class = "credibility-low"
                    badge_text = "Verify Carefully"
                
                # st.markdown(f"""
                # <div class="source-card">
                #     <h4>[{source['number']}] {source['title']}</h4>
                #     <div class="source-meta">
                #         🔗 <a href="{source['url']}" target="_blank" style="color:#4CAF50;">{source['url']}</a>
                #     </div>
                #     <div class="source-meta">
                #         📅 {source['date']} | 
                #         <span class="credibility-badge {badge_class}">{badge_text} ({credibility:.1f}/10)</span>
                #     </div>
                #     <p style="margin-top:10px; color:#ccc;">{source['snippet']}</p>
                # </div>
                # """, unsafe_allow_html=True)
                # Get ML component scores
                components = source.get('credibility_components', {})

                st.markdown(f"""
                <div class="source-card">
                    <h4>[{source.get('id', '?')}] {source.get('title', 'Unknown Title')}</h4>
                    <div class="source-meta">
                        🔗 <a href="{source.get('url', '#')}" target="_blank" style="color:#4CAF50;">{source.get('url', 'No URL')}</a>
                    </div>
                    <div class="source-meta">
                        📅 {source.get('date', 'N/A')} | 
                        <span class="credibility-badge {badge_class}">
                            ML Score: {credibility:.1f}/10
                        </span>
                    </div>
                    <div class="source-meta" style="font-size:0.85em; color:#bbb; margin-top:8px;">
                        🤖 ML Analysis: {source.get('credibility_explanation', 'Standard quality')}
                    </div>
                    <div class="source-meta" style="font-size:0.8em; color:#999; margin-top:5px;">
                        📊 Components: 
                        Language {components.get('hedging', 6.0):.1f} | 
                        Citations {components.get('citations', 6.0):.1f} | 
                        Tone {components.get('emotional', 6.0):.1f} | 
                        Structure {components.get('structure', 6.0):.1f}
                    </div>
                    <p style="margin-top:10px; color:#ccc;">{source.get('snippet', 'No description available')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Export
        st.markdown("---")
        st.markdown("### 📥 Export This Investigation")
        
        pdf_buffer = generate_pdf_with_sources(
            topic=investigation['topic'],
            report_text=investigation['theory'],
            sources=investigation['sources']
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_buffer,
                file_name=f"{investigation['topic'].replace(' ', '_')}_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        with col2:
            export_data = {
                'topic': investigation['topic'],
                'report': investigation['theory'],
                'sources': investigation['sources'],
                'created': investigation['created_at']
            }
            
            st.download_button(
                label="📊 Download JSON Data",
                data=json.dumps(export_data, indent=2),
                file_name=f"{investigation['topic'].replace(' ', '_')}_data.json",
                mime="application/json",
                use_container_width=True
            )

# Main analysis view (new investigation)
elif run and topic:
    with st.spinner("🔍 Searching web sources and analyzing evidence..."):
        # Generate evidence-based hypothesis
        report_text, sources = generate_hypotheses_with_evidence(topic, custom_query, max_sources)
        
        # Save to database
        hypothesis_id = save_theories_with_sources(topic, report_text, sources)
    
    st.success("✅ Analysis complete with web-sourced evidence!")
    
    # Main Report Section
    st.markdown("## 📊 Detailed Investigative Report")
    
    # Display the report
    st.markdown(
        f"<div style='background:#111111bb;padding:24px;border-radius:16px;'>{report_text}</div>",
        unsafe_allow_html=True
    )
    
    # Sources Section
    st.markdown("---")
    st.markdown("## 📚 Evidence Sources & Citations")
    
    if sources:
        st.markdown(f"**Total Sources Analyzed:** {len(sources)}")
        
        # Display sources in an organized way
        for source in sources:
            credibility = source.get('credibility_score', 6.0)
            
            # Determine credibility badge
            if credibility >= 8.0:
                badge_class = "credibility-high"
                badge_text = "High Credibility"
            elif credibility >= 6.5:
                badge_class = "credibility-medium"
                badge_text = "Medium Credibility"
            else:
                badge_class = "credibility-low"
                badge_text = "Verify Carefully"
            
            st.markdown(f"""
            <div class="source-card">
                <h4>[{source.get('id', '?')}] {source.get('title', 'Unknown Title')}</h4>
                <div class="source-meta">
                    🔗 <a href="{source.get('url', '#')}" target="_blank" style="color:#4CAF50;">{source.get('url', 'No URL')}</a>
                </div>
                <div class="source-meta">
                    📅 Published: {source.get('date', 'N/A')} | 
                    <span class="credibility-badge {badge_class}">{badge_text} ({credibility:.1f}/10)</span>
                </div>
                <p style="margin-top:10px; color:#ccc;">{source.get('snippet', 'No description available')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No web sources were retrieved. Check your API configuration in .env file.")
    
    # Export Section
    st.markdown("---")
    st.markdown("## 📥 Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # PDF Export with sources
        pdf_buffer = generate_pdf_with_sources(
            topic=topic,
            report_text=report_text,
            sources=sources
        )
        
        st.download_button(
            label="📄 Download PDF Report with Sources",
            data=pdf_buffer,
            file_name=f"{topic.replace(' ', '_')}_evidence_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        # JSON Export (for data analysis)
        export_data = {
            'topic': topic,
            'report': report_text,
            'sources': sources,
            'timestamp': str(st.session_state.get('analysis_time', 'N/A'))
        }
        
        st.download_button(
            label="📊 Download JSON Data",
            data=json.dumps(export_data, indent=2),
            file_name=f"{topic.replace(' ', '_')}_data.json",
            mime="application/json",
            use_container_width=True
        )

else:
    # Welcome screen when no investigation is running
    st.markdown("## 🔍 Welcome to AI-Augmented Hypothesis Explorer")
    st.markdown("""
    This tool helps you conduct **evidence-based research** with AI assistance:
    
    ### ✨ Key Features:
    - 🌐 **Web Search Integration** - Automatically finds credible sources
    - 📖 **Citation System** - Every claim backed by [1][2][3] references
    - ⭐ **Credibility Scoring** - Sources rated 0-10 based on authority
    - 📊 **Professional Reports** - Export PDFs with full bibliography
    - 💾 **Investigation History** - Save and revisit past analyses
    
    ### 🚀 Get Started:
    1. Enter your research topic in the sidebar
    2. Optionally add custom questions
    3. Click "Generate Evidence-Based Analysis"
    4. Review sources and download your report
    
    ---
    """)

# History Section (always visible at bottom)
st.markdown("---")
st.markdown("## 📁 Investigation History")

# Aligned buttons in columns
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📋 Show All Investigations", use_container_width=True):
        st.session_state.show_history = not st.session_state.show_history

with col2:
    # Manual ID input for quick access
    quick_id = st.number_input("Quick Access by ID", min_value=1, step=1, label_visibility="collapsed")
    if st.button("🔍 Load by ID", use_container_width=True):
        st.session_state.viewing_investigation = quick_id
        st.rerun()

with col3:
    if st.button("🗑️ Clear All History", use_container_width=True):
        clear_history()
        st.success("✅ History cleared!")
        st.rerun()

# Show investigations as clickable cards
if st.session_state.show_history:
    st.markdown("### 📚 Your Previous Investigations")
    
    df = load_theories()
    
    if not df.empty:
        # Display as clickable cards instead of dataframe
        for idx, row in df.iterrows():
            # Create clickable card for each investigation
            investigation_id = row['id']
            topic_text = row['topic']
            created_date = row.get('created_at', 'Unknown date')
            confidence = row.get('confidence', 0.5)
            
            # Truncate long topics
            if len(topic_text) > 100:
                topic_display = topic_text[:97] + "..."
            else:
                topic_display = topic_text
            
            # Use columns for better layout
            col_card, col_btn = st.columns([4, 1])
            
            with col_card:
                st.markdown(f"""
                <div class="investigation-card">
                    <div class="investigation-title">#{investigation_id}: {topic_display}</div>
                    <div class="investigation-meta">
                        📅 Created: {created_date} | 🎯 Confidence: {confidence:.1%}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_btn:
                if st.button("Open", key=f"open_{investigation_id}", use_container_width=True):
                    st.session_state.viewing_investigation = investigation_id
                    st.rerun()
        
    else:
        st.info("📭 No investigations saved yet. Run your first analysis to get started!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#666; font-size:0.85em;'>
    <p>AI-Augmented Hypothesis Explorer v2.0 | Evidence-Based Analysis Engine</p>
    <p>⚠️ Remember: Always verify critical information through multiple independent sources</p>
</div>
""", unsafe_allow_html=True)

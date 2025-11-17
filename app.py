import streamlit as st
import pandas as pd
from lead_processor import process_leads, get_metrics_summary
import os

# Page config
st.set_page_config(
    page_title="AI Lead Intelligence Pipeline",
    page_icon="🎯",
    layout="wide"
)

# Title and description
st.title("🎯 AI Lead Intelligence Pipeline")
st.markdown("""
**Automate lead qualification, scoring, and deduplication using Claude AI**

This system:
- ✅ Enriches leads with AI-powered insights
- ✅ Scores leads 0-10 based on sales-readiness
- ✅ Detects duplicates automatically
- ✅ Recommends specific actions for each lead
- ✅ Saves 18+ hours per 500 leads
""")

st.divider()

# Sidebar for API key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Enter OpenAI API Key",
        type="password",
        help="Get your API key from console.anthropic.com"
    )
    
    st.divider()
    
    st.markdown("### 📊 About This Project")
    st.markdown("""
    Built to solve the lead chaos problem that costs B2B companies 
    125+ hours per month in manual lead processing.
    
    **Tech Stack:**
    - Claude AI (Anthropic)
    - Streamlit
    - Python/Pandas
    
    **Impact:**
    - 150x faster processing
    - ₹480K+ annual savings
    - 95%+ duplicate detection
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📁 Upload Leads Data")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload your leads CSV file",
        type=['csv'],
        help="CSV should contain: name, email, company, title, etc."
    )
    
    # Sample data option
    if st.button("📋 Use Sample Dataset"):
        try:
            sample_df = pd.read_csv('leads_dataset.csv')
            st.session_state['df'] = sample_df
            st.success(f"✅ Loaded {len(sample_df)} sample leads!")
        except Exception as e:
            st.error(f"Could not load sample data: {str(e)}")
    
    # Process uploaded file
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.session_state['df'] = df
            st.success(f"✅ Uploaded {len(df)} leads successfully!")
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

with col2:
    st.header("📈 Quick Stats")
    if 'df' in st.session_state:
        df = st.session_state['df']
        st.metric("Total Leads", len(df))
        st.metric("Unique Companies", df['company'].nunique() if 'company' in df.columns else 0)
        st.metric("Lead Sources", df['source'].nunique() if 'source' in df.columns else 0)

st.divider()

# Process leads section
if 'df' in st.session_state and api_key:
    df = st.session_state['df']
    
    st.header("🤖 AI Analysis")
    
    if st.button("🚀 Analyze Leads with AI", type="primary"):
        with st.spinner("🔄 Processing leads with Claude AI... This may take 30-60 seconds..."):
            result = process_leads(df, api_key)
            
            if result['success']:
                st.session_state['result'] = result
                st.success("✅ Lead analysis complete!")
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    # Display results
    if 'result' in st.session_state:
        result = st.session_state['result']
        
        st.divider()
        st.header("📊 Results Dashboard")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🔥 Hot Leads",
                result['hot_count'],
                help="Score 9-10: Call immediately"
            )
        
        with col2:
            st.metric(
                "🌡️ Warm Leads",
                result['warm_count'],
                help="Score 7-8: Email + LinkedIn"
            )
        
        with col3:
            st.metric(
                "❄️ Cold Leads",
                result['cold_count'],
                help="Score 5-6: Nurture campaign"
            )
        
        with col4:
            st.metric(
                "⚠️ Duplicates Found",
                result['duplicates'],
                help="Potential duplicate contacts"
            )
        
        # ROI metrics
        st.divider()
        st.header("💰 Business Impact")
        
        col1, col2, col3 = st.columns(3)
        
        metrics = get_metrics_summary(len(df))
        
        with col1:
            st.metric(
                "⏱️ Time Saved",
                f"{metrics['hours_saved']} hours",
                help=f"Manual: {metrics['manual_hours']}h → Automated: {metrics['automated_hours']}h"
            )
        
        with col2:
            st.metric(
                "💵 Annual ROI",
                f"₹{result['annual_roi']:,}",
                help="Based on ₹500/hour sales rep cost"
            )
        
        with col3:
            st.metric(
                "⚡ Speed Improvement",
                metrics['speed_improvement'],
                help="15 min/lead → 6 sec/lead"
            )
        
        # Processed leads table
        st.divider()
        st.header("📋 Processed Leads")
        
        processed_df = result['processed_df']
        
        # Filter options
        filter_col1, filter_col2 = st.columns(2)
        
        with filter_col1:
            score_filter = st.selectbox(
                "Filter by Score",
                ["All", "Hot (9-10)", "Warm (7-8)", "Cold (5-6)", "Not Qualified (<5)"]
            )
        
        with filter_col2:
            show_duplicates = st.checkbox("Show only duplicates")
        
        # Apply filters
        display_df = processed_df.copy()
        
        if score_filter != "All":
            if score_filter == "Hot (9-10)":
                display_df = display_df[display_df['ai_score'] >= 9]
            elif score_filter == "Warm (7-8)":
                display_df = display_df[(display_df['ai_score'] >= 7) & (display_df['ai_score'] < 9)]
            elif score_filter == "Cold (5-6)":
                display_df = display_df[(display_df['ai_score'] >= 5) & (display_df['ai_score'] < 7)]
            else:
                display_df = display_df[display_df['ai_score'] < 5]
        
        if show_duplicates:
            display_df = display_df[display_df['is_duplicate'] == True]
        
        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400
        )
        
        # Download button
        st.download_button(
            label="📥 Download Processed Leads (CSV)",
            data=processed_df.to_csv(index=False),
            file_name="processed_leads.csv",
            mime="text/csv"
        )

elif 'df' in st.session_state and not api_key:
    st.warning("⚠️ Please enter your Claude API key in the sidebar to analyze leads")

else:
    st.info("👆 Upload a CSV file or use the sample dataset to get started")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; padding: 20px;'>
    Built with Streamlit + Claude AI | Saves 18+ hours per 500 leads | ₹480K+ annual ROI
</div>
""", unsafe_allow_html=True)

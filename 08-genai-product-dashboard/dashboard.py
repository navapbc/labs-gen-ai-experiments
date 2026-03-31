"""
Phoenix Arize Product Dashboard
Interactive dashboard for analyzing GenAI product logs
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
import re
from dotenv import load_dotenv

from phoenix_client import PhoenixClient
from data_analyzer import TraceAnalyzer

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Phoenix Product Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .big-metric {
        font-size: 2.5rem !important;
        font-weight: bold !important;
    }
    .metric-label {
        font-size: 0.9rem !important;
        color: #666 !important;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_phoenix_client(api_url, api_key):
    """Initialize Phoenix client (cached)"""
    return PhoenixClient(api_url, api_key)


def _extract_project_id_from_url(url: str) -> str:
    """Extract Phoenix project ID from URLs like .../projects/<id>/spans."""
    if not url:
        return ""
    m = re.search(r"/projects/([^/]+)/spans", url)
    return m.group(1) if m else ""


def _normalize_api_base_url(url: str) -> str:
    """
    Normalize Phoenix URL to base host.
    Supports users pasting either:
    - base URL: https://phoenix.example.com:6006
    - full spans URL: https://phoenix.example.com:6006/projects/<id>/spans
    """
    if not url:
        return ""
    # Drop /projects/<id>/spans suffix if present
    return re.sub(r"/projects/[^/]+/spans/?$", "", url.strip()).rstrip("/")


@st.cache_data(ttl=43200)  # Cache for 12 hours (trace data changes slowly)
def load_data(
    _client,
    project_id,
    start_time,
    end_time,
    max_spans,
    cache_bust: str = "0",
    _secondary_client=None,
    secondary_project_id: str = "",
):
    """Load spans data from one or two Phoenix projects and dedupe by span identity."""
    if start_time and end_time and end_time <= start_time:
        raise ValueError("end_time must be after start_time")

    primary_spans = _client.get_all_spans(
        project_id=project_id,
        start_time=start_time,
        end_time=end_time,
        max_spans=max_spans,
    )

    secondary_spans = []
    if _secondary_client and secondary_project_id:
        secondary_spans = _secondary_client.get_all_spans(
            project_id=secondary_project_id,
            start_time=start_time,
            end_time=end_time,
            max_spans=max_spans,
        )

    merged = []
    seen = set()
    for span in (primary_spans or []) + (secondary_spans or []):
        dedupe_key = (
            str(span.get("span_id", "")),
            str(span.get("trace_id", "")),
            str(span.get("name", "")),
            str(span.get("start_time", "")),
            str(span.get("end_time", "")),
            str(span.get("parent_id", "")),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        merged.append(span)

    # Keep newest spans first so dashboard reflects recent usage even when volume is high.
    def _span_start_key(s):
        t = pd.to_datetime(s.get("start_time"), errors="coerce", utc=True)
        return t if pd.notna(t) else pd.Timestamp.min.tz_localize("UTC")

    merged.sort(key=_span_start_key, reverse=True)
    if len(merged) > max_spans:
        merged = merged[:max_spans]

    source_stats = {
        "primary_count": len(primary_spans or []),
        "secondary_count": len(secondary_spans or []),
        "merged_count": len(merged),
        "primary_latest": (
            max(
                [s.get("start_time") for s in (primary_spans or []) if s.get("start_time")],
                default=None,
            )
        ),
        "secondary_latest": (
            max(
                [s.get("start_time") for s in (secondary_spans or []) if s.get("start_time")],
                default=None,
            )
        ),
    }
    return {"spans": merged, "source_stats": source_stats}


def main():
    st.title("📊 Phoenix Product Analytics Dashboard")
    st.markdown("*Analyze your GenAI product usage and quality metrics*")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Configuration
        api_url = st.text_input(
            "Phoenix API URL",
            value=os.getenv('PHOENIX_API_URL', 'https://your-phoenix-instance.arize.com'),
            help="Your Phoenix instance URL"
        )

        dev_url_default = os.getenv(
            "PHOENIX_DEV_SPANS_URL",
            "https://phoenix.referral-pilot-dev.navateam.com:6006/projects/UHJvamVjdDoxOA==/spans",
        )
        include_secondary_source = st.checkbox(
            "Include Keystone dev traces",
            value=True,
            help="If enabled, dashboard also loads spans from the Keystone dev Phoenix project and merges with prod data.",
        )
        secondary_url = st.text_input(
            "Keystone Dev Phoenix URL",
            value=dev_url_default,
            help="Can be full spans URL (recommended) or base API URL.",
            disabled=not include_secondary_source,
        )
        
        api_key = st.text_input(
            "API Key (optional)",
            value=os.getenv('PHOENIX_API_KEY', ''),
            type="password",
            help="Leave empty if no authentication required"
        )
        
        st.divider()
        
        # Data filters
        st.header("🔍 Data Filters")
        
        # Time range
        time_range = st.selectbox(
            "Time Range",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom"]
        )
        
        if time_range == "Custom":
            start_date = st.date_input("Start Date", value=datetime.now(timezone.utc).date() - timedelta(days=7))
            end_date = st.date_input("End Date", value=datetime.now(timezone.utc).date())
            # Combine dates with time and make timezone-aware (UTC)
            start_time = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_time = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        else:
            days_map = {"Last 24 Hours": 1, "Last 7 Days": 7, "Last 30 Days": 30}
            days = days_map.get(time_range, 7)
            # Use UTC-aware datetimes for proper timezone handling
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)
        
        max_spans = st.number_input(
            "Max Spans to Load",
            min_value=100,
            max_value=50000,
            value=10000,
            step=1000,
            help="Maximum number of traces to analyze"
        )
        
        project_id = st.text_input(
            "Project ID (optional)",
            value=os.getenv('PHOENIX_PROJECT_ID', 'UHJvamVjdDoxOQ=='),
            help="Filter by specific project (default: pilot-prod)"
        )

        secondary_project_default = os.getenv(
            "PHOENIX_PROJECT_ID_DEV",
            _extract_project_id_from_url(dev_url_default) or "UHJvamVjdDoxOA==",
        )
        secondary_project_id = st.text_input(
            "Keystone Dev Project ID",
            value=secondary_project_default,
            help="Project ID for Keystone dev Phoenix source.",
            disabled=not include_secondary_source,
        )
        
        st.divider()
        
        # Load/refresh controls
        if 'cache_bust' not in st.session_state:
            st.session_state.cache_bust = "0"

        col1, col2 = st.columns(2)
        with col1:
            load_button = st.button("🔄 Load Data", type="primary", use_container_width=True)
        with col2:
            force_refresh = st.button(
                "♻️ Force Refresh",
                help="Bypasses the cache and re-pulls from Phoenix immediately.",
                use_container_width=True
            )
            if force_refresh:
                st.session_state.cache_bust = str(datetime.now(timezone.utc).timestamp())
    
    # Initialize session state
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Load data
    if load_button or st.session_state.data_loaded:
        try:
            with st.spinner("Connecting to Phoenix API..."):
                primary_base_url = _normalize_api_base_url(api_url)
                client = get_phoenix_client(primary_base_url, api_key if api_key else None)
                secondary_client = None
                secondary_project_final = ""
                if include_secondary_source and secondary_url:
                    secondary_base_url = _normalize_api_base_url(secondary_url)
                    if secondary_base_url:
                        secondary_client = get_phoenix_client(
                            secondary_base_url, api_key if api_key else None
                        )
                        secondary_project_final = (
                            secondary_project_id.strip()
                            or _extract_project_id_from_url(secondary_url)
                        )
            
            with st.spinner("Loading trace data..."):
                load_result = load_data(
                    client,
                    project_id if project_id else None,
                    start_time,
                    end_time,
                    max_spans,
                    st.session_state.get('cache_bust', "0"),
                    secondary_client,
                    secondary_project_final,
                )
                spans = load_result.get("spans", []) if isinstance(load_result, dict) else load_result
                source_stats = (
                    load_result.get("source_stats", {}) if isinstance(load_result, dict) else {}
                )
            
            if not spans:
                st.error("No data found. Please check your configuration and filters.")
                return
            
            st.session_state.analyzer = TraceAnalyzer(spans)
            st.session_state.source_stats = source_stats
            st.session_state.data_loaded = True
            st.success(f"✅ Loaded {len(spans)} spans successfully!")
            if source_stats:
                st.caption(
                    "Source counts — "
                    f"Primary: {source_stats.get('primary_count', 0):,} "
                    f"(latest: {source_stats.get('primary_latest', 'n/a')}), "
                    f"Dev: {source_stats.get('secondary_count', 0):,} "
                    f"(latest: {source_stats.get('secondary_latest', 'n/a')}), "
                    f"Merged used by dashboard: {source_stats.get('merged_count', len(spans)):,}."
                )
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return
    
    if not st.session_state.data_loaded:
        st.info("👈 Configure your settings in the sidebar and click 'Load Data' to begin")
        return
    
    analyzer = st.session_state.analyzer
    source_stats = st.session_state.get("source_stats", {})
    if source_stats:
        st.caption(
            "Loaded sources — "
            f"Primary: {source_stats.get('primary_count', 0):,} spans "
            f"(latest: {source_stats.get('primary_latest', 'n/a')}), "
            f"Dev: {source_stats.get('secondary_count', 0):,} spans "
            f"(latest: {source_stats.get('secondary_latest', 'n/a')})."
        )

    # Pilot cohort email defaults (editable in UI)
    G1_EMAILS_DEFAULT = """user01@gwctx.org
user02@gwctx.org
user03@gwctx.org
user04@gwctx.org
user05@gwctx.org
user06@gwctx.org
user07@gwctx.org
user08@gwctx.org
user09@gwctx.org
user10@gwctx.org
user11@gwctx.org
user12@gwctx.org
user13@gwctx.org
user14@gwctx.org
user15@gwctx.org
user16@gwctx.org"""

    G2_EMAILS_DEFAULT = """user17@gwctx.org
user18@gwctx.org
user19@gwctx.org
user20@gwctx.org
user21@gwctx.org
user22@gwctx.org
user23@gwctx.org
user24@gwctx.org
user25@gwctx.org
user26@gwctx.org
user27@gwctx.org
user28@gwctx.org
user29@gwctx.org
user30@gwctx.org
user31@gwctx.org
user32@gwctx.org"""

    G3_EMAILS_DEFAULT = """user33@gwctx.org
user34@gwctx.org
user35@gwctx.org
user36@gwctx.org
user37@gwctx.org
user38@gwctx.org
user39@gwctx.org
user40@gwctx.org
user41@gwctx.org
user42@gwctx.org
user43@gwctx.org
user44@gwctx.org
user45@gwctx.org
user46@gwctx.org
user47@gwctx.org"""

    KEYSTONE_EMAILS_DEFAULT = """user01@yourgoodwill.org
user02@yourgoodwill.org
user03@yourgoodwill.org
user04@yourgoodwill.org
user05@yourgoodwill.org
user06@yourgoodwill.org
user07@yourgoodwill.org
user08@yourgoodwill.org
user09@yourgoodwill.org
user10@yourgoodwill.org
user11@yourgoodwill.org
user12@yourgoodwill.org
user13@yourgoodwill.org
user14@yourgoodwill.org
user15@yourgoodwill.org
user16@yourgoodwill.org
user17@yourgoodwill.org
user18@yourgoodwill.org
user19@yourgoodwill.org"""

    CAB_EMAILS_DEFAULT = """user01@example.com
user02@example.com
user03@example.com
user04@example.com
user05@example.com
user06@example.com
user07@example.com
user08@example.com"""

    def _parse_emails(text: str) -> set:
        return {e.strip().lower() for e in (text or "").splitlines() if e.strip()}
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Executive Summary",
        "📊 Usage Analytics",
        "📋 Usage Report",
        "⚡ Performance Metrics",
        "🔎 Log Explorer",
        "🧠 Advanced Analytics",
        "✅ Evals"
    ])
    
    # TAB 1: Executive Summary
    with tab1:
        st.header("Executive Summary")
        st.markdown("*High-level KPIs for leadership reporting*")
        
        stats = analyzer.get_macro_statistics()
        
        if stats:
            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Requests",
                    f"{stats['total_requests']:,}",
                    help="Total number of API requests"
                )
            
            with col2:
                st.metric(
                    "Unique Traces",
                    f"{stats['unique_traces']:,}",
                    help="Number of unique user sessions"
                )
            
            with col3:
                st.metric(
                    "Success Rate",
                    f"{stats['success_rate']:.1f}%",
                    help="Percentage of successful requests"
                )
            
            with col4:
                st.metric(
                    "Avg Latency",
                    f"{stats['avg_latency_s']:.2f}s",
                    help="Average response time"
                )
            
            st.divider()
            
            # Second row of metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Tokens",
                    f"{stats['total_tokens']:,}",
                    help="Total tokens consumed"
                )
            
            with col2:
                st.metric(
                    "Avg Tokens/Request",
                    f"{stats['avg_tokens_per_request']:.0f}",
                    help="Average tokens per request"
                )
            
            with col3:
                st.metric(
                    "P95 Latency",
                    f"{stats['p95_latency_s']:.2f}s",
                    help="95th percentile latency"
                )
            
            with col4:
                st.metric(
                    "P99 Latency",
                    f"{stats['p99_latency_s']:.2f}s",
                    help="99th percentile latency"
                )
            
            st.divider()
            
            # Trace counts by type
            if 'trace_counts' in stats:
                st.subheader("Trace Counts by Type")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Generating Referrals",
                        f"{stats['trace_counts']['referrals']:,}",
                        help="Number of traces for generating referrals"
                    )
                
                with col2:
                    st.metric(
                        "Generating Action Plans",
                        f"{stats['trace_counts']['action_plans']:,}",
                        help="Number of traces for generating action plans"
                    )
                
                with col3:
                    st.metric(
                        "Emailing Results",
                        f"{stats['trace_counts'].get('email_results', 0):,}",
                        help="Number of traces for emailing results to users"
                    )
                
                with col4:
                    st.metric(
                        "Other Traces",
                        f"{stats['trace_counts']['other']:,}",
                        help="Number of other trace types"
                    )
            
            st.divider()
            
            # Date range
            if stats['date_range']['start'] and stats['date_range']['end']:
                st.info(f"📅 Data Range: {stats['date_range']['start'].strftime('%Y-%m-%d %H:%M')} to {stats['date_range']['end'].strftime('%Y-%m-%d %H:%M')}")
            
            # Model usage breakdown
            if stats.get('models_used'):
                st.subheader("Model Usage Distribution")
                model_df = pd.DataFrame(
                    list(stats['models_used'].items()),
                    columns=['Model', 'Requests']
                )
                fig = px.pie(
                    model_df,
                    values='Requests',
                    names='Model',
                    title='Requests by Model'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # TAB 2: Usage Analytics (Trace-based)
    with tab2:
        st.header("Usage Analytics")
        st.markdown("*User-level analytics based on traces*")
        
        # User Analytics Table
        st.subheader("👥 User Usage Summary")
        user_analytics = analyzer.get_user_analytics()
        
        if not user_analytics.empty:
            # Display user table with key metrics
            display_cols = ['user_name', 'user_email', 'total_traces', 'referrals_count', 'action_plans_count', 
                          'email_results_count', 'first_trace', 'last_trace', 'avg_duration_s', 'total_tokens']
            
            user_display = user_analytics[display_cols].copy()
            user_display.columns = ['Name', 'Email', 'Total Traces', 'Referrals', 'Action Plans', 
                                  'Emails', 'First Trace', 'Last Trace', 'Avg Duration (s)', 'Total Tokens']
            
            # Format dates and handle NaT
            user_display['First Trace'] = pd.to_datetime(user_display['First Trace'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
            user_display['Last Trace'] = pd.to_datetime(user_display['Last Trace'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
            user_display['Avg Duration (s)'] = user_display['Avg Duration (s)'].round(2).fillna(0)
            user_display = user_display.fillna('N/A')
            
            st.dataframe(
                user_display,
                use_container_width=True,
                hide_index=True
            )
            
            # User selection for detailed view
            st.subheader("🔍 User Detail View")
            selected_user = st.selectbox(
                "Select a user to view detailed trace history",
                options=user_analytics['user_email'].tolist(),
                format_func=lambda x: f"{user_analytics[user_analytics['user_email']==x]['user_name'].iloc[0]} ({x})"
            )
            
            if selected_user:
                user_traces = analyzer.get_user_trace_details(selected_user)
                
                if not user_traces.empty:
                    st.write(f"**Traces for {selected_user}**")
                    
                    # Display trace details
                    display_cols = ['trace_start', 'trace_type', 'query', 'category',
                                   'location_preference', 'zip_code',
                                   'trace_duration_s', 'total_tokens', 'status']
                    available_cols = [col for col in display_cols if col in user_traces.columns]
                    
                    trace_display = user_traces[available_cols].copy()
                    col_names = [
                        'Timestamp', 'Type', 'Query', 'Category', 'Location Pref',
                        'Zip Code', 'Duration (s)', 'Tokens', 'Status'
                    ]
                    trace_display.columns = col_names[:len(available_cols)]
                    
                    if 'Timestamp' in trace_display.columns:
                        trace_display['Timestamp'] = pd.to_datetime(trace_display['Timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                    if 'Duration (s)' in trace_display.columns:
                        trace_display['Duration (s)'] = pd.to_numeric(trace_display['Duration (s)'], errors='coerce').round(2)
                    
                    trace_display = trace_display.fillna('N/A')
                    st.dataframe(trace_display, use_container_width=True, hide_index=True)
                    
                    # Show summary stats for this user
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Traces", len(user_traces))
                    with col2:
                        referrals = len(user_traces[user_traces['trace_type'] == 'referrals'])
                        st.metric("Referrals", referrals)
                    with col3:
                        action_plans = len(user_traces[user_traces['trace_type'] == 'action_plans'])
                        st.metric("Action Plans", action_plans)
                    with col4:
                        avg_dur = user_traces['trace_duration_s'].mean()
                        st.metric("Avg Duration", f"{avg_dur:.2f}s" if pd.notna(avg_dur) else "N/A")
        
        # Time series based on traces
        st.subheader("📈 Trace Volume Over Time")
        col1, col2 = st.columns([1, 3])
        with col1:
            freq = st.selectbox(
                "Time Granularity",
                ["Hourly", "Daily", "Weekly"],
                index=1,
                key="trace_freq"
            )
        
        freq_map = {"Hourly": "H", "Daily": "D", "Weekly": "W"}
        trace_time_series = analyzer.get_trace_time_series(freq=freq_map[freq])
        
        if not trace_time_series.empty:
            # Trace volume over time with type breakdown
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Trace Volume Over Time", "Trace Types Breakdown"),
                vertical_spacing=0.15
            )
            
            fig.add_trace(
                go.Scatter(
                    x=trace_time_series['timestamp'],
                    y=trace_time_series['trace_count'],
                    name='Total Traces',
                    fill='tozeroy',
                    line=dict(color='#1f77b4')
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=trace_time_series['timestamp'],
                    y=trace_time_series['referrals_count'],
                    name='Referrals',
                    fill='tozeroy',
                    line=dict(color='#2ca02c')
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=trace_time_series['timestamp'],
                    y=trace_time_series['action_plans_count'],
                    name='Action Plans',
                    fill='tozeroy',
                    line=dict(color='#ff7f0e')
                ),
                row=2, col=1
            )
            
            fig.update_xaxes(title_text="Time", row=2, col=1)
            fig.update_yaxes(title_text="Trace Count", row=1, col=1)
            fig.update_yaxes(title_text="Count by Type", row=2, col=1)
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Average duration over time
            st.subheader("⏱️ Average Trace Duration Over Time")
            fig_duration = px.line(
                trace_time_series,
                x='timestamp',
                y='avg_duration',
                title='Average Trace Duration',
                labels={'avg_duration': 'Duration (s)', 'timestamp': 'Time'}
            )
            st.plotly_chart(fig_duration, use_container_width=True)

        # Organic usage (exclude planned advisory board sessions)
        st.divider()
        st.subheader("🌿 Organic Usage (excluding NAB/CAB meeting windows)")
        st.caption("Filters out traces that occurred during scheduled advisory board meetings, so you can see organic (non-planned) usage trends.")

        exclude_meetings = st.checkbox(
            "Exclude advisory board meeting windows",
            value=True,
            help="If enabled, traces during the listed meeting windows will be counted as 'planned' and removed from 'organic' usage."
        )
        meeting_duration_min = st.slider(
            "Assumed meeting session length (minutes)",
            min_value=15,
            max_value=180,
            value=60,
            step=15,
            help="Used to convert each meeting start time into an exclusion window."
        )

        # Extracted from:
        # - Goodwill NAB Sessions.pdf
        # - Goodwill CAB Sessions.pdf
        # Times are normalized to ET (America/New_York).
        default_meeting_starts_et = [
            # September/October 2025 - NAB Session 2
            "2025-09-29 13:00", "2025-09-29 15:00",
            "2025-09-30 14:00", "2025-09-30 15:00",
            "2025-10-02 14:30",
            "2025-10-06 13:00",
            # November 2025 - NAB Session 3
            "2025-11-04 14:15", "2025-11-04 15:00",
            "2025-11-05 14:15", "2025-11-05 13:30",
            "2025-11-06 12:00",
            "2025-11-07 13:30",
            "2025-11-10 12:00", "2025-11-10 12:45", "2025-11-10 13:30",
            # December 2025 - NAB Session 4
            "2025-12-08 13:00", "2025-12-08 14:00",
            "2025-12-09 14:00",
            "2025-12-10 14:00",
            "2025-12-11 14:00",
            "2025-12-18 14:00",

            # November 2025 - CAB Session 1
            "2025-11-17 12:30", "2025-11-17 13:20",
            "2025-11-18 14:10", "2025-11-18 15:00",
            # 11/19 had a "NO SHOW" at 12:30 ET in the PDF; we do NOT exclude that slot.
            "2025-11-19 13:10", "2025-11-19 15:00",

            # December 2025 - CAB Session 2
            "2025-12-15 13:00",
            "2025-12-16 14:00", "2025-12-16 15:00",
            "2025-12-17 14:00",
            "2025-12-22 13:00",

            # January 2026 - Training meeting (provided as 3pm CST => 4pm ET)
            "2026-01-06 16:00",

            # January 2026 - NAB Session 5
            "2026-01-20 09:00",
            "2026-01-20 14:00", "2026-01-20 15:00",
            "2026-01-21 13:00", "2026-01-21 14:00",
            "2026-01-22 14:00",
            # 2026-01-22 15:00 ET was marked no-show in the latest NAB schedule
            "2026-01-27 11:45",
            "2026-02-04 12:30",

            # January 2026 - CAB Session 3
            "2026-01-26 12:30",
            "2026-01-27 12:30", "2026-01-27 15:30",
            "2026-01-28 12:00", "2026-01-28 13:00", "2026-01-28 14:00",
            # 2026-01-29 15:00 ET was marked no-show in the latest CAB schedule
        ]

        st.caption(
            "Meeting exclusion schedule last updated: 2026-02-19 "
            "(includes latest NAB Session 5 and CAB Session 3 updates from shared screenshots)."
        )

        with st.expander("📅 Meeting window schedule (editable)", expanded=False):
            st.markdown("Paste additional meeting start times below (ET), one per line as `YYYY-MM-DD HH:MM`.")
            additional_starts_text = st.text_area(
                "Additional meeting starts (ET)",
                value="",
                height=120,
                key="additional_meeting_starts_et"
            )
            show_default = st.checkbox("Show default meeting starts extracted from the PDF", value=False)
            if show_default:
                st.code("\n".join(default_meeting_starts_et))

        # Build meeting windows in UTC
        ny_tz = ZoneInfo("America/New_York")
        meeting_starts_et = list(default_meeting_starts_et)
        if additional_starts_text.strip():
            for line in additional_starts_text.splitlines():
                s = line.strip()
                if s:
                    meeting_starts_et.append(s)

        windows_utc = []
        for s in meeting_starts_et:
            try:
                dt_local = datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=ny_tz)
                start_utc = dt_local.astimezone(timezone.utc)
                end_utc = start_utc + timedelta(minutes=int(meeting_duration_min))
                windows_utc.append((start_utc, end_utc))
            except Exception:
                continue

        if analyzer.traces_df.empty or 'trace_start' not in analyzer.traces_df.columns:
            st.info("No trace timestamps available to compute organic usage.")
        else:
            traces_for_org = analyzer.traces_df.copy()
            ts_utc = pd.to_datetime(traces_for_org['trace_start'], errors='coerce', utc=True)
            traces_for_org = traces_for_org.assign(_trace_start_utc=ts_utc).dropna(subset=['_trace_start_utc'])

            planned_mask = pd.Series(False, index=traces_for_org.index)
            if exclude_meetings and windows_utc:
                for start_utc, end_utc in windows_utc:
                    planned_mask = planned_mask | (
                        (traces_for_org['_trace_start_utc'] >= pd.Timestamp(start_utc)) &
                        (traces_for_org['_trace_start_utc'] < pd.Timestamp(end_utc))
                    )

                # Always count intake@gwctx.org as organic (pilot usage), even if within meeting windows
                if 'user_email' in traces_for_org.columns:
                    intake_mask = (
                        traces_for_org['user_email']
                        .astype(str)
                        .str.lower()
                        .str.strip()
                        .eq('intake@gwctx.org')
                    )
                    if intake_mask.any():
                        planned_mask = planned_mask & ~intake_mask

            organic_df = traces_for_org[~planned_mask].copy()
            planned_df = traces_for_org[planned_mask].copy()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Traces", f"{len(traces_for_org):,}")
            with col2:
                st.metric("Planned (meeting) Traces", f"{len(planned_df):,}")
            with col3:
                st.metric("Organic Traces", f"{len(organic_df):,}")
            with col4:
                pct = (len(organic_df) / len(traces_for_org) * 100) if len(traces_for_org) else 0
                st.metric("% Organic", f"{pct:.1f}%")

            # Clarify "uses" (traces) vs people (unique users)
            st.markdown("#### 👥 Uses vs Unique Users (Organic)")
            st.caption(
                "In this dashboard, a 'use' equals one trace (any type: referrals, action plans, email results, etc.). "
                "Use the metrics below to compare trace volume vs. active people."
            )

            organic_daily = organic_df.copy()
            organic_daily["day"] = organic_daily["_trace_start_utc"].dt.floor("D")
            daily_uses = organic_daily.groupby("day").size().rename("uses")

            if "user_email" in organic_daily.columns:
                organic_daily["_user_norm"] = (
                    organic_daily["user_email"].astype(str).str.lower().str.strip()
                )
                valid_user_mask = (
                    organic_daily["_user_norm"].ne("")
                    & ~organic_daily["_user_norm"].eq("unknown")
                    & ~organic_daily["_user_norm"].str.startswith("unknown_")
                )
                daily_unique_users = (
                    organic_daily.loc[valid_user_mask]
                    .groupby("day")["_user_norm"]
                    .nunique()
                    .rename("unique_users")
                )
            else:
                daily_unique_users = pd.Series(dtype=float, name="unique_users")

            daily_compare = (
                pd.concat([daily_uses, daily_unique_users], axis=1)
                .fillna(0)
                .reset_index()
                .rename(columns={"day": "timestamp"})
            )
            daily_compare["uses"] = daily_compare["uses"].astype(int)
            daily_compare["unique_users"] = daily_compare["unique_users"].astype(int)
            daily_compare["uses_per_active_user"] = np.where(
                daily_compare["unique_users"] > 0,
                daily_compare["uses"] / daily_compare["unique_users"],
                np.nan,
            )

            avg_uses_per_day = float(daily_compare["uses"].mean()) if not daily_compare.empty else 0.0
            avg_unique_users_per_day = (
                float(daily_compare["unique_users"].mean()) if not daily_compare.empty else 0.0
            )
            avg_uses_per_active_user = (
                float(daily_compare["uses_per_active_user"].dropna().mean())
                if not daily_compare["uses_per_active_user"].dropna().empty
                else 0.0
            )

            # Share of organic traces by type to give workflow context
            if "trace_type" in organic_df.columns and not organic_df.empty:
                organic_type_counts = organic_df["trace_type"].fillna("other").value_counts()
                referral_pct = organic_type_counts.get("referrals", 0) / len(organic_df) * 100
                action_plan_pct = organic_type_counts.get("action_plans", 0) / len(organic_df) * 100
                email_pct = organic_type_counts.get("email_results", 0) / len(organic_df) * 100
            else:
                referral_pct = action_plan_pct = email_pct = 0.0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Organic Uses / Day", f"{avg_uses_per_day:.1f}")
            m2.metric("Avg Unique Users / Day", f"{avg_unique_users_per_day:.1f}")
            m3.metric("Avg Uses per Active User / Day", f"{avg_uses_per_active_user:.2f}")
            m4.metric(
                "Organic Mix",
                f"R {referral_pct:.0f}% | A {action_plan_pct:.0f}% | E {email_pct:.0f}%",
                help="R=referrals, A=action_plans, E=email_results",
            )

            if not daily_compare.empty:
                fig_people = go.Figure()
                fig_people.add_trace(
                    go.Scatter(
                        x=daily_compare["timestamp"],
                        y=daily_compare["uses"],
                        name="Organic Uses (Traces)",
                        mode="lines+markers",
                        line=dict(color="#2ca02c", width=3),
                    )
                )
                fig_people.add_trace(
                    go.Scatter(
                        x=daily_compare["timestamp"],
                        y=daily_compare["unique_users"],
                        name="Unique Users",
                        mode="lines+markers",
                        line=dict(color="#17becf", width=3),
                    )
                )
                fig_people.update_layout(
                    title="Organic Uses vs Unique Users per Day",
                    height=380,
                    xaxis_title="Time",
                    yaxis_title="Count",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_people, use_container_width=True)

            # Same-day workflow completion (Referrals -> Action Plan -> Email)
            st.markdown("#### 🔁 Workflow Completion (same user, same day)")
            st.caption(
                "Tracks how many organic users complete key workflow steps on the same day. "
                "Helps distinguish 'many traces by few users' from broad user adoption."
            )
            if (
                not organic_df.empty
                and "trace_type" in organic_df.columns
                and "user_email" in organic_df.columns
            ):
                workflow_df = organic_df.copy()
                workflow_df["day"] = workflow_df["_trace_start_utc"].dt.floor("D")
                workflow_df["_user_norm"] = (
                    workflow_df["user_email"].astype(str).str.lower().str.strip()
                )
                workflow_df = workflow_df[
                    workflow_df["_user_norm"].ne("")
                    & ~workflow_df["_user_norm"].eq("unknown")
                    & ~workflow_df["_user_norm"].str.startswith("unknown_")
                ].copy()

                if not workflow_df.empty:
                    user_day = (
                        workflow_df.groupby(["day", "_user_norm"])["trace_type"]
                        .agg(lambda s: set(s.dropna().astype(str)))
                        .reset_index(name="trace_types")
                    )
                    user_day["did_referrals"] = user_day["trace_types"].apply(
                        lambda t: "referrals" in t
                    )
                    user_day["did_action_plan"] = user_day["trace_types"].apply(
                        lambda t: "action_plans" in t
                    )
                    user_day["did_email"] = user_day["trace_types"].apply(
                        lambda t: "email_results" in t
                    )
                    user_day["did_full_workflow"] = (
                        user_day["did_referrals"]
                        & user_day["did_action_plan"]
                        & user_day["did_email"]
                    )
                    user_day["steps_completed"] = (
                        user_day[["did_referrals", "did_action_plan", "did_email"]]
                        .astype(int)
                        .sum(axis=1)
                    )

                    daily_workflow = (
                        user_day.groupby("day")
                        .agg(
                            active_users=("_user_norm", "nunique"),
                            users_referrals=("did_referrals", "sum"),
                            users_action_plans=("did_action_plan", "sum"),
                            users_email=("did_email", "sum"),
                            users_full_workflow=("did_full_workflow", "sum"),
                        )
                        .reset_index()
                        .rename(columns={"day": "timestamp"})
                    )
                    for c in [
                        "users_referrals",
                        "users_action_plans",
                        "users_email",
                        "users_full_workflow",
                    ]:
                        daily_workflow[f"{c}_rate"] = np.where(
                            daily_workflow["active_users"] > 0,
                            daily_workflow[c] / daily_workflow["active_users"] * 100,
                            0,
                        )

                    wf1, wf2, wf3, wf4 = st.columns(4)
                    wf1.metric(
                        "Avg Users/Day - Referrals",
                        f"{daily_workflow['users_referrals'].mean():.1f}",
                    )
                    wf2.metric(
                        "Avg Users/Day - Action Plans",
                        f"{daily_workflow['users_action_plans'].mean():.1f}",
                    )
                    wf3.metric(
                        "Avg Users/Day - Email",
                        f"{daily_workflow['users_email'].mean():.1f}",
                    )
                    wf4.metric(
                        "Avg Users/Day - Full Workflow",
                        f"{daily_workflow['users_full_workflow'].mean():.1f}",
                    )

                    # Workflow conversion summary
                    st.markdown("**Workflow Conversion Rates (user-days)**")
                    total_user_days = len(user_day)
                    referral_user_days = int(user_day["did_referrals"].sum())
                    action_user_days = int(user_day["did_action_plan"].sum())
                    _email_user_days = int(user_day["did_email"].sum())
                    full_user_days = int(user_day["did_full_workflow"].sum())

                    referral_rate = (
                        referral_user_days / total_user_days * 100 if total_user_days else 0.0
                    )
                    action_after_referral_rate = (
                        int((user_day["did_referrals"] & user_day["did_action_plan"]).sum())
                        / referral_user_days
                        * 100
                        if referral_user_days
                        else 0.0
                    )
                    email_after_action_rate = (
                        int((user_day["did_action_plan"] & user_day["did_email"]).sum())
                        / action_user_days
                        * 100
                        if action_user_days
                        else 0.0
                    )
                    full_workflow_rate = (
                        full_user_days / total_user_days * 100 if total_user_days else 0.0
                    )

                    cv1, cv2, cv3, cv4 = st.columns(4)
                    cv1.metric(
                        "Referral Reach",
                        f"{referral_rate:.1f}%",
                        help="Percent of active organic user-days that included at least one referral trace.",
                    )
                    cv2.metric(
                        "Action Plan after Referral",
                        f"{action_after_referral_rate:.1f}%",
                        help="Of user-days with referrals, percent that also included action plan generation.",
                    )
                    cv3.metric(
                        "Email after Action Plan",
                        f"{email_after_action_rate:.1f}%",
                        help="Of user-days with action plans, percent that also included email_result traces.",
                    )
                    cv4.metric(
                        "Full Workflow Completion",
                        f"{full_workflow_rate:.1f}%",
                        help="Percent of active organic user-days that completed referrals + action plan + email.",
                    )

                    fig_wf = go.Figure()
                    fig_wf.add_trace(
                        go.Scatter(
                            x=daily_workflow["timestamp"],
                            y=daily_workflow["users_referrals"],
                            name="Users: Referrals",
                            line=dict(color="#2ca02c", width=2),
                        )
                    )
                    fig_wf.add_trace(
                        go.Scatter(
                            x=daily_workflow["timestamp"],
                            y=daily_workflow["users_action_plans"],
                            name="Users: Action Plans",
                            line=dict(color="#ff7f0e", width=2),
                        )
                    )
                    fig_wf.add_trace(
                        go.Scatter(
                            x=daily_workflow["timestamp"],
                            y=daily_workflow["users_email"],
                            name="Users: Email",
                            line=dict(color="#9467bd", width=2),
                        )
                    )
                    fig_wf.add_trace(
                        go.Scatter(
                            x=daily_workflow["timestamp"],
                            y=daily_workflow["users_full_workflow"],
                            name="Users: Full Workflow",
                            line=dict(color="#17becf", width=3),
                        )
                    )
                    fig_wf.update_layout(
                        title="Daily Unique Users by Workflow Step",
                        height=380,
                        xaxis_title="Time",
                        yaxis_title="Unique Users",
                        legend=dict(
                            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                        ),
                    )
                    st.plotly_chart(fig_wf, use_container_width=True)

                    # User intensity and step-completion distribution
                    st.markdown("#### 🧭 User Behavior Cuts (Organic)")
                    user_totals = (
                        workflow_df.groupby("_user_norm")
                        .size()
                        .reset_index(name="organic_traces")
                        .sort_values("organic_traces", ascending=False)
                    )
                    user_totals["intensity_bucket"] = pd.cut(
                        user_totals["organic_traces"],
                        bins=[0, 1, 4, 9, np.inf],
                        labels=["1 trace", "2-4 traces", "5-9 traces", "10+ traces"],
                    )
                    bucket_counts = (
                        user_totals["intensity_bucket"]
                        .value_counts(dropna=False)
                        .reset_index()
                    )
                    bucket_counts.columns = ["Bucket", "Users"]

                    step_counts = (
                        user_day["steps_completed"]
                        .value_counts()
                        .reindex([1, 2, 3], fill_value=0)
                        .reset_index()
                    )
                    step_counts.columns = ["Steps Completed (same day)", "User-Day Count"]

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**User intensity distribution (entire period)**")
                        st.dataframe(bucket_counts, use_container_width=True, hide_index=True)
                    with c2:
                        st.markdown("**Step completion distribution (user-days)**")
                        st.dataframe(step_counts, use_container_width=True, hide_index=True)
                else:
                    st.info("No valid user emails in organic traces to compute workflow metrics.")
            else:
                st.info("Workflow metrics require `user_email` and `trace_type` fields.")

            # Time series (use the same granularity selection as the main trace chart)
            ts_freq = freq_map.get(freq, "D")

            total_series = traces_for_org.set_index('_trace_start_utc').resample(ts_freq).size().rename("total_traces")
            organic_series = organic_df.set_index('_trace_start_utc').resample(ts_freq).size().rename("organic_traces")
            planned_series = planned_df.set_index('_trace_start_utc').resample(ts_freq).size().rename("planned_traces")

            org_ts = pd.concat([total_series, organic_series, planned_series], axis=1).fillna(0).reset_index().rename(columns={'_trace_start_utc': 'timestamp'})
            org_ts[['total_traces', 'organic_traces', 'planned_traces']] = org_ts[['total_traces', 'organic_traces', 'planned_traces']].astype(int)

            fig_org = go.Figure()
            fig_org.add_trace(go.Scatter(
                x=org_ts['timestamp'], y=org_ts['organic_traces'],
                name="Organic Traces", line=dict(color="#2ca02c")
            ))
            fig_org.add_trace(go.Scatter(
                x=org_ts['timestamp'], y=org_ts['total_traces'],
                name="Total Traces", line=dict(color="#1f77b4"), opacity=0.5
            ))
            fig_org.add_trace(go.Bar(
                x=org_ts['timestamp'], y=org_ts['planned_traces'],
                name="Planned (meeting) Traces", marker_color="#ff7f0e", opacity=0.25
            ))
            fig_org.update_layout(
                title="Organic vs Planned Usage Over Time",
                barmode="overlay",
                height=450,
                xaxis_title="Time",
                yaxis_title="Trace Count",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_org, use_container_width=True)

            # Usage by Pilot Location (domain-based + known cohort emails)
            st.subheader("🏢 Usage by Pilot Location")
            st.caption(
                "Total organic usage grouped by pilot location (domain-based, plus known cohort emails). "
                "This captures ALL users from each location without needing exact email lists."
            )

            if 'user_email' not in organic_df.columns:
                st.info("No user email field available to compute location-based usage.")
            else:
                # Categorize by domain and known cohort email lists
                emails_lower = organic_df["user_email"].astype(str).str.lower().str.strip()
                g1_set = _parse_emails(st.session_state.get("g1_org_emails", G1_EMAILS_DEFAULT))
                g2_set = _parse_emails(st.session_state.get("g2_org_emails", G2_EMAILS_DEFAULT))
                g3_set = _parse_emails(st.session_state.get("g3_org_emails", G3_EMAILS_DEFAULT))
                keystone_set = _parse_emails(
                    st.session_state.get("keystone_org_emails", KEYSTONE_EMAILS_DEFAULT)
                )
                cab_set = _parse_emails(
                    st.session_state.get("cab_org_emails", CAB_EMAILS_DEFAULT)
                )
                ctx_set = g1_set | g2_set | g3_set
                intake_count = (emails_lower == "intake@gwctx.org").sum()

                organic_df_loc = organic_df.copy()
                organic_df_loc["pilot_location"] = "Other"
                unknown_mask = (~emails_lower.str.contains("@", na=False)) | emails_lower.str.contains(
                    "unknown", na=False
                )
                organic_df_loc.loc[unknown_mask, "pilot_location"] = "Unknown"
                organic_df_loc.loc[
                    emails_lower.str.contains("@gwctx.org", na=False)
                    | emails_lower.isin(ctx_set),
                    "pilot_location",
                ] = "CTX (Goodwill Central Texas)"
                organic_df_loc.loc[
                    emails_lower.str.contains("@yourgoodwill.org", na=False)
                    | emails_lower.isin(keystone_set),
                    "pilot_location",
                ] = "Keystone (Goodwill Keystone)"
                organic_df_loc.loc[emails_lower.isin(cab_set), "pilot_location"] = "CAB (Advisory)"

                # Summary metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                ctx_count = len(
                    organic_df_loc[
                        organic_df_loc["pilot_location"] == "CTX (Goodwill Central Texas)"
                    ]
                )
                keystone_count = len(
                    organic_df_loc[
                        organic_df_loc["pilot_location"] == "Keystone (Goodwill Keystone)"
                    ]
                )
                cab_count = len(
                    organic_df_loc[organic_df_loc["pilot_location"] == "CAB (Advisory)"]
                )
                unknown_count = len(
                    organic_df_loc[organic_df_loc["pilot_location"] == "Unknown"]
                )
                other_count = len(organic_df_loc[organic_df_loc["pilot_location"] == "Other"])
                total_organic = len(organic_df_loc)
                
                col1.metric("Total Organic", f"{total_organic:,}")
                col2.metric(
                    "CTX",
                    f"{ctx_count:,}",
                    f"{ctx_count/total_organic*100:.0f}%" if total_organic else "0%",
                )
                col3.metric(
                    "Keystone",
                    f"{keystone_count:,}",
                    f"{keystone_count/total_organic*100:.0f}%" if total_organic else "0%",
                )
                col4.metric(
                    "CAB",
                    f"{cab_count:,}",
                    f"{cab_count/total_organic*100:.0f}%" if total_organic else "0%",
                )
                col5.metric(
                    "Other/Unknown",
                    f"{other_count + unknown_count:,}",
                    f"{(other_count + unknown_count)/total_organic*100:.0f}%"
                    if total_organic
                    else "0%",
                )

                if intake_count > 0:
                    st.info(
                        f"✅ `intake@gwctx.org` is included in Organic usage: {intake_count} traces "
                        "(counted under CTX)."
                    )
                
                # Time series by location
                ctx_series = (
                    organic_df_loc[
                        organic_df_loc["pilot_location"]
                        == "CTX (Goodwill Central Texas)"
                    ]
                    .set_index("_trace_start_utc")
                    .resample(ts_freq)
                    .size()
                    .rename("CTX")
                )
                keystone_loc_series = (
                    organic_df_loc[
                        organic_df_loc["pilot_location"]
                        == "Keystone (Goodwill Keystone)"
                    ]
                    .set_index("_trace_start_utc")
                    .resample(ts_freq)
                    .size()
                    .rename("Keystone")
                )
                cab_series = (
                    organic_df_loc[
                        organic_df_loc["pilot_location"] == "CAB (Advisory)"
                    ]
                    .set_index("_trace_start_utc")
                    .resample(ts_freq)
                    .size()
                    .rename("CAB")
                )
                other_series = (
                    organic_df_loc[organic_df_loc["pilot_location"] == "Other"]
                    .set_index("_trace_start_utc")
                    .resample(ts_freq)
                    .size()
                    .rename("Other")
                )
                unknown_series = (
                    organic_df_loc[organic_df_loc["pilot_location"] == "Unknown"]
                    .set_index("_trace_start_utc")
                    .resample(ts_freq)
                    .size()
                    .rename("Unknown")
                )
                
                location_ts = (
                    pd.concat(
                        [
                            ctx_series,
                            keystone_loc_series,
                            cab_series,
                            other_series,
                            unknown_series,
                        ],
                        axis=1,
                    )
                    .fillna(0)
                    .astype(int)
                    .reset_index()
                    .rename(columns={'_trace_start_utc': 'timestamp'})
                )
                
                fig_loc = go.Figure()
                fig_loc.add_trace(go.Scatter(
                    x=location_ts['timestamp'], y=location_ts['CTX'],
                    name="CTX (Central Texas)", line=dict(color="#1f77b4", width=3),
                    mode='lines+markers'
                ))
                fig_loc.add_trace(go.Scatter(
                    x=location_ts['timestamp'], y=location_ts['Keystone'],
                    name="Keystone", line=dict(color="#9467bd", width=3),
                    mode='lines+markers'
                ))
                fig_loc.add_trace(go.Scatter(
                    x=location_ts["timestamp"],
                    y=location_ts["CAB"],
                    name="CAB (Advisory)",
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                    mode="lines+markers",
                ))
                fig_loc.add_trace(go.Scatter(
                    x=location_ts['timestamp'], y=location_ts['Other'],
                    name="Other", line=dict(color="#7f7f7f", width=1, dash='dot'),
                    opacity=0.5
                ))
                fig_loc.add_trace(go.Scatter(
                    x=location_ts["timestamp"],
                    y=location_ts["Unknown"],
                    name="Unknown",
                    line=dict(color="#bcbd22", width=1, dash="dot"),
                    opacity=0.5,
                ))
                fig_loc.update_layout(
                    title="Organic Usage Over Time by Pilot Location",
                    height=450,
                    xaxis_title="Time",
                    yaxis_title="Trace Count",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_loc, use_container_width=True)
                
                # Show who's in Other/Unknown (for cleanup)
                if other_count + unknown_count > 0:
                    with st.expander(
                        f"ℹ️ {other_count + unknown_count} traces in Other/Unknown (click to see details)",
                        expanded=False,
                    ):
                        other_emails = (
                            organic_df_loc[
                                organic_df_loc["pilot_location"].isin(["Other", "Unknown"])
                            ]["user_email"]
                            .value_counts()
                            .reset_index()
                        )
                        other_emails.columns = ["Email", "Trace Count"]
                        st.dataframe(other_emails, use_container_width=True, hide_index=True)
                        st.caption(
                            "These are organic traces not matching CTX/Keystone domains or known cohort lists."
                        )
                        domain_counts = (
                            other_emails["Email"]
                            .str.extract(r"@(.+)$")[0]
                            .fillna("unknown")
                            .value_counts()
                            .reset_index()
                        )
                        domain_counts.columns = ["Domain", "Trace Count"]
                        st.dataframe(
                            domain_counts, use_container_width=True, hide_index=True
                        )

            st.divider()

            # Organic pilot cohort usage (G1/G2/G3/Keystone)
            st.subheader("🌿 Organic Pilot Usage by Cohort Wave (G1/G2/G3/Keystone)")
            st.caption(
                "Tracks organic usage for the pilot cohorts only (after excluding meeting windows)."
            )

            if 'user_email' not in organic_df.columns:
                st.info("No user email field available to compute pilot cohort organic usage.")
            else:
                with st.expander("🎯 Pilot cohort emails (editable)", expanded=False):
                    g1_org_text = st.text_area(
                        "G1 emails (one per line)",
                        value=G1_EMAILS_DEFAULT,
                        height=140,
                        key="g1_org_emails",
                    )
                    g2_org_text = st.text_area(
                        "G2 emails (one per line)",
                        value=G2_EMAILS_DEFAULT,
                        height=140,
                        key="g2_org_emails",
                    )
                    g3_org_text = st.text_area(
                        "G3 emails (one per line)",
                        value=G3_EMAILS_DEFAULT,
                        height=140,
                        key="g3_org_emails",
                    )
                    keystone_org_text = st.text_area(
                        "Keystone emails (one per line)",
                        value=KEYSTONE_EMAILS_DEFAULT,
                        height=140,
                        key="keystone_org_emails",
                    )

                g1_set = _parse_emails(g1_org_text)
                g2_set = _parse_emails(g2_org_text)
                g3_set = _parse_emails(g3_org_text)
                keystone_set = _parse_emails(keystone_org_text)

                org_emails = (
                    organic_df['user_email'].astype(str).str.lower().str.strip()
                )
                keystone_domain_mask = org_emails.str.contains('@yourgoodwill.org', na=False)
                keystone_manual_mask = org_emails.isin(keystone_set)
                keystone_match_mask = keystone_domain_mask | keystone_manual_mask

                g1_series = organic_df.loc[org_emails.isin(g1_set)].set_index('_trace_start_utc').resample(ts_freq).size().rename('G1')
                g2_series = organic_df.loc[org_emails.isin(g2_set)].set_index('_trace_start_utc').resample(ts_freq).size().rename('G2')
                g3_series = organic_df.loc[org_emails.isin(g3_set)].set_index('_trace_start_utc').resample(ts_freq).size().rename('G3')
                keystone_series = organic_df.loc[keystone_match_mask].set_index('_trace_start_utc').resample(ts_freq).size().rename('Keystone')

                cohort_ts = (
                    pd.concat([g1_series, g2_series, g3_series, keystone_series], axis=1)
                    .fillna(0)
                    .astype(int)
                    .reset_index()
                    .rename(columns={'_trace_start_utc': 'timestamp'})
                )

                fig_coh = go.Figure()
                fig_coh.add_trace(go.Scatter(
                    x=cohort_ts['timestamp'], y=cohort_ts['G1'],
                    name="G1 Organic", line=dict(color="#1f77b4")
                ))
                fig_coh.add_trace(go.Scatter(
                    x=cohort_ts['timestamp'], y=cohort_ts['G2'],
                    name="G2 Organic", line=dict(color="#2ca02c")
                ))
                fig_coh.add_trace(go.Scatter(
                    x=cohort_ts['timestamp'], y=cohort_ts['G3'],
                    name="G3 Organic", line=dict(color="#ff7f0e")
                ))
                fig_coh.add_trace(go.Scatter(
                    x=cohort_ts['timestamp'], y=cohort_ts['Keystone'],
                    name="Keystone Organic", line=dict(color="#9467bd")
                ))
                fig_coh.update_layout(
                    title="Organic Usage Over Time — Pilot Cohorts (G1/G2/G3/Keystone)",
                    height=420,
                    xaxis_title="Time",
                    yaxis_title="Trace Count",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_coh, use_container_width=True)

                # Show unmatched organic traces (users not in any defined cohort)
                all_non_keystone_cohort_emails = g1_set | g2_set | g3_set
                unmatched_mask = ~(org_emails.isin(all_non_keystone_cohort_emails) | keystone_match_mask)
                unmatched_organic = organic_df[unmatched_mask].copy()
                
                if not unmatched_organic.empty:
                    with st.expander(f"⚠️ {len(unmatched_organic)} organic traces NOT in any cohort (click to investigate)", expanded=False):
                        st.markdown("These organic traces have user emails that don't match G1/G2/G3 lists or Keystone domain/list matching:")
                        
                        # Show unique unmatched emails
                        unmatched_emails = unmatched_organic['user_email'].value_counts().reset_index()
                        unmatched_emails.columns = ['Email', 'Trace Count']
                        st.dataframe(unmatched_emails.head(20), use_container_width=True, hide_index=True)
                        
                        st.markdown("**Possible causes:**")
                        st.markdown("""
                        - Email extracted in different format than cohort list
                        - User not added to any cohort list yet
                        - Email showing as 'unknown_xxx' (extraction failed)
                        """)
                        
                        # Check for potential matches (close but not exact)
                        st.markdown("**Potential cohort matches (partial email match):**")
                        for email in unmatched_organic['user_email'].unique()[:10]:
                            email_lower = str(email).lower()
                            if '@yourgoodwill.org' in email_lower:
                                st.warning(f"'{email}' looks like a Keystone user but isn't in the Keystone email list")
                            elif '@gwctx.org' in email_lower:
                                st.warning(f"'{email}' looks like a G1/G2/G3 user but isn't in those lists")
    
    # TAB 3: Usage Report
    with tab3:
        st.header("📋 Comprehensive Usage Report")
        st.markdown("*Detailed breakdown by user level, resource type, and geography*")
        
        # Define cohorts with default values
        # (shared with the Organic Pilot chart)
        g1_emails_default = G1_EMAILS_DEFAULT
        g2_emails_default = G2_EMAILS_DEFAULT
        g3_emails_default = G3_EMAILS_DEFAULT
        keystone_emails_default = KEYSTONE_EMAILS_DEFAULT

        # CAB (Client Advisory Board) users
        cab_emails_default = """jswann40@yahoo.com
lukearodriguez07@gmail.com
malikjkobethomas@gmail.com
marielacalanchi3@gmail.com
mtmaguire@gmail.com
mleake86@gmail.com
chanelunknown1@gmail.com
ritadecarlo675@gmail.com"""

        # Keystone name lookup (for display purposes)
        keystone_name_lookup = {
            'user01@yourgoodwill.org': 'Keystone User 1',
            'user02@yourgoodwill.org': 'Keystone User 2',
            'user03@yourgoodwill.org': 'Keystone User 3',
            'user04@yourgoodwill.org': 'Keystone User 4',
            'user05@yourgoodwill.org': 'Keystone User 5',
            'user06@yourgoodwill.org': 'Keystone User 6',
            'user07@yourgoodwill.org': 'Keystone User 7',
            'user08@yourgoodwill.org': 'Keystone User 8',
            'user09@yourgoodwill.org': 'Keystone User 9',
            'user10@yourgoodwill.org': 'Keystone User 10',
            'user11@yourgoodwill.org': 'Keystone User 11',
            'user12@yourgoodwill.org': 'Keystone User 12',
            'user13@yourgoodwill.org': 'Keystone User 13',
            'user14@yourgoodwill.org': 'Keystone User 14',
            'user15@yourgoodwill.org': 'Keystone User 15',
            'user16@yourgoodwill.org': 'Keystone User 16',
            'user17@yourgoodwill.org': 'Keystone User 17',
            'user18@yourgoodwill.org': 'Keystone User 18',
            'user19@yourgoodwill.org': 'Keystone User 19',
        }

        # CAB name lookup (for display purposes)
        cab_name_lookup = {
            'user01@example.com': 'CAB User 1',
            'user02@example.com': 'CAB User 2',
            'user03@example.com': 'CAB User 3',
            'user04@example.com': 'CAB User 4',
            'user05@example.com': 'CAB User 5',
            'user06@example.com': 'CAB User 6',
            'user07@example.com': 'CAB User 7',
            'user08@example.com': 'CAB User 8',
        }
        
        # Report configuration
        with st.expander("⚙️ Cohort Configuration", expanded=False):
            cohort_tab1, cohort_tab2, cohort_tab3, cohort_tab4, cohort_tab5 = st.tabs(
                ["G1 Users", "G2 Users", "G3 Users", "Keystone Users", "CAB Users"]
            )
            
            with cohort_tab1:
                g1_emails_text = st.text_area(
                    "G1 User Emails (one per line)",
                    value=g1_emails_default,
                    height=200,
                    key="g1_config"
                )
            
            with cohort_tab2:
                g2_emails_text = st.text_area(
                    "G2 User Emails (one per line)",
                    value=g2_emails_default,
                    height=200,
                    key="g2_config"
                )
            
            with cohort_tab3:
                g3_emails_text = st.text_area(
                    "G3 User Emails (one per line)",
                    value=g3_emails_default,
                    height=200,
                    key="g3_config"
                )
            
            with cohort_tab4:
                keystone_emails_text = st.text_area(
                    "Keystone User Emails (one per line)",
                    value=keystone_emails_default,
                    height=200,
                    key="keystone_config"
                )

            with cohort_tab5:
                cab_emails_text = st.text_area(
                    "CAB User Emails (one per line)",
                    value=cab_emails_default,
                    height=200,
                    key="cab_config"
                )
        
        # Parse emails
        g1_emails = [e.strip() for e in g1_emails_text.split('\n') if e.strip()]
        g2_emails = [e.strip() for e in g2_emails_text.split('\n') if e.strip()]
        g3_emails = [e.strip() for e in g3_emails_text.split('\n') if e.strip()]
        keystone_emails = [e.strip() for e in keystone_emails_text.split('\n') if e.strip()]
        cab_emails = [e.strip() for e in cab_emails_text.split('\n') if e.strip()]

        # Auto-include Keystone users by domain from loaded traces (captures dev endpoint users
        # who may not yet be listed in the manual cohort list).
        auto_keystone_emails = []
        if not analyzer.traces_df.empty and 'user_email' in analyzer.traces_df.columns:
            active_emails_lower = (
                analyzer.traces_df['user_email'].astype(str).str.lower().str.strip()
            )
            auto_keystone_emails = sorted(
                {
                    e
                    for e in active_emails_lower.unique().tolist()
                    if '@yourgoodwill.org' in e and e and e != 'unknown' and not e.startswith('unknown_')
                }
            )
        keystone_emails = sorted({e.lower() for e in keystone_emails} | set(auto_keystone_emails))
        
        # Generate comprehensive report
        usage_breakdown = analyzer.get_usage_breakdown_by_level()
        resource_categories = analyzer.get_resource_category_breakdown()
        geo_data = analyzer.extract_zip_codes()
        
        # Overall metrics
        st.subheader("✅ Total Usage Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total_users = (len(usage_breakdown['high']) + 
                      len(usage_breakdown['medium']) + 
                      len(usage_breakdown['low']))
        
        with col1:
            st.metric("Unique Users", total_users)
        with col2:
            st.metric("Total Traces", len(analyzer.traces_df))
        with col3:
            referrals = len(analyzer.traces_df[analyzer.traces_df['trace_type'] == 'referrals'])
            st.metric("Referrals", referrals)
        with col4:
            action_plans = len(analyzer.traces_df[analyzer.traces_df['trace_type'] == 'action_plans'])
            st.metric("Action Plans", action_plans)
        with col5:
            email_results = len(analyzer.traces_df[analyzer.traces_df['trace_type'] == 'email_results'])
            st.metric("Emails Sent", email_results)
        
        st.divider()
        
        # User breakdown by level
        st.subheader("🧑‍💼 User Breakdown by Usage Level")
        if auto_keystone_emails:
            st.caption(
                f"Keystone cohort includes {len(auto_keystone_emails)} auto-discovered @yourgoodwill.org users from loaded traces."
            )
        
        # High-usage staff (4+ traces)
        if usage_breakdown['high']:
            st.markdown("### ⭐ High-Usage Staff (4+ traces)")
            high_df = pd.DataFrame(usage_breakdown['high'])
            high_df.columns = ['Email', 'Name', 'Total Traces']
            st.dataframe(high_df, use_container_width=True, hide_index=True)
        
        # Medium-usage staff (2-3 traces)
        if usage_breakdown['medium']:
            st.markdown("### 🧑‍💼 Medium-Usage Staff (2-3 traces)")
            medium_df = pd.DataFrame(usage_breakdown['medium'])
            medium_df.columns = ['Email', 'Name', 'Total Traces']
            st.dataframe(medium_df, use_container_width=True, hide_index=True)
        
        # Low-usage staff (1 trace)
        if usage_breakdown['low']:
            st.markdown("### 🧑‍💼 Low-Usage Staff (1 trace)")
            low_df = pd.DataFrame(usage_breakdown['low'])
            low_df.columns = ['Email', 'Name', 'Total Traces']
            st.dataframe(low_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # All Cohorts Analysis
        st.subheader("👥 User Cohort Analysis")
        
        # Create tabs for different cohorts
        cohort_display_tabs = st.tabs(
            ["📊 Overview", "G1 Users", "G2 Users", "G3 Users", "🏛️ Keystone Users", "🎯 CAB Users"]
        )
        
        # Get all cohort analyses
        g1_cohort = analyzer.get_cohort_analysis(g1_emails, "G1") if g1_emails else {}
        g2_cohort = analyzer.get_cohort_analysis(g2_emails, "G2") if g2_emails else {}
        g3_cohort = analyzer.get_cohort_analysis(g3_emails, "G3") if g3_emails else {}
        keystone_cohort = analyzer.get_cohort_analysis(keystone_emails, "Keystone") if keystone_emails else {}
        cab_cohort = analyzer.get_cohort_analysis(cab_emails, "CAB") if cab_emails else {}
        
        # Overview Tab
        with cohort_display_tabs[0]:
            st.markdown("### 📊 Cohort Adoption Summary")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                g1_rate = g1_cohort.get('adoption_rate', 0) if g1_cohort else 0
                st.metric("G1 Adoption", f"{g1_rate:.0f}%", 
                         f"{g1_cohort.get('active_count', 0)}/{g1_cohort.get('total_cohort', 0)}")
            with col2:
                g2_rate = g2_cohort.get('adoption_rate', 0) if g2_cohort else 0
                st.metric("G2 Adoption", f"{g2_rate:.0f}%",
                         f"{g2_cohort.get('active_count', 0)}/{g2_cohort.get('total_cohort', 0)}")
            with col3:
                g3_rate = g3_cohort.get('adoption_rate', 0) if g3_cohort else 0
                st.metric("G3 Adoption", f"{g3_rate:.0f}%",
                         f"{g3_cohort.get('active_count', 0)}/{g3_cohort.get('total_cohort', 0)}")
            with col4:
                keystone_rate = keystone_cohort.get('adoption_rate', 0) if keystone_cohort else 0
                st.metric("Keystone Adoption", f"{keystone_rate:.0f}%",
                         f"{keystone_cohort.get('active_count', 0)}/{keystone_cohort.get('total_cohort', 0)}")
            with col5:
                cab_rate = cab_cohort.get('adoption_rate', 0) if cab_cohort else 0
                st.metric("CAB Adoption", f"{cab_rate:.0f}%",
                         f"{cab_cohort.get('active_count', 0)}/{cab_cohort.get('total_cohort', 0)}")
            
            # Combined activity table
            st.markdown("### 📈 All Active Users Across Cohorts")
            all_active = []
            for cohort_data, cohort_name in [
                (g1_cohort, 'G1'),
                (g2_cohort, 'G2'),
                (g3_cohort, 'G3'),
                (keystone_cohort, 'Keystone'),
                (cab_cohort, 'CAB'),
            ]:
                if cohort_data and cohort_data.get('active_users'):
                    for user in cohort_data['active_users']:
                        user_copy = user.copy()
                        user_copy['cohort'] = cohort_name
                        if cohort_name == 'CAB':
                            for orig_email, name in cab_name_lookup.items():
                                if user['email'].lower() == orig_email.lower():
                                    user_copy['name'] = name
                                    break
                        if cohort_name == 'Keystone':
                            for orig_email, name in keystone_name_lookup.items():
                                if user['email'].lower() == orig_email.lower():
                                    user_copy['name'] = name
                                    break
                        all_active.append(user_copy)
            
            if all_active:
                all_active_df = pd.DataFrame(all_active)
                display_cols = ['cohort', 'name', 'email', 'trace_count', 'first_trace', 'last_trace']
                available_cols = [c for c in display_cols if c in all_active_df.columns]
                all_active_display = all_active_df[available_cols].copy()
                all_active_display.columns = ['Cohort', 'Name', 'Email', 'Traces', 'First Use', 'Last Use'][:len(available_cols)]
                if 'First Use' in all_active_display.columns:
                    all_active_display['First Use'] = pd.to_datetime(all_active_display['First Use']).dt.strftime('%Y-%m-%d')
                if 'Last Use' in all_active_display.columns:
                    all_active_display['Last Use'] = pd.to_datetime(all_active_display['Last Use']).dt.strftime('%Y-%m-%d')
                all_active_display = all_active_display.sort_values('Traces', ascending=False)
                st.dataframe(all_active_display, use_container_width=True, hide_index=True)
            else:
                st.info("No active users found across any cohort")
        
        # Helper function to display cohort details
        def display_cohort(cohort_data, cohort_name, name_lookup=None):
            if not cohort_data:
                st.info(f"No {cohort_name} cohort data configured")
                return
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"Total {cohort_name} Users", cohort_data.get('total_cohort', 0))
            with col2:
                st.metric("Active Users", cohort_data.get('active_count', 0))
            with col3:
                adoption = cohort_data.get('adoption_rate', 0)
                st.metric("Adoption Rate", f"{adoption:.1f}%")
            
            # Active users
            if cohort_data.get('active_users'):
                st.markdown(f"### ✅ {cohort_name} Users Who HAVE Used the Tool")
                active_df = pd.DataFrame(cohort_data['active_users'])
                
                # Apply name lookup if provided
                if name_lookup:
                    active_df['name'] = active_df['email'].apply(
                        lambda e: name_lookup.get(e.lower(), name_lookup.get(e, e.split('@')[0]))
                    )
                
                display_cols = ['name', 'email', 'trace_count', 'first_trace', 'last_trace']
                available_cols = [c for c in display_cols if c in active_df.columns]
                active_display = active_df[available_cols].copy()
                active_display.columns = ['Name', 'Email', 'Traces', 'First Use', 'Last Use'][:len(available_cols)]
                if 'First Use' in active_display.columns:
                    active_display['First Use'] = pd.to_datetime(active_display['First Use']).dt.strftime('%Y-%m-%d')
                if 'Last Use' in active_display.columns:
                    active_display['Last Use'] = pd.to_datetime(active_display['Last Use']).dt.strftime('%Y-%m-%d')
                st.dataframe(active_display, use_container_width=True, hide_index=True)
            
            # Inactive users
            if cohort_data.get('non_users'):
                st.markdown(f"### ❌ {cohort_name} Users Who Have NOT Used the Tool")
                non_users_df = pd.DataFrame(cohort_data['non_users'])
                
                # Apply name lookup if provided
                if name_lookup:
                    non_users_df['name'] = non_users_df['email'].apply(
                        lambda e: name_lookup.get(e.lower(), name_lookup.get(e, e.split('@')[0]))
                    )
                
                non_users_display = non_users_df[['name', 'email']].copy()
                non_users_display.columns = ['Name', 'Email']
                st.dataframe(non_users_display, use_container_width=True, hide_index=True)
        
        # G1 Tab
        with cohort_display_tabs[1]:
            st.markdown("### 🔵 G1 User Cohort (Wave 1)")
            display_cohort(g1_cohort, "G1")
        
        # G2 Tab
        with cohort_display_tabs[2]:
            st.markdown("### 🟢 G2 User Cohort (Wave 2)")
            display_cohort(g2_cohort, "G2")
        
        # G3 Tab
        with cohort_display_tabs[3]:
            st.markdown("### 🟡 G3 User Cohort (Wave 3)")
            display_cohort(g3_cohort, "G3")
        
        # Keystone Tab
        with cohort_display_tabs[4]:
            st.markdown("### 🏛️ Keystone User Cohort")
            keystone_name_lookup_lower = {k.lower(): v for k, v in keystone_name_lookup.items()}
            display_cohort(keystone_cohort, "Keystone", keystone_name_lookup_lower)

        # CAB Tab
        with cohort_display_tabs[5]:
            st.markdown("### 🎯 Client Advisory Board (CAB)")
            # Create lowercase lookup for CAB names
            cab_name_lookup_lower = {k.lower(): v for k, v in cab_name_lookup.items()}
            display_cohort(cab_cohort, "CAB", cab_name_lookup_lower)
        
        st.divider()
        
        # Resource category breakdown
        st.subheader("🎯 Resource Type Demand")
        
        if resource_categories:
            # Summary table
            cat_summary = []
            for category, data in resource_categories.items():
                cat_summary.append({
                    'Resource Type': category,
                    'Count': data['count'],
                    '% of Total': f"{data['percentage']:.1f}%"
                })
            
            cat_df = pd.DataFrame(cat_summary)
            st.dataframe(cat_df, use_container_width=True, hide_index=True)
            
            # Visualization
            fig = px.bar(
                cat_df,
                x='Resource Type',
                y='Count',
                title='Resource Demand by Category',
                text='Count'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed breakdown
            st.markdown("### 🧭 Category Breakdown with Examples")
            for category, data in resource_categories.items():
                with st.expander(f"{category} — {data['count']} traces ({data['percentage']:.1f}%)"):
                    if data.get('examples'):
                        st.markdown("**Sample queries:**")
                        for i, example in enumerate(data['examples'], 1):
                            st.markdown(f"{i}. **{example['user']}**: {example['query']}")
        
        st.divider()
        
        # Geographic analysis
        st.subheader("📍 Geographic Coverage")
        
        if geo_data.get('all_zips'):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Unique Zip Codes", geo_data['total_unique'])
                
                # Texas zips
                if geo_data.get('texas'):
                    st.markdown("**Central Texas Cluster:**")
                    for item in geo_data['texas'][:10]:
                        city = item.get('city', 'Unknown')
                        st.text(f"{item['zip']} - {city} ({item['count']} traces)")
            
            with col2:
                # Out of state
                if geo_data.get('out_of_state'):
                    st.markdown("**Out-of-Region:**")
                    for item in geo_data['out_of_state']:
                        city = item.get('city', 'Unknown')
                        st.text(f"{item['zip']} - {city} ({item['count']} traces)")
        else:
            st.info("No zip codes detected in trace queries")
        
        # Download report
        st.divider()
        st.subheader("📥 Export Report")
        
        # Prepare export data
        _export_data = {
            'Usage Summary': pd.DataFrame([{
                'Total Users': total_users,
                'Total Traces': len(analyzer.traces_df),
                'Referrals': referrals,
                'Action Plans': action_plans
            }]),
            'High Usage Users': high_df if usage_breakdown['high'] else pd.DataFrame(),
            'Medium Usage Users': medium_df if usage_breakdown['medium'] else pd.DataFrame(),
            'Low Usage Users': low_df if usage_breakdown['low'] else pd.DataFrame()
        }
        
        # Create download button for each sheet
        col1, col2 = st.columns(2)
        with col1:
            if usage_breakdown['high']:
                csv = high_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download High-Usage Users CSV",
                    csv,
                    "high_usage_users.csv",
                    "text/csv"
                )
        with col2:
            if resource_categories:
                cat_csv = cat_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download Resource Categories CSV",
                    cat_csv,
                    "resource_categories.csv",
                    "text/csv"
                )
    
    # TAB 4: Performance Metrics
    with tab4:
        st.header("Performance Metrics")
        st.markdown("*Detailed performance analysis*")
        
        user_facing_traces = (
            analyzer.get_user_facing_traces()
            if hasattr(analyzer, "get_user_facing_traces")
            else pd.DataFrame()
        )

        # Latency distribution
        st.subheader("Latency Distribution")
        latency_dist = analyzer.get_latency_distribution()
        
        if latency_dist:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.histogram(
                    x=latency_dist['histogram'],
                    nbins=50,
                    title="Latency Distribution",
                    labels={'x': 'Latency (s)', 'y': 'Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("**Latency Statistics**")
                if 'population' in latency_dist:
                    st.caption(
                        f"Population: `{latency_dist['population']}` (prefers real user questions when available)"
                    )
                st.metric("Mean", f"{latency_dist['mean']:.2f}s")
                st.metric("Median", f"{latency_dist['median']:.2f}s")
                st.metric("Std Dev", f"{latency_dist['std']:.2f}s")
                st.metric("Min", f"{latency_dist['min']:.2f}s")
                st.metric("Max", f"{latency_dist['max']:.2f}s")
        
        # Percentiles
        if latency_dist and 'percentiles' in latency_dist:
            st.subheader("Latency Percentiles")
            percentiles_df = pd.DataFrame(
                list(latency_dist['percentiles'].items()),
                columns=['Percentile', 'Latency (s)']
            )
            
            fig = px.bar(
                percentiles_df,
                x='Percentile',
                y='Latency (s)',
                title='Latency Percentiles'
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Latency Over Time (Percentiles)")
        st.caption("Percentiles are usually the best way to track perceived speed (tail latency).")

        # Time granularity (reuse the same mapping as Usage Analytics)
        freq_map = {"Hourly": "H", "Daily": "D", "Weekly": "W"}
        perf_freq = st.selectbox(
            "Time Granularity",
            list(freq_map.keys()),
            index=1,
            key="perf_latency_granularity",
        )

        ts_df = user_facing_traces.copy() if not user_facing_traces.empty else analyzer.traces_df.copy()
        if ts_df is None or ts_df.empty:
            st.info("No trace data available for latency trends.")
        else:
            if 'trace_start' in ts_df.columns:
                ts_df['trace_start'] = pd.to_datetime(ts_df['trace_start'], errors='coerce', utc=True)
            if 'trace_duration_s' in ts_df.columns:
                ts_df['trace_duration_s'] = pd.to_numeric(ts_df['trace_duration_s'], errors='coerce')

            ts_df = ts_df.dropna(subset=[c for c in ['trace_start', 'trace_duration_s'] if c in ts_df.columns])
            ts_df = ts_df[ts_df['trace_duration_s'] > 0] if 'trace_duration_s' in ts_df.columns else ts_df

            if ts_df.empty or 'trace_start' not in ts_df.columns or 'trace_duration_s' not in ts_df.columns:
                st.info("Not enough data to plot latency percentiles over time.")
            else:
                freq_code = freq_map.get(perf_freq, "D")
                grouped = ts_df.set_index('trace_start').resample(freq_code)['trace_duration_s']
                latency_over_time = pd.DataFrame({
                    'p50': grouped.quantile(0.50),
                    'p90': grouped.quantile(0.90),
                    'p95': grouped.quantile(0.95),
                    'count': grouped.size(),
                }).reset_index().rename(columns={'trace_start': 'timestamp'})
                latency_over_time = latency_over_time.dropna(subset=['timestamp'])

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=latency_over_time['timestamp'], y=latency_over_time['p50'],
                    name="p50", line=dict(color="#1f77b4")
                ))
                fig.add_trace(go.Scatter(
                    x=latency_over_time['timestamp'], y=latency_over_time['p90'],
                    name="p90", line=dict(color="#ff7f0e")
                ))
                fig.add_trace(go.Scatter(
                    x=latency_over_time['timestamp'], y=latency_over_time['p95'],
                    name="p95", line=dict(color="#d62728")
                ))
                fig.update_layout(
                    height=420,
                    xaxis_title="Time",
                    yaxis_title="Latency (s)",
                    title="Latency Percentiles Over Time",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig, use_container_width=True)

                st.caption("Trace counts per bucket help interpret percentiles (low volume buckets can be noisy).")
                fig_count = px.bar(
                    latency_over_time,
                    x="timestamp",
                    y="count",
                    title="Trace Volume Over Time",
                    labels={"count": "Traces", "timestamp": "Time"},
                )
                st.plotly_chart(fig_count, use_container_width=True)

        st.divider()
        st.subheader("Tail Latency Volume (Thresholds)")
        st.caption("Shows how often users experience very slow responses.")

        thresholds = st.multiselect(
            "Latency thresholds (seconds)",
            options=[5, 10, 20, 30, 60, 120],
            default=[10, 30, 60],
            key="perf_tail_thresholds",
        )
        if ts_df is None or ts_df.empty or 'trace_start' not in ts_df.columns or 'trace_duration_s' not in ts_df.columns:
            st.info("Not enough data to compute tail thresholds.")
        else:
            if not thresholds:
                st.info("Select at least one threshold.")
            else:
                freq_code = freq_map.get(perf_freq, "D")
                tail = ts_df[['trace_start', 'trace_duration_s']].copy()
                tail = tail.set_index('trace_start')
                out = pd.DataFrame(index=tail.resample(freq_code).size().index)
                out.index.name = 'timestamp'
                for t in thresholds:
                    out[f'>{t}s'] = tail['trace_duration_s'].resample(freq_code).apply(lambda s, _t=t: int((s > _t).sum()))
                out = out.reset_index()
                long_df = out.melt(id_vars=['timestamp'], var_name='threshold', value_name='slow_traces')
                fig = px.line(
                    long_df,
                    x='timestamp',
                    y='slow_traces',
                    color='threshold',
                    title="Slow Trace Counts Over Time",
                    labels={'slow_traces': 'Slow traces', 'timestamp': 'Time'},
                )
                st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Latency by Trace Type")
        st.caption("Useful for spotting which workflow is slowest.")

        by_type = user_facing_traces.copy() if not user_facing_traces.empty else analyzer.traces_df.copy()
        if by_type is None or by_type.empty or 'trace_type' not in by_type.columns or 'trace_duration_s' not in by_type.columns:
            st.info("Not enough data to plot latency by trace type.")
        else:
            by_type['trace_duration_s'] = pd.to_numeric(by_type['trace_duration_s'], errors='coerce')
            by_type = by_type.dropna(subset=['trace_duration_s'])
            by_type = by_type[by_type['trace_duration_s'] > 0]
            fig = px.box(
                by_type,
                x='trace_type',
                y='trace_duration_s',
                points="outliers",
                title="Latency Distribution by Trace Type",
                labels={'trace_duration_s': 'Latency (s)', 'trace_type': 'Trace Type'},
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Slowest Users (by p95)")
        st.caption("Helps identify user segments that consistently experience slowness.")

        by_user = user_facing_traces.copy() if not user_facing_traces.empty else analyzer.traces_df.copy()
        if by_user is None or by_user.empty or 'user_email' not in by_user.columns or 'trace_duration_s' not in by_user.columns:
            st.info("Not enough data to compute slowest users.")
        else:
            by_user['trace_duration_s'] = pd.to_numeric(by_user['trace_duration_s'], errors='coerce')
            by_user = by_user.dropna(subset=['trace_duration_s'])
            by_user = by_user[by_user['trace_duration_s'] > 0]

            min_traces_per_user = st.slider(
                "Minimum traces per user",
                min_value=1,
                max_value=50,
                value=5,
                step=1,
                key="perf_min_traces_user",
            )
            user_stats = (
                by_user.groupby('user_email', as_index=False)
                .agg(
                    traces=('trace_id', 'count') if 'trace_id' in by_user.columns else ('trace_duration_s', 'count'),
                    avg_latency_s=('trace_duration_s', 'mean'),
                    p95_latency_s=('trace_duration_s', lambda x: x.quantile(0.95)),
                )
            )
            user_stats = user_stats[user_stats['traces'] >= min_traces_per_user]
            user_stats = user_stats.sort_values('p95_latency_s', ascending=False).head(25)
            st.dataframe(user_stats, use_container_width=True, hide_index=True)

            fig = px.bar(
                user_stats.sort_values('p95_latency_s', ascending=True),
                x='p95_latency_s',
                y='user_email',
                orientation='h',
                title="Top 25 Slowest Users (p95 latency)",
                labels={'p95_latency_s': 'p95 latency (s)', 'user_email': 'User'},
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("Top Slow Traces (Downloadable)")
        st.caption("This is the best dataset to hand to engineering for concrete latency debugging.")

        slow = user_facing_traces.copy() if not user_facing_traces.empty else analyzer.traces_df.copy()
        if slow is None or slow.empty or 'trace_duration_s' not in slow.columns:
            st.info("No trace duration data available.")
        else:
            slow['trace_duration_s'] = pd.to_numeric(slow['trace_duration_s'], errors='coerce')
            slow = slow.dropna(subset=['trace_duration_s'])
            slow = slow[slow['trace_duration_s'] > 0]

            include_errors = st.checkbox(
                "Include ERROR traces",
                value=False,
                key="perf_include_error_traces",
            )
            if not include_errors and 'status' in slow.columns:
                slow = slow[slow['status'] != 'ERROR']

            trace_types = sorted(slow['trace_type'].dropna().unique().tolist()) if 'trace_type' in slow.columns else []
            selected_types = st.multiselect(
                "Trace types",
                options=trace_types,
                default=trace_types,
                key="perf_trace_types",
            )
            if selected_types and 'trace_type' in slow.columns:
                slow = slow[slow['trace_type'].isin(selected_types)]

            top_n = st.slider(
                "How many slow traces to show",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                key="perf_top_n_traces",
            )
            slow = slow.sort_values('trace_duration_s', ascending=False).head(top_n)

            cols = [c for c in [
                'trace_start', 'trace_id', 'user_email', 'user_name', 'trace_type',
                'trace_duration_s', 'total_tokens', 'status', 'query', 'category', 'location_preference', 'zip_code'
            ] if c in slow.columns]
            slow_view = slow[cols].copy()
            st.dataframe(slow_view, use_container_width=True, hide_index=True)

            st.download_button(
                "📥 Download slow traces (CSV)",
                slow_view.to_csv(index=False).encode('utf-8'),
                file_name="phoenix_slowest_traces.csv",
                mime="text/csv",
                key="download-slowest-traces",
            )

        st.divider()
        st.subheader("Per-Trace Bottleneck Breakdown (Selected Trace)")
        st.caption("Shows which span(s) dominate end-to-end latency for a single slow trace.")

        if slow is None or slow.empty or 'trace_id' not in slow.columns:
            st.info("Select a time range with trace IDs available.")
        else:
            trace_id_options = slow['trace_id'].dropna().astype(str).tolist()
            selected_trace_id = st.selectbox(
                "Select a trace_id to inspect",
                options=trace_id_options,
                index=0 if trace_id_options else None,
                key="perf_selected_trace_id",
            )

            if not selected_trace_id:
                st.info("No trace selected.")
            else:
                spans_df = analyzer.df.copy() if hasattr(analyzer, "df") else pd.DataFrame()
                if spans_df is None or spans_df.empty or 'trace_id' not in spans_df.columns:
                    st.info("No span-level data available to compute per-trace breakdown.")
                else:
                    spans = spans_df[spans_df['trace_id'].astype(str) == str(selected_trace_id)].copy()
                    if spans.empty:
                        st.info("No spans found for selected trace.")
                    else:
                        spans['start_time'] = pd.to_datetime(spans.get('start_time'), errors='coerce', utc=True)
                        spans['end_time'] = pd.to_datetime(spans.get('end_time'), errors='coerce', utc=True)
                        spans['latency_s'] = pd.to_numeric(spans.get('latency_s'), errors='coerce')
                        spans = spans.dropna(subset=['latency_s'])
                        spans = spans[spans['latency_s'] > 0]
                        spans = spans.sort_values('start_time')

                        trace_total = float(
                            pd.to_numeric(
                                analyzer.traces_df.loc[
                                    analyzer.traces_df['trace_id'].astype(str) == str(selected_trace_id),
                                    'trace_duration_s'
                                ].iloc[0],
                                errors='coerce'
                            )
                        ) if analyzer.traces_df is not None and not analyzer.traces_df.empty and 'trace_duration_s' in analyzer.traces_df.columns else None

                        view = spans[['name', 'latency_s', 'start_time', 'end_time']].copy() if 'name' in spans.columns else spans[['latency_s', 'start_time', 'end_time']].copy()
                        if trace_total and trace_total > 0:
                            view['pct_of_trace'] = (view['latency_s'] / trace_total * 100).round(1)

                        # Waterfall-ish bar: span durations in execution order
                        fig = px.bar(
                            view,
                            x='latency_s',
                            y=view.index.astype(str),
                            orientation='h',
                            title=f"Span durations for trace {selected_trace_id}",
                            labels={'latency_s': 'Latency (s)', 'y': 'Span (execution order)'},
                            hover_data=[c for c in ['name', 'pct_of_trace', 'start_time', 'end_time'] if c in view.columns],
                        )
                        fig.update_layout(height=520, yaxis=dict(showticklabels=False))
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(view.reset_index(drop=True), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Where Time Goes (Aggregate Span Contribution)")
        st.caption("Aggregates span latency across user-facing traces to highlight systemic bottlenecks.")

        spans_df = analyzer.df.copy() if hasattr(analyzer, "df") else pd.DataFrame()
        if spans_df is None or spans_df.empty or 'latency_s' not in spans_df.columns:
            st.info("No span-level latency data available.")
        else:
            spans_df['latency_s'] = pd.to_numeric(spans_df['latency_s'], errors='coerce')
            spans_df = spans_df.dropna(subset=['latency_s'])
            spans_df = spans_df[spans_df['latency_s'] > 0]

            # Restrict to user-facing trace IDs when available
            if user_facing_traces is not None and not user_facing_traces.empty and 'trace_id' in user_facing_traces.columns and 'trace_id' in spans_df.columns:
                uf_ids = set(user_facing_traces['trace_id'].dropna().astype(str))
                spans_df = spans_df[spans_df['trace_id'].astype(str).isin(uf_ids)]

            if spans_df.empty or 'name' not in spans_df.columns:
                st.info("Not enough span data to compute aggregate contribution.")
            else:
                agg = (
                    spans_df.groupby('name', as_index=False)
                    .agg(
                        spans=('span_id', 'count') if 'span_id' in spans_df.columns else ('latency_s', 'count'),
                        avg_latency_s=('latency_s', 'mean'),
                        p95_latency_s=('latency_s', lambda x: x.quantile(0.95)),
                        total_span_time_s=('latency_s', 'sum'),
                    )
                )
                total_time = float(agg['total_span_time_s'].sum()) if not agg.empty else 0
                if total_time > 0:
                    agg['contribution_pct'] = (agg['total_span_time_s'] / total_time * 100).round(2)
                agg = agg.sort_values('total_span_time_s', ascending=False).head(30)
                st.dataframe(agg, use_container_width=True, hide_index=True)

                fig = px.bar(
                    agg.sort_values('total_span_time_s', ascending=True),
                    x='total_span_time_s',
                    y='name',
                    orientation='h',
                    title="Top span groups by total time (sum of span latencies)",
                    labels={'total_span_time_s': 'Total time (s)', 'name': 'Span name'},
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Model comparison
        st.subheader("Model Performance Comparison")
        model_comparison = analyzer.get_model_performance_comparison()
        
        if not model_comparison.empty:
            st.dataframe(
                model_comparison.style.format({
                    'total_requests': '{:,.0f}',
                    'avg_latency': '{:.2f}s',
                    'median_latency': '{:.2f}s',
                    'avg_tokens': '{:.2f}',
                    'total_tokens': '{:,.0f}',
                    'error_rate': '{:.2f}%'
                }),
                use_container_width=True
            )
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(
                    model_comparison,
                    x='model',
                    y='avg_latency',
                    title='Average Latency by Model',
                    labels={'avg_latency': 'Avg Latency (s)'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    model_comparison,
                    x='model',
                    y='error_rate',
                    title='Error Rate by Model',
                    labels={'error_rate': 'Error Rate (%)'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Error analysis
        st.subheader("Error Analysis")
        error_analysis = analyzer.get_error_analysis()
        
        if error_analysis and error_analysis['total_errors'] > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Errors", error_analysis['total_errors'])
                st.metric("Error Rate", f"{error_analysis['error_rate']:.2f}%")
            
            with col2:
                if error_analysis['errors_by_type']:
                    errors_df = pd.DataFrame(
                        list(error_analysis['errors_by_type'].items()),
                        columns=['Error Type', 'Count']
                    )
                    fig = px.pie(
                        errors_df,
                        values='Count',
                        names='Error Type',
                        title='Errors by Type'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No errors detected in the analyzed period!")
    
    # TAB 5: Log Explorer
    with tab5:
        st.header("Log Explorer")
        st.markdown("*Exportable trace list + latency bottleneck breakdown*")

        if analyzer.traces_df.empty:
            st.info("No trace data available to explore.")
        else:
            st.subheader("📄 All Traces (User, Query, Trace Latency)")
            st.caption("This is designed to be your download-ready dataset of what users asked + how long the end-to-end trace took.")

            only_query_traces = st.checkbox(
                "Only include traces with a non-empty query (recommended for a 'questions' dataset)",
                value=True
            )

            traces = analyzer.traces_df.copy()
            # Keep the most useful columns for export / regression testing.
            preferred_cols = [
                'trace_start', 'trace_id', 'user_name', 'user_email',
                'trace_type', 'query', 'category', 'location_preference',
                'zip_code', 'trace_duration_s', 'status', 'total_tokens', 'tokens_estimated'
            ]
            cols = [c for c in preferred_cols if c in traces.columns]
            traces = traces[cols].copy()

            if 'query' in traces.columns:
                traces['query'] = traces['query'].fillna('').astype(str)
                if only_query_traces:
                    traces = traces[traces['query'].str.strip().str.len() > 0]

            if 'trace_start' in traces.columns:
                traces = traces.sort_values('trace_start', ascending=False)

            display = traces.copy()
            if 'trace_start' in display.columns:
                display['trace_start'] = pd.to_datetime(display['trace_start'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
                display = display.rename(columns={'trace_start': 'timestamp'})

            if 'trace_duration_s' in display.columns:
                display['trace_duration_s'] = pd.to_numeric(display['trace_duration_s'], errors='coerce').round(3)
                display = display.rename(columns={'trace_duration_s': 'trace_latency_s'})

            if 'total_tokens' in display.columns:
                display['total_tokens'] = (
                    pd.to_numeric(display['total_tokens'], errors='coerce')
                    .fillna(0)
                    .astype(int)
                )

            rename_map = {
                'user_name': 'user',
                'user_email': 'email',
            }
            display = display.rename(columns=rename_map)

            st.dataframe(display.fillna(''), use_container_width=True, hide_index=True)

            csv_bytes = display.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download trace list (CSV)",
                csv_bytes,
                "phoenix_trace_list.csv",
                "text/csv",
                key="download-trace-list-csv"
            )

            st.divider()
            st.subheader("📈 Trends & Correlation (Latency vs Tokens)")

            # Build a numeric/time series-friendly view (separate from the display table formatting).
            trend_df = traces.copy()
            if 'trace_start' in trend_df.columns:
                trend_df['trace_start'] = pd.to_datetime(trend_df['trace_start'], errors='coerce')
            if 'trace_duration_s' in trend_df.columns:
                trend_df['trace_duration_s'] = pd.to_numeric(trend_df['trace_duration_s'], errors='coerce')
            if 'total_tokens' in trend_df.columns:
                trend_df['total_tokens'] = pd.to_numeric(trend_df['total_tokens'], errors='coerce')

            trend_df = trend_df.dropna(subset=[c for c in ['trace_start', 'trace_duration_s', 'total_tokens'] if c in trend_df.columns])

            if trend_df.empty or 'trace_start' not in trend_df.columns:
                st.info("Not enough data to plot trends.")
            else:
                trend_df = trend_df.sort_values('trace_start')

                col1, col2 = st.columns(2)
                with col1:
                    fig = px.line(
                        trend_df,
                        x='trace_start',
                        y='trace_duration_s',
                        title='Trace Latency Over Time',
                        labels={'trace_start': 'Time', 'trace_duration_s': 'Latency (s)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    if 'total_tokens' in trend_df.columns:
                        fig = px.line(
                            trend_df,
                            x='trace_start',
                            y='total_tokens',
                            title='Tokens Over Time',
                            labels={'trace_start': 'Time', 'total_tokens': 'Tokens'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No token data available for tokens-over-time chart.")

                if 'total_tokens' in trend_df.columns:
                    st.subheader("🔎 Latency vs Tokens (Correlation)")
                    corr = trend_df['trace_duration_s'].corr(trend_df['total_tokens'])
                    st.metric("Pearson correlation (latency vs tokens)", f"{corr:.3f}" if pd.notna(corr) else "N/A")

                    fig = px.scatter(
                        trend_df,
                        x='total_tokens',
                        y='trace_duration_s',
                        title='Latency vs Tokens',
                        labels={'total_tokens': 'Tokens', 'trace_duration_s': 'Latency (s)'},
                        hover_data=[c for c in ['user_email', 'user_name', 'trace_type', 'query', 'trace_id'] if c in trend_df.columns]
                    )
                    st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("⏱️ Average Latency by Trace Step (Span Name)")
            st.caption("Aggregated across the currently listed traces; use this to spot the biggest latency bottlenecks.")

            if analyzer.df.empty or 'name' not in analyzer.df.columns:
                st.info("Span-level data is not available for step breakdown.")
            else:
                spans_df = analyzer.df.copy()
                if 'trace_id' in spans_df.columns and 'trace_id' in traces.columns:
                    spans_df = spans_df[spans_df['trace_id'].isin(traces['trace_id'].dropna().unique())]

                if 'latency_s' in spans_df.columns:
                    spans_df['latency_s'] = pd.to_numeric(spans_df['latency_s'], errors='coerce')

                spans_df = spans_df.dropna(subset=['name', 'latency_s'])

                if spans_df.empty:
                    st.info("No spans with latency were found for the selected traces.")
                else:
                    step_df = spans_df.groupby('name').agg(
                        avg_latency_s=('latency_s', 'mean'),
                        p95_latency_s=('latency_s', lambda x: x.quantile(0.95)),
                        count_spans=('latency_s', 'count'),
                        count_traces=('trace_id', pd.Series.nunique) if 'trace_id' in spans_df.columns else ('latency_s', 'count'),
                    ).reset_index().rename(columns={'name': 'step'})

                    step_df = step_df.sort_values('avg_latency_s', ascending=False)
                    step_display = step_df.copy()
                    for c in ['avg_latency_s', 'p95_latency_s']:
                        if c in step_display.columns:
                            step_display[c] = pd.to_numeric(step_display[c], errors='coerce').round(3)

                    st.dataframe(step_display, use_container_width=True, hide_index=True)

                    step_csv = step_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "📥 Download step latency breakdown (CSV)",
                        step_csv,
                        "phoenix_span_step_latency.csv",
                        "text/csv",
                        key="download-step-latency-csv"
                    )

    # TAB 6: Advanced Analytics
    with tab6:
        st.header("🧠 Advanced Analytics")
        st.markdown("*Deep insights into query patterns, resource effectiveness, and user behavior*")
        
        # Feature #1: Query Pattern Analysis
        st.divider()
        st.subheader("🔍 Query Pattern Analysis & Search Intelligence")
        
        with st.spinner("Analyzing query patterns..."):
            query_analysis = analyzer.analyze_query_patterns()
        
        if query_analysis:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Unique Queries", query_analysis.get('total_unique_queries', 0))
            with col2:
                st.metric("Avg Query Length", f"{query_analysis.get('avg_query_length', 0):.0f} chars")
            with col3:
                st.metric("Refinement Rate", f"{query_analysis.get('refinement_rate', 0):.1f}%")
            with col4:
                st.metric("No Action Rate", f"{query_analysis.get('no_action_rate', 0):.1f}%")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🔥 Most Common Query Terms**")
                top_terms = query_analysis.get('top_terms', {})
                if top_terms:
                    term_df = pd.DataFrame([
                        {'Term': term, 'Count': count} 
                        for term, count in list(top_terms.items())[:15]
                    ])
                    st.dataframe(term_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**🔄 Query Refinements** (users re-querying within 15 min)")
                refinements = query_analysis.get('refinements', [])
                if refinements:
                    for ref in refinements[:5]:
                        with st.expander(f"{ref.get('user', 'Unknown')} - {ref.get('time_gap_minutes', 0)} min gap"):
                            st.text(f"Query 1: {ref.get('query1', '')}")
                            st.text(f"Query 2: {ref.get('query2', '')}")
                            st.text(f"Category: {ref.get('category', 'N/A')}")
                else:
                    st.info("No query refinements detected")
            
            st.markdown("**⚠️ Queries Without Follow-up Actions** (Potential Unmet Needs)")
            no_action = query_analysis.get('no_action_examples', [])
            if no_action:
                no_action_df = pd.DataFrame(no_action)
                st.dataframe(no_action_df, use_container_width=True, hide_index=True)
            else:
                st.success("All queries have follow-up actions!")
        else:
            st.info("No query data available for analysis")
        
        # Feature #2: Resource Effectiveness
        st.divider()
        st.subheader("⚡ Resource Effectiveness Scoring")
        
        with st.spinner("Analyzing resource effectiveness..."):
            resource_analysis = analyzer.analyze_resource_effectiveness()
        
        if resource_analysis and 'message' not in resource_analysis:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Referrals", resource_analysis.get('total_referrals', 0))
            with col2:
                st.metric("Action Plans Created", resource_analysis.get('total_action_plans', 0))
            with col3:
                st.metric("Conversion Rate", f"{resource_analysis.get('overall_conversion_rate', 0):.1f}%")
            with col4:
                users_both = resource_analysis.get('users_both', 0)
                users_searched = resource_analysis.get('users_searched', 1)
                st.metric("User Conversion", f"{users_both}/{users_searched}")
            
            st.markdown("**📊 Category Effectiveness** (Referral → Action Plan Conversion)")
            effectiveness = resource_analysis.get('category_effectiveness', [])
            if effectiveness:
                eff_df = pd.DataFrame(effectiveness)
                
                # Create bar chart
                import altair as alt
                chart = alt.Chart(eff_df).mark_bar().encode(
                    x=alt.X('conversion_rate:Q', title='Conversion Rate (%)'),
                    y=alt.Y('category:N', sort='-x', title='Category'),
                    color=alt.Color('conversion_rate:Q', scale=alt.Scale(scheme='blues')),
                    tooltip=['category', 'referrals', 'action_plans', 'conversion_rate']
                ).properties(height=400)
                
                st.altair_chart(chart, use_container_width=True)
                
                st.dataframe(eff_df, use_container_width=True, hide_index=True)
        else:
            st.info(resource_analysis.get('message', 'No resource effectiveness data available'))
        
        # Feature #3: User Journey & Workflow Analytics
        st.divider()
        st.subheader("🛣️ User Journey & Workflow Analytics")
        
        with st.spinner("Analyzing user journeys..."):
            journey_analysis = analyzer.analyze_user_journeys()
        
        if journey_analysis:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sessions", journey_analysis.get('total_sessions', 0))
            with col2:
                st.metric("Avg Session Duration", f"{journey_analysis.get('avg_session_duration', 0):.1f} min")
            with col3:
                st.metric("Multi-Category Rate", f"{journey_analysis.get('multi_category_rate', 0):.1f}%")
            with col4:
                st.metric("Drop-off Rate", f"{journey_analysis.get('drop_off_rate', 0):.1f}%")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**⏱️ Time to Action** (First referral → First action plan)")
                st.metric("Average", f"{journey_analysis.get('avg_time_to_action', 0):.1f} minutes")
                st.metric("Median", f"{journey_analysis.get('median_time_to_action', 0):.1f} minutes")
                
                time_examples = journey_analysis.get('time_to_action_examples', [])
                if time_examples:
                    st.markdown("**Fastest Users:**")
                    for ex in time_examples:
                        st.text(f"{ex.get('user', 'Unknown')}: {ex.get('time_minutes', 0)} min")
            
            with col2:
                st.markdown("**🚪 Drop-off Analysis**")
                users_dropped = journey_analysis.get('users_dropped', 0)
                st.metric("Users Who Searched But Never Acted", users_dropped)
                
                dropped_cats = journey_analysis.get('dropped_user_categories', {})
                if dropped_cats:
                    st.markdown("**Categories where users dropped off:**")
                    for cat, count in list(dropped_cats.items())[:5]:
                        st.text(f"{cat}: {count} users")
            
            st.markdown("**📝 Sample User Sessions**")
            session_examples = journey_analysis.get('session_examples', [])
            if session_examples:
                for sess in session_examples[:3]:
                    with st.expander(f"{sess.get('user', 'Unknown')} - {sess.get('duration_minutes', 0):.1f} min session"):
                        st.text(f"Traces: {sess.get('trace_count', 0)}")
                        st.text(f"Types: {', '.join(sess.get('types', []))}")
                        st.text(f"Categories: {', '.join(sess.get('categories', []))}")
        else:
            st.info("No user journey data available for analysis")
        
        # Feature #4: Performance & Quality Metrics
        st.divider()
        st.subheader("🎯 Performance & Quality Metrics")
        
        with st.spinner("Analyzing performance..."):
            perf_analysis = analyzer.analyze_performance_quality()
        
        if perf_analysis:
            # Key performance metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Overall Error Rate", f"{perf_analysis.get('overall_error_rate', 0):.1f}%")
            with col2:
                benchmarks = perf_analysis.get('benchmarks', {})
                st.metric("Median Response Time", f"{benchmarks.get('p50', 0):.2f}s")
            with col3:
                st.metric("P95 Response Time", f"{benchmarks.get('p95', 0):.2f}s")
            with col4:
                llm_perf = perf_analysis.get('llm_performance', {})
                st.metric("Total LLM Calls", llm_perf.get('total_llm_calls', 0))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**⏱️ Response Time Benchmarks**")
                benchmarks = perf_analysis.get('benchmarks', {})
                if benchmarks:
                    bench_df = pd.DataFrame([
                        {'Percentile': 'P50 (Median)', 'Time (s)': f"{benchmarks.get('p50', 0):.2f}"},
                        {'Percentile': 'P75', 'Time (s)': f"{benchmarks.get('p75', 0):.2f}"},
                        {'Percentile': 'P90', 'Time (s)': f"{benchmarks.get('p90', 0):.2f}"},
                        {'Percentile': 'P95', 'Time (s)': f"{benchmarks.get('p95', 0):.2f}"},
                        {'Percentile': 'P99', 'Time (s)': f"{benchmarks.get('p99', 0):.2f}"}
                    ])
                    st.dataframe(bench_df, use_container_width=True, hide_index=True)
                
                st.markdown("**🔥 LLM Performance**")
                llm_perf = perf_analysis.get('llm_performance', {})
                if llm_perf:
                    st.text(f"Avg LLM Latency: {llm_perf.get('avg_llm_latency_s', 0):.2f}s")
                    st.text(f"Median LLM Latency: {llm_perf.get('median_llm_latency_s', 0):.2f}s")
                    st.text(f"P95 LLM Latency: {llm_perf.get('p95_llm_latency_s', 0):.2f}s")
            
            with col2:
                st.markdown("**📊 Token Usage**")
                token_usage = perf_analysis.get('token_usage', {})
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Total Tokens", f"{token_usage.get('total_tokens', 0):,}")
                with col_b:
                    st.metric("Avg per Trace", f"{token_usage.get('avg_tokens_per_trace', 0):,.0f}")
                
                st.markdown("**🚨 Error Rates by Category**")
                error_by_cat = perf_analysis.get('error_rate_by_category', {})
                if error_by_cat:
                    error_df = pd.DataFrame([
                        {'Category': cat, 'Total': data['total'], 'Errors': data['errors'], 'Error Rate': f"{data['error_rate']:.1f}%"}
                        for cat, data in error_by_cat.items() if cat and data['total'] > 0
                    ])
                    if not error_df.empty:
                        st.dataframe(error_df.head(10), use_container_width=True, hide_index=True)
            
            # Slow traces
            slow_traces = perf_analysis.get('slow_traces', [])
            if slow_traces:
                st.markdown(f"**🐢 Slowest Traces** (>{perf_analysis.get('slow_threshold_s', 10):.1f}s)")
                slow_df = pd.DataFrame(slow_traces)
                st.dataframe(slow_df, use_container_width=True, hide_index=True)
        else:
            st.info("No performance data available")
        
        # Feature #5: Geographic Service Gap Analysis
        st.divider()
        st.subheader("🗺️ Geographic Service Gap Analysis")
        
        with st.spinner("Analyzing geographic coverage..."):
            geo_analysis = analyzer.analyze_geographic_gaps()
        
        if geo_analysis:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Zip Mentions", geo_analysis.get('total_zip_mentions', 0))
            with col2:
                st.metric("Unique Zip Codes", geo_analysis.get('unique_zips', 0))
            with col3:
                st.metric("In-Region Zips", geo_analysis.get('in_region_zips', 0))
            with col4:
                st.metric("Out-of-Region", geo_analysis.get('out_of_region_zips', 0))
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🏠 Central Texas Coverage**")
                coverage = geo_analysis.get('coverage_summary', {})
                if coverage:
                    coverage_df = pd.DataFrame([
                        {'Area': 'Austin Metro', 'Zip Codes Served': coverage.get('austin_metro', 0)},
                        {'Area': 'Round Rock', 'Zip Codes Served': coverage.get('round_rock', 0)},
                        {'Area': 'Georgetown', 'Zip Codes Served': coverage.get('georgetown', 0)},
                        {'Area': 'Pflugerville', 'Zip Codes Served': coverage.get('pflugerville', 0)},
                        {'Area': 'Cedar Park/Leander', 'Zip Codes Served': coverage.get('cedar_park_leander', 0)},
                        {'Area': 'South Austin (Buda/Kyle)', 'Zip Codes Served': coverage.get('south_austin', 0)}
                    ])
                    st.dataframe(coverage_df, use_container_width=True, hide_index=True)
                
                st.markdown("**📍 In-Region Details**")
                in_region = geo_analysis.get('in_region_details', {})
                if in_region:
                    region_df = pd.DataFrame([
                        {'Zip': z, 'City': data['city'], 'Requests': data['count'], 'Categories': ', '.join(data['categories'][:2])}
                        for z, data in list(in_region.items())[:10]
                    ])
                    st.dataframe(region_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("**🌎 Out-of-Region Requests**")
                out_region = geo_analysis.get('out_of_region_details', {})
                if out_region:
                    out_df = pd.DataFrame([
                        {'Zip': z, 'City': data['city'], 'Requests': data['count'], 'Categories': ', '.join(data['categories'][:2])}
                        for z, data in list(out_region.items())[:10]
                    ])
                    st.dataframe(out_df, use_container_width=True, hide_index=True)
                else:
                    st.success("All requests are within Central Texas region!")
                
                st.markdown("**⚠️ Locations Without Zip Codes** (Potential Service Gaps)")
                no_zip = geo_analysis.get('location_without_zip', {})
                if no_zip:
                    for loc, count in list(no_zip.items())[:5]:
                        st.text(f"{loc}: {count} mentions")
                else:
                    st.success("All location requests have associated zip codes")
            
            # Category by region
            cat_by_region = geo_analysis.get('category_by_region', {})
            if cat_by_region:
                st.markdown("**📊 Category Demand by Region**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("*Central Texas*")
                    ctx = cat_by_region.get('central_texas', {})
                    if ctx:
                        for cat, count in sorted(ctx.items(), key=lambda x: x[1], reverse=True)[:5]:
                            st.text(f"{cat}: {count}")
                with col2:
                    st.markdown("*Out-of-Region*")
                    oor = cat_by_region.get('out_of_region', {})
                    if oor:
                        for cat, count in sorted(oor.items(), key=lambda x: x[1], reverse=True)[:5]:
                            st.text(f"{cat}: {count}")
        else:
            st.info("No geographic data available")
        
        # Feature #6: Comparative Period Analysis
        st.divider()
        st.subheader("📅 Comparative Period Analysis")
        
        st.markdown("*Compare metrics between two time periods*")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Period 1 (Previous)**")
            _p1_days = st.slider("Days ago (start)", 7, 30, 14, key="p1_days")
        with col2:
            st.markdown("**Period 2 (Recent)**")
            p2_days = st.slider("Days to compare", 3, 14, 7, key="p2_days")
        
        # Calculate period dates
        now = datetime.now(timezone.utc)
        p2_end = now
        p2_start = now - pd.Timedelta(days=p2_days)
        p1_end = p2_start
        p1_start = p1_end - pd.Timedelta(days=p2_days)
        
        with st.spinner("Comparing periods..."):
            compare_analysis = analyzer.analyze_comparative_periods(p1_start, p1_end, p2_start, p2_end)
        
        if compare_analysis:
            # Period summaries
            p1 = compare_analysis.get('period1', {})
            p2 = compare_analysis.get('period2', {})
            changes = compare_analysis.get('changes', {})
            
            st.markdown(f"**Comparing:** {p1.get('start', '')[:10]} to {p1.get('end', '')[:10]} vs {p2.get('start', '')[:10]} to {p2.get('end', '')[:10]}")
            
            # Growth trajectory indicator
            trajectory = compare_analysis.get('growth_trajectory', 'stable')
            trajectory_icon = '📈' if trajectory == 'growing' else ('📉' if trajectory == 'declining' else '➡️')
            st.markdown(f"**Overall Trajectory:** {trajectory_icon} {trajectory.upper()}")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            _p1_metrics = p1.get('metrics', {})
            p2_metrics = p2.get('metrics', {})
            
            with col1:
                delta = changes.get('traces_change', 0)
                st.metric("Traces", p2_metrics.get('total_traces', 0), 
                         f"{delta:+.1f}%" if delta != 0 else "0%")
            with col2:
                delta = changes.get('users_change', 0)
                st.metric("Users", p2_metrics.get('unique_users', 0),
                         f"{delta:+.1f}%" if delta != 0 else "0%")
            with col3:
                delta = changes.get('referrals_change', 0)
                st.metric("Referrals", p2_metrics.get('referrals', 0),
                         f"{delta:+.1f}%" if delta != 0 else "0%")
            with col4:
                delta = changes.get('action_plans_change', 0)
                st.metric("Action Plans", p2_metrics.get('action_plans', 0),
                         f"{delta:+.1f}%" if delta != 0 else "0%")
            with col5:
                delta = changes.get('duration_change', 0)
                st.metric("Avg Duration", f"{p2_metrics.get('avg_duration_s', 0):.1f}s",
                         f"{delta:+.1f}%" if delta != 0 else "0%")
            
            # Category changes
            cat_changes = compare_analysis.get('category_changes', {})
            if cat_changes:
                st.markdown("**Category Shifts**")
                cat_df = pd.DataFrame([
                    {
                        'Category': cat,
                        'Period 1': data['period1'],
                        'Period 2': data['period2'],
                        'Change': f"{data['change_pct']:+.0f}%"
                    }
                    for cat, data in cat_changes.items() 
                    if cat and (data['period1'] > 0 or data['period2'] > 0)
                ])
                if not cat_df.empty:
                    st.dataframe(cat_df.sort_values('Period 2', ascending=False).head(10), 
                                use_container_width=True, hide_index=True)
            
            # New/dropped categories
            col1, col2 = st.columns(2)
            with col1:
                new_cats = compare_analysis.get('new_categories', [])
                if new_cats:
                    st.markdown("**🆕 New Categories in Period 2:**")
                    for cat in new_cats:
                        st.text(f"• {cat}")
            with col2:
                dropped_cats = compare_analysis.get('dropped_categories', [])
                if dropped_cats:
                    st.markdown("**📉 Categories Not in Period 2:**")
                    for cat in dropped_cats:
                        st.text(f"• {cat}")
        else:
            st.info("Not enough data for period comparison")
        
        # Feature #8: Real-time Alerting
        st.divider()
        st.subheader("🚨 System Health & Alerts")
        
        with st.spinner("Checking system health..."):
            alert_analysis = analyzer.analyze_realtime_alerts()
        
        if alert_analysis:
            status = alert_analysis.get('status', 'healthy')
            
            # Status indicator
            status_colors = {
                'healthy': '🟢',
                'attention': '🟡', 
                'warning': '🟠',
                'critical': '🔴'
            }
            
            st.markdown(f"### System Status: {status_colors.get(status, '⚪')} {status.upper()}")
            
            # Health checks
            health_checks = alert_analysis.get('health_checks', {})
            if health_checks:
                cols = st.columns(5)
                check_icons = {'ok': '✅', 'issue': '⚠️'}
                
                for i, (check, result) in enumerate(health_checks.items()):
                    with cols[i]:
                        st.markdown(f"{check_icons.get(result, '❓')} **{check.replace('_', ' ').title()}**")
            
            # Alert counts
            alert_counts = alert_analysis.get('alert_counts', {})
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Critical Alerts", alert_counts.get('critical', 0))
            with col2:
                st.metric("Warnings", alert_counts.get('warning', 0))
            with col3:
                st.metric("Info Notices", alert_counts.get('info', 0))
            
            # Alert details
            alerts = alert_analysis.get('alerts', [])
            if alerts:
                st.markdown("**📋 Active Alerts**")
                for alert in alerts:
                    severity = alert.get('severity', 'info')
                    icon = {'critical': '🔴', 'warning': '🟠', 'info': '🔵'}[severity]
                    
                    with st.expander(f"{icon} [{severity.upper()}] {alert.get('type', 'Unknown').replace('_', ' ').title()}"):
                        st.markdown(f"**Message:** {alert.get('message', '')}")
                        st.markdown(f"**Value:** {alert.get('value', 'N/A')}")
                        st.markdown(f"**Threshold:** {alert.get('threshold', 'N/A')}")
            else:
                st.success("🎉 No alerts! All systems operating normally.")
        else:
            st.info("Unable to perform health check")
        
        # Feature #9: AI-Powered Query Understanding
        st.divider()
        st.subheader("🤖 AI-Powered Query Understanding")
        st.markdown("*Deep analysis of query patterns, intents, entities, and quality*")
        
        with st.spinner("Analyzing queries with AI..."):
            query_intel = analyzer.analyze_query_intelligence()
        
        if query_intel:
            # Top-level metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Queries Analyzed", query_intel.get('total_queries_analyzed', 0))
            with col2:
                quality_stats = query_intel.get('quality_stats', {})
                st.metric("Avg Quality Score", f"{quality_stats.get('avg', 0):.0f}/100")
            with col3:
                complexity_stats = query_intel.get('complexity_stats', {})
                st.metric("Avg Complexity", f"{complexity_stats.get('avg', 0):.1f}/10")
            with col4:
                st.metric("Need Improvement", f"{quality_stats.get('needs_improvement_pct', 0):.0f}%")
            
            # AI Insights
            insights = query_intel.get('insights', [])
            if insights:
                st.markdown("### 💡 AI-Generated Insights")
                for insight in insights:
                    st.info(insight)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Intent Distribution
                st.markdown("**🎯 Intent Classification**")
                intent_dist = query_intel.get('intent_distribution', {})
                if intent_dist:
                    intent_df = pd.DataFrame([
                        {'Intent': k.replace('_', ' ').title(), 'Count': v}
                        for k, v in sorted(intent_dist.items(), key=lambda x: x[1], reverse=True)
                    ])
                    st.dataframe(intent_df, use_container_width=True, hide_index=True)
                
                # Urgency Distribution
                st.markdown("**⏰ Urgency Levels**")
                urgency_dist = query_intel.get('urgency_distribution', {})
                if urgency_dist:
                    urgency_icons = {'critical': '🔴', 'high': '🟠', 'moderate': '🟡', 'normal': '🟢'}
                    for level in ['critical', 'high', 'moderate', 'normal']:
                        count = urgency_dist.get(level, 0)
                        if count > 0:
                            st.text(f"{urgency_icons.get(level, '⚪')} {level.title()}: {count}")
            
            with col2:
                # Entity Extraction Summary
                st.markdown("**🏷️ Extracted Entities**")
                entity_summary = query_intel.get('entity_summary', {})
                
                with st.expander("👤 Client Demographics"):
                    demos = entity_summary.get('top_demographics', {})
                    if demos:
                        for demo, count in demos.items():
                            st.text(f"{demo.replace('_', ' ').title()}: {count}")
                    else:
                        st.text("No demographics detected")
                
                with st.expander("🔧 Services Requested"):
                    services = entity_summary.get('top_services', {})
                    if services:
                        for service, count in services.items():
                            st.text(f"{service.replace('_', ' ').title()}: {count}")
                    else:
                        st.text("No services detected")
                
                with st.expander("📍 Locations Mentioned"):
                    locations = entity_summary.get('top_locations', {})
                    if locations:
                        for loc, count in locations.items():
                            st.text(f"{loc}: {count}")
                    else:
                        st.text("No locations detected")
            
            # Common Query Patterns
            st.markdown("**📊 Common Query Patterns**")
            patterns = query_intel.get('common_patterns', {})
            if patterns:
                pattern_df = pd.DataFrame([
                    {'Pattern': k, 'Frequency': len(v), 'Example': v[0][:60] + '...' if len(v[0]) > 60 else v[0]}
                    for k, v in list(patterns.items())[:8]
                ])
                st.dataframe(pattern_df, use_container_width=True, hide_index=True)
            
            # Quality Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**✅ High-Quality Query Examples**")
                high_quality = query_intel.get('sample_high_quality', [])
                if high_quality:
                    for q in high_quality[:3]:
                        with st.expander(f"Score: {q['quality_score']}/100 - {q['query'][:40]}..."):
                            st.text(f"Query: {q['query']}")
                            st.text(f"Services: {', '.join(q['services']) if q['services'] else 'None'}")
                            st.text(f"Demographics: {', '.join(q['demographics']) if q['demographics'] else 'None'}")
                            st.text(f"Locations: {', '.join(q['locations']) if q['locations'] else 'None'}")
                            st.text(f"Complexity: {q['complexity']}/10")
                else:
                    st.info("No high-quality queries found")
            
            with col2:
                st.markdown("**⚠️ Queries Needing Improvement**")
                needs_improvement = query_intel.get('sample_needs_improvement', [])
                if needs_improvement:
                    for q in needs_improvement[:3]:
                        with st.expander(f"Score: {q['quality_score']}/100 - {q['query'][:40]}..."):
                            st.text(f"Query: {q['query']}")
                            if q['suggestions']:
                                st.markdown("**Suggestions:**")
                                for sug in q['suggestions']:
                                    st.text(f"• {sug}")
                else:
                    st.success("All queries meet quality standards!")
            
            # Detailed Query Browser
            st.markdown("**🔍 Query Detail Browser**")
            all_analyzed = query_intel.get('all_analyzed', [])
            if all_analyzed:
                # Filter options
                col1, col2, col3 = st.columns(3)
                with col1:
                    intent_filter = st.selectbox(
                        "Filter by Intent",
                        ["All"] + list(set(q['intent'] for q in all_analyzed)),
                        key="intent_filter"
                    )
                with col2:
                    urgency_filter = st.selectbox(
                        "Filter by Urgency",
                        ["All", "critical", "high", "moderate", "normal"],
                        key="urgency_filter"
                    )
                with col3:
                    quality_filter = st.selectbox(
                        "Filter by Quality",
                        ["All", "High (70+)", "Medium (50-69)", "Low (<50)"],
                        key="quality_filter"
                    )
                
                # Apply filters
                filtered = all_analyzed
                if intent_filter != "All":
                    filtered = [q for q in filtered if q['intent'] == intent_filter]
                if urgency_filter != "All":
                    filtered = [q for q in filtered if q['urgency'] == urgency_filter]
                if quality_filter == "High (70+)":
                    filtered = [q for q in filtered if q['quality_score'] >= 70]
                elif quality_filter == "Medium (50-69)":
                    filtered = [q for q in filtered if 50 <= q['quality_score'] < 70]
                elif quality_filter == "Low (<50)":
                    filtered = [q for q in filtered if q['quality_score'] < 50]
                
                st.text(f"Showing {len(filtered)} queries")
                
                # Display filtered queries
                if filtered:
                    query_display = pd.DataFrame([
                        {
                            'Query': q['query'][:50] + '...' if len(q['query']) > 50 else q['query'],
                            'Intent': q['intent'].replace('_', ' ').title(),
                            'Urgency': q['urgency'].title(),
                            'Quality': q['quality_score'],
                            'Complexity': q['complexity'],
                            'Services': ', '.join(q['services'][:2]) if q['services'] else '-',
                            'Demographics': ', '.join(q['demographics'][:2]) if q['demographics'] else '-'
                        }
                        for q in filtered[:20]
                    ])
                    st.dataframe(query_display, use_container_width=True, hide_index=True)
        else:
            st.info("No query data available for AI analysis")
        
        # Output Quality Analysis
        st.divider()
        st.subheader("📊 Output Quality Analysis")
        st.markdown("*Analyzing the quality, relevance, and completeness of AI responses*")
        
        with st.spinner("Analyzing output quality..."):
            output_quality = analyzer.analyze_output_quality()
        
        if output_quality:
            # Top-level metrics
            quality_stats = output_quality.get('quality_stats', {})
            alignment_stats = output_quality.get('alignment_stats', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Responses Analyzed", output_quality.get('total_analyzed', 0))
            with col2:
                avg_score = quality_stats.get('avg_score', 0)
                st.metric("Avg Quality Score", f"{avg_score:.0f}/100",
                         delta="Good" if avg_score >= 70 else ("Fair" if avg_score >= 50 else "Needs Work"))
            with col3:
                st.metric("Location Match Rate", f"{alignment_stats.get('location_match_rate', 0):.0f}%")
            with col4:
                st.metric("Category Match Rate", f"{alignment_stats.get('category_match_rate', 0):.0f}%")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Has Resources", f"{alignment_stats.get('has_resources_rate', 0):.0f}%")
            with col2:
                st.metric("Has Contact Info", f"{alignment_stats.get('actionable_rate', 0):.0f}%")
            with col3:
                st.metric("High Quality", quality_stats.get('high_quality_count', 0))
            with col4:
                st.metric("Low Quality", quality_stats.get('low_quality_count', 0))
            
            # Insights
            insights = output_quality.get('insights', [])
            if insights:
                st.markdown("### 💡 Output Quality Insights")
                for insight in insights:
                    if insight.startswith("⚠️") or insight.startswith("📍") or insight.startswith("🏷️") or insight.startswith("📋") or insight.startswith("🔄"):
                        st.warning(insight)
                    elif insight.startswith("✅"):
                        st.success(insight)
                    else:
                        st.info(insight)
            
            # Issue breakdown
            st.markdown("### 🚨 Issue Detection")
            issue_counts = output_quality.get('issue_counts', {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("No Resources", issue_counts.get('no_resources', 0),
                         delta="issue" if issue_counts.get('no_resources', 0) > 5 else None,
                         delta_color="inverse")
                st.metric("Generic Responses", issue_counts.get('generic_response', 0),
                         delta="issue" if issue_counts.get('generic_response', 0) > 3 else None,
                         delta_color="inverse")
            with col2:
                st.metric("Location Mismatch", issue_counts.get('location_mismatch', 0),
                         delta="issue" if issue_counts.get('location_mismatch', 0) > 5 else None,
                         delta_color="inverse")
                st.metric("Category Mismatch", issue_counts.get('category_mismatch', 0),
                         delta="issue" if issue_counts.get('category_mismatch', 0) > 5 else None,
                         delta_color="inverse")
            with col3:
                st.metric("Low Quality", issue_counts.get('low_quality', 0),
                         delta="issue" if issue_counts.get('low_quality', 0) > 5 else None,
                         delta_color="inverse")
                st.metric("Too Short", issue_counts.get('too_short', 0),
                         delta="issue" if issue_counts.get('too_short', 0) > 3 else None,
                         delta_color="inverse")
            
            # Issue examples
            issues = output_quality.get('issues', {})
            if any(issues.values()):
                st.markdown("### 🔍 Issue Examples")
                
                issue_tabs = st.tabs(["Location Mismatch", "Category Mismatch", "No Resources", "Generic", "Low Quality"])
                
                with issue_tabs[0]:
                    loc_issues = issues.get('location_mismatch', [])
                    if loc_issues:
                        for item in loc_issues[:3]:
                            with st.expander(f"Score: {item['quality_score']} - {item['query'][:50]}..."):
                                st.text(f"User: {item['user']}")
                                st.text(f"Query: {item['query']}")
                                st.text(f"Factors: {', '.join(item.get('factors', []))}")
                    else:
                        st.success("No location mismatch issues!")
                
                with issue_tabs[1]:
                    cat_issues = issues.get('category_mismatch', [])
                    if cat_issues:
                        for item in cat_issues[:3]:
                            with st.expander(f"Score: {item['quality_score']} - {item['query'][:50]}..."):
                                st.text(f"User: {item['user']}")
                                st.text(f"Query: {item['query']}")
                                st.text(f"Factors: {', '.join(item.get('factors', []))}")
                    else:
                        st.success("No category mismatch issues!")
                
                with issue_tabs[2]:
                    no_res = issues.get('no_resources', [])
                    if no_res:
                        for item in no_res[:3]:
                            with st.expander(f"Score: {item['quality_score']} - {item['query'][:50]}..."):
                                st.text(f"User: {item['user']}")
                                st.text(f"Query: {item['query']}")
                    else:
                        st.success("All responses include resources!")
                
                with issue_tabs[3]:
                    generic = issues.get('generic_response', [])
                    if generic:
                        for item in generic[:3]:
                            with st.expander(f"Score: {item['quality_score']} - {item['query'][:50]}..."):
                                st.text(f"User: {item['user']}")
                                st.text(f"Query: {item['query']}")
                                st.text(f"Factors: {', '.join(item.get('factors', []))}")
                    else:
                        st.success("No generic/template responses detected!")
                
                with issue_tabs[4]:
                    low_qual = issues.get('low_quality', [])
                    if low_qual:
                        for item in low_qual[:3]:
                            with st.expander(f"Score: {item['quality_score']} - {item['query'][:50]}..."):
                                st.text(f"User: {item['user']}")
                                st.text(f"Query: {item['query']}")
                                st.text(f"Factors: {', '.join(item.get('factors', []))}")
                    else:
                        st.success("No low quality responses!")
            
            # Best vs Worst responses
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🏆 Best Quality Responses**")
                best = output_quality.get('best_responses', [])
                if best:
                    for item in best[:5]:
                        with st.expander(f"✅ Score: {item['quality_score']}/100"):
                            st.text(f"Query: {item['query']}")
                            st.text(f"User: {item['user']}")
                            st.text(f"Resources: {item['resource_count']}")
                            st.text(f"Has Contact Info: {'Yes' if item['has_actionable_info'] else 'No'}")
                            st.text(f"Positive Factors: {', '.join([f for f in item.get('factors', []) if not f.startswith('-')])}")
            
            with col2:
                st.markdown("**⚠️ Responses Needing Review**")
                worst = output_quality.get('all_analyses', [])
                if worst:
                    for item in worst[:5]:
                        with st.expander(f"⚠️ Score: {item['quality_score']}/100"):
                            st.text(f"Query: {item['query']}")
                            st.text(f"User: {item['user']}")
                            st.text(f"Issues: {', '.join(item.get('factors', []))}")
        else:
            st.info("No output data available for quality analysis")
        
        # Resource Recommendation Analysis
        st.divider()
        st.subheader("📚 Resource Recommendation Analysis")
        st.markdown("*Tracking which resources are recommended and their effectiveness*")
        
        with st.spinner("Analyzing resource recommendations..."):
            resource_analysis = analyzer.analyze_resource_recommendations()
        
        if resource_analysis:
            # Check for note (limited data)
            if resource_analysis.get('note'):
                st.warning(resource_analysis['note'])
            
            # Top-level metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Recommendations", resource_analysis.get('total_recommendations', 0))
            with col2:
                st.metric("Unique Resources", resource_analysis.get('unique_resources', 0))
            with col3:
                st.metric("Avg per Trace", f"{resource_analysis.get('recommendations_per_trace', 0):.1f}")
            with col4:
                concentration = resource_analysis.get('concentration_ratio', 0)
                st.metric("Top 5 Concentration", f"{concentration:.0f}%",
                         delta="High" if concentration > 50 else ("Balanced" if concentration > 30 else "Diverse"))
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Diversity Score", f"{resource_analysis.get('diversity_score', 0):.0f}/100")
            with col2:
                st.metric("Location Match Rate", f"{resource_analysis.get('location_match_rate', 0):.0f}%")
            with col3:
                st.metric("Traces with Resources", resource_analysis.get('traces_with_resources', 0))
            with col4:
                st.metric("Traces without Resources", resource_analysis.get('traces_without_resources', 0))
            
            # Insights
            insights = resource_analysis.get('insights', [])
            if insights:
                st.markdown("### 💡 Resource Insights")
                for insight in insights:
                    if insight.startswith("⚠️"):
                        st.warning(insight)
                    elif insight.startswith("✅"):
                        st.success(insight)
                    else:
                        st.info(insight)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Top recommended resources
                st.markdown("**🏆 Most Recommended Resources**")
                top_resources = resource_analysis.get('top_resources', [])
                if top_resources:
                    resource_df = pd.DataFrame([
                        {
                            'Resource': r['name'][:40] + '...' if len(r['name']) > 40 else r['name'],
                            'Count': r['count'],
                            '%': f"{r['percentage']:.1f}%"
                        }
                        for r in top_resources[:10]
                    ])
                    st.dataframe(resource_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No resource data available")
                
                # Category distribution
                st.markdown("**📂 Resource Categories**")
                cat_dist = resource_analysis.get('category_distribution', {})
                if cat_dist:
                    cat_df = pd.DataFrame([
                        {'Category': k, 'Count': v}
                        for k, v in list(cat_dist.items())[:10]
                    ])
                    st.dataframe(cat_df, use_container_width=True, hide_index=True)
            
            with col2:
                # Geographic distribution
                st.markdown("**📍 Geographic Distribution**")
                geo_dist = resource_analysis.get('geographic_distribution', {})
                
                if geo_dist:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Central Texas", geo_dist.get('central_texas_count', 0))
                    with col_b:
                        st.metric("Out of Region", geo_dist.get('out_of_region_count', 0))
                    
                    by_city = geo_dist.get('by_city', {})
                    if by_city:
                        st.markdown("**By City:**")
                        city_df = pd.DataFrame([
                            {'City': k, 'Count': v}
                            for k, v in list(by_city.items())[:8]
                        ])
                        st.dataframe(city_df, use_container_width=True, hide_index=True)
                    
                    by_zip = geo_dist.get('by_zip', {})
                    if by_zip:
                        with st.expander("📮 By Zip Code"):
                            zip_df = pd.DataFrame([
                                {'Zip': k, 'Count': v}
                                for k, v in list(by_zip.items())[:10]
                            ])
                            st.dataframe(zip_df, use_container_width=True, hide_index=True)
                    
                    out_of_region = geo_dist.get('out_of_region_zips', [])
                    if out_of_region:
                        st.warning(f"Out-of-region zips: {', '.join(out_of_region)}")
            
            # Resource detail browser
            st.markdown("**🔍 Resource Detail Browser**")
            sample_resources = resource_analysis.get('sample_resources', [])
            if sample_resources:
                res_display = pd.DataFrame([
                    {
                        'Name': r.get('name', 'Unknown')[:30],
                        'Category': r.get('category', '-'),
                        'City': r.get('city', '-'),
                        'Zip': r.get('zip_code', '-'),
                        'Phone': '✓' if r.get('phone') else '-',
                        'Website': '✓' if r.get('website') else '-'
                    }
                    for r in sample_resources[:15]
                ])
                st.dataframe(res_display, use_container_width=True, hide_index=True)
        else:
            st.info("No resource recommendation data available")

    # TAB 7: Evals
    with tab7:
        st.header("✅ Comprehensive AI Output Evaluation")
        st.markdown(
            "*Automated quality checks, hallucination detection, and failure taxonomy for confident leadership reporting.*"
        )

        # Create sub-tabs for different eval sections
        eval_tabs = st.tabs([
            "📊 Executive Summary",
            "🚨 Failure Taxonomy",
            "🔍 Resource Validation",
            "📈 Coverage Analysis",
            "🧪 Test Cases",
            "🔄 Consistency",
            "📋 Detailed Flags",
        ])

        # =====================================================================
        # RESOURCE INVENTORY CONFIGURATION
        # =====================================================================
        with st.sidebar.expander("📦 Resource Inventory (S3)", expanded=False):
            st.markdown("**Connect to your S3 resource inventory for hallucination detection.**")
            s3_bucket = st.text_input(
                "S3 Bucket Name",
                value=os.getenv('RESOURCE_S3_BUCKET', ''),
                help="e.g., goodwill-resources"
            )
            s3_key = st.text_input(
                "S3 Object Key",
                value=os.getenv('RESOURCE_S3_KEY', 'resources.json'),
                help="Path to JSON file in bucket"
            )
            aws_region = st.text_input(
                "AWS Region",
                value=os.getenv('AWS_REGION', 'us-east-1'),
            )
            use_inventory = st.checkbox("Enable inventory validation", value=False)

            # For now, allow CSV upload as alternative
            st.markdown("**Or upload inventory CSV/JSON:**")
            inventory_file = st.file_uploader(
                "Upload resource inventory",
                type=['csv', 'json'],
                key='inventory_upload'
            )

        # Load resource inventory
        resource_inventory = []
        if inventory_file is not None:
            try:
                if inventory_file.name.endswith('.json'):
                    import json as json_lib
                    resource_inventory = json_lib.load(inventory_file)
                    if isinstance(resource_inventory, dict):
                        # Handle nested structures
                        for key in ['resources', 'data', 'items']:
                            if key in resource_inventory:
                                resource_inventory = resource_inventory[key]
                                break
                else:
                    inv_df = pd.read_csv(inventory_file)
                    resource_inventory = inv_df.to_dict('records')
                st.sidebar.success(f"✅ Loaded {len(resource_inventory)} resources from file")
            except Exception as e:
                st.sidebar.error(f"Error loading inventory: {e}")
        elif use_inventory and s3_bucket:
            try:
                import boto3
                s3_client = boto3.client('s3', region_name=aws_region)
                response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
                import json as json_lib
                resource_inventory = json_lib.loads(response['Body'].read().decode('utf-8'))
                if isinstance(resource_inventory, dict):
                    for key in ['resources', 'data', 'items']:
                        if key in resource_inventory:
                            resource_inventory = resource_inventory[key]
                            break
                st.sidebar.success(f"✅ Loaded {len(resource_inventory)} resources from S3")
            except Exception as e:
                st.sidebar.warning(f"Could not load from S3: {e}")

        # Test case upload
        with st.sidebar.expander("🧪 Gold Standard Test Cases", expanded=False):
            st.markdown("Upload test cases (JSON format):")
            st.markdown("""
            ```json
            [
              {
                "query": "food assistance in Austin",
                "expected_resources": ["Central Texas Food Bank"],
                "expected_category": "food",
                "expected_location": "Austin"
              }
            ]
            ```
            """)
            test_case_file = st.file_uploader(
                "Upload test cases",
                type=['json'],
                key='testcase_upload'
            )

        test_cases = []
        if test_case_file is not None:
            try:
                import json as json_lib
                test_cases = json_lib.load(test_case_file)
                st.sidebar.success(f"✅ Loaded {len(test_cases)} test cases")
            except Exception as e:
                st.sidebar.error(f"Error loading test cases: {e}")

        # Run comprehensive evals
        comprehensive_results = analyzer.get_comprehensive_evals(
            resource_inventory=resource_inventory if resource_inventory else None,
            test_cases=test_cases if test_cases else None,
        )

        if comprehensive_results.get('error'):
            st.warning(comprehensive_results['error'])
        else:
            # -----------------------------------------------------------------
            # TAB: EXECUTIVE SUMMARY
            # -----------------------------------------------------------------
            with eval_tabs[0]:
                st.subheader("📊 Executive Summary for Leadership")
                st.markdown("*One-page view of AI output quality health*")

                exec_summary = comprehensive_results.get('executive_summary', {})
                if exec_summary.get('error'):
                    st.warning(exec_summary['error'])
                else:
                    # Health score banner
                    health_score = exec_summary.get('health_score', 0)
                    health_status = exec_summary.get('health_status', 'unknown')
                    status_colors = {
                        'excellent': '🟢',
                        'good': '🟡',
                        'needs_attention': '🟠',
                        'critical': '🔴',
                    }
                    status_emoji = status_colors.get(health_status, '⚪')

                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); 
                                padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 20px;">
                        <h1 style="color: white; margin: 0; font-size: 3rem;">{status_emoji} {health_score}/100</h1>
                        <p style="color: #ccc; margin: 10px 0 0 0; font-size: 1.2rem;">
                            Overall Quality Health Score ({health_status.replace('_', ' ').title()})
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Key metrics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric(
                        "Pass Rate",
                        f"{exec_summary.get('pass_rate', 0):.1f}%",
                        help="Traces with no critical failures"
                    )
                    col2.metric(
                        "Avg Quality Score",
                        f"{exec_summary.get('avg_quality_score', 0):.1f}",
                    )
                    col3.metric(
                        "Inventory Match",
                        f"{exec_summary.get('match_rate', 0):.1f}%",
                        help="Resources found in known inventory (lower = potential hallucinations)"
                    )
                    col4.metric(
                        "Actionable Rate",
                        f"{exec_summary.get('actionable_rate', 0):.1f}%",
                        help="Responses with contact details"
                    )

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Traces Evaluated", f"{exec_summary.get('total_traces_evaluated', 0):,}")
                    col2.metric("Traces with Failures", f"{exec_summary.get('traces_with_any_failure', 0):,}")
                    col3.metric("Failure Rate", f"{exec_summary.get('failure_rate', 0):.1f}%")
                    col4.metric(
                        "Hallucination Rate",
                        f"{exec_summary.get('hallucination_rate', 0):.1f}%",
                        delta=None if exec_summary.get('hallucination_rate', 0) == 0 else "needs inventory",
                    )

                    # Top failure types
                    st.markdown("### 🚨 Top Failure Types")
                    top_failures = exec_summary.get('top_failure_types', [])
                    if top_failures:
                        failure_df = pd.DataFrame([
                            {'Failure Type': f[0].replace('_', ' ').title(), 'Count': f[1]}
                            for f in top_failures
                        ])
                        fig_failures = px.bar(
                            failure_df,
                            x='Failure Type',
                            y='Count',
                            title="Failure counts by type",
                            color='Count',
                            color_continuous_scale='Reds',
                        )
                        st.plotly_chart(fig_failures, use_container_width=True)
                    else:
                        st.success("No failures detected!")

                    # Recommendations
                    st.markdown("### 💡 Recommendations")
                    recommendations = exec_summary.get('recommendations', [])
                    for rec in recommendations:
                        if '🚨' in rec or '⚠️' in rec:
                            st.warning(rec)
                        elif '✅' in rec:
                            st.success(rec)
                        else:
                            st.info(rec)

            # -----------------------------------------------------------------
            # TAB: FAILURE TAXONOMY
            # -----------------------------------------------------------------
            with eval_tabs[1]:
                st.subheader("🚨 Structured Failure Taxonomy")
                st.markdown("*Specific, actionable failure categories for diagnosis*")

                taxonomy = comprehensive_results.get('failure_taxonomy', {})
                failure_counts = taxonomy.get('failure_counts', {})

                # Overview metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Traces with Failures", taxonomy.get('traces_with_failures', 0))
                col2.metric("Traces without Failures", taxonomy.get('traces_without_failures', 0))
                col3.metric("Failure Rate", f"{taxonomy.get('failure_rate', 0):.1f}%")

                # Failure breakdown chart
                if failure_counts:
                    failure_data = pd.DataFrame([
                        {'Failure Type': k.replace('_', ' ').title(), 'Count': v}
                        for k, v in failure_counts.items() if v > 0
                    ]).sort_values('Count', ascending=True)

                    if not failure_data.empty:
                        fig = px.bar(
                            failure_data,
                            y='Failure Type',
                            x='Count',
                            orientation='h',
                            title="Failures by Type",
                            color='Count',
                            color_continuous_scale='Reds',
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

                # Drill-down by failure type
                st.markdown("### 🔍 Drill-down by Failure Type")
                failure_types = [k for k, v in failure_counts.items() if v > 0]
                if failure_types:
                    selected_failure = st.selectbox("Select failure type to inspect:", failure_types)
                    failures_by_type = taxonomy.get('failures_by_type', {})
                    examples = failures_by_type.get(selected_failure, [])

                    if examples:
                        st.markdown(f"**{len(examples)} examples of {selected_failure.replace('_', ' ')} failures:**")
                        examples_df = pd.DataFrame(examples)
                        st.dataframe(examples_df, use_container_width=True, hide_index=True)

                        csv = examples_df.to_csv(index=False)
                        st.download_button(
                            f"⬇️ Download {selected_failure} failures",
                            csv,
                            file_name=f"{selected_failure}_failures.csv",
                            mime="text/csv",
                        )
                    else:
                        st.info("No examples available for this failure type.")
                else:
                    st.success("No failures detected in current data!")

            # -----------------------------------------------------------------
            # TAB: RESOURCE VALIDATION
            # -----------------------------------------------------------------
            with eval_tabs[2]:
                st.subheader("🔍 Resource Validation (Hallucination Detection)")
                st.markdown("*Compare recommended resources against known inventory*")

                validation = comprehensive_results.get('resource_validation', {})
                if validation.get('note'):
                    st.warning(validation['note'])
                    st.info("Upload a resource inventory file in the sidebar to enable validation.")
                else:
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Recommended", validation.get('total_resources_recommended', 0))
                    col2.metric("Matched to Inventory", validation.get('matched_to_inventory', 0))
                    col3.metric("Unmatched (Potential Hallucinations)", validation.get('unmatched_count', 0))
                    col4.metric("Inventory Size", validation.get('inventory_size', 0))

                    match_rate = validation.get('match_rate', 0)
                    hallucination_rate = validation.get('hallucination_rate', 0)
                    health = validation.get('health', 'unknown')

                    health_colors = {'good': '🟢', 'warning': '🟡', 'critical': '🔴'}
                    st.markdown(f"""
                    ### {health_colors.get(health, '⚪')} Match Rate: {match_rate:.1f}%
                    **Hallucination Rate: {hallucination_rate:.1f}%**
                    """)

                    if hallucination_rate > 10:
                        st.error(f"⚠️ High hallucination rate ({hallucination_rate:.1f}%) - review unmatched resources")

                    # Unmatched resources
                    unmatched = validation.get('unmatched_resources', [])
                    if unmatched:
                        st.markdown("### ❓ Unmatched Resources (Potential Hallucinations)")
                        unmatched_df = pd.DataFrame(unmatched)
                        st.dataframe(unmatched_df, use_container_width=True, hide_index=True)

                        csv = unmatched_df.to_csv(index=False)
                        st.download_button(
                            "⬇️ Download unmatched resources",
                            csv,
                            file_name="unmatched_resources.csv",
                            mime="text/csv",
                        )

            # -----------------------------------------------------------------
            # TAB: COVERAGE ANALYSIS
            # -----------------------------------------------------------------
            with eval_tabs[3]:
                st.subheader("📈 Coverage Analysis")
                st.markdown("*Are we recommending the right breadth of resources?*")

                coverage = comprehensive_results.get('coverage_analysis', {})
                if coverage.get('note'):
                    st.warning(coverage['note'])
                    st.info("Upload a resource inventory to enable coverage analysis.")
                else:
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total in Inventory", coverage.get('total_in_inventory', 0))
                    col2.metric("Ever Recommended", coverage.get('total_ever_recommended', 0))
                    col3.metric("Overall Coverage", f"{coverage.get('overall_coverage_pct', 0):.1f}%")

                    # Under-utilized resources
                    under_utilized = coverage.get('under_utilized_resources', [])
                    st.metric("Under-utilized Resources", coverage.get('under_utilized_count', 0))

                    if under_utilized:
                        st.markdown("### 📋 Under-utilized Resources (Never Recommended)")
                        st.write(", ".join(under_utilized[:30]))
                        if len(under_utilized) > 30:
                            st.caption(f"... and {len(under_utilized) - 30} more")

                    # Category coverage
                    cat_coverage = coverage.get('category_coverage', {})
                    if cat_coverage:
                        st.markdown("### 📊 Coverage by Category")
                        cat_data = pd.DataFrame([
                            {
                                'Category': k.title(),
                                'In Inventory': v['inventory_count'],
                                'Ever Recommended': v['recommended_count'],
                                'Coverage %': v['coverage_pct'],
                            }
                            for k, v in cat_coverage.items()
                        ]).sort_values('Coverage %')

                        fig = px.bar(
                            cat_data,
                            x='Category',
                            y='Coverage %',
                            title="Coverage % by Category",
                            color='Coverage %',
                            color_continuous_scale='RdYlGn',
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        st.dataframe(cat_data, use_container_width=True, hide_index=True)

            # -----------------------------------------------------------------
            # TAB: TEST CASES
            # -----------------------------------------------------------------
            with eval_tabs[4]:
                st.subheader("🧪 Gold Standard Test Cases")
                st.markdown("*Automated testing against expected outputs*")

                test_results = comprehensive_results.get('test_case_results', {})
                if test_results.get('note'):
                    st.info(test_results['note'])
                    st.markdown("""
                    **To enable test case evaluation:**
                    1. Create a JSON file with test cases
                    2. Upload it in the sidebar under "Gold Standard Test Cases"

                    **Test case format:**
                    ```json
                    [
                      {
                        "query": "I need food assistance in Austin",
                        "expected_resources": ["Central Texas Food Bank", "Caritas of Austin"],
                        "expected_category": "food",
                        "expected_location": "Austin"
                      }
                    ]
                    ```
                    """)
                else:
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Total Test Cases", test_results.get('total_test_cases', 0))
                    col2.metric("Passed", test_results.get('passed', 0))
                    col3.metric("Failed", test_results.get('failed', 0))
                    col4.metric("Pass Rate", f"{test_results.get('pass_rate', 0):.1f}%")

                    results = test_results.get('results', [])
                    if results:
                        st.markdown("### Test Case Results")
                        for result in results:
                            status = result.get('status', 'unknown')
                            icon = '✅' if status == 'pass' else ('❌' if status == 'fail' else '⚠️')
                            with st.expander(f"{icon} {result.get('query', 'Unknown query')[:60]}..."):
                                st.markdown(f"**Status:** {status.upper()}")
                                st.markdown(f"**Resource Recall:** {result.get('resource_recall', 0):.1f}%")
                                st.markdown(f"**Resource Precision:** {result.get('resource_precision', 0):.1f}%")
                                st.markdown(f"**Category Match:** {'✅' if result.get('category_match') else '❌'}")
                                st.markdown(f"**Location Match:** {'✅' if result.get('location_match') else '❌'}")

                                if result.get('missing_resources'):
                                    st.warning(f"Missing resources: {', '.join(result['missing_resources'])}")
                                if result.get('extra_resources'):
                                    st.info(f"Extra resources: {', '.join(result['extra_resources'])}")

            # -----------------------------------------------------------------
            # TAB: CONSISTENCY
            # -----------------------------------------------------------------
            with eval_tabs[5]:
                st.subheader("🔄 Consistency Analysis")
                st.markdown("*Do similar queries produce similar results?*")

                consistency = analyzer.run_consistency_analysis([])

                col1, col2, col3 = st.columns(3)
                col1.metric("Query Groups Analyzed", consistency.get('groups_analyzed', 0))
                col2.metric("Inconsistent Groups", consistency.get('inconsistent_groups', 0))
                col3.metric("Consistency Rate", f"{consistency.get('consistency_rate', 0):.1f}%")

                most_inconsistent = consistency.get('most_inconsistent', [])
                if most_inconsistent:
                    st.markdown("### ⚠️ Most Inconsistent Query Groups")
                    st.caption("These query patterns show high variance in responses")
                    inconsistent_df = pd.DataFrame([
                        {
                            'Query Pattern': r.get('query_group', ''),
                            'Traces': r.get('num_traces', 0),
                            'Quality Variance': f"{r.get('quality_variance', 0):.1f}",
                            'Resource Similarity': f"{r.get('resource_similarity', 0):.1%}",
                        }
                        for r in most_inconsistent
                    ])
                    st.dataframe(inconsistent_df, use_container_width=True, hide_index=True)
                else:
                    st.success("Not enough repeated queries to analyze consistency.")

            # -----------------------------------------------------------------
            # TAB: DETAILED FLAGS (original functionality)
            # -----------------------------------------------------------------
            with eval_tabs[6]:
                st.subheader("📋 Detailed Automated Flags")
                st.markdown("*Threshold-based flagging with full drill-down*")

                eval_df = analyzer.get_output_quality_evals()
                if eval_df.empty:
                    st.info("No eval data available for automated checks.")
                else:
                    eval_df = eval_df.copy()
                    eval_df['timestamp'] = pd.to_datetime(eval_df.get('timestamp'), errors='coerce')

                    st.markdown("#### ⚙️ Evaluation filters & thresholds")
                    trace_types = sorted([t for t in eval_df['trace_type'].dropna().unique() if t])
                    default_types = [t for t in ['referrals', 'email_results', 'action_plans'] if t in trace_types]
                    selected_types = st.multiselect(
                        "Trace types to evaluate",
                        trace_types,
                        default=default_types or trace_types,
                        key="detailed_trace_types",
                    )

                    filter_user_facing = st.checkbox(
                        "Only user-facing traces (non-empty query & real user)",
                        value=True,
                        key="detailed_user_facing",
                    )

                    with st.expander("Eval thresholds", expanded=False):
                        min_quality = st.slider(
                            "Minimum quality score",
                            min_value=0,
                            max_value=100,
                            value=60,
                            step=5,
                            key="detailed_min_quality",
                        )
                        min_resources = st.slider(
                            "Minimum resources per response",
                            min_value=0,
                            max_value=10,
                            value=2,
                            step=1,
                            key="detailed_min_resources",
                        )
                        min_detail_score = st.slider(
                            "Minimum resource detail score",
                            min_value=0,
                            max_value=100,
                            value=50,
                            step=5,
                            help="Proxy for hallucination risk: missing location/contact info lowers score.",
                            key="detailed_min_detail",
                        )
                        require_actionable = st.checkbox(
                            "Require actionable info when resources are present",
                            value=True,
                            key="detailed_require_actionable",
                        )
                        enforce_location = st.checkbox(
                            "Enforce location match when user specified a location",
                            value=True,
                            key="detailed_enforce_location",
                        )
                        enforce_category = st.checkbox(
                            "Enforce category match when category is known",
                            value=False,
                            key="detailed_enforce_category",
                        )

                    filtered = eval_df
                    if selected_types:
                        filtered = filtered[filtered['trace_type'].isin(selected_types)]

                    if filter_user_facing:
                        q = filtered['query'].astype(str).str.strip()
                        u = filtered['user'].astype(str).str.lower().str.strip()
                        filtered = filtered[
                            (q != "") & (q != ".") & (~u.str.startswith("unknown")) & (u != "unknown")
                        ]

                    if filtered.empty:
                        st.info("No traces match the current filters.")
                    else:
                        filtered = filtered.copy()
                        filtered['quality_score'] = pd.to_numeric(filtered['quality_score'], errors='coerce').fillna(0)
                        filtered['resource_count'] = pd.to_numeric(filtered['resource_count'], errors='coerce').fillna(0)
                        filtered['resource_detail_score'] = pd.to_numeric(
                            filtered.get('resource_detail_score'), errors='coerce'
                        ).fillna(0)

                        total = len(filtered)
                        avg_quality = filtered['quality_score'].mean()
                        location_match_rate = filtered['location_aligned'].mean() * 100 if 'location_aligned' in filtered else 0
                        category_match_rate = filtered['category_aligned'].mean() * 100 if 'category_aligned' in filtered else 0
                        _actionable_rate = filtered['has_actionable_info'].mean() * 100 if 'has_actionable_info' in filtered else 0
                        resources_rate = (filtered['resource_count'] > 0).mean() * 100
                        avg_detail = filtered['resource_detail_score'].mean()

                        st.markdown("#### 📊 Summary")
                        col1, col2, col3, col4, col5, col6 = st.columns(6)
                        col1.metric("Traces", f"{total:,}")
                        col2.metric("Avg Quality", f"{avg_quality:.1f}")
                        col3.metric("Location Match", f"{location_match_rate:.1f}%")
                        col4.metric("Category Match", f"{category_match_rate:.1f}%")
                        col5.metric("Has Resources", f"{resources_rate:.1f}%")
                        col6.metric("Detail Score", f"{avg_detail:.1f}")

                        st.markdown("#### 🚨 Failure flags")
                        filtered['flag_no_resources'] = filtered['resource_count'] < min_resources
                        filtered['flag_low_quality'] = filtered['quality_score'] < min_quality
                        filtered['flag_low_detail'] = (
                            (filtered['resource_count'] > 0) & (filtered['resource_detail_score'] < min_detail_score)
                        )
                        filtered['flag_generic'] = filtered.get('is_generic', False).fillna(False)
                        filtered['flag_too_short'] = filtered.get('too_short', False).fillna(False)
                        filtered['flag_location_mismatch'] = (
                            enforce_location & (~filtered.get('location_aligned', True))
                        )
                        filtered['flag_category_mismatch'] = (
                            enforce_category & (~filtered.get('category_aligned', True))
                        )
                        filtered['flag_not_actionable'] = (
                            require_actionable
                            & (filtered['resource_count'] > 0)
                            & (~filtered.get('has_actionable_info', True))
                        )

                        flag_cols = [
                            'flag_no_resources',
                            'flag_low_quality',
                            'flag_low_detail',
                            'flag_generic',
                            'flag_too_short',
                            'flag_location_mismatch',
                            'flag_category_mismatch',
                            'flag_not_actionable',
                        ]
                        issue_counts = {
                            'No resources': int(filtered['flag_no_resources'].sum()),
                            'Low quality': int(filtered['flag_low_quality'].sum()),
                            'Low detail score': int(filtered['flag_low_detail'].sum()),
                            'Generic response': int(filtered['flag_generic'].sum()),
                            'Too short': int(filtered['flag_too_short'].sum()),
                            'Location mismatch': int(filtered['flag_location_mismatch'].sum()),
                            'Category mismatch': int(filtered['flag_category_mismatch'].sum()),
                            'Not actionable': int(filtered['flag_not_actionable'].sum()),
                        }

                        issues_df = pd.DataFrame(
                            [{'Issue': k, 'Count': v} for k, v in issue_counts.items() if v > 0]
                        ).sort_values('Count', ascending=False)

                        if not issues_df.empty:
                            fig_issues = px.bar(
                                issues_df,
                                x='Issue',
                                y='Count',
                                title="Flag counts by issue type",
                            )
                            st.plotly_chart(fig_issues, use_container_width=True)
                        else:
                            st.success("No automated failures for the current thresholds.")

                        # Flagged traces table
                        flagged = filtered[filtered[flag_cols].any(axis=1)].copy()
                        if not flagged.empty:
                            def _build_flag_list_inner(row: pd.Series) -> str:
                                labels = []
                                if row.get('flag_no_resources'):
                                    labels.append("no_resources")
                                if row.get('flag_low_quality'):
                                    labels.append("low_quality")
                                if row.get('flag_low_detail'):
                                    labels.append("low_detail")
                                if row.get('flag_generic'):
                                    labels.append("generic")
                                if row.get('flag_too_short'):
                                    labels.append("too_short")
                                if row.get('flag_location_mismatch'):
                                    labels.append("location_mismatch")
                                if row.get('flag_category_mismatch'):
                                    labels.append("category_mismatch")
                                if row.get('flag_not_actionable'):
                                    labels.append("not_actionable")
                                return ", ".join(labels)

                            flagged['flags'] = flagged.apply(_build_flag_list_inner, axis=1)
                            flagged = flagged.sort_values('quality_score')

                            st.markdown("#### 🧾 Flagged traces")
                            display_cols = [
                                'timestamp',
                                'user',
                                'query',
                                'trace_type',
                                'quality_score',
                                'resource_count',
                                'resource_detail_score',
                                'flags',
                            ]
                            display_cols = [c for c in display_cols if c in flagged.columns]
                            st.dataframe(
                                flagged[display_cols].head(200),
                                use_container_width=True,
                                hide_index=True,
                            )

                            csv = flagged[display_cols].to_csv(index=False)
                            st.download_button(
                                "⬇️ Download flagged traces (CSV)",
                                csv,
                                file_name="flagged_traces_detailed.csv",
                                mime="text/csv",
                                key="detailed_download",
                            )
                        else:
                            st.success("No traces failed the automated checks with current thresholds.")


if __name__ == "__main__":
    main()


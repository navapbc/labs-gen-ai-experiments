"""
Agentic AI Product Dashboard
Enhanced version with full trace log analysis and weekly reporting
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import re
import os
import hashlib
import hmac

# =============================================================================
# AUTHENTICATION
# =============================================================================
ALLOWED_USERS = {
    "user@example.com": "change-me",
}

def check_password():
    """Returns True if the user has entered valid credentials."""
    
    def get_users():
        """Get allowed users from st.secrets or fallback to defaults."""
        try:
            return dict(st.secrets["passwords"])
        except (KeyError, FileNotFoundError):
            return ALLOWED_USERS
    
    def login_form():
        """Render the login form."""
        st.markdown("""
        <style>
            .login-container {
                max-width: 400px;
                margin: 80px auto;
                padding: 40px;
                background: rgba(18, 18, 26, 0.95);
                border: 1px solid rgba(0, 212, 255, 0.2);
                border-radius: 16px;
                backdrop-filter: blur(10px);
            }
            .login-title {
                text-align: center;
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            .login-subtitle {
                text-align: center;
                color: #888899;
                font-size: 0.9rem;
                margin-bottom: 2rem;
            }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-title">🤖 Agentic AI</div>', unsafe_allow_html=True)
            st.markdown('<div class="login-subtitle">Enter your credentials to access the dashboard</div>', unsafe_allow_html=True)
            
            with st.form("login"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                
                if submitted:
                    users = get_users()
                    email_clean = email.lower().strip()
                    
                    if email_clean in users and hmac.compare_digest(
                        password, users[email_clean]
                    ):
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email_clean
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
            
            st.markdown(
                '<p style="text-align:center; color:#555; font-size:0.8rem; margin-top:1rem;">'
                'Contact your administrator for access</p>',
                unsafe_allow_html=True
            )
    
    if st.session_state.get("authenticated"):
        return True
    
    login_form()
    return False

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Agentic AI Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM STYLING
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-tertiary: #1a1a24;
        --accent-cyan: #00d4ff;
        --accent-magenta: #ff00aa;
        --accent-lime: #adff2f;
        --accent-orange: #ff6b35;
        --text-primary: #e8e8e8;
        --text-muted: #888899;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #0f0f1a 50%, #0a0f0a 100%);
    }
    
    .main-header {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #ff00aa, #adff2f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-family: 'Outfit', sans-serif;
        color: #888899;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #12121a 0%, #1a1a24 100%);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(0, 212, 255, 0.5);
        box-shadow: 0 4px 30px rgba(0, 212, 255, 0.15);
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #00d4ff;
    }
    
    .metric-label {
        font-family: 'Outfit', sans-serif;
        font-size: 0.8rem;
        color: #888899;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 0.5rem;
    }
    
    .metric-delta-positive {
        color: #adff2f;
        font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-delta-negative {
        color: #ff6b6b;
        font-size: 0.85rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .section-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.2rem;
        color: #e8e8e8;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(0, 212, 255, 0.3);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .stSidebar {
        background: linear-gradient(180deg, #0a0a0f 0%, #12121a 100%);
    }
    
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 4px 12px;
        background: rgba(173, 255, 47, 0.1);
        border: 1px solid rgba(173, 255, 47, 0.3);
        border-radius: 20px;
        font-size: 0.75rem;
        color: #adff2f;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .live-dot {
        width: 8px;
        height: 8px;
        background: #adff2f;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.9); }
    }
    
    .tool-badge {
        display: inline-block;
        padding: 4px 10px;
        margin: 2px;
        background: rgba(255, 0, 170, 0.15);
        border: 1px solid rgba(255, 0, 170, 0.3);
        border-radius: 12px;
        font-size: 0.75rem;
        color: #ff00aa;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(136, 136, 153, 0.1);
    }
    
    .stat-label {
        color: #888899;
        font-size: 0.85rem;
    }
    
    .stat-value {
        color: #e8e8e8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
    }
    
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
    }
    
    .data-source-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: rgba(0, 212, 255, 0.1);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        font-size: 0.7rem;
        color: #00d4ff;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .report-card {
        background: linear-gradient(145deg, #12121a 0%, #1a1a24 100%);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .report-card-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1rem;
        color: #00d4ff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .risk-high {
        background: rgba(255, 107, 107, 0.15);
        border: 1px solid rgba(255, 107, 107, 0.3);
        color: #ff6b6b;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .risk-medium {
        background: rgba(255, 165, 0, 0.15);
        border: 1px solid rgba(255, 165, 0, 0.3);
        color: #ffa500;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .risk-low {
        background: rgba(173, 255, 47, 0.15);
        border: 1px solid rgba(173, 255, 47, 0.3);
        color: #adff2f;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .trend-up {
        color: #adff2f;
    }
    
    .trend-down {
        color: #ff6b6b;
    }
    
    .trend-neutral {
        color: #888899;
    }
    
    .feedback-item {
        background: rgba(18, 18, 26, 0.8);
        border-left: 3px solid #ff00aa;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .incident-item {
        background: rgba(18, 18, 26, 0.8);
        border-left: 3px solid #ff6b6b;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .incident-resolved {
        border-left-color: #adff2f;
    }
    
    .wow-change {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        padding: 2px 8px;
        border-radius: 4px;
    }
    
    .wow-positive {
        background: rgba(173, 255, 47, 0.2);
        color: #adff2f;
    }
    
    .wow-negative {
        background: rgba(255, 107, 107, 0.2);
        color: #ff6b6b;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATA LOADING & PARSING
# =============================================================================
@st.cache_data(ttl=300)
def load_csv_data(file_path: str):
    """Load and parse the CSV trace data from file path"""
    df = pd.read_csv(file_path)
    return df

def load_uploaded_file(uploaded_file):
    """Load data from an uploaded file (CSV or Excel)"""
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError(f"Unsupported file type: {uploaded_file.name}")
    return df

def parse_request_payload(payload_str):
    """Extract key information from request payload"""
    try:
        if pd.isna(payload_str) or payload_str == '' or payload_str is None:
            return {}
        
        # Handle if it's already a dict
        if isinstance(payload_str, dict):
            payload = payload_str
        else:
            # Try to parse as JSON string
            payload_str = str(payload_str).strip()
            if not payload_str or payload_str == 'nan':
                return {}
            payload = json.loads(payload_str)
        
        # Extract system - can be list or string
        system = payload.get('system', [])
        has_system = False
        if isinstance(system, list):
            has_system = len(system) > 0
        elif isinstance(system, str):
            has_system = len(system) > 0
        
        # Extract tools
        tools = payload.get('tools', [])
        if not isinstance(tools, list):
            tools = []
        
        # Extract tool choice
        tool_choice = payload.get('tool_choice', {})
        if isinstance(tool_choice, dict):
            tool_choice_type = tool_choice.get('type', 'none')
        else:
            tool_choice_type = str(tool_choice) if tool_choice else 'none'
        
        return {
            'max_tokens': payload.get('max_tokens'),
            'temperature': payload.get('temperature'),
            'num_messages': len(payload.get('messages', [])) if isinstance(payload.get('messages'), list) else 0,
            'num_tools': len(tools),
            'tool_names': [t.get('name', 'unknown') for t in tools if isinstance(t, dict)],
            'has_system': has_system,
            'stream': payload.get('stream', False),
            'tool_choice': tool_choice_type
        }
    except Exception as e:
        return {}

def parse_response_payload(payload_str):
    """Extract token usage from response payload"""
    try:
        if pd.isna(payload_str) or payload_str == '' or payload_str is None:
            return {}
        
        # Convert to string if needed
        payload_str = str(payload_str)
        if not payload_str or payload_str == 'nan':
            return {}
        
        # Look for usage info in the streaming response
        input_tokens = 0
        output_tokens = 0
        
        # Try multiple patterns to find token counts
        # Pattern 1: "input_tokens":8465
        input_match = re.search(r'"input_tokens"\s*:\s*(\d+)', payload_str)
        if input_match:
            input_tokens = int(input_match.group(1))
        
        # Pattern 2: Find all output_tokens and sum them (streaming can have multiple)
        output_matches = re.findall(r'"output_tokens"\s*:\s*(\d+)', payload_str)
        if output_matches:
            # Take the largest value (final count)
            output_tokens = max(int(m) for m in output_matches)
        
        # Look for cache tokens
        cache_creation = 0
        cache_read = 0
        cache_match = re.search(r'"cache_creation_input_tokens"\s*:\s*(\d+)', payload_str)
        if cache_match:
            cache_creation = int(cache_match.group(1))
        cache_read_match = re.search(r'"cache_read_input_tokens"\s*:\s*(\d+)', payload_str)
        if cache_read_match:
            cache_read = int(cache_read_match.group(1))
        
        return {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cache_creation_tokens': cache_creation,
            'cache_read_tokens': cache_read,
            'total_tokens': input_tokens + output_tokens
        }
    except Exception as e:
        return {}

def process_dataframe(df):
    """Process the raw dataframe with parsed fields"""
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Parse logging_time
    df['logging_time'] = pd.to_datetime(df['logging_time'], format='mixed', errors='coerce')
    df['date'] = df['logging_time'].dt.date
    df['hour'] = df['logging_time'].dt.hour
    df['day_of_week'] = df['logging_time'].dt.day_name()
    
    # Ensure payload columns exist
    if 'request_payload' not in df.columns:
        df['request_payload'] = ''
    if 'response_payload' not in df.columns:
        df['response_payload'] = ''
    
    # Parse request payloads
    request_data = df['request_payload'].apply(parse_request_payload)
    df['max_tokens'] = request_data.apply(lambda x: x.get('max_tokens') if x else None)
    df['temperature'] = request_data.apply(lambda x: x.get('temperature') if x else None)
    df['num_messages'] = request_data.apply(lambda x: x.get('num_messages', 0) if x else 0)
    df['num_tools'] = request_data.apply(lambda x: x.get('num_tools', 0) if x else 0)
    df['tool_names'] = request_data.apply(lambda x: x.get('tool_names', []) if x else [])
    df['has_system'] = request_data.apply(lambda x: x.get('has_system', False) if x else False)
    df['is_streaming'] = request_data.apply(lambda x: x.get('stream', False) if x else False)
    df['tool_choice'] = request_data.apply(lambda x: x.get('tool_choice', 'none') if x else 'none')
    
    # Parse response payloads
    response_data = df['response_payload'].apply(parse_response_payload)
    df['input_tokens'] = response_data.apply(lambda x: x.get('input_tokens', 0) if x else 0)
    df['output_tokens'] = response_data.apply(lambda x: x.get('output_tokens', 0) if x else 0)
    df['cache_creation_tokens'] = response_data.apply(lambda x: x.get('cache_creation_tokens', 0) if x else 0)
    df['cache_read_tokens'] = response_data.apply(lambda x: x.get('cache_read_tokens', 0) if x else 0)
    df['total_tokens'] = response_data.apply(lambda x: x.get('total_tokens', 0) if x else 0)
    
    # Convert to numeric and fill NaN with 0
    for col in ['input_tokens', 'output_tokens', 'cache_creation_tokens', 'cache_read_tokens', 'total_tokens', 'num_messages', 'num_tools']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    for col in ['max_tokens']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    for col in ['temperature']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Extract model name (clean up the full path)
    df['model_clean'] = df['model'].apply(lambda x: str(x).split('/')[-1] if pd.notna(x) and str(x).strip() else 'unknown')
    
    return df

# =============================================================================
# BIGQUERY CONNECTION
# =============================================================================
def get_bigquery_client():
    """Initialize BigQuery client - supports st.secrets (cloud) and local file"""
    from google.cloud import bigquery
    from google.oauth2 import service_account

    # GCP project is read from secrets/env so no project name is hardcoded here.
    gcp_project = os.environ.get("GCP_PROJECT_ID")

    scopes = [
        "https://www.googleapis.com/auth/bigquery",
        "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Method 1: Try st.secrets (for Streamlit Cloud deployment)
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=scopes
        )
        # Prefer explicit env var; fall back to project_id from the credentials dict.
        project = gcp_project or creds_dict.get("project_id")
        return bigquery.Client(credentials=credentials, project=project)
    except (KeyError, FileNotFoundError):
        pass

    # Method 2: Try local service account file
    key_path = os.path.join(os.path.dirname(__file__), 'service-account.json')
    if os.path.exists(key_path):
        credentials = service_account.Credentials.from_service_account_file(
            key_path, scopes=scopes
        )
        return bigquery.Client(credentials=credentials, project=gcp_project)

    # Method 3: Fall back to default credentials (gcloud auth)
    return bigquery.Client(project=gcp_project)

def get_cache_path():
    """Get path to the local cache file"""
    return os.path.join(os.path.dirname(__file__), '.cache', 'bigquery_cache.parquet')

def load_cached_data():
    """Load data from local cache if it exists"""
    cache_path = get_cache_path()
    if os.path.exists(cache_path):
        try:
            df = pd.read_parquet(cache_path)
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
            return df, cache_time
        except:
            return None, None
    return None, None

def save_to_cache(df):
    """Save data to local cache"""
    cache_path = get_cache_path()
    cache_dir = os.path.dirname(cache_path)
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    df.to_parquet(cache_path, index=False)

def fetch_bigquery_data(use_cache=True):
    """Fetch ALL data from BigQuery with smart caching"""

    # Check cache first (valid for 1 hour)
    if use_cache:
        cached_df, cache_time = load_cached_data()
        if cached_df is not None:
            cache_age = datetime.now() - cache_time
            if cache_age.total_seconds() < 3600:  # 1 hour cache
                return cached_df, cache_time

    # Fetch from BigQuery
    client = get_bigquery_client()

    # Table path is read from env so no project/dataset name is hardcoded here.
    # Set BQ_TABLE in .env or Streamlit secrets, e.g.:
    #   BQ_TABLE=my-project.my_dataset.request_response_logging
    bq_table = os.environ.get("BQ_TABLE")
    if not bq_table:
        raise RuntimeError("BQ_TABLE environment variable is not set. "
                           "Set it to the fully-qualified BigQuery table path.")

    query = f"""
    SELECT
        endpoint,
        deployed_model_id,
        logging_time,
        request_id,
        request_payload,
        response_payload,
        model,
        model_version,
        api_method
    FROM `{bq_table}`
    ORDER BY logging_time DESC
    """
    
    df = client.query(query).to_dataframe()
    
    # Handle REPEATED fields (arrays) - flatten/join them
    # BigQuery can return numpy arrays for REPEATED fields
    import numpy as np
    
    if 'request_payload' in df.columns:
        def flatten_payload(x):
            try:
                if x is None or (isinstance(x, float) and pd.isna(x)):
                    return ''
                if isinstance(x, (list, np.ndarray)):
                    return ''.join(str(item) for item in x)
                return str(x)
            except (ValueError, TypeError):
                return ''
        df['request_payload'] = df['request_payload'].apply(flatten_payload)
    
    if 'response_payload' in df.columns:
        def flatten_response(x):
            try:
                if x is None or (isinstance(x, float) and pd.isna(x)):
                    return ''
                if isinstance(x, (list, np.ndarray)):
                    return ''.join(str(item) for item in x)
                return str(x)
            except (ValueError, TypeError):
                return ''
        df['response_payload'] = df['response_payload'].apply(flatten_response)
    
    # Save to cache
    save_to_cache(df)
    
    return df, datetime.now()

# =============================================================================
# MAIN DASHBOARD
# =============================================================================
def main():
    # Auth gate - must sign in first
    if not check_password():
        st.stop()
    
    # Header
    st.markdown('<h1 class="main-header">⚡ Agentic AI Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Show logged-in user and logout
        user_email = st.session_state.get("user_email", "")
        st.markdown(f"👤 **{user_email}**")
        if st.button("Sign Out", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state.pop("user_email", None)
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🎛️ Data Source")
        
        # Check if service account exists (local file OR st.secrets)
        key_path = os.path.join(os.path.dirname(__file__), 'service-account.json')
        has_service_account = os.path.exists(key_path)
        if not has_service_account:
            try:
                _ = st.secrets["gcp_service_account"]
                has_service_account = True
            except (KeyError, FileNotFoundError):
                pass
        
        data_source = st.radio(
            "Select data source:",
            ["☁️ BigQuery (Live)", "📁 Upload File"],
            index=0  # Default to BigQuery
        )
        
        uploaded_file = None
        
        if data_source == "☁️ BigQuery (Live)":
            if has_service_account:
                st.success("✅ Connected to BigQuery")
            else:
                st.warning("""
                **Setup required:**
                
                Contact your administrator to configure BigQuery access.
                """)
            use_bigquery = True
        else:
            use_bigquery = False
            st.markdown("#### Upload trace logs")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['csv', 'xlsx', 'xls'],
                help="Upload your Claude trace logs (CSV or Excel format)"
            )
            if uploaded_file is not None:
                st.success(f"✅ Loaded: {uploaded_file.name}")
            else:
                st.info("👆 Upload a CSV or Excel file to get started")
        
        st.markdown("---")
        
        # Refresh buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True, help="Reload from cache"):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("⚡ Sync", use_container_width=True, help="Fetch fresh data from BigQuery"):
                st.session_state['force_refresh'] = True
                st.cache_data.clear()
                # Clear the cache file
                cache_path = os.path.join(os.path.dirname(__file__), '.cache', 'bigquery_cache.parquet')
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                st.rerun()
    
    # Load data
    try:
        df = None
        data_source_label = ""
        
        if use_bigquery:
            # Try BigQuery connection with caching
            try:
                # Check if force refresh was requested
                force_refresh = st.session_state.get('force_refresh', False)
                if force_refresh:
                    st.session_state['force_refresh'] = False
                
                with st.spinner("Loading data..." if not force_refresh else "Fetching fresh data from BigQuery..."):
                    df, cache_time = fetch_bigquery_data(use_cache=not force_refresh)
                    df = process_dataframe(df)
                    
                    # Show cache status
                    if cache_time:
                        cache_age = datetime.now() - cache_time
                        if cache_age.total_seconds() < 60:
                            cache_status = "just now"
                        elif cache_age.total_seconds() < 3600:
                            cache_status = f"{int(cache_age.total_seconds() / 60)}m ago"
                        else:
                            cache_status = f"{int(cache_age.total_seconds() / 3600)}h ago"
                        data_source_label = f"☁️ BIGQUERY • {len(df):,} traces • cached {cache_status}"
                    else:
                        data_source_label = f"☁️ BIGQUERY LIVE • {len(df):,} traces"
            except Exception as bq_error:
                st.error(f"BigQuery connection failed: {str(bq_error)}")
                st.info("Try uploading a file instead, or contact your administrator.")
                return
        
        else:
            # Load from uploaded file
            if uploaded_file is not None:
                try:
                    df = load_uploaded_file(uploaded_file)
                    df = process_dataframe(df)
                    data_source_label = f"📁 {uploaded_file.name} • {len(df):,} traces"
                except Exception as upload_error:
                    st.error(f"Error reading file: {str(upload_error)}")
                    return
            else:
                # Show upload prompt
                st.markdown('''
                    <p class="sub-header">
                        Real-time monitoring for your AI agents
                    </p>
                ''', unsafe_allow_html=True)
                
                st.markdown("""
                <div style="text-align: center; padding: 4rem 2rem; background: linear-gradient(145deg, #12121a 0%, #1a1a24 100%); border-radius: 16px; border: 1px dashed rgba(0, 212, 255, 0.3); margin: 2rem 0;">
                    <h2 style="color: #e8e8e8; font-family: 'JetBrains Mono', monospace;">📁 Upload Your Trace Logs</h2>
                    <p style="color: #888899; margin-top: 1rem;">Use the sidebar to upload a CSV or Excel file with your Claude trace logs.</p>
                    <p style="color: #666677; font-size: 0.85rem; margin-top: 2rem;">Or switch to <strong>BigQuery (Live)</strong> for real-time data.</p>
                </div>
                """, unsafe_allow_html=True)
                return
        
        # Data source indicator
        st.markdown(f'''
            <p class="sub-header">
                Real-time monitoring for your AI agents 
                <span class="data-source-badge">{data_source_label}</span>
            </p>
        ''', unsafe_allow_html=True)
        
        # Date filter in sidebar
        with st.sidebar:
            st.markdown("### 📅 Date Range")
            valid_dates = df[df['date'].notna()]['date']
            if len(valid_dates) > 0:
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                
                # Quick presets
                preset = st.selectbox(
                    "Quick select",
                    ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
                    index=0
                )
                
                today = datetime.now().date()
                if preset == "Last 7 Days":
                    filter_start = today - timedelta(days=7)
                    filter_end = today
                elif preset == "Last 30 Days":
                    filter_start = today - timedelta(days=30)
                    filter_end = today
                elif preset == "Last 90 Days":
                    filter_start = today - timedelta(days=90)
                    filter_end = today
                elif preset == "Custom":
                    date_range = st.date_input(
                        "Select range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    if len(date_range) == 2:
                        filter_start, filter_end = date_range
                    else:
                        filter_start, filter_end = min_date, max_date
                else:  # All Time
                    filter_start = min_date
                    filter_end = max_date
                
                # Apply date filter
                df = df[(df['date'] >= filter_start) & (df['date'] <= filter_end)]
                
                # Show date range info
                st.caption(f"📊 {filter_start} → {filter_end}")
            
            st.markdown("---")
            st.markdown("### 🤖 Model Filter")
            models = df['model_clean'].dropna().unique().tolist()
            selected_models = st.multiselect(
                "Select models",
                options=models,
                default=models
            )
            if selected_models:
                df = df[df['model_clean'].isin(selected_models)]
            
            # Debug section
            with st.expander("🔧 Debug Data", expanded=False):
                st.caption("Sample request_payload:")
                if len(df) > 0 and 'request_payload' in df.columns:
                    sample = df['request_payload'].iloc[0]
                    st.code(str(sample)[:500] + "..." if len(str(sample)) > 500 else str(sample))
                    st.caption(f"Type: {type(sample)}")
                
                st.caption("Parsed fields sample:")
                if len(df) > 0:
                    st.write({
                        'max_tokens': df['max_tokens'].iloc[0],
                        'temperature': df['temperature'].iloc[0],
                        'num_tools': df['num_tools'].iloc[0],
                        'num_messages': df['num_messages'].iloc[0],
                        'is_streaming': df['is_streaming'].iloc[0],
                        'has_system': df['has_system'].iloc[0],
                    })
        
        # =================================================================
        # TABS: Dashboard vs Weekly Report
        # =================================================================
        tab1, tab2 = st.tabs(["📊 Dashboard", "📋 Weekly Report"])
        
        with tab1:
            render_dashboard_tab(df)
        
        with tab2:
            render_weekly_report_tab(df)
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def render_dashboard_tab(df):
    """Render the main dashboard metrics tab"""
    # =================================================================
    # TOP METRICS ROW
    # =================================================================
    st.markdown('<div class="section-title">📊 Key Metrics</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_requests = len(df)
    total_input_tokens = df['input_tokens'].sum()
    total_output_tokens = df['output_tokens'].sum()
    avg_tokens_per_request = (total_input_tokens + total_output_tokens) / max(total_requests, 1)
    unique_tools = len(set([tool for tools in df['tool_names'] for tool in tools]))
    
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Requests</div>
                <div class="metric-value">{total_requests:,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Input Tokens</div>
                <div class="metric-value" style="color: #ff00aa;">{total_input_tokens:,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Output Tokens</div>
                <div class="metric-value" style="color: #adff2f;">{total_output_tokens:,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Tokens/Request</div>
                <div class="metric-value" style="color: #ff6b35;">{avg_tokens_per_request:,.0f}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Unique Tools</div>
                <div class="metric-value" style="color: #00ff88;">{unique_tools}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # =================================================================
    # CHARTS ROW 1: Request Volume & Model Distribution
    # =================================================================
    st.markdown('<div class="section-title">📈 Request Analytics</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Daily request volume
        daily_stats = df.groupby('date').agg({
            'request_id': 'count',
            'input_tokens': 'sum',
            'output_tokens': 'sum'
        }).reset_index()
        daily_stats.columns = ['date', 'requests', 'input_tokens', 'output_tokens']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['requests'],
            mode='lines+markers',
            name='Requests',
            line=dict(color='#00d4ff', width=3),
            marker=dict(size=8, color='#00d4ff'),
            fill='tozeroy',
            fillcolor='rgba(0, 212, 255, 0.1)'
        ))
        
        fig.update_layout(
            title=dict(text='Daily Request Volume', font=dict(color='#e8e8e8', size=16, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899', family='Outfit'),
            xaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            hovermode='x unified',
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Model distribution
        model_counts = df['model_clean'].value_counts().reset_index()
        model_counts.columns = ['model', 'count']
        
        colors = ['#00d4ff', '#ff00aa', '#adff2f', '#ff6b35', '#00ff88']
        
        fig = go.Figure(data=[go.Pie(
            labels=model_counts['model'],
            values=model_counts['count'],
            hole=0.6,
            marker=dict(colors=colors[:len(model_counts)]),
            textinfo='percent',
            textfont=dict(color='#e8e8e8', family='JetBrains Mono'),
            hovertemplate='%{label}<br>%{value:,} requests<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=dict(text='Model Distribution', font=dict(color='#e8e8e8', size=16, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899'),
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5, font=dict(size=10)),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # =================================================================
    # CHARTS ROW 2: Token Usage & Tools
    # =================================================================
    st.markdown('<div class="section-title">🔧 Token Usage & Tools</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Token usage over time
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=daily_stats['date'],
            y=daily_stats['input_tokens'],
            name='Input Tokens',
            marker_color='#ff00aa'
        ))
        
        fig.add_trace(go.Bar(
            x=daily_stats['date'],
            y=daily_stats['output_tokens'],
            name='Output Tokens',
            marker_color='#adff2f'
        ))
        
        fig.update_layout(
            title=dict(text='Daily Token Consumption', font=dict(color='#e8e8e8', size=16, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899'),
            barmode='stack',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tool usage
        all_tools = [tool for tools in df['tool_names'] for tool in tools]
        tool_counts = pd.Series(all_tools).value_counts().head(15)
        
        fig = go.Figure(go.Bar(
            x=tool_counts.values,
            y=tool_counts.index,
            orientation='h',
            marker=dict(
                color=tool_counts.values,
                colorscale=[[0, '#12121a'], [0.5, '#ff00aa'], [1, '#00d4ff']]
            )
        ))
        
        fig.update_layout(
            title=dict(text='Top Tools Used', font=dict(color='#e8e8e8', size=16, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899', size=10),
            xaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            yaxis=dict(showgrid=False, autorange='reversed'),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # =================================================================
    # CHARTS ROW 3: Hourly Patterns & Temperature/Settings
    # =================================================================
    st.markdown('<div class="section-title">⏰ Usage Patterns & Settings</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Hourly distribution
        hourly_stats = df.groupby('hour').size().reset_index(name='count')
        
        fig = go.Figure(go.Bar(
            x=hourly_stats['hour'],
            y=hourly_stats['count'],
            marker=dict(
                color=hourly_stats['count'],
                colorscale=[[0, '#12121a'], [0.5, '#00d4ff'], [1, '#ff00aa']]
            )
        ))
        
        fig.update_layout(
            title=dict(text='Requests by Hour', font=dict(color='#e8e8e8', size=14, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899'),
            xaxis=dict(showgrid=False, title='Hour of Day'),
            yaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Temperature distribution
        temp_data = df[df['temperature'].notna()]['temperature']
        
        fig = go.Figure(go.Histogram(
            x=temp_data,
            nbinsx=20,
            marker_color='#adff2f',
            opacity=0.8
        ))
        
        fig.update_layout(
            title=dict(text='Temperature Distribution', font=dict(color='#e8e8e8', size=14, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899'),
            xaxis=dict(showgrid=False, title='Temperature'),
            yaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Max tokens distribution
        max_tokens_data = df[df['max_tokens'].notna()]['max_tokens']
        
        fig = go.Figure(go.Histogram(
            x=max_tokens_data,
            nbinsx=20,
            marker_color='#ff6b35',
            opacity=0.8
        ))
        
        fig.update_layout(
            title=dict(text='Max Tokens Distribution', font=dict(color='#e8e8e8', size=14, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899'),
            xaxis=dict(showgrid=False, title='Max Tokens'),
            yaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # =================================================================
    # CHARTS ROW 4: Conversation Depth & Cost Analysis
    # =================================================================
    st.markdown('<div class="section-title">💬 Conversation & Cost Analysis</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Messages per request
        msg_data = df[df['num_messages'] > 0]['num_messages']
        
        fig = go.Figure(go.Histogram(
            x=msg_data,
            marker_color='#00d4ff',
            opacity=0.8
        ))
        
        fig.update_layout(
            title=dict(text='Conversation Depth (Messages per Request)', font=dict(color='#e8e8e8', size=14, family='JetBrains Mono')),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899'),
            xaxis=dict(showgrid=False, title='Number of Messages'),
            yaxis=dict(showgrid=True, gridcolor='rgba(136, 136, 153, 0.1)'),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Estimated cost (using Claude pricing approximation)
        # Claude 3.5 Sonnet: $3/M input, $15/M output (approximate)
        input_cost = (total_input_tokens / 1_000_000) * 3
        output_cost = (total_output_tokens / 1_000_000) * 15
        total_cost = input_cost + output_cost
        
        fig = go.Figure()
        
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=total_cost,
            number={'prefix': "$", 'font': {'color': '#ff00aa', 'size': 48, 'family': 'JetBrains Mono'}, 'valueformat': ',.2f'},
            title={'text': "Estimated API Cost", 'font': {'color': '#e8e8e8', 'size': 14}},
            domain={'x': [0, 0.5], 'y': [0.2, 1]}
        ))
        
        fig.add_annotation(
            x=0.25, y=0.05,
            text=f"Input: ${input_cost:.2f} | Output: ${output_cost:.2f}",
            showarrow=False,
            font=dict(color='#888899', size=12)
        )
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#888899'),
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # =================================================================
    # SUMMARY STATS TABLE
    # =================================================================
    st.markdown('<div class="section-title">📋 Summary Statistics</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Request Settings</div>
        """, unsafe_allow_html=True)
        
        streaming_pct = (df['is_streaming'].sum() / max(len(df), 1)) * 100
        has_system_pct = (df['has_system'].sum() / max(len(df), 1)) * 100
        avg_temp = df['temperature'].dropna().mean()
        avg_max_tokens = df['max_tokens'].dropna().mean()
        
        # Handle NaN values for display
        avg_temp_display = f"{avg_temp:.2f}" if pd.notna(avg_temp) else "N/A"
        avg_max_tokens_display = f"{avg_max_tokens:,.0f}" if pd.notna(avg_max_tokens) else "N/A"
        
        st.markdown(f"""
            <div class="stat-row"><span class="stat-label">Streaming Requests</span><span class="stat-value">{streaming_pct:.1f}%</span></div>
            <div class="stat-row"><span class="stat-label">With System Prompt</span><span class="stat-value">{has_system_pct:.1f}%</span></div>
            <div class="stat-row"><span class="stat-label">Avg Temperature</span><span class="stat-value">{avg_temp_display}</span></div>
            <div class="stat-row"><span class="stat-label">Avg Max Tokens</span><span class="stat-value">{avg_max_tokens_display}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Tool Usage</div>
        """, unsafe_allow_html=True)
        
        avg_tools = df['num_tools'].mean()
        max_tools = df['num_tools'].max()
        requests_with_tools = (df['num_tools'] > 0).sum()
        tools_pct = (requests_with_tools / len(df)) * 100
        
        st.markdown(f"""
            <div class="stat-row"><span class="stat-label">Requests with Tools</span><span class="stat-value">{tools_pct:.1f}%</span></div>
            <div class="stat-row"><span class="stat-label">Avg Tools per Request</span><span class="stat-value">{avg_tools:.1f}</span></div>
            <div class="stat-row"><span class="stat-label">Max Tools in Request</span><span class="stat-value">{max_tools}</span></div>
            <div class="stat-row"><span class="stat-label">Unique Tools</span><span class="stat-value">{unique_tools}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Conversation Stats</div>
        """, unsafe_allow_html=True)
        
        avg_messages = df['num_messages'].mean() if len(df) > 0 else 0
        max_messages = df['num_messages'].max() if len(df) > 0 else 0
        avg_input = df['input_tokens'].mean() if len(df) > 0 else 0
        avg_output = df['output_tokens'].mean() if len(df) > 0 else 0
        
        st.markdown(f"""
            <div class="stat-row"><span class="stat-label">Avg Messages/Request</span><span class="stat-value">{avg_messages:.1f}</span></div>
            <div class="stat-row"><span class="stat-label">Max Messages</span><span class="stat-value">{int(max_messages)}</span></div>
            <div class="stat-row"><span class="stat-label">Avg Input Tokens</span><span class="stat-value">{avg_input:,.0f}</span></div>
            <div class="stat-row"><span class="stat-label">Avg Output Tokens</span><span class="stat-value">{avg_output:,.0f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #888899; font-size: 0.8rem; font-family: JetBrains Mono;">'
        'Built with Streamlit • Data from BigQuery/CSV • Last updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M') +
        '</p>',
        unsafe_allow_html=True
    )

def render_weekly_report_tab(df):
    """Render the weekly report tab with executive summary, usage, errors, and feedback"""
    
    st.markdown('<div class="section-title">📋 Weekly Report</div>', unsafe_allow_html=True)
    
    # Calculate week-over-week metrics
    today = datetime.now().date()
    this_week_start = today - timedelta(days=7)
    last_week_start = today - timedelta(days=14)
    
    # Filter for this week and last week
    df_this_week = df[(df['date'] >= this_week_start) & (df['date'] <= today)]
    df_last_week = df[(df['date'] >= last_week_start) & (df['date'] < this_week_start)]
    
    # Calculate metrics
    this_week_requests = len(df_this_week)
    last_week_requests = len(df_last_week)
    wow_change = ((this_week_requests - last_week_requests) / max(last_week_requests, 1)) * 100
    
    this_week_tokens = df_this_week['total_tokens'].sum()
    last_week_tokens = df_last_week['total_tokens'].sum()
    tokens_wow = ((this_week_tokens - last_week_tokens) / max(last_week_tokens, 1)) * 100
    
    # =================================================================
    # EXECUTIVE SUMMARY
    # =================================================================
    st.markdown("### 📌 Executive Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">📈 This Week vs Last Week</div>
        """, unsafe_allow_html=True)
        
        wow_class = "wow-positive" if wow_change >= 0 else "wow-negative"
        wow_arrow = "↑" if wow_change >= 0 else "↓"
        tokens_class = "wow-positive" if tokens_wow >= 0 else "wow-negative"
        tokens_arrow = "↑" if tokens_wow >= 0 else "↓"
        
        st.markdown(f"""
            <div class="stat-row">
                <span class="stat-label">Total Requests</span>
                <span class="stat-value">{this_week_requests:,} <span class="{wow_class} wow-change">{wow_arrow} {abs(wow_change):.1f}%</span></span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Token Usage</span>
                <span class="stat-value">{this_week_tokens:,} <span class="{tokens_class} wow-change">{tokens_arrow} {abs(tokens_wow):.1f}%</span></span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Last Week Requests</span>
                <span class="stat-value">{last_week_requests:,}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">⚠️ Risks & Attention Items</div>
        """, unsafe_allow_html=True)
        
        # Auto-detect potential risks
        risks = []
        if wow_change < -20:
            risks.append(("high", "Significant drop in usage (>20% WoW)"))
        elif wow_change < -10:
            risks.append(("medium", "Moderate usage decline (>10% WoW)"))
        
        if this_week_tokens > last_week_tokens * 1.5:
            risks.append(("medium", "Token usage spike (+50% WoW) - monitor costs"))
        
        if len(risks) == 0:
            st.markdown('<div class="risk-low">✅ No major risks identified this week</div>', unsafe_allow_html=True)
        else:
            for level, desc in risks:
                st.markdown(f'<div class="risk-{level}">{desc}</div>', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # =================================================================
    # USAGE & ENGAGEMENT
    # =================================================================
    st.markdown("### 📊 Usage & Engagement")
    st.caption("*Metrics from trace logs. Connect PostHog for additional user analytics.*")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">👥 Active Users</div>
        """, unsafe_allow_html=True)
        
        # Estimate unique sessions from request patterns
        unique_sessions = df_this_week['request_id'].nunique() if 'request_id' in df_this_week.columns else 0
        last_week_sessions = df_last_week['request_id'].nunique() if 'request_id' in df_last_week.columns else 0
        
        st.markdown(f"""
            <div class="stat-row">
                <span class="stat-label">Unique Sessions (This Week)</span>
                <span class="stat-value">{unique_sessions:,}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Unique Sessions (Last Week)</span>
                <span class="stat-value">{last_week_sessions:,}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Manual input for PostHog data
        st.markdown("**From PostHog (manual):**")
        active_users = st.number_input("Active Pilot Users", min_value=0, value=0, key="active_users")
    
    with col2:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">📈 Frequency of Use</div>
        """, unsafe_allow_html=True)
        
        avg_daily_requests = this_week_requests / 7 if this_week_requests > 0 else 0
        peak_day = df_this_week.groupby('date').size().idxmax() if len(df_this_week) > 0 else "N/A"
        peak_requests = df_this_week.groupby('date').size().max() if len(df_this_week) > 0 else 0
        
        st.markdown(f"""
            <div class="stat-row">
                <span class="stat-label">Avg Daily Requests</span>
                <span class="stat-value">{avg_daily_requests:.0f}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Peak Day</span>
                <span class="stat-value">{peak_day}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Peak Day Requests</span>
                <span class="stat-value">{peak_requests:,}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">🤖 AI Takeover Feature</div>
        """, unsafe_allow_html=True)
        
        # Look for browser/automation tools usage
        all_tools = [tool for tools in df_this_week['tool_names'] for tool in tools]
        automation_tools = [t for t in all_tools if 'browser' in t.lower() or 'playwright' in t.lower()]
        automation_pct = (len(automation_tools) / max(len(all_tools), 1)) * 100
        
        st.markdown(f"""
            <div class="stat-row">
                <span class="stat-label">Automation Tool Calls</span>
                <span class="stat-value">{len(automation_tools):,}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">% of All Tool Usage</span>
                <span class="stat-value">{automation_pct:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # =================================================================
    # ERRORS & SYSTEM HEALTH
    # =================================================================
    st.markdown("### 🔴 Errors & System Health")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">📉 Error Summary</div>
        """, unsafe_allow_html=True)
        
        # Look for errors in response payloads
        error_count = 0
        if 'response_payload' in df_this_week.columns:
            error_responses = df_this_week['response_payload'].astype(str).str.contains('error|Error|ERROR|exception|failed', case=False, na=False)
            error_count = error_responses.sum()
        
        error_rate = (error_count / max(this_week_requests, 1)) * 100
        
        st.markdown(f"""
            <div class="stat-row">
                <span class="stat-label">Total Errors Detected</span>
                <span class="stat-value">{error_count}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Error Rate</span>
                <span class="stat-value">{error_rate:.2f}%</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">System Uptime</span>
                <span class="stat-value">{100 - error_rate:.2f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">🚨 Incidents</div>
        """, unsafe_allow_html=True)
        
        # Manual incident input
        incident_text = st.text_area(
            "Log incidents this week",
            placeholder="• [RESOLVED] 1/15 - API timeout during peak hours\n• [ONGOING] Form submission errors on WIC portal",
            height=120,
            key="incidents"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # =================================================================
    # USER-REPORTED FEEDBACK
    # =================================================================
    st.markdown("### 💬 User-Reported Feedback")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">📧 Feedback Summary</div>
        """, unsafe_allow_html=True)
        
        issues_reported = st.number_input("Issues Reported This Week", min_value=0, value=0, key="issues_count")
        escalated = st.number_input("Escalated Issues", min_value=0, value=0, key="escalated_count")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="report-card">
            <div class="report-card-title">🔄 Top Recurring Themes</div>
        """, unsafe_allow_html=True)
        
        feedback_themes = st.text_area(
            "Top feedback themes",
            placeholder="1. Users requesting faster form completion\n2. Questions about supported benefit programs\n3. Language preference not saving",
            height=120,
            key="feedback_themes"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # =================================================================
    # EXPORT REPORT
    # =================================================================
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📄 Generate Report Summary", use_container_width=True):
            report_date = datetime.now().strftime("%Y-%m-%d")
            report = f"""
# Weekly Report - {report_date}

## Executive Summary
- **Total Requests This Week:** {this_week_requests:,} ({wow_arrow}{abs(wow_change):.1f}% WoW)
- **Token Usage:** {this_week_tokens:,} ({tokens_arrow}{abs(tokens_wow):.1f}% WoW)

## Usage & Engagement
- Active Pilot Users: {active_users}
- Unique Sessions: {unique_sessions:,}
- Avg Daily Requests: {avg_daily_requests:.0f}
- AI Takeover Tool Calls: {len(automation_tools):,}

## Errors & System Health
- Errors Detected: {error_count}
- Error Rate: {error_rate:.2f}%
- System Uptime: {100 - error_rate:.2f}%

### Incidents
{incident_text if incident_text else "No incidents logged"}

## User Feedback
- Issues Reported: {issues_reported}
- Escalated: {escalated}

### Themes
{feedback_themes if feedback_themes else "No themes recorded"}

---
Generated by Agentic AI Dashboard
            """
            st.code(report, language="markdown")
            st.download_button(
                "⬇️ Download Report",
                report,
                file_name=f"weekly_report_{report_date}.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    main()

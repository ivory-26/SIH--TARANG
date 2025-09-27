import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.graph_objects as go
import streamlit.components.v1 as components
import time
import json
import os
from datetime import datetime
import re

# Base directory and file paths
BASE_DIR = os.path.dirname(__file__)
SAMPLE_PATH = os.path.join(BASE_DIR, "static", "sample_data.json")
CESIUM_MAP_PATH = os.path.join(BASE_DIR, "components", "cesium_map.html")

# Try load SVG icon for header embellishment and strip XML prolog (prevents raw code rendering)
APP_ICON_SVG = ""
try:
    with open(os.path.join(BASE_DIR, "static", "app_icon.svg"), "r", encoding="utf-8") as _svgf:
        _raw_svg = _svgf.read()
        # Remove XML declaration if present
        APP_ICON_SVG = re.sub(r"<\?xml[^>]*?>", "", _raw_svg).strip()
except Exception:
    APP_ICON_SVG = ""

# Set page config
st.set_page_config(
    page_title="Argo Float Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load sample data
def load_samples():
    try:
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"responses": {}, "samples": []}

def simulate_query(text: str):
    """Simulate API response for demo purposes"""
    sample_responses = SAMPLE.get("responses", {})
    
    # Find best matching response
    for key, response in sample_responses.items():
        if any(word.lower() in text.lower() for word in key.split()):
            return response
    
    # Default response
    return {
        "response": f"Based on your query about '{text}', here's what I found from the Argo float data: This appears to be related to oceanographic measurements. The data shows various parameters like temperature, salinity, and pressure measurements from autonomous Argo floats deployed across different ocean regions.",
        "data_summary": "Sample oceanographic data analysis",
        "relevant_floats": ["5906334", "5906335", "5906336"]
    }

def get_sample_queries():
    """Get sample queries from JSON file"""
    return SAMPLE.get("samples", [
        "Show me temperature profiles for the Arabian Sea",
        "What's the salinity distribution in the Indian Ocean?",
        "Display pressure measurements from recent Argo floats",
        "Compare temperature variations across different depths"
    ])

SAMPLE = load_samples()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "local_session"
if "user_name" not in st.session_state:
    st.session_state.user_name = "Guest"
if "map_selection" not in st.session_state:
    st.session_state.map_selection = None
if "selected_marker" not in st.session_state:
    st.session_state.selected_marker = None
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False
if "sessions" not in st.session_state:
    st.session_state.sessions = []  # list of {id, timestamp, config, source, reason, response_text, plot, data}
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = str(int(time.time()*1000))
if "_committed_session_ids" not in st.session_state:
    st.session_state._committed_session_ids = set()

# --- Session Lifecycle Helpers ---
def start_new_session(reason: str = "user-action"):
    """Begin a fresh logical session. Does NOT remove existing committed visualizations
    but clears any in-progress configuration (map_selection, selected_marker, dialog)."""
    st.session_state.active_session_id = str(int(time.time()*1000))
    st.session_state.selected_marker = None
    st.session_state.show_dialog = False
    st.session_state.map_selection = None
    st.session_state.current_session_reason = reason

def commit_visualization(config: dict, resp: dict | None = None):
    """Persist the visualization config & response details to session history and
    start a new session. Also schedules clearing of visual area on next rerun."""
    sid = config.get("session_id") or st.session_state.active_session_id
    if sid in st.session_state._committed_session_ids:
        return
    record = {
        "id": sid,
        "timestamp": datetime.utcnow().isoformat(),
        "config": config,
        "source": config.get("source", "manual"),
        "reason": st.session_state.get("current_session_reason", "unknown"),
        "response_text": resp.get("text") if resp else None,
        "plot": resp.get("plot") if resp else None,
        "data": resp.get("data") if resp else None,
    }
    st.session_state.sessions.append(record)
    st.session_state._committed_session_ids.add(sid)
    # Prepare next session id
    st.session_state.active_session_id = str(int(time.time()*1000))
    # Schedule clearing of visual section after rerun
    st.session_state.clear_after_commit = True

# Process deferred clearing of visual area if flagged
if st.session_state.get("clear_after_commit"):
    # Clear only if not viewing a specific session
    if not st.session_state.get("view_session_id"):
        st.session_state.map_selection = None
    st.session_state.clear_after_commit = False

# Sidebar session navigation (left side bar)
with st.sidebar:
    st.header("Sessions")
    if st.session_state.sessions:
        for s in reversed(st.session_state.sessions[-50:]):
            cfg = s["config"]
            label = cfg.get("query") or f"{cfg.get('parameter','?')} {cfg.get('graphType','?')}"\
                f" ({cfg.get('xAxis','?')} vs {cfg.get('yAxis','?')})"
            if st.button(label, key=f"sessnav_{s['id']}"):
                st.session_state.view_session_id = s['id']
                st.rerun()
    else:
        st.caption("No sessions yet")
    if st.session_state.get("view_session_id"):
        if st.button("⬅️ Back to Explorer", key="back_explorer"):
            st.session_state.view_session_id = None
            st.rerun()

# Dedicated session view page
if st.session_state.get("view_session_id"):
    sid = st.session_state.view_session_id
    session_obj = next((s for s in st.session_state.sessions if s["id"] == sid), None)
    st.title("📄 Session Detail")
    if session_obj:
        cfg = session_obj["config"]
        st.markdown(f"**Session ID:** {sid}")
        st.markdown(f"**Timestamp (UTC):** {session_obj['timestamp']}")
        if cfg.get("query"):
            st.markdown(f"**Query:** {cfg['query']}")
        st.markdown(f"**Visualization:** {cfg.get('parameter','?').title()} {cfg.get('graphType','?').title()} — {cfg.get('floatName','')} ({cfg.get('xAxis')} vs {cfg.get('yAxis')})")
        if session_obj.get("response_text"):
            st.info(session_obj.get("response_text"))
        plot_dict = session_obj.get("plot")
        if plot_dict:
            fig = go.Figure()
            gtype = plot_dict.get("graph_type", "line")
            if gtype == "scatter":
                fig.add_trace(go.Scatter(x=plot_dict.get("x", []), y=plot_dict.get("y", []), mode="markers"))
            elif gtype == "profile":
                fig.add_trace(go.Scatter(x=plot_dict.get("x", []), y=plot_dict.get("y", []), mode="lines+markers"))
                if plot_dict.get("reverse_y"):
                    fig.update_yaxes(autorange="reversed")
            else:
                fig.add_trace(go.Scatter(x=plot_dict.get("x", []), y=plot_dict.get("y", []), mode="lines+markers"))
            fig.update_xaxes(title=plot_dict.get("x_label", "X"))
            fig.update_yaxes(title=plot_dict.get("y_label", "Y"))
            fig.update_layout(height=500, title="Stored Visualization")
            st.plotly_chart(fig, use_container_width=True)
        if session_obj.get("data"):
            with st.expander("Raw Data JSON"):
                st.json(session_obj.get("data"))
    else:
        st.error("Session not found")
    st.stop()


# Polished UI styles (reduced emoji reliance)
st.markdown("""
<style>
.stApp {max-width:1500px; margin:0 auto; font-family:'Inter',system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,'Open Sans','Helvetica Neue',sans-serif;}
h1,h2,h3,h4 {font-weight:600; letter-spacing:.4px;}
h1 {font-size:2.15rem;}
h2 {font-size:1.55rem; margin-top:1.8rem;}
h3 {font-size:1.25rem; margin-top:1.4rem;}
p,.stMarkdown {line-height:1.48;}
.float-info-card {background:linear-gradient(145deg,#1e2530,#15202b)!important; border:1px solid #243441!important; border-radius:14px; padding:14px 18px; backdrop-filter:blur(4px); transition:border-color .25s ease, transform .25s ease;}
.float-info-card:hover {border-color:#3b82f6; transform:translateY(-2px);} 
.info-row {display:flex; justify-content:space-between; padding:6px 4px; border-bottom:1px solid #243241; font-size:.82rem;}
.info-row:last-of-type {border-bottom:none;}
.info-label {color:#94a3b8; font-weight:500;}
.info-value {color:#f1f5f9; font-weight:500; letter-spacing:.3px;}
div[data-testid="stForm"] {background:rgba(17,25,36,0.65)!important; border:1px solid #22303d; border-radius:16px; padding:1.2rem 1.2rem .85rem!important; box-shadow:0 4px 22px -4px rgba(0,0,0,.35);} 
div[data-testid="stForm"] label {font-size:.78rem; text-transform:uppercase; letter-spacing:.6px; font-weight:600; color:#e2e8f0 !important;}
div[data-testid="stForm"] div[data-baseweb] {background:#0f1720!important; border-radius:10px; border:1px solid #283847;}
div[data-testid="stForm"] div[data-baseweb]:focus-within {outline:2px solid #3b82f6;}
button[kind="primary"], .stButton > button {transition:background .25s, transform .18s, box-shadow .25s; font-weight:600; letter-spacing:.4px; border-radius:10px !important;}
.stButton > button:hover {transform:translateY(-2px); box-shadow:0 8px 18px -6px rgba(0,0,0,.45);} 
.stButton > button:active {transform:translateY(0);}
.copilot-wrapper {background:transparent; border:0; border-radius:16px; padding:4px 2px 12px;} 
.chat-messages {background:rgba(15,23,32,0.55)!important; border:1px solid #243240!important; border-radius:12px;}
.chat-messages .stMarkdown {font-size:.82rem;}
div[data-testid="stChatInput"] textarea {font-size:.85rem !important;}
hr, div.block-container > div:has(> hr) {border-color:#20303d !important;}
.stDownloadButton > button {border-radius:10px !important; font-size:.78rem; text-transform:uppercase; letter-spacing:.9px; font-weight:600;}
.app-title-wrapper {display:flex; align-items:center; gap:.9rem; margin-bottom:.35rem;}
.app-title-wrapper svg, .app-title-wrapper img.app-icon {width:64px; height:64px; border-radius:14px; box-shadow:0 6px 16px -4px rgba(0,0,0,.55);} 
@media (max-width:850px){ .app-title-wrapper svg, .app-title-wrapper img.app-icon {width:48px; height:48px;} h1 {font-size:1.85rem;} }
.subtitle {margin-top:.15rem; color:#94a3b8; font-size:.92rem;}
@media (max-width:1100px){ .copilot-wrapper {position:relative;} }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_parameter_unit(parameter):
    """Get the unit for a given parameter"""
    units = {
        "temperature": "°C",
        "salinity": "PSU",
        "pressure": "dbar",
        "oxygen": "μmol/kg"
    }
    return units.get(parameter, "")

def get_axis_label(axis, parameter=None):
    """Get appropriate axis label with units"""
    if axis == "depth":
        return "Depth (m)"
    elif axis == "time":
        return "Time"
    elif axis == "cycle":
        return "Cycle Number"
    elif axis == "parameter":
        if parameter == "temperature":
            return f"Temperature ({get_parameter_unit('temperature')})"
        elif parameter == "salinity":
            return f"Salinity ({get_parameter_unit('salinity')})"
        elif parameter == "pressure":
            return f"Pressure ({get_parameter_unit('pressure')})"
        elif parameter == "oxygen":
            return f"Oxygen ({get_parameter_unit('oxygen')})"
        else:
            return parameter.title() if parameter else "Parameter"
    else:
        return axis.title() if axis else "Axis"

def create_3d_cesium_map():
    """Create a 3D Cesium map with Argo floats.""" 
    st.subheader("3D Cesium Interactive Map")
    
    # Display the Cesium map using HTML component
    cesium_html_path = os.path.join(BASE_DIR, "components", "cesium_map.html")
    
    try:
        if os.path.exists(cesium_html_path):
            with open(cesium_html_path, 'r', encoding='utf-8') as f:
                cesium_html = f.read()
            
            # Display the HTML component
            components.html(cesium_html, height=450, scrolling=False)
            
            # Instructions
            col1, col2 = st.columns(2)
            with col1:
                st.info("**3D Map Controls:**\n- Click and drag to rotate\n- Mouse wheel to zoom\n- Single click to select float\n- Double click to configure visualization")
            with col2:
                st.success("**Float Interaction:**\n- Blue markers = Active floats\n- Gray markers = Inactive floats\n- Detailed info panel appears on selection")
        else:
            st.error(f"Cesium map file not found at: {cesium_html_path}")
            st.info("Please ensure the cesium_map.html file exists in the components directory.")
            st.info("Tip: Switch to 2D Plotly map for full functionality.")
            
    except Exception as e:
        st.error(f"Failed to load 3D map: {str(e)}")
        st.info("Switch to 2D Plotly map for full functionality.")

def generate_synthetic_data(parameter, x_axis, y_axis):
    """Generate synthetic data when real data is not available."""
    np.random.seed(42)  # for reproducible results
    
    if x_axis == "depth" or y_axis == "depth":
        depths = np.linspace(0, 2000, 20)
        if parameter == "temperature":
            values = 25 * np.exp(-depths/500) + 2 + np.random.normal(0, 0.5, len(depths))
        elif parameter == "salinity":
            values = 35.0 - 0.6 * (depths/2000) + np.random.normal(0, 0.1, len(depths))
        elif parameter == "pressure":
            values = depths * 0.98 + np.random.normal(0, 5, len(depths))
        else:  # oxygen
            values = 300 * np.exp(-depths/200) + 50 + np.random.normal(0, 5, len(depths))
            
        # For profile, x is parameter, y is depth
        if x_axis == "parameter" and y_axis == "depth":
            return {"x": values.tolist(), "y": depths.tolist()}
        else:  # depth is x-axis
            return {"x": depths.tolist(), "y": values.tolist()}
            
    elif x_axis == "time" or y_axis == "time":
        # Create 30 days of data
        dates = [datetime(2023, 1, 1) + pd.Timedelta(days=i) for i in range(30)]
        times = [d.timestamp() * 1000 for d in dates]  # milliseconds for JS
        
        if parameter == "temperature":
            values = 24 + 2 * np.sin(np.linspace(0, 2*np.pi, 30)) + np.random.normal(0, 0.3, 30)
        elif parameter == "salinity":
            values = 35.2 + 0.3 * np.sin(np.linspace(0, 4*np.pi, 30)) + np.random.normal(0, 0.05, 30)
        elif parameter == "pressure":
            values = 100 + 20 * np.sin(np.linspace(0, 2*np.pi, 30)) + np.random.normal(0, 2, 30)
        else:  # oxygen
            values = 250 + 30 * np.sin(np.linspace(0, 2*np.pi, 30)) + np.random.normal(0, 8, 30)
        
        if x_axis == "time":
            return {"x": times, "y": values.tolist()}
        else:
            return {"x": values.tolist(), "y": times}
    
    elif x_axis == "cycle" or y_axis == "cycle":
        # Create 20 cycles of data
        cycles = list(range(1, 21))
        
        if parameter == "temperature":
            values = 24 + 0.1 * np.array(cycles) + np.random.normal(0, 0.5, 20)
        elif parameter == "salinity":
            values = 35.2 + 0.02 * np.array(cycles) + np.random.normal(0, 0.1, 20)
        elif parameter == "pressure":
            values = 100 + 5 * np.array(cycles) + np.random.normal(0, 10, 20)
        else:  # oxygen
            values = 250 - 2 * np.array(cycles) + np.random.normal(0, 15, 20)
            
        if x_axis == "cycle":
            return {"x": cycles, "y": values.tolist()}
        else:
            return {"x": values.tolist(), "y": cycles}
    
    # Fallback
    return {"x": list(range(10)), "y": list(range(10))}

def generate_argo_graph(config):
    """Generate graph based on Argo float configuration."""
    float_id = config.get("floatId")
    parameter = config.get("parameter")
    graph_type = config.get("graphType")
    x_axis = config.get("xAxis")
    y_axis = config.get("yAxis")
    
    # Get data from sample data
    # In a real app, this would fetch from an API or database
    
    # Placeholder for parameter data
    param_data = {}
    
    # Determine data source based on axes
    data_source = None
    if x_axis == "time" or y_axis == "time":
        data_source = param_data.get("time_series")
    elif x_axis == "depth" or y_axis == "depth":
        data_source = param_data.get("depth_profile")
    elif x_axis == "cycle" or y_axis == "cycle":
        data_source = param_data.get("cycle_data")
    else:
        data_source = param_data.get("depth_profile")  # default
    
    if not data_source:
        # Generate synthetic data
        data_source = generate_synthetic_data(parameter, x_axis, y_axis)
    
    # Prepare plot data
    plot_data = {
        "x": data_source.get("x", []),
        "y": data_source.get("y", []),
        "x_label": get_axis_label(x_axis, parameter),
        "y_label": get_axis_label(y_axis, parameter),
        "reverse_y": y_axis == "depth",
        "graph_type": graph_type
    }
    
    response_text = f"Generated {graph_type} visualization for {parameter} from {config.get('floatName', float_id)} (Position: {config.get('latitude', 0):.2f}°N, {config.get('longitude', 0):.2f}°E)"
    
    return {
        "text": response_text,
        "data": {
            "float_id": float_id,
            "parameter": parameter,
            "graph_type": graph_type,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "position": f"{config.get('latitude', 0):.2f}°N, {config.get('longitude', 0):.2f}°E"
        },
        "plot": plot_data
    }

def show_parameter_dialog(float_data):
    """Parameter selection dialog for a selected float."""
    
    # Float information card
    st.markdown('<div class="float-info-card">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="info-row">
        <span class="info-label">Name</span>
        <span class="info-value">{float_data['name']}</span>
    </div>
    <div class="info-row">
        <span class="info-label">ID</span>
        <span class="info-value">{float_data['id']}</span>
    </div>
    <div class="info-row">
        <span class="info-label">Location</span>
        <span class="info-value">{float_data['latitude']:.3f}°N, {float_data['longitude']:.3f}°E</span>
    </div>
    <div class="info-row">
        <span class="info-label">Temperature</span>
        <span class="info-value">{float_data['temperature']}°C</span>
    </div>
    <div class="info-row">
        <span class="info-label">Status</span>
        <span class="info-value">{float_data['status']}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Parameter selection form
    with st.form("parameter_form", clear_on_submit=False):
        st.markdown("### Visualization Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            parameter = st.selectbox(
                "Parameter",
                ["temperature", "salinity", "pressure", "oxygen"],
                help="Choose the oceanographic parameter to visualize",
                format_func=lambda x: f"{x.title()} ({get_parameter_unit(x)})"
            )
        
        with col2:
            graph_type = st.selectbox(
                "Graph Type:",
                ["profile", "line", "scatter"],
                help="Select the visualization style",
                format_func=lambda x: f"🌊 Depth Profile" if x == "profile" else f"📈 Line Plot" if x == "line" else f"⚪ Scatter Plot"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            if graph_type == "profile":
                x_axis = st.selectbox("X-Axis:", ["parameter"], disabled=True, help="Fixed for depth profiles")
            else:
                x_axis = st.selectbox("X-Axis:", ["time", "depth", "cycle", "parameter"])
        
        with col4:
            if graph_type == "profile":
                y_axis = st.selectbox("Y-Axis:", ["depth"], disabled=True, help="Fixed for depth profiles")
            else:
                y_axis = st.selectbox("Y-Axis:", ["parameter", "depth", "time", "cycle"])
        
        # Submit button with enhanced styling
        submitted = st.form_submit_button("Generate Visualization", type="primary", use_container_width=True)
        
        if submitted:
            config = {
                "floatId": float_data['id'],
                "floatName": float_data['name'],
                "parameter": parameter,
                "graphType": graph_type,
                "xAxis": x_axis,
                "yAxis": y_axis,
                "latitude": float_data['latitude'],
                "longitude": float_data['longitude'],
                "source": "manual",
                "session_id": st.session_state.active_session_id
            }
            
            # Store selection and close dialog
            st.session_state.map_selection = config
            st.session_state.show_dialog = False
            st.session_state.selected_marker = None
            st.success(f"Generating {parameter} {graph_type} for {float_data['name']}...")
            time.sleep(0.5)  # Brief pause for user feedback
            st.rerun()

# Define sample Argo float data
argo_floats = [
    {"id": "ARGO_001", "name": "Float 001", "latitude": 20.5, "longitude": 65.2, "status": "Active", "cycles": 45, "temperature": 24.5},
    {"id": "ARGO_002", "name": "Float 002", "latitude": 18.7, "longitude": 67.8, "status": "Active", "cycles": 32, "temperature": 25.1},
    {"id": "ARGO_003", "name": "Float 003", "latitude": 22.1, "longitude": 63.5, "status": "Inactive", "cycles": 28, "temperature": 23.8},
    {"id": "ARGO_004", "name": "Float 004", "latitude": 19.3, "longitude": 69.1, "status": "Active", "cycles": 51, "temperature": 24.9},
    {"id": "ARGO_005", "name": "Float 005", "latitude": 21.8, "longitude": 64.7, "status": "Active", "cycles": 39, "temperature": 24.3}
]

# --- Query -> Visualization Config Heuristic ---
def parse_query_to_config(query: str):
    """Heuristically map a natural language query to a visualization config.
    Returns a config dict or None if no reasonable mapping found."""
    if not query:
        return None
    q = query.lower()

    # Detect parameter
    param_map = ["temperature", "salinity", "pressure", "oxygen"]
    parameter = next((p for p in param_map if p in q), None) or "temperature"

    # Detect graph intent
    if any(w in q for w in ["profile", "depth", "vertical"]):
        graph_type = "profile"
        x_axis, y_axis = "parameter", "depth"
    elif any(w in q for w in ["time", "trend", "daily", "over time", "temporal"]):
        graph_type = "line"
        x_axis, y_axis = "time", "parameter"
    elif "cycle" in q:
        graph_type = "line"
        x_axis, y_axis = "cycle", "parameter"
    elif any(w in q for w in ["compare", "correl", "relation", "scatter"]):
        graph_type = "scatter"
        # Use parameter vs depth by default
        x_axis, y_axis = "parameter", "depth"
    else:
        # Default generic line/time if unspecified
        graph_type = "line"
        x_axis, y_axis = "time", "parameter"

    # Detect specific float ID if mentioned
    float_id_match = re.search(r"ARGO_\d+", query, re.IGNORECASE)
    float_record = None
    if float_id_match:
        fid = float_id_match.group(0).upper()
        float_record = next((f for f in argo_floats if f["id"] == fid), None)
    # Fallback: currently selected marker
    if not float_record and st.session_state.get("selected_marker"):
        float_record = st.session_state.selected_marker
    # Fallback: first active float else first
    if not float_record:
        float_record = next((f for f in argo_floats if f["status"] == "Active"), argo_floats[0])

    config = {
        "floatId": float_record["id"],
        "floatName": float_record["name"],
        "parameter": parameter,
        "graphType": graph_type,
        "xAxis": x_axis,
        "yAxis": y_axis,
        "latitude": float_record["latitude"],
        "longitude": float_record["longitude"],
        "source": "chat"
    }
    return config

# --- Map rendering helper functions ---
def render_2d_interactive_map(argo_floats):
    """Render 2D interactive Plotly map centered on page; selection handled here, parameter UI elsewhere."""
    fig = go.Figure()
    active_floats = [f for f in argo_floats if f["status"] == "Active"]
    if active_floats:
        fig.add_trace(go.Scattermapbox(
            lat=[f["latitude"] for f in active_floats],
            lon=[f["longitude"] for f in active_floats],
            mode='markers',
            marker=dict(size=15, color='blue', opacity=0.8),
            text=[f"{f['name']} ({f['id']})<br>Status: {f['status']}<br>Temp: {f['temperature']}°C" for f in active_floats],
            name="Active Floats",
            hovertemplate='<b>%{text}</b><br>Click to configure<extra></extra>'
        ))
    inactive_floats = [f for f in argo_floats if f["status"] == "Inactive"]
    if inactive_floats:
        fig.add_trace(go.Scattermapbox(
            lat=[f["latitude"] for f in inactive_floats],
            lon=[f["longitude"] for f in inactive_floats],
            mode='markers',
            marker=dict(size=15, color='gray', opacity=0.6),
            text=[f"{f['name']} ({f['id']})<br>Status: {f['status']}<br>Temp: {f['temperature']}°C" for f in inactive_floats],
            name="Inactive Floats",
            hovertemplate='<b>%{text}</b><br>Click to configure<extra></extra>'
        ))
    fig.update_layout(
        mapbox=dict(style="open-street-map", center=dict(lat=20.0, lon=66.0), zoom=5),
        height=520,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    plotly_events = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
    if plotly_events and 'selection' in plotly_events and plotly_events['selection']['points']:
        selected_point = plotly_events['selection']['points'][0]
        point_index = selected_point.get('pointIndex', 0)
        curve_number = selected_point.get('curveNumber', 0)
        if curve_number == 0 and point_index < len(active_floats):
            selected_float = active_floats[point_index]
        elif curve_number == 1 and point_index < len(inactive_floats):
            selected_float = inactive_floats[point_index]
        else:
            selected_float = argo_floats[0]
        # New marker selection: start fresh session & clear prior visualization
        start_new_session("marker-selected")
        st.session_state.selected_marker = selected_float
        st.session_state.show_dialog = True
        st.rerun()

def render_3d_pydeck_map(argo_floats):
    """Render 3D PyDeck map and allow clicking a column / point to open parameter dialog."""
    df = pd.DataFrame(argo_floats)
    df["color"] = df["status"].apply(lambda s: [0, 0, 255, 200] if s == "Active" else [128, 128, 128, 160])
    df["elevation"] = df["temperature"] * 100
    column_layer = pdk.Layer(
        "ColumnLayer", data=df, get_position=["longitude", "latitude"], get_elevation="elevation", elevation_scale=1,
        radius=10000, get_fill_color="color", pickable=True, auto_highlight=True, extruded=True,
    )
    scatter_layer = pdk.Layer(
        "ScatterplotLayer", data=df, get_position=["longitude", "latitude"], get_color="color", get_radius=7000, pickable=True,
    )
    text_layer = pdk.Layer(
        "TextLayer", data=df, get_position=["longitude", "latitude"], get_text="name", get_size=16,
        get_color=[255, 255, 255, 255], get_pixel_offset=[0, -20], pickable=True
    )
    view_state = pdk.ViewState(longitude=66.0, latitude=20.0, zoom=5, pitch=45, bearing=0, height=520)
    r = pdk.Deck(
        layers=[column_layer, scatter_layer, text_layer],
        initial_view_state=view_state,
        map_style="light",
        tooltip=True,
    )
    clicked = st.pydeck_chart(r, use_container_width=True)
    # PyDeck doesn't give direct click callbacks in Streamlit; workaround: offer a selection dropdown below as fallback
    with st.expander("Select Float (3D interaction fallback)", expanded=False):
        choice = st.selectbox("Choose a float to configure", [f"{f['name']} ({f['id']})" for f in argo_floats], key="pydeck_select")
        if st.button("Configure Selected Float", key="pydeck_select_btn"):
            idx = [f"{f['name']} ({f['id']})" for f in argo_floats].index(choice)
            start_new_session("marker-selected-3d")
            st.session_state.selected_marker = argo_floats[idx]
            st.session_state.show_dialog = True
            st.rerun()

# --- Application Header (resilient icon handling) ---
# If user added a PNG (e.g. static/app_icon.png), prefer that; else use inline SVG if loaded; else just text.
png_icon_path = os.path.join(BASE_DIR, "static", "app_icon.png")
icon_markup = ""
if os.path.exists(png_icon_path):
    # Use base64 to embed so it survives reruns and remote hosting
    import base64
    try:
        with open(png_icon_path, "rb") as _pf:
            b64png = base64.b64encode(_pf.read()).decode("utf-8")
        icon_markup = f"<img class='app-icon' src='data:image/png;base64,{b64png}' alt='App Icon' />"
    except Exception:
        icon_markup = ""
elif APP_ICON_SVG:
    # Sanitize width/height inline if missing
    svg_tag = APP_ICON_SVG
    if '<svg' in svg_tag and 'width' not in svg_tag:
        svg_tag = svg_tag.replace('<svg', '<svg width="48" height="48"')
    icon_markup = svg_tag

st.markdown(
    f"""
    <div class='app-title-wrapper'>
        {icon_markup}
        <div>
            <h1 style='margin-bottom:0.25rem;'>FloatChat</h1>
            <div class='subtitle'>Interactive dashboard for exploring Argo float observations in the Arabian Sea</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize collapse state
if "copilot_open" not in st.session_state:
    st.session_state.copilot_open = True

if st.session_state.copilot_open:
    # When copilot is open allocate space for future expansion (empty param column placeholder)
    map_col, chat_col = st.columns([3.5, 1.5])
else:
    map_col = st.container()
    chat_col = None

with map_col:
    header_cols = st.columns([0.8, 0.2])
    with header_cols[0]:
        st.subheader("Argo Float Map")
    with header_cols[1]:
        toggle_label = "Hide Chat" if st.session_state.copilot_open else "Show Chat"
        st.markdown("<div style='display:flex; justify-content:flex-end; align-items:center; margin-top:4px;'>", unsafe_allow_html=True)
        if st.button(toggle_label, key="toggle_copilot"):
            st.session_state.copilot_open = not st.session_state.copilot_open
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    # Restore original explicit labels; keep backward compatibility with earlier ad-hoc edits ("3D", "3D World Map")
    map_type = st.radio(
        "Map Type",
        ["2D Interactive", "3D PyDeck", "3D Cesium"],
        horizontal=True,
        key="map_type_radio"
    )

    # Normalize to handle legacy / user edited labels
    mt_lower = map_type.lower()
    if map_type == "2D Interactive":
        render_2d_interactive_map(argo_floats)
    elif ("pydeck" in mt_lower) or map_type in {"3D", "PyDeck"}:
        render_3d_pydeck_map(argo_floats)
    elif ("cesium" in mt_lower) or ("world" in mt_lower) or map_type in {"3D World Map", "World Map"}:
        create_3d_cesium_map()
    else:
        # Fallback: default to 2D so the UI isn't blank
        render_2d_interactive_map(argo_floats)

# Parameter section appears only when a marker is selected (no placeholder otherwise)
if st.session_state.show_dialog and st.session_state.selected_marker:
    st.subheader("Configure Visualization Parameters")
    show_parameter_dialog(st.session_state.selected_marker)

if chat_col is not None:
    with chat_col:
        # Full-height sticky styled container
        st.markdown(
            """
            <style>
            .copilot-wrapper {position: sticky; top: 0; max-height: 100vh; overflow-y: auto; padding-right:6px;}
            .copilot-section-title {margin-top:0.2rem;}
            .copilot-queries button {width:100%; text-align:left;}
            .chat-messages {border:1px solid #e5e5e5; border-radius:8px; padding:0.5rem; background:#fafafa; max-height:48vh; overflow-y:auto;}
            .chat-messages::-webkit-scrollbar {width:8px;} .chat-messages::-webkit-scrollbar-track {background:transparent;} .chat-messages::-webkit-scrollbar-thumb {background:#c1c1c1; border-radius:4px;}
            </style>
            <div class='copilot-wrapper'>
            """,
            unsafe_allow_html=True,
        )
        st.header("Assistant", anchor=False)
        st.markdown("<h4 class='copilot-section-title'>Quick Queries</h4>", unsafe_allow_html=True)
        sample_queries = get_sample_queries()
        for i, query in enumerate(sample_queries):
            if st.button(query, key=f"sample_{i}"):
                start_new_session("sample-query")
                st.session_state.messages.append({"role": "user", "content": query})
                response = simulate_query(query)
                st.session_state.messages.append({"role": "assistant", "content": response["response"]})
                cfg = parse_query_to_config(query)
                if cfg:
                    cfg["query"] = query
                    cfg["session_id"] = st.session_state.active_session_id
                    st.session_state.map_selection = cfg
                st.rerun()
        st.markdown("---")
        st.markdown("<h4 class='copilot-section-title'>Chat</h4>", unsafe_allow_html=True)
        chat_container_html = st.container()
        with chat_container_html:
            st.markdown("<div class='chat-messages'>", unsafe_allow_html=True)
            for message in st.session_state.messages[-80:]:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            st.markdown("</div>", unsafe_allow_html=True)
        prompt = st.chat_input("Ask or request a visualization...", key="chat_prompt")
        if prompt:
            start_new_session("chat-query")
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking & charting..."):
                    response = simulate_query(prompt)
                    st.markdown(response["response"])
                    st.session_state.messages.append({"role": "assistant", "content": response["response"]})
                    cfg = parse_query_to_config(prompt)
                    if cfg:
                        cfg["query"] = prompt
                        cfg["session_id"] = st.session_state.active_session_id
                        st.session_state.map_selection = cfg
                        st.session_state.show_dialog = False
                        st.session_state.selected_marker = None
            st.rerun()
        st.caption("Panel scrolls independently. Collapse for a wider canvas.")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("Visualizations & Outputs")

# Check if there's a graph to display
if st.session_state.map_selection is not None:
    config = st.session_state.map_selection
    
    # Generate the graph using the configuration
    resp = generate_argo_graph(config)
    
    # Display visualization header
    st.header(f"Visualization: {config.get('parameter', '').title()} {config.get('graphType', '').title()} - {config.get('floatName', '')}")
    
    # Display graph configuration
    st.markdown(f"**Configuration:** {config.get('parameter', '')} - {config.get('graphType', '')} ({config.get('xAxis', '')} vs {config.get('yAxis', '')})")
    
    # Show the plot if available
    if resp.get("plot"):
        p = resp.get("plot")
        if p and isinstance(p, dict):
            fig = go.Figure()
            
            graph_type = p.get("graph_type", "line")
            if graph_type == "scatter":
                fig.add_trace(go.Scatter(x=p.get("x", []), y=p.get("y", []), mode="markers", marker=dict(size=8)))
            elif graph_type == "profile":
                fig.add_trace(go.Scatter(x=p.get("x", []), y=p.get("y", []), mode="lines+markers", line=dict(width=3)))
            else:  # line plot
                fig.add_trace(go.Scatter(x=p.get("x", []), y=p.get("y", []), mode="lines+markers"))
            
            if p.get("reverse_y"):
                fig.update_yaxes(autorange="reversed")
            
            fig.update_xaxes(title=p.get("x_label", "X-Axis"))
            fig.update_yaxes(title=p.get("y_label", "Y-Axis"))
        fig.update_layout(
            title=f"Argo Float Data Visualization ({graph_type.title()} Plot)",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        # Commit this visualization to session history (once)
        config.setdefault("session_id", st.session_state.active_session_id)
        commit_visualization(config, resp)

        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "Download Data (JSON)", 
                data=json.dumps(resp.get("data", {}), indent=2), 
                file_name=f"argo_{config.get('floatId', 'data')}_{config.get('parameter', 'param')}.json", 
                mime="application/json"
            )
        with col2:
            if p and isinstance(p, dict):
                st.download_button(
                    "Download Plot Data (CSV)", 
                    data=pd.DataFrame({
                        p.get("x_label", "x"): p.get("x", []),
                        p.get("y_label", "y"): p.get("y", [])
                    }).to_csv(index=False), 
                    file_name=f"argo_{config.get('floatId', 'data')}_{config.get('parameter', 'param')}.csv", 
                    mime="text/csv"
                )
else:
    pass  # No placeholder message; map itself is interactive

# Session history panel
if st.session_state.get("sessions"):
    with st.expander("Session History", expanded=False):
        for s in reversed(st.session_state.sessions[-20:]):
            cfg = s["config"]
            st.markdown(f"**Session {s['id']}** · {s['timestamp']} · {cfg.get('parameter','?')} {cfg.get('graphType','?')} ({cfg.get('xAxis')} vs {cfg.get('yAxis')}) · Source: {cfg.get('source','?')}" )

# Footer
st.markdown("---")
st.caption("This is a Streamlit prototype that uses synthetic data. Click on any marker in the map to configure and generate visualizations.")
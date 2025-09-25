import streamlit as st
import json
import os
import time
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import datetime
import numpy as np
import pandas as pd
import pydeck as pdk

BASE_DIR = os.path.dirname(__file__)
SAMPLE_PATH = os.path.join(BASE_DIR, "static", "sample_data.json")
CESIUM_MAP_PATH = os.path.join(BASE_DIR, "components", "cesium_map.html")

def load_samples():
    try:
        with open(SAMPLE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"responses": {}, "samples": []}

SAMPLE = load_samples()

st.set_page_config(page_title="Float-Chat-AI (Static)", layout="wide")

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
if "show_map" not in st.session_state:
    st.session_state.show_map = True
if "selected_marker" not in st.session_state:
    st.session_state.selected_marker = None
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False
if "dialog_config" not in st.session_state:
    st.session_state.dialog_config = {}

def simulate_query(text: str):
    """Return a canned response from SAMPLE based on naive keyword matching."""
    time.sleep(0.5)  # mimic latency
    key = None
    t = text.lower()
    if "temperature" in t and "1000" in t:
        key = "avg_temp"
    elif "salinity" in t:
        key = "salinity_profile"
    elif "maximum" in t or "max" in t:
        key = "max_temp"
    else:
        # try exact sample matching
        for s in SAMPLE.get("samples", []):
            if s.lower() in t:
                # pick first matching response key
                key = list(SAMPLE.get("responses", {}).keys())[0] if SAMPLE.get("responses") else None
                break

    if key and key in SAMPLE.get("responses", {}):
        return SAMPLE["responses"][key]

    return {"text": "No canned response found. Try a sample query from the sidebar.", "data": None}

def create_pydeck_argo_map():
    """Create a 3D PyDeck map with Argo floats following streamlit-geospatial patterns."""
    # Sample Argo float data in Arabian Sea region
    argo_floats = [
        {"id": "ARGO_001", "name": "Float 001", "lat": 20.5, "lon": 65.2, "status": "Active", "temperature": 24.5, "elevation": 1000},
        {"id": "ARGO_002", "name": "Float 002", "lat": 18.7, "lon": 67.8, "status": "Active", "temperature": 25.1, "elevation": 800},
        {"id": "ARGO_003", "name": "Float 003", "lat": 22.1, "lon": 63.5, "status": "Inactive", "temperature": 23.8, "elevation": 600},
        {"id": "ARGO_004", "name": "Float 004", "lat": 19.3, "lon": 69.1, "status": "Active", "temperature": 24.9, "elevation": 1200},
        {"id": "ARGO_005", "name": "Float 005", "lat": 21.8, "lon": 64.7, "status": "Active", "temperature": 24.3, "elevation": 900}
    ]
    
    # Convert to DataFrame
    df = pd.DataFrame(argo_floats)
    
    # Add color coding based on status
    df["color"] = df["status"].map({
        "Active": [0, 150, 255, 180],  # Blue for active
        "Inactive": [128, 128, 128, 120]  # Gray for inactive
    })
    
    # Create ScatterplotLayer for Argo floats
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius=500,  # Fixed radius instead of variable
        radius_scale=1,
        radius_min_pixels=12,  # Increased minimum size
        radius_max_pixels=30,  # Increased maximum size
        pickable=True,
        auto_highlight=True,
        stroked=True,
        line_width_min_pixels=2,
        get_line_color=[255, 255, 255, 255],  # White border for visibility
    )
    
    # Create ColumnLayer for 3D visualization
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon", "lat"],
        get_elevation="temperature",
        elevation_scale=2000,  # Increased scale for visibility
        get_fill_color="color",
        radius=8000,  # Increased radius for visibility
        pickable=True,
        auto_highlight=True,
        extruded=True,
        coverage=1,
    )
    
    # Set the viewport location to Arabian Sea
    view_state = pdk.ViewState(
        longitude=66.0,  # Arabian Sea region
        latitude=20.0,   # Arabian Sea region
        zoom=5,
        min_zoom=2,
        max_zoom=15,
        pitch=45,
        bearing=0,
        height=600,
        width=None,
    )
    
    # Tooltip configuration
    tooltip = {
        "html": "<b>Float:</b> {name}<br/>"
                "<b>ID:</b> {id}<br/>"
                "<b>Status:</b> {status}<br/>"
                "<b>Temperature:</b> {temperature}°C<br/>"
                "<b>Location:</b> ({lat:.2f}, {lon:.2f})",
        "style": {
            "backgroundColor": "steelblue",
            "color": "white",
            "fontSize": "12px",
            "padding": "10px",
            "borderRadius": "5px"
        }
    }
    
    # Create TextLayer for labels
    text_layer = pdk.Layer(
        "TextLayer",
        data=df,
        get_position=["lon", "lat"],
        get_text="name",
        get_size=16,
        get_color=[255, 255, 255, 255],
        get_pixel_offset=[0, -20],
        pickable=True
    )
    
    # Create the deck with multiple layers for better visibility
    r = pdk.Deck(
        layers=[column_layer, scatter_layer, text_layer],  # Reordered for better visibility
        initial_view_state=view_state,
        map_style="light",  # Use light style
    )
    
    # Display the map
    st.subheader("🌊 Interactive Argo Float Map (3D PyDeck)")
    
    # Debug information
    with st.expander("🔍 Debug Info"):
        st.write("**Float Data:**")
        st.dataframe(df)
        st.write(f"**Map Center:** {view_state.latitude}°N, {view_state.longitude}°E")
        st.write(f"**Number of floats:** {len(df)}")
    
    st.pydeck_chart(r, use_container_width=True)
    
    # Instructions for PyDeck map  
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("💡 **Map Interaction:**\n- 🎯 Use the float selector buttons below (PyDeck click events coming soon!)\n- 🔍 Hover over 3D markers for details\n- 📊 Each selection opens parameter dialog overlay")
    
    with col2:
        st.success("🎯 **Visual Guide:**\n- 🔵 Blue columns = Active floats\n- ⚫ Gray columns = Inactive floats\n- 📏 Column height = Temperature")
    
    # Quick float selector and PyDeck dialog removed per request

def generate_argo_graph(config):
    """Generate graph based on Argo float configuration."""
    float_id = config.get("floatId")
    parameter = config.get("parameter")
    graph_type = config.get("graphType")
    x_axis = config.get("xAxis")
    y_axis = config.get("yAxis")
    
    # Get data from sample data
    argo_data = SAMPLE.get("argo_data", {}).get(float_id, {})
    param_data = argo_data.get(parameter, {})
    
    if not param_data:
        return {
            "text": f"No {parameter} data available for {config.get('floatName', float_id)}",
            "data": None,
            "plot": None
        }
    
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
            values = depths * 0.1 + np.random.normal(0, 2, len(depths))
        else:  # oxygen
            values = 220 - 115 * (depths/2000) + np.random.normal(0, 5, len(depths))
        
        return {"x": values.tolist() if x_axis != "depth" else depths.tolist(),
                "y": depths.tolist() if y_axis == "depth" else values.tolist()}
    
    elif x_axis == "time" or y_axis == "time":
        times = [f"2024-{i:02d}-01" for i in range(1, 13)]
        if parameter == "temperature":
            values = 24.0 + 2.0 * np.sin(np.linspace(0, 2*np.pi, 12)) + np.random.normal(0, 0.3, 12)
        else:
            values = np.random.normal(35.0, 0.2, 12)
        
        return {"x": times if x_axis == "time" else values.tolist(),
                "y": values.tolist() if y_axis != "time" else times}
    
    else:  # cycle data
        cycles = list(range(1, 21))
        values = np.random.normal(24.0 if parameter == "temperature" else 35.0, 
                                 0.5 if parameter == "temperature" else 0.1, 20)
        
        return {"x": cycles if x_axis == "cycle" else values.tolist(),
                "y": values.tolist() if y_axis != "cycle" else cycles}

def get_axis_label(axis_type, parameter):
    """Get appropriate axis label."""
    labels = {
        "time": "Time",
        "depth": "Depth (m)",
        "cycle": "Cycle Number",
        "parameter": f"{parameter.title()} ({get_parameter_unit(parameter)})"
    }
    return labels.get(axis_type, axis_type)

def get_parameter_unit(parameter):
    """Get unit for parameter."""
    units = {
        "temperature": "°C",
        "salinity": "PSU",
        "pressure": "dbar",
        "oxygen": "μmol/kg"
    }
    return units.get(parameter, "")

def show_parameter_dialog(float_data):
    """Show parameter selection dialog for a selected float."""
    
    # Add custom CSS for the dialog
    st.markdown("""
    <style>
    .dialog-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid #4a90e2;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .dialog-header {
        color: white;
        font-size: 1.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .float-info-card {
        background: rgba(255,255,255,0.9);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Dialog container
    st.markdown('<div class="dialog-container">', unsafe_allow_html=True)
    
    st.markdown(f'<div class="dialog-header">🎯 Configure Visualization for {float_data["name"]}</div>', unsafe_allow_html=True)
    
    # Float information and close button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        status_color = "🟢" if float_data['status'] == 'Active' else "🔴"
        st.markdown(f"""
        <div class="float-info-card">
        <h4>{status_color} Float Information</h4>
        <p><strong>ID:</strong> {float_data['id']}</p>
        <p><strong>Status:</strong> {float_data['status']}</p>
        <p><strong>Location:</strong> {float_data['lat']:.2f}°N, {float_data['lon']:.2f}°E</p>
        <p><strong>Temperature:</strong> {float_data['temperature']}°C</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.write("")  # Spacing
        if st.button("❌ Close", type="secondary", use_container_width=True):
            st.session_state.show_dialog = False
            st.session_state.selected_marker = None
            st.rerun()
        
    # Parameter selection form
    with st.form("parameter_form", clear_on_submit=False):
        st.markdown("### 📊 Visualization Parameters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            parameter = st.selectbox(
                "🌊 Parameter:",
                ["temperature", "salinity", "pressure", "oxygen"],
                help="Choose the oceanographic parameter to visualize",
                format_func=lambda x: f"{x.title()} ({get_parameter_unit(x)})"
            )
        
        with col2:
            graph_type = st.selectbox(
                "📈 Graph Type:",
                ["profile", "line", "scatter"],
                help="Select the visualization style",
                format_func=lambda x: f"🌊 Depth Profile" if x == "profile" else f"📈 Line Plot" if x == "line" else f"⚪ Scatter Plot"
            )
        
        with col3:
            if graph_type == "profile":
                x_axis = st.selectbox("📐 X-Axis:", ["parameter"], disabled=True, help="Fixed for depth profiles")
                y_axis = st.selectbox("📏 Y-Axis:", ["depth"], disabled=True, help="Fixed for depth profiles")
            else:
                x_axis = st.selectbox("📐 X-Axis:", ["time", "depth", "cycle", "parameter"])
                y_axis = st.selectbox("📏 Y-Axis:", ["parameter", "depth", "time", "cycle"])
        
        # Submit button with enhanced styling
        col_btn1, col_btn2, col_btn3 = st.columns([1,2,1])
        with col_btn2:
            submitted = st.form_submit_button(
                "🎨 Generate Visualization", 
                type="primary", 
                use_container_width=True
            )
        
        if submitted:
            config = {
                "floatId": float_data['id'],
                "floatName": float_data['name'],
                "parameter": parameter,
                "graphType": graph_type,
                "xAxis": x_axis,
                "yAxis": y_axis,
                "latitude": float_data['lat'],
                "longitude": float_data['lon']
            }
            
            # Store selection and close dialog
            st.session_state.map_selection = config
            st.session_state.show_dialog = False
            st.session_state.selected_marker = None
            st.success(f"🎯 Generating {parameter} {graph_type} for {float_data['name']}...")
            time.sleep(0.5)  # Brief pause for user feedback
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close dialog container


with st.sidebar:
    st.title("Float-Chat-AI (Static)")
    st.text_input("User / session id", value=st.session_state.session_id, key="_sidebar_session")
    if st.button("Start / Update Session"):
        st.session_state.session_id = st.session_state.get("_sidebar_session") or st.session_state.session_id
    st.markdown("---")
    st.subheader("Sample queries")
    for s in SAMPLE.get("samples", []):
        if st.button(s, key=f"sample_{s}"):
            st.session_state._prefill = s
    st.markdown("---")
    st.write("History (local):")
    for h in reversed(st.session_state.history[-20:]):
        st.write(f"- {h['query']} — {h.get('result_text','')[:80]}")

# Main layout with single column for map
st.header("🌊 Argo Float Interactive Map")

# Map toggle and options
col1, col2 = st.columns([2, 1])
with col1:
    map_type = st.selectbox("Map Type", ["2D Plotly", "3D PyDeck"], key="map_type")
with col2:
    st.info("👆 Click on a float marker to configure visualization")

show_map_checkbox = st.checkbox("Show interactive map", value=st.session_state.show_map)
st.session_state.show_map = show_map_checkbox

if st.session_state.show_map:
    if map_type == "2D Plotly":
        # Create 2D Plotly map
        st.subheader("🌊 Argo Float Map (2D)")

        # Sample Argo float data
        argo_floats = [
            {"id": "ARGO_001", "name": "Float 001", "latitude": 20.5, "longitude": 65.2, "status": "Active", "cycles": 45, "temperature": 24.5},
            {"id": "ARGO_002", "name": "Float 002", "latitude": 18.7, "longitude": 67.8, "status": "Active", "cycles": 32, "temperature": 25.1},
            {"id": "ARGO_003", "name": "Float 003", "latitude": 22.1, "longitude": 63.5, "status": "Inactive", "cycles": 28, "temperature": 23.8},
            {"id": "ARGO_004", "name": "Float 004", "latitude": 19.3, "longitude": 69.1, "status": "Active", "cycles": 51, "temperature": 24.9},
            {"id": "ARGO_005", "name": "Float 005", "latitude": 21.8, "longitude": 64.7, "status": "Active", "cycles": 39, "temperature": 24.3}
        ]

        fig = go.Figure()

        # Add active floats
        active_floats = [f for f in argo_floats if f["status"] == "Active"]
        if active_floats:
            fig.add_trace(go.Scattermapbox(
                lat=[f["latitude"] for f in active_floats],
                lon=[f["longitude"] for f in active_floats],
                mode='markers',
                marker=dict(size=15, color='blue', opacity=0.8),
                text=[f"{f['name']} - {f['status']}<br>Cycles: {f['cycles']}<br>Temp: {f['temperature']}°C" for f in active_floats],
                name="Active Floats",
                hovertemplate='<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>'
            ))

        # Add inactive floats
        inactive_floats = [f for f in argo_floats if f["status"] == "Inactive"]
        if inactive_floats:
            fig.add_trace(go.Scattermapbox(
                lat=[f["latitude"] for f in inactive_floats],
                lon=[f["longitude"] for f in inactive_floats],
                mode='markers',
                marker=dict(size=15, color='gray', opacity=0.6),
                text=[f"{f['name']} - {f['status']}<br>Cycles: {f['cycles']}<br>Temp: {f['temperature']}°C" for f in inactive_floats],
                name="Inactive Floats",
                hovertemplate='<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>'
            ))

        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=20.0, lon=66.0),
                zoom=5
            ),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0),
            title="Argo Floats in Arabian Sea - Click markers to configure visualization"
        )

        # Display map with click detection
        plotly_events = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")

        # Instructions for 2D map
        col1, col2 = st.columns(2)
        with col1:
            st.info("💡 **Map Controls:**\n- Drag to pan\n- Scroll to zoom\n- **Click markers** to configure visualization")

        with col2:
            st.success("🎯 **Interactive Map:**\n- Click any float marker to open dialog\n- Blue = Active, Gray = Inactive floats")

        # Handle map marker clicks
        if plotly_events and 'selection' in plotly_events and plotly_events['selection']['points']:
            selected_point = plotly_events['selection']['points'][0]
            point_index = selected_point.get('pointIndex', 0)
            curve_number = selected_point.get('curveNumber', 0)

            # Determine which float was clicked based on curve and point index
            if curve_number == 0 and point_index < len(active_floats):
                selected_float = active_floats[point_index]
            elif curve_number == 1 and point_index < len(inactive_floats):
                selected_float = inactive_floats[point_index]
            else:
                selected_float = argo_floats[0]  # fallback

            st.session_state.selected_marker = selected_float
            st.session_state.show_dialog = True
            st.rerun()

        # Show parameter dialog as overlay if a marker is selected
        if st.session_state.show_dialog and st.session_state.selected_marker:
            # Create dialog as overlay on the map area
            with st.container():
                st.markdown("""
                <style>
                .map-dialog-overlay {
                    position: relative;
                    z-index: 1000;
                    background: rgba(255, 255, 255, 0.95);
                    border: 2px solid #4a90e2;
                    border-radius: 15px;
                    padding: 20px;
                    margin: -50px 20px 20px 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    backdrop-filter: blur(10px);
                }
                </style>
                """, unsafe_allow_html=True)

                st.markdown('<div class="map-dialog-overlay">', unsafe_allow_html=True)
                st.markdown("### 🌊 Configure Argo Float Visualization")

                # Close button
                col1, col2, col3 = st.columns([4, 1, 1])
                with col3:
                    if st.button("❌ Close", key="close_plotly_dialog"):
                        st.session_state.show_dialog = False
                        st.session_state.selected_marker = None
                        st.rerun()

                # Show the parameter dialog content inline
                show_parameter_dialog(st.session_state.selected_marker)
                st.markdown('</div>', unsafe_allow_html=True)

    else:
        try:
            create_pydeck_argo_map()
            st.info("💡 **PyDeck 3D Map Tips:**\n- Hover over 3D columns for float details\n- Use the 2D Plotly map to configure visualizations\n- Switch views with the selector above")
        except Exception as e:
            st.error(f"PyDeck map failed to load: {str(e)}")
            st.info("Try switching to '2D Plotly' map type for a guaranteed working map!")
else:
    st.info("Map is hidden. Check the box above to show the interactive Argo float map.")

# Ensure chat container exists before use
chat_col = st.container()
with chat_col:
    st.header("Chat Interface")
    
    # Display conversation
    with st.container():
        for m in st.session_state.messages:
            role = m.get("role", "assistant")
            if role == "user":
                st.markdown(f"**You:** {m['content']}")
            else:
                st.markdown(f"**Assistant:** {m['content']}")
                if m.get("data"):
                    with st.expander("View Data Details"):
                        st.json(m.get("data"))
    
    # Query input
    st.markdown("---")
    with st.form("query_form", clear_on_submit=True):
        query = st.text_area("Enter query", value=st.session_state.get("_prefill", ""), height=80, key="_query")
        submitted = st.form_submit_button("Send", use_container_width=True)
        if submitted and query and query.strip():
            st.session_state.messages.append({"role": "user", "content": query})
            resp = simulate_query(query)
            assistant_text = resp.get("text", "")
            st.session_state.messages.append({"role": "assistant", "content": assistant_text, "data": resp.get("data"), "plot": resp.get("plot")})
            st.session_state.history.append({"query": query, "result_text": assistant_text, "timestamp": int(time.time())})
            st.session_state._prefill = ""
            st.rerun()

# Full-width visualization area
st.markdown("---")
st.header("Data Visualization")

# Check if there's a plot to display from messages
latest_plot = None
for m in reversed(st.session_state.messages):
    if m.get("plot"):
        latest_plot = m.get("plot")
        break

# Handle map-generated graphs  
if st.session_state.map_selection is not None:
    config = st.session_state.map_selection
    if isinstance(config, dict):
        resp = generate_argo_graph(config)
        
        float_name = config.get('floatName', 'Unknown Float')
        parameter = config.get('parameter', 'unknown')
        graph_type = config.get('graphType', 'line')
        x_axis = config.get('xAxis', 'time')
        y_axis = config.get('yAxis', 'parameter')
        
        st.success(f"Generated visualization for {float_name}")
        st.markdown(f"**Configuration:** {parameter} - {graph_type} ({x_axis} vs {y_axis})")
        
        if resp.get("plot"):
            latest_plot = resp.get("plot")
        
        # Add to conversation history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": resp.get("text", ""), 
            "data": resp.get("data"), 
            "plot": resp.get("plot")
        })
    
    # Clear the selection
    st.session_state.map_selection = None
    st.rerun()

# Check for JavaScript communication via URL parameters (alternative approach)
query_params = st.query_params
if "argo_config" in query_params:
    try:
        import urllib.parse
        config_str = urllib.parse.unquote(query_params["argo_config"])
        config = json.loads(config_str)
        st.session_state.map_selection = config
        # Clear the query param
        st.query_params.clear()
        st.rerun()
    except (json.JSONDecodeError, KeyError):
        pass

# Display the latest plot
if latest_plot:
    p = latest_plot
    fig = go.Figure()
    
    graph_type = p.get("graph_type", "line")
    if graph_type == "scatter":
        fig.add_trace(go.Scatter(x=p.get("x"), y=p.get("y"), mode="markers", marker=dict(size=8)))
    elif graph_type == "profile":
        fig.add_trace(go.Scatter(x=p.get("x"), y=p.get("y"), mode="lines+markers", line=dict(width=3)))
    else:  # line plot
        fig.add_trace(go.Scatter(x=p.get("x"), y=p.get("y"), mode="lines+markers"))
    
    if p.get("reverse_y"):
        fig.update_yaxes(autorange="reversed")
    
    fig.update_xaxes(title=p.get("x_label"))
    fig.update_yaxes(title=p.get("y_label"))
    fig.update_layout(
        title=f"Argo Float Data Visualization ({graph_type.title()} Plot)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{len(st.session_state.messages)}")
else:
    st.info("No visualization to display. Use the chat interface or select a float from the map to generate graphs.")

# Download section
if st.session_state.history:
    st.markdown("---")
    last = st.session_state.history[-1]
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download Last Result (JSON)", data=json.dumps(last, indent=2), file_name="result.json", mime="application/json")
    with col2:
        if latest_plot:
            st.download_button("Download Plot Data (JSON)", data=json.dumps(latest_plot, indent=2), file_name="plot_data.json", mime="application/json")


st.markdown("---")
st.caption("This is a static Streamlit prototype that uses local canned responses and sample data. Replace simulate_query() with real API calls to integrate with the backend.")

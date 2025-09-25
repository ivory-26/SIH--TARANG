import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.graph_objects as go
import time
import json
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Argo Float Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "map_selection" not in st.session_state:
    st.session_state.map_selection = None
if "selected_marker" not in st.session_state:
    st.session_state.selected_marker = None
if "show_dialog" not in st.session_state:
    st.session_state.show_dialog = False

# Custom CSS for the app
st.markdown("""
<style>
.stApp {
    max-width: 1200px;
    margin: 0 auto;
}

.float-card {
    background: white;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    margin: 10px 0;
}

.side-dialog {
    position: absolute;
    right: 20px;
    width: 350px;
    z-index: 1000;
    background: white;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    border: 2px solid #4a90e2;
}

.graph-container {
    margin-top: 20px;
    padding: 20px;
    border-radius: 10px;
    background: rgba(240, 242, 246, 0.8);
}

/* Parameter dialog styling */
.dialog-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    backdrop-filter: blur(4px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    max-width: 500px;
}

.dialog-header {
    color: white;
    text-align: center;
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 15px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

.float-info-card {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 10px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.info-row {
    display: flex;
    justify-content: space-between;
    margin: 5px 0;
    padding: 5px;
    border-bottom: 1px solid #eee;
}

.info-label {
    font-weight: bold;
    color: #333;
}

.info-value {
    color: #666;
}
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
            return parameter.title()
    else:
        return axis.title()

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
        <span class="info-label">🎯 Float Name:</span>
        <span class="info-value">{float_data['name']}</span>
    </div>
    <div class="info-row">
        <span class="info-label">🆔 Float ID:</span>
        <span class="info-value">{float_data['id']}</span>
    </div>
    <div class="info-row">
        <span class="info-label">📍 Location:</span>
        <span class="info-value">{float_data['latitude']:.3f}°N, {float_data['longitude']:.3f}°E</span>
    </div>
    <div class="info-row">
        <span class="info-label">🌡️ Temperature:</span>
        <span class="info-value">{float_data['temperature']}°C</span>
    </div>
    <div class="info-row">
        <span class="info-label">📊 Status:</span>
        <span class="info-value">{float_data['status']}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Parameter selection form
    with st.form("parameter_form", clear_on_submit=False):
        st.markdown("### 📊 Visualization Parameters")
        
        col1, col2 = st.columns(2)
        
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
        
        col3, col4 = st.columns(2)
        with col3:
            if graph_type == "profile":
                x_axis = st.selectbox("📐 X-Axis:", ["parameter"], disabled=True, help="Fixed for depth profiles")
            else:
                x_axis = st.selectbox("📐 X-Axis:", ["time", "depth", "cycle", "parameter"])
        
        with col4:
            if graph_type == "profile":
                y_axis = st.selectbox("📏 Y-Axis:", ["depth"], disabled=True, help="Fixed for depth profiles")
            else:
                y_axis = st.selectbox("📏 Y-Axis:", ["parameter", "depth", "time", "cycle"])
        
        # Submit button with enhanced styling
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
                "latitude": float_data['latitude'],
                "longitude": float_data['longitude']
            }
            
            # Store selection and close dialog
            st.session_state.map_selection = config
            st.session_state.show_dialog = False
            st.session_state.selected_marker = None
            st.success(f"🎯 Generating {parameter} {graph_type} for {float_data['name']}...")
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

# Application Header
st.title("🌊 Argo Float Data Explorer")
st.markdown("Interactive dashboard for exploring Argo float data in the Arabian Sea")

# Main layout with map
st.subheader("📍 Argo Float Map - Click on a float to configure visualization")

# Map options
map_type = st.radio("Select Map Type:", ["2D Interactive", "3D View"], horizontal=True)

# Create and display the selected map type
if map_type == "2D Interactive":
    # Create 2D Plotly map
    fig = go.Figure()
    
    # Add active floats
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
    
    # Add inactive floats
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
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=20.0, lon=66.0),
            zoom=5
        ),
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Display map with click detection
    map_col1, map_col2 = st.columns([7, 3])
    
    with map_col1:
        # Show the map with click events
        plotly_events = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
        
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
    
    # Show parameter dialog in side column if a marker is selected
    with map_col2:
        if st.session_state.show_dialog and st.session_state.selected_marker:
            st.markdown(f"### 🌊 Configure {st.session_state.selected_marker['name']}")
            
            # Close button
            if st.button("❌ Close", key="close_dialog"):
                st.session_state.show_dialog = False
                st.session_state.selected_marker = None
                st.rerun()
            
            # Show the parameter dialog content
            show_parameter_dialog(st.session_state.selected_marker)
        else:
            st.info("👈 Click on any marker in the map to configure visualization parameters")
            st.markdown("""
            **Available Parameters:**
            - Temperature (°C)
            - Salinity (PSU)
            - Pressure (dbar)
            - Oxygen (μmol/kg)
            
            **Visualization Types:**
            - Depth Profiles
            - Time Series
            - Parameter Correlations
            """)

else:  # 3D View
    # Convert to DataFrame for PyDeck
    df = pd.DataFrame(argo_floats)
    
    # Create color column based on status
    df["color"] = df["status"].apply(lambda s: [0, 0, 255, 200] if s == "Active" else [128, 128, 128, 160])
    
    # Calculate elevation based on temperature (for visual effect)
    df["elevation"] = df["temperature"] * 100
    
    # Create PyDeck layers
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=10000,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        extruded=True,
    )
    
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_color="color",
        get_radius=7000,
        pickable=True,
    )
    
    # Create TextLayer for labels
    text_layer = pdk.Layer(
        "TextLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_text="name",
        get_size=16,
        get_color=[255, 255, 255, 255],
        get_pixel_offset=[0, -20],
        pickable=True
    )
    
    # Set the viewport location to Arabian Sea
    view_state = pdk.ViewState(
        longitude=66.0,
        latitude=20.0,
        zoom=5,
        pitch=45,
        bearing=0,
        height=500,
    )
    
    # Create the deck with multiple layers
    r = pdk.Deck(
        layers=[column_layer, scatter_layer, text_layer],
        initial_view_state=view_state,
        map_style="light",
        tooltip={
            "html": "<b>{name}</b> ({id})<br/><b>Status:</b> {status}<br/><b>Temp:</b> {temperature}°C",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        }
    )
    
    # Display the 3D map with side panel for selection
    map3d_col1, map3d_col2 = st.columns([7, 3])
    
    with map3d_col1:
        st.pydeck_chart(r, use_container_width=True)
        st.info("💡 **Note:** Click a float button in the panel to configure visualization")
    
    with map3d_col2:
        st.markdown("### 🌊 Select Argo Float")
        
        # Since PyDeck doesn't have click events in Streamlit, provide buttons
        for float_data in argo_floats:
            status_icon = "🔵" if float_data["status"] == "Active" else "⚫"
            if st.button(f"{status_icon} {float_data['name']}", key=f"float_{float_data['id']}"):
                st.session_state.selected_marker = float_data
                st.session_state.show_dialog = True
                st.rerun()
        
        # Show parameter dialog if a marker is selected
        if st.session_state.show_dialog and st.session_state.selected_marker:
            st.markdown(f"### 🌊 Configure {st.session_state.selected_marker['name']}")
            
            # Close button
            if st.button("❌ Close", key="close_3d_dialog"):
                st.session_state.show_dialog = False
                st.session_state.selected_marker = None
                st.rerun()
                
            # Show the parameter dialog
            show_parameter_dialog(st.session_state.selected_marker)

# Visualization section - Appears below the map
st.markdown("---")

# Check if there's a graph to display
if st.session_state.map_selection is not None:
    config = st.session_state.map_selection
    
    # Generate the graph using the configuration
    resp = generate_argo_graph(config)
    
    # Display visualization header
    st.header(f"📊 Visualization: {config.get('parameter', '').title()} {config.get('graphType', '').title()} - {config.get('floatName', '')}")
    
    # Display graph configuration
    st.markdown(f"**Configuration:** {config.get('parameter', '')} - {config.get('graphType', '')} ({config.get('xAxis', '')} vs {config.get('yAxis', '')})")
    
    # Show the plot if available
    if resp.get("plot"):
        p = resp.get("plot")
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
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download Data (JSON)", 
                data=json.dumps(resp.get("data", {}), indent=2), 
                file_name=f"argo_{config.get('floatId', 'data')}_{config.get('parameter', 'param')}.json", 
                mime="application/json"
            )
        with col2:
            st.download_button(
                "📥 Download Plot Data (CSV)", 
                data=pd.DataFrame({
                    p.get("x_label", "x"): p.get("x", []),
                    p.get("y_label", "y"): p.get("y", [])
                }).to_csv(index=False), 
                file_name=f"argo_{config.get('floatId', 'data')}_{config.get('parameter', 'param')}.csv", 
                mime="text/csv"
            )
else:
    st.info("👆 Select a float from the map above to generate visualizations")

# Footer
st.markdown("---")
st.caption("This is a Streamlit prototype that uses synthetic data. Click on any marker in the map to configure and generate visualizations.")
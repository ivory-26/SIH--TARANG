# Float-Chat-AI Frontend

This document provides a comprehensive overview of the Float-Chat-AI Streamlit frontend, including its features, usage instructions, and troubleshooting tips.

## 📜 Overview

The Float-Chat-AI frontend is an interactive Streamlit web application designed for visualizing and querying Argo float data. It features a dual map system, a chat interface for natural language queries, and a dynamic visualization panel for generating custom graphs.

## ✨ Features

-   **Dual Interactive Maps**: Choose between a reliable 2D Plotly map and an advanced 3D PyDeck visualization.
-   **Custom Graph Generation**: Dynamically create line plots, scatter plots, and depth profiles from float data.
-   **Interactive Chat Interface**: Ask questions about Argo floats and get responses, including data and visualizations.
-   **Responsive Design**: The layout is optimized for a seamless experience on different screen sizes.
-   **Data Export**: Download chat results and plot data as JSON files.

## 🗺️ The Dual Map System

You can switch between two different map types for visualizing the Argo floats.

### 1. 2D Plotly Map (Recommended)

This is the default and recommended map for most users.

-   **Reliability**: ✅ Always works, using OpenStreetMap tiles that are not blocked by firewalls.
-   **Interactivity**: ✅ Click on any float marker to open the visualization configuration dialog.
-   **Clarity**: ✅ Active (blue) and inactive (gray) floats are clearly distinguished.
-   **Performance**: ✅ Fast and responsive across all browsers and networks.

### 2. 3D PyDeck Map (Advanced)

This map offers an advanced 3D view but may have limitations.

-   **3D Visualization**: 🧊 Displays floats as 3D columns where height can represent a data parameter like temperature.
-   **Aesthetics**: ✨ Provides a more visually impressive presentation.
-   **Limitations**: ⚠️ The map background tiles may not load due to network restrictions or missing API keys, showing only the 3D markers on a blank background. Interaction is limited to hovering.

## 🚀 Usage Instructions

1.  **Show the Map**: Check the **"Show interactive map"** checkbox at the top.
2.  **Select Map Type**: Use the **"Map Type"** dropdown to switch between "2D Plotly" and "3D PyDeck".
3.  **Interact with the 2D Map**:
    -   Click any float marker (blue or gray dot).
    -   A dialog will appear, allowing you to configure a visualization.
4.  **Generate a Visualization**:
    -   In the dialog, select a **Parameter** (e.g., Temperature), **Graph Type**, and configure the **Axes**.
    -   Click **"Generate Visualization"**. The graph will appear in the "Data Visualization" section below.
5.  **Use the Chat**:
    -   Type a query into the chat box and press Send.
    -   The assistant's response, including any data or plots, will appear in the conversation.

## 🔧 Troubleshooting

**Problem: The 3D PyDeck map background is blank or gray.**

This is a common issue with PyDeck.

-   **Quick Fix**: Switch to the **"2D Plotly"** map type. It is guaranteed to work.
-   **Cause**: This usually happens because your network or a firewall is blocking the map tile service that PyDeck uses, or a required Mapbox API key is not configured.
-   **Advanced Check**: Open your browser's developer tools (F12) and check the "Console" and "Network" tabs for errors related to map tile requests.

**Problem: No floats are visible on the PyDeck map.**

-   **Check Coordinates**: Expand the "🔍 Debug Info" section (if available) to ensure the float coordinates are correct (e.g., in the Arabian Sea, not Hawaii).
-   **Zoom/Pan**: Try zooming out and rotating the globe to find the markers.

## 🛠️ Technical Details

### File Structure

```
frontend/
├── streamlit_app.py        # Main Streamlit application
├── requirements.txt        # Python dependencies
├── components/
│   └── cesium_map.html     # (Legacy) Cesium map component
└── static/
    ├── sample_data.json    # Sample data and canned responses
    └── argo_config.json    # Float and parameter configurations
```

### Dependencies

-   `streamlit`
-   `plotly`
-   `numpy`
-   `pandas`
-   `pydeck`

This application uses synthetic data generated via NumPy for demonstration purposes. For a production environment, this should be replaced with API calls to a live Argo data source.

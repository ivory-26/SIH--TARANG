# Float-Chat-AI Frontend with Cesium Map Integration

This Streamlit application now includes an interactive Cesium.js map for visualizing Argo float locations and generating custom data visualizations.

## New Features

### 🗺️ Interactive Cesium Map
- **3D Globe View**: Interactive Cesium.js map showing Argo float locations in the Arabian Sea
- **Float Status**: Active floats shown in blue, inactive floats in gray
- **Hover Information**: Click on floats to see detailed information
- **Double-click to Configure**: Double-click any float to open the visualization dialog

### 📊 Custom Graph Generation
- **Parameter Selection**: Choose from Temperature, Salinity, Pressure, or Dissolved Oxygen
- **Graph Types**: Line plots, scatter plots, or depth profiles
- **Axis Configuration**: Customize X and Y axes (Time, Depth, Cycle Number, Parameter Value)
- **Real-time Generation**: Graphs generated instantly with synthetic data

### 💬 Enhanced Chat Interface
- **Map Integration**: Results from map interactions appear in chat
- **Data Downloads**: Export results and plot data as JSON
- **Conversation History**: Persistent chat history with timestamps

## Sample Argo Floats

The application includes 5 sample Argo floats in the Arabian Sea region:

1. **ARGO_001** (20.5°N, 65.2°E) - Active, 45 cycles
2. **ARGO_002** (18.7°N, 67.8°E) - Active, 32 cycles  
3. **ARGO_003** (22.1°N, 63.5°E) - Inactive, 28 cycles
4. **ARGO_004** (19.3°N, 69.1°E) - Active, 51 cycles
5. **ARGO_005** (21.8°N, 64.7°E) - Active, 39 cycles

## Usage Instructions

1. **Map Interaction**:
   - Check "Show Interactive Map" to display the Cesium globe
   - Click on blue/gray dots to view float information
   - Double-click on any float to open the visualization dialog

2. **Graph Configuration**:
   - Select parameter (Temperature, Salinity, etc.)
   - Choose graph type (Line, Scatter, Profile)
   - Configure X and Y axes
   - Click "Generate Graph" to create visualization

3. **Chat Interface**:
   - Use the chat for text-based queries
   - Try sample queries from the sidebar
   - View generated graphs in the full-width visualization area

4. **Testing**:
   - Use the "🎯 Test Float Selection" button to simulate map interaction
   - This generates a sample temperature depth profile for Float 001

## File Structure

```
frontend/
├── streamlit_app.py              # Main Streamlit application
├── components/
│   └── cesium_map.html          # Cesium.js map component
├── static/
│   ├── sample_data.json         # Sample data and responses
│   └── argo_config.json         # Float and parameter configurations
└── requirements.txt             # Python dependencies
```

## Technical Details

### Data Generation
- **Synthetic Data**: Realistic synthetic data generated using NumPy
- **Temperature Profiles**: Exponential decay with depth + noise
- **Salinity Profiles**: Linear decrease with depth + noise  
- **Pressure**: Linear relationship with depth
- **Oxygen**: Decreasing concentration with depth

### Communication
- **Map ↔ Streamlit**: URL parameters for configuration passing
- **Fallback Support**: Static Plotly map when Cesium.js unavailable
- **Session Management**: Persistent state across interactions

### Visualization
- **Plotly Integration**: All graphs rendered using Plotly
- **Responsive Design**: Full-width visualizations
- **Multiple Graph Types**: Line, scatter, and profile plots
- **Axis Control**: Flexible X/Y axis configuration

## Dependencies

- `streamlit>=1.24.0` - Web app framework
- `plotly>=5.17.0` - Interactive plotting
- `numpy>=1.24.0` - Numerical computations
- `pandas>=2.1.4` - Data manipulation

## Development Notes

- Uses Cesium Ion default token (replace in production)
- Sample data is static (replace with real Argo data API)
- Map communication via URL parameters (could be enhanced with WebSocket)
- Designed for prototype/demo purposes

## Future Enhancements

1. **Real Data Integration**: Connect to actual Argo float databases
2. **Advanced Filtering**: Filter floats by date, parameter ranges, regions
3. **Animation**: Time-series animation of float movements
4. **Export Options**: PDF, PNG export of visualizations
5. **User Authentication**: Multi-user support with saved configurations
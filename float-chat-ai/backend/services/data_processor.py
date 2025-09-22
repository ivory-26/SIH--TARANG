"""
Data Processor Service
Handles netCDF data processing, SQL queries, and data visualization
"""

import xarray as xr
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import os
import json
import uuid
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
from loguru import logger
import io
import base64


class DataProcessor:
    """
    Handles all data processing operations for ARGO float data
    """

    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        self.sample_nc_file = os.path.join(self.data_path, "sample_argo.nc")
        self.cached_data = {}

    async def load_netcdf_data(self, file_path: Optional[str] = None) -> xr.Dataset:
        """
        Load netCDF data using xarray
        """
        try:
            file_to_load = file_path or self.sample_nc_file

            if file_to_load in self.cached_data:
                logger.info(f"Using cached data for {file_to_load}")
                return self.cached_data[file_to_load]

            if os.path.exists(file_to_load):
                dataset = xr.open_dataset(file_to_load)
                self.cached_data[file_to_load] = dataset
                logger.info(f"Loaded netCDF data from {file_to_load}")
                return dataset
            else:
                logger.warning(f"NetCDF file not found: {file_to_load}")
                # Return mock data for prototype
                return self._create_mock_argo_data()

        except Exception as e:
            logger.error(f"Error loading netCDF data: {str(e)}")
            return self._create_mock_argo_data()

    def _create_mock_argo_data(self) -> xr.Dataset:
        """
        Create mock ARGO data for prototype demonstration
        """
        logger.info("Creating mock ARGO data for prototype")

        # Create sample dimensions
        n_profiles = 50
        n_levels = 100

        # Create coordinate arrays
        profile_ids = np.arange(1, n_profiles + 1)
        pressure_levels = np.linspace(0, 2000, n_levels)  # 0-2000 dbar
        times = pd.date_range('2023-01-01', periods=n_profiles, freq='D')

        # Create realistic oceanographic data
        # Temperature: warmer at surface, colder at depth
        temperature = np.zeros((n_profiles, n_levels))
        for i in range(n_profiles):
            surface_temp = 20 + 5 * np.random.random()  # 20-25°C surface
            temperature[i] = surface_temp * np.exp(-pressure_levels / 500) + 2 * np.random.random(n_levels)

        # Salinity: more realistic ocean salinity profiles
        salinity = np.zeros((n_profiles, n_levels))
        for i in range(n_profiles):
            base_salinity = 34.5 + 0.5 * np.random.random()  # ~35 PSU
            salinity[i] = base_salinity + 0.5 * (pressure_levels / 1000) + 0.2 * np.random.random(n_levels)

        # Coordinates (mock locations in North Atlantic)
        latitudes = 40 + 10 * np.random.random(n_profiles)  # 40-50°N
        longitudes = -50 + 20 * np.random.random(n_profiles)  # -50 to -30°W

        # Create xarray dataset
        dataset = xr.Dataset({
            'TEMP': (['N_PROF', 'N_LEVELS'], temperature, {
                'long_name': 'Temperature',
                'units': 'degrees_Celsius',
                'standard_name': 'sea_water_temperature'
            }),
            'PSAL': (['N_PROF', 'N_LEVELS'], salinity, {
                'long_name': 'Practical Salinity',
                'units': 'PSU',
                'standard_name': 'sea_water_practical_salinity'
            }),
            'PRES': (['N_PROF', 'N_LEVELS'], np.tile(pressure_levels, (n_profiles, 1)), {
                'long_name': 'Pressure',
                'units': 'dbar',
                'standard_name': 'sea_water_pressure'
            }),
            'LATITUDE': (['N_PROF'], latitudes, {
                'long_name': 'Latitude',
                'units': 'degrees_north'
            }),
            'LONGITUDE': (['N_PROF'], longitudes, {
                'long_name': 'Longitude',
                'units': 'degrees_east'
            }),
            'JULD': (['N_PROF'], times, {
                'long_name': 'Julian Date',
                'units': 'days since 1950-01-01T00:00:00Z'
            })
        }, coords={
            'N_PROF': profile_ids,
            'N_LEVELS': pressure_levels
        })

        return dataset

    async def execute_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a data query based on parsed natural language input
        """
        try:
            logger.info(f"Executing query: {parsed_query}")

            # Load the dataset
            dataset = await self.load_netcdf_data()

            # Extract query parameters
            variable = parsed_query.get('variable', 'TEMP').upper()
            depth_range = parsed_query.get('depth_range')
            location = parsed_query.get('location')
            time_range = parsed_query.get('time_range')
            operation = parsed_query.get('operation', 'mean')  # mean, max, min, profile

            # Apply filters
            filtered_data = dataset

            # Depth/pressure filtering
            if depth_range:
                pressure_mask = (filtered_data.PRES >= depth_range[0]) & (filtered_data.PRES <= depth_range[1])
                filtered_data = filtered_data.where(pressure_mask, drop=True)

            # Location filtering (if specified)
            if location and 'lat_range' in location and 'lon_range' in location:
                lat_mask = (filtered_data.LATITUDE >= location['lat_range'][0]) & (filtered_data.LATITUDE <= location['lat_range'][1])
                lon_mask = (filtered_data.LONGITUDE >= location['lon_range'][0]) & (filtered_data.LONGITUDE <= location['lon_range'][1])
                filtered_data = filtered_data.where(lat_mask & lon_mask, drop=True)

            # Perform the requested operation
            if variable in filtered_data.data_vars:
                data_var = filtered_data[variable]

                if operation == 'mean':
                    result_data = data_var.mean().values.item()
                    result_description = f"Average {variable}"
                elif operation == 'max':
                    result_data = data_var.max().values.item()
                    result_description = f"Maximum {variable}"
                elif operation == 'min':
                    result_data = data_var.min().values.item()
                    result_description = f"Minimum {variable}"
                elif operation == 'profile':
                    # Return depth profile data
                    profile_data = data_var.mean(dim='N_PROF')
                    result_data = {
                        'pressure': profile_data.N_LEVELS.values.tolist(),
                        'values': profile_data.values.tolist()
                    }
                    result_description = f"{variable} depth profile"
                else:
                    result_data = data_var.mean().values.item()
                    result_description = f"Average {variable}"

                # Prepare metadata
                metadata = {
                    'variable': variable,
                    'operation': operation,
                    'depth_range': depth_range,
                    'n_profiles': int(filtered_data.dims.get('N_PROF', 0)),
                    'n_levels': int(filtered_data.dims.get('N_LEVELS', 0)),
                    'units': str(data_var.attrs.get('units', '')),
                    'long_name': str(data_var.attrs.get('long_name', variable))
                }

                return {
                    'success': True,
                    'data': result_data,
                    'metadata': metadata,
                    'description': result_description,
                    'query_type': operation,
                    'variable_info': {
                        'name': variable,
                        'units': metadata['units'],
                        'long_name': metadata['long_name']
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Variable '{variable}' not found in dataset",
                    'available_variables': list(dataset.data_vars.keys())
                }

        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_visualization(self, data: Any, viz_type: str = "table") -> Optional[Dict[str, Any]]:
        """
        Create visualizations for the data
        """
        try:
            if data is None:
                return None

            if viz_type == "profile" and isinstance(data, dict) and 'pressure' in data:
                # Create depth profile plot
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=data['values'],
                    y=data['pressure'],
                    mode='lines+markers',
                    name='Profile',
                    line=dict(color='blue', width=2)
                ))
                fig.update_layout(
                    title='Oceanographic Profile',
                    xaxis_title='Value',
                    yaxis_title='Pressure (dbar)',
                    yaxis=dict(autorange='reversed'),  # Reverse y-axis for depth
                    height=500
                )

                return {
                    'type': 'plotly',
                    # Use PlotlyJSONEncoder to handle numpy arrays and other special types
                    'data': json.loads(json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder))
                }

            elif viz_type == "table":
                # Simple table representation
                if isinstance(data, (int, float)):
                    return {
                        'type': 'table',
                        'data': [{'Value': round(data, 2)}]
                    }
                elif isinstance(data, dict):
                    return {
                        'type': 'table',
                        'data': [data]
                    }

            return None

        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return None

    async def get_raw_data(self, data_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Retrieve raw data by ID
        """
        try:
            dataset = await self.load_netcdf_data()

            if format == "json":
                # Convert xarray dataset to JSON-serializable format
                data_dict = {}
                for var_name, var_data in dataset.data_vars.items():
                    data_dict[var_name] = {
                        'values': var_data.values.tolist(),
                        'dimensions': list(var_data.dims),
                        'attributes': dict(var_data.attrs)
                    }

                return {
                    'variables': data_dict,
                    'coordinates': {name: coord.values.tolist() for name, coord in dataset.coords.items()},
                    'global_attributes': dict(dataset.attrs)
                }

            return {'error': f'Format {format} not supported'}

        except Exception as e:
            logger.error(f"Error retrieving raw data: {str(e)}")
            return {'error': str(e)}

    async def export_results(self, query_id: str, format: str = "csv") -> str:
        """
        Export query results in specified format
        """
        try:
            # For prototype, return a mock download URL
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"argo_export_{query_id}_{timestamp}.{format}"

            # In production, this would generate actual files
            return f"/downloads/{filename}"

        except Exception as e:
            logger.error(f"Error exporting results: {str(e)}")
            return ""

    def get_available_variables(self) -> List[Dict[str, str]]:
        """
        Get list of available variables in the dataset
        """
        return [
            {"name": "TEMP", "description": "Sea Water Temperature", "units": "degrees_Celsius"},
            {"name": "PSAL", "description": "Practical Salinity", "units": "PSU"},
            {"name": "PRES", "description": "Pressure", "units": "dbar"},
            {"name": "LATITUDE", "description": "Latitude", "units": "degrees_north"},
            {"name": "LONGITUDE", "description": "Longitude", "units": "degrees_east"}
              ]
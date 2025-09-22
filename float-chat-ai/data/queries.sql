-- Float-Chat-AI Database Initialization
-- Common SQL queries for ARGO oceanographic data analysis

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Example queries that could be used with actual ARGO data
-- These are templates that demonstrate the types of queries the system supports

-- 1. Average temperature by depth range
-- SELECT AVG(temperature) as avg_temp, depth_range
-- FROM argo_profiles 
-- WHERE depth BETWEEN ? AND ?
-- GROUP BY depth_range;

-- 2. Salinity profiles by location
-- SELECT latitude, longitude, depth, salinity
-- FROM argo_profiles
-- WHERE latitude BETWEEN ? AND ?
-- AND longitude BETWEEN ? AND ?
-- ORDER BY depth;

-- 3. Temperature-Salinity correlation
-- SELECT 
--     CORR(temperature, salinity) as temp_sal_correlation,
--     COUNT(*) as sample_count
-- FROM argo_profiles
-- WHERE temperature IS NOT NULL AND salinity IS NOT NULL;

-- 4. Seasonal temperature variations
-- SELECT 
--     EXTRACT(MONTH FROM measurement_date) as month,
--     AVG(temperature) as avg_temperature,
--     STDDEV(temperature) as temp_stddev
-- FROM argo_profiles
-- WHERE depth BETWEEN 0 AND 100  -- Surface layer
-- GROUP BY EXTRACT(MONTH FROM measurement_date)
-- ORDER BY month;

-- 5. Deep water characteristics
-- SELECT 
--     AVG(temperature) as deep_temp,
--     AVG(salinity) as deep_salinity,
--     AVG(pressure) as deep_pressure
-- FROM argo_profiles
-- WHERE depth > 1000;

-- Note: In the prototype, we use mock data generated in Python
-- These queries serve as examples of what would be possible with real ARGO data
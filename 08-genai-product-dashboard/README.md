# Phoenix Arize Product Dashboard

An interactive dashboard for analyzing GenAI product logs from Phoenix Arize, designed for product managers, data scientists, engineers, and research designers.

## Features

### 📈 Executive Summary
- High-level KPIs for leadership reporting
- Total requests, unique traces, success rates
- Token usage and latency metrics
- Model usage distribution

### 📊 Usage Analytics
- Request volume trends over time
- Token consumption patterns
- Detailed usage statistics by time period
- Model-specific usage breakdowns

### 🔍 Quality Analysis
- Qualitative review of prompts and outputs
- Search and filter interactions
- Flag slow or problematic responses
- Export filtered data for deeper analysis

### ⚡ Performance Metrics
- Latency distribution and percentiles
- Model performance comparisons
- Error analysis and tracking
- Performance trends over time

### 🔎 Log Explorer
- Raw data exploration
- Full dataset export (CSV/JSON)
- Column-level statistics
- Data preview and inspection

## Setup

### Prerequisites
- Python 3.8 or higher
- Access to a Phoenix Arize instance
- Optional: API key for authentication

### Installation

1. Clone or navigate to this directory:
```bash
cd phoenix-dashboard
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your environment:
```bash
cp .env.example .env
# Edit .env with your Phoenix API URL and API key
```

### Configuration

Edit the `.env` file with your Phoenix configuration:

```env
PHOENIX_API_URL=https://your-phoenix-instance.arize.com
PHOENIX_API_KEY=your_api_key_here
```

**Note:** If your Phoenix instance doesn't require authentication, you can leave the API key empty.

## Usage

### Start the Dashboard

Run the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

The dashboard will open in your web browser at `http://localhost:8501`

### Using the Dashboard

1. **Configure Connection**
   - Enter your Phoenix API URL in the sidebar
   - Add your API key if required
   - Select time range and filters

2. **Load Data**
   - Click "Load Data" to fetch traces from Phoenix
   - Wait for data to load (progress shown)
   - Data is cached for 5 minutes

3. **Explore Tabs**
   - **Executive Summary**: High-level metrics for leadership
   - **Usage Analytics**: Detailed usage patterns and trends
   - **Quality Analysis**: Review individual interactions
   - **Performance Metrics**: Latency and error analysis
   - **Log Explorer**: Raw data export and exploration

### API Reference

The dashboard uses the Phoenix REST API. Key endpoints:

- `/v1/projects` - List all projects
- `/v1/spans` - Retrieve spans/traces
- `/v1/traces/{id}` - Get specific trace details
- `/v1/datasets` - Access datasets

For full API documentation, visit: https://phoenix-demo.arize.com/apis

## Project Structure

```
phoenix-dashboard/
├── dashboard.py          # Main Streamlit application
├── phoenix_client.py     # Phoenix API client
├── data_analyzer.py      # Data analysis and processing
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variable template
└── README.md            # This file
```

## Key Modules

### PhoenixClient (`phoenix_client.py`)
Handles all interactions with the Phoenix REST API:
- Fetch spans and traces
- Project and dataset management
- Pagination handling
- Error handling and logging

### TraceAnalyzer (`data_analyzer.py`)
Processes and analyzes trace data:
- Convert spans to pandas DataFrames
- Calculate macro statistics
- Time series analysis
- Latency distribution
- Quality insights
- Token usage analysis

### Dashboard (`dashboard.py`)
Interactive Streamlit interface:
- Multi-tab interface
- Real-time data loading
- Interactive visualizations
- Search and filter capabilities
- Data export options

## Customization

### Adjust Data Loading
Modify the cache TTL in `dashboard.py`:
```python
@st.cache_data(ttl=300)  # Change to your preferred cache time in seconds
```

### Add Custom Metrics
Extend `TraceAnalyzer` in `data_analyzer.py` with new analysis methods:
```python
def your_custom_analysis(self) -> Dict:
    # Your analysis logic here
    return results
```

### Modify Visualizations
Update chart configurations in `dashboard.py` using Plotly Express or Graph Objects.

## Troubleshooting

### Connection Issues
- Verify your Phoenix API URL is correct
- Check if API key is required and properly configured
- Ensure network connectivity to Phoenix instance

### No Data Loading
- Check your time range filters
- Verify project ID if specified
- Try increasing max_spans limit
- Check Phoenix instance has data for selected period

### Performance Issues
- Reduce max_spans value
- Use shorter time ranges
- Clear cache and reload data
- Check system memory usage

## Best Practices

1. **For Leadership Reporting**
   - Use Executive Summary tab for high-level metrics
   - Export charts and metrics for presentations
   - Schedule regular data refreshes

2. **For Quality Analysis**
   - Use search functionality to find specific issues
   - Filter slow responses for performance investigation
   - Export filtered data for deeper analysis

3. **For Team Collaboration**
   - Share CSV exports with data scientists
   - Document findings in quality analysis tab
   - Use model comparison for optimization decisions

## Support and Documentation

- Phoenix Arize Documentation: https://arize.com/docs/phoenix/
- REST API Reference: https://phoenix-demo.arize.com/apis
- Streamlit Documentation: https://docs.streamlit.io/

## License

This dashboard is provided as-is for use with Phoenix Arize instances.

## Contributing

To add features or improvements:
1. Add new analysis methods to `data_analyzer.py`
2. Create new visualizations in `dashboard.py`
3. Extend API capabilities in `phoenix_client.py`
4. Update this README with new features


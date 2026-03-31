# 🚀 Quick Start Guide

## ✅ Setup Complete!

All required packages are installed and your dashboard is ready to use.

## 📝 Configuration (Required)

1. **Edit the `.env` file** with your Phoenix credentials:

```bash
# Open in your favorite editor
nano .env
# or
code .env
```

Update these values:
- `PHOENIX_API_URL`: Your Phoenix instance URL (e.g., `https://app.phoenix.arize.com` or your self-hosted URL)
- `PHOENIX_API_KEY`: Your API key (optional - leave as-is if no auth required)

## 🎯 Running the Dashboard

From the `phoenix-dashboard` directory, run:

```bash
streamlit run dashboard.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

## 🎨 Dashboard Features

### 📈 Executive Summary Tab
- **For Leadership Reporting**
- Total requests, success rates, latency metrics
- Token usage overview
- Model distribution

### 📊 Usage Analytics Tab
- **For Product Metrics**
- Request volume trends over time
- Token consumption patterns
- Time-based analytics (hourly/daily/weekly)

### 🔍 Quality Analysis Tab
- **For Qualitative Review**
- Search prompts and outputs
- Filter by status, model, performance
- Review individual interactions
- Export filtered data

### ⚡ Performance Metrics Tab
- **For Engineering Team**
- Latency distribution and percentiles
- Model performance comparison
- Error analysis

### 🔎 Log Explorer Tab
- **For Data Scientists**
- Raw data preview
- Export full dataset (CSV/JSON)
- Column statistics

## 💡 Usage Tips

### First Time Use
1. Start with "Last 24 Hours" or "Last 7 Days" timeframe
2. Keep max_spans at 10,000 for faster initial load
3. Click "Load Data" in the sidebar

### For Different Team Members

**Product Managers:**
- Use Executive Summary for stakeholder reports
- Usage Analytics for growth tracking
- Quality Analysis to identify improvement areas

**Data Scientists:**
- Log Explorer for data export
- Download CSV/JSON for analysis in Jupyter/Python
- Use filters to create focused datasets

**Engineers:**
- Performance Metrics for optimization
- Error Analysis for debugging
- Model comparison for evaluation

**Research Designers:**
- Quality Analysis to review user interactions
- Search functionality to find specific patterns
- Filter slow responses to identify UX issues

## 🔧 Troubleshooting

**"No data found":**
- Verify your `PHOENIX_API_URL` is correct
- Check if API key is required and properly set
- Try a different time range
- Confirm your Phoenix instance has data

**Slow loading:**
- Reduce `max_spans` value (try 1,000-5,000)
- Use shorter time ranges
- Data is cached for 5 minutes to improve performance

**Connection errors:**
- Verify network connectivity to Phoenix instance
- Check if firewall allows outbound connections
- Confirm API URL format (should include https://)

## 📊 Exporting Data

- **CSV Export**: Click download buttons in Quality Analysis or Log Explorer tabs
- **Charts**: Use Plotly's built-in export (camera icon on charts)
- **Screenshots**: Take screenshots of metrics for presentations

## 🆘 Need Help?

Refer to:
- Full documentation in `README.md`
- Phoenix API docs: https://phoenix-demo.arize.com/apis
- Phoenix documentation: https://arize.com/docs/phoenix/

## 🎉 You're All Set!

Your dashboard is ready. Just configure your `.env` file and run:

```bash
streamlit run dashboard.py
```


# CSE Stock Buying Suggesting System

A comprehensive stock analysis and recommendation system designed to help investors make informed decisions on the Colombo Stock Exchange (CSE). This system leverages historical data, technical indicators, and financial metrics to suggest optimal buying opportunities.

## Features

- **Stock Data Analysis**: Fetch and analyze historical stock data from the CSE
- **Technical Indicators**: Calculate moving averages, RSI, MACD, and other key indicators
- **Buying Recommendations**: AI-powered suggestions based on multiple analysis criteria
- **Portfolio Tracking**: Monitor and manage your stock portfolio
- **Price Predictions**: Predict future stock price movements using machine learning
- **Risk Assessment**: Evaluate risk factors and volatility metrics
- **Real-time Data**: Access up-to-date stock market information

## Tech Stack

- **Backend**: Python
- **Data Analysis**: Pandas, NumPy
- **Machine Learning**: Scikit-learn, TensorFlow (if applicable)
- **Database**: (Specify your database)
- **Frontend**: (Specify if applicable)
- **APIs**: CSE Data API / Web Scraping

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/nyenushapahan-lgtm/CSE-Stock-Buying-Suggesting-System.git
   cd CSE-Stock-Buying-Suggesting-System
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

## Usage

### Basic Example

```python
from stock_analyzer import StockAnalyzer

# Initialize the analyzer
analyzer = StockAnalyzer()

# Analyze a specific stock
analysis = analyzer.analyze_stock('SYMBOL')

# Get buying recommendations
recommendations = analyzer.get_recommendations()

# Print results
print(recommendations)
```

### Command Line Interface

```bash
# Get stock analysis
python main.py analyze --symbol SYMBOL

# Get buying recommendations
python main.py recommend --top 10

# Update stock data
python main.py update-data
```

## Project Structure

```
CSE-Stock-Buying-Suggesting-System/
├── README.md
├── requirements.txt
├── main.py
├── config/
│   └── settings.py
├── src/
│   ├── data/
│   │   ├── fetcher.py
│   │   └── preprocessor.py
│   ├── analysis/
│   │   ├── technical_indicators.py
│   │   └── stock_analyzer.py
│   ├── models/
│   │   ├── predictor.py
│   │   └── recommender.py
│   └── utils/
│       └── helpers.py
├── tests/
│   ├── test_analysis.py
│   └── test_recommender.py
└── notebooks/
    └── analysis.ipynb
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```
CSE_API_KEY=your_api_key_here
DATABASE_URL=your_database_url
LOG_LEVEL=INFO
```

For Ollama cloud analysis, add `OLLAMA_API_KEY` to the root `.env` file. The desktop app sends the key from server-side Python code and does not expose it to the UI.

## Data Sources

- Colombo Stock Exchange (CSE) official data
- Historical price data and market indices
- Company financial statements and reports

### Data freshness

When the desktop application starts, it repairs the historical-price and sector-mapping schema, then refreshes `resources/data/data.csv` from the CSE. While the application remains open, it checks for updates every 24 hours and retains existing historical rows. Dashboard and sector charts show the data source and latest available date; if refresh fails, they continue using available bundled or cached data.

Use **Data → Import → Fetching_CSE** to fetch a date range from the CSE, or **Data → Import → Upload_CSV** to import a local CSV into the historical prices table. CSV files must include `trade_date`, `symbol`, `name`, `open`, `high`, `low`, `close`, and `volume`; `turnover` and `pct_change` are optional. CSE API column names such as `closingPrice` and `sharevolume` are normalized automatically.

## Methodology

The system uses a multi-factor approach:

1. **Technical Analysis**: Trend analysis using moving averages and momentum indicators
2. **Fundamental Analysis**: P/E ratio, dividend yield, and financial health metrics
3. **Sentiment Analysis**: Market sentiment and news-based indicators
4. **Machine Learning**: Pattern recognition and predictive modeling

## Results Interpretation

### Buy Signals
- Green flags indicate strong buying opportunities
- Confidence scores (0-100%) show recommendation reliability
- Risk levels help assess volatility

### Recommendations
- **Strong Buy**: High confidence with favorable risk/reward ratio
- **Buy**: Good opportunity with moderate confidence
- **Hold**: Current position is stable
- **Sell**: Negative indicators suggest exiting the position

## Performance Metrics

- Accuracy: (Update with your actual metrics)
- Precision: (Update with your actual metrics)
- Recall: (Update with your actual metrics)

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your code follows PEP 8 style guidelines and includes appropriate tests.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=src
```

## Limitations & Disclaimers

⚠️ **Important**: 
- This system is for educational and informational purposes only
- Past performance does not guarantee future results
- Always conduct your own research before making investment decisions
- Consult with a qualified financial advisor before investing
- The system may not account for unexpected market events or black swan events

## Troubleshooting

### Common Issues

**Issue**: API connection failed
- **Solution**: Check internet connection and API key validity

**Issue**: Data not updating
- **Solution**: Verify data source availability and database connection

**Issue**: Incorrect predictions
- **Solution**: Ensure data is preprocessed correctly and model is retrained

## Future Enhancements

- [ ] Integration with real-time data feeds
- [ ] Advanced deep learning models
- [ ] Web-based dashboard
- [ ] Mobile application
- [ ] Portfolio optimization algorithms
- [ ] Risk management features
- [ ] Backtesting framework

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**nyenushapahan-lgtm**

## Acknowledgments

- Colombo Stock Exchange for data
- Community contributors
- Open-source libraries and frameworks

## Contact & Support

For questions, issues, or suggestions:
- Open an Issue on GitHub
- Contact: [your-email@example.com]
- Twitter: [@yourhandle]

## Changelog

### Version 1.0.0 (Initial Release)
- Basic stock analysis functionality
- Technical indicators implementation
- Initial buying recommendation system

---

**Last Updated**: 2026-07-10

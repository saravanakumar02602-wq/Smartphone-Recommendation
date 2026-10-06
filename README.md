# Phone Nexora

A personalized smartphone recommendation and comparison platform for India, built to help users discover the best phone based on their real needs rather than generic rankings.

Phone Nexora turns a simple brief like "best phone under ₹25,000 for gaming and long battery life" into a transparent recommendation engine that balances budget, priorities, technical constraints, and trade-offs.

## Why this project?

Smartphone buying decisions are often noisy and overwhelming. Most shoppers compare specs in isolation, but real purchasing decisions depend on:

- budget and value for money
- usage patterns such as gaming, photography, work, or travel
- hard constraints like minimum RAM, storage, or 5G support
- trade-offs between camera quality, battery life, and performance

Phone Nexora addresses this by combining:

- natural-language requirement parsing
- weighted personal scoring
- transparent explainability
- comparison and what-if analysis
- recommendation history and analytics

## Key features

- Natural-language requirement parsing for user intents
- Smart filtering based on budget, usage, and minimum spec thresholds
- Personalized scoring based on user-defined weights
- Top-N recommendation engine with explainable reasoning
- Conflict detection when user requirements are unrealistic or contradictory
- Trade-off analysis to compare competing options
- What-if analysis for budget changes or feature upgrades
- Phone-to-phone comparison with visual summaries
- Price tracking and historical analysis
- Recommendation history and preference learning
- Evaluation and analytics using Python and R

## Tech stack

- Backend: Python, Flask
- Data handling: pandas, NumPy
- Recommendation logic: scikit-learn, custom scoring models
- Database: SQLite
- Analytics: Python + R (dplyr, ggplot2, tidyr)
- Frontend: HTML, CSS, JavaScript, Bootstrap, Chart.js

## Project overview

The app follows a clear workflow:

1. User enters requirements or preference text
2. The app parses and normalizes the request
3. Price and technical constraints are applied
4. A personalized score is calculated using weighted sub-scores
5. Candidate phones are ranked with explainable reasons
6. Users can compare phones, explore trade-offs, and simulate budget changes

This is not a simple vendor list. It is a decision-support system that aims to make the recommendation logic understandable and actionable.

## Quick start

### Prerequisites

- Python 3.10+
- pip
- Optional: R (for advanced analytics charts)

### Installation

```bash
# Clone the repository
cd SmartPhoneMatch

# Create a virtual environment
python -m venv .venv

# Activate it
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run the app

```bash
python app.py
```

Then open the app in your browser:

```text
http://127.0.0.1:5000
```

## Project structure

```text
SmartPhoneMatch/
├── app.py                    # Flask application entry point
├── config.py                 # App configuration and constants
├── requirements.txt          # Python dependencies
├── data/
│   ├── phones.csv            # Smartphone catalogue
│   ├── price_history.csv     # Historical price observations
│   └── generate_data.py      # Data validation and generation utilities
├── database/
│   └── database.py           # SQLite database logic
├── recommendation/
│   ├── filtering.py          # Budget and constraint filtering
│   ├── scoring.py            # Personalized scoring engine
│   ├── preferences.py       # NLP parsing and weight learning
│   ├── explanation.py        # Explainable ranking reasons
│   ├── tradeoff.py           # Trade-off analysis
│   ├── conflict.py           # Requirement conflict detection
│   └── __init__.py           # Recommendation orchestration
├── services/
│   ├── phone_data.py         # Catalogue access and normalization
│   ├── price_tracker.py      # Pricing analytics and alerts
│   └── source_manager.py     # Data-source management
├── analytics/
│   └── evaluation.py         # Synthetic evaluation and export logic
├── R/
│   ├── analysis.R            # Summary analytics
│   ├── price_analysis.R      # Price analytics
│   └── recommendation_analysis.R
├── templates/
│   ├── index.html            # Landing page
│   ├── results.html          # Recommendation results
│   ├── compare.html          # Comparison page
│   ├── phone_details.html    # Phone details view
│   ├── what_if.html          # Scenario analysis
│   ├── history.html          # History / preferences
│   └── analytics.html        # Analytics dashboard
├── static/
│   ├── css/
│   ├── js/
│   └── r_output/            # Exported charts from R
└── README.md
```

## Recommendation engine

The engine scores phones across several dimensions, including:

- camera performance
- processing power and benchmark capability
- battery capacity and charging speed
- storage and memory
- display quality and refresh rate
- software and update support
- value per rupee

These dimensions are normalized and combined using user-defined weights, allowing a user to prioritize what matters most. The app also applies budget bands and near-budget adjustments to avoid overly optimistic recommendations.

## Data and reliability

The bundled catalogue is based on public India-market smartphone information and is intended for recommendation and comparison use.

Important notes:

- Prices are indicative launch-price references, not live offers
- Benchmark values are approximations for comparison use
- Specifications and availability should be verified with the seller before purchase
- Price-drop alerts require an authorized, trusted data feed
- Do not scrape sources whose terms prohibit automated access

## Analytics and evaluation

The project includes evaluation workflows for understanding recommendation quality and model behavior.

```bash
python -m analytics.evaluation
Rscript R/analysis.R
```

This generates charts and reports for:

- specification distributions
- catalogue price trends
- recommendation profile comparison
- quality checks
- response-time / evaluation summaries

## Use cases

Phone Nexora is useful for:

- comparing smartphones in a structured way
- finding the best value under a specific budget
- exploring trade-offs between camera, battery, and performance
- understanding why one phone is ranked above another
- simulating how budget changes affect rankings

## Future enhancements

Possible extension areas include:

- live pricing and retailer integration
- improved NLP interpretation for complex requirements
- user authentication and saved profiles
- more robust recommendation explanations and confidence scores
- mobile-friendly app interface improvements
- more advanced analytics dashboards

## Contributing

Contributions are welcome. If you want to improve the recommendation logic, add data sources, or improve the UX:

1. Fork the repository
2. Create a feature branch
3. Commit your improvements
4. Open a pull request with a clear summary of the changes

## Notes

- Chart.js, Bootstrap, and fonts are loaded from CDNs, so internet access is required in the browser
- The app automatically creates the SQLite database on first run
- All recommendation outputs are based on the available catalogue and user preferences, not real-time market feeds

## Project status

This project is designed as a practical recommendation engine and research-style comparison platform for smartphone shopping. It is suitable for learning, experimentation, and extension in data-driven product recommendation workflows.

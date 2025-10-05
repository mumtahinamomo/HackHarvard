# Political Campaign Finance Tracker

A comprehensive web application for exploring political campaign finance data, featuring interactive visualizations, AI-powered politician descriptions, and detailed funding network analysis.

## 🎯 Features

### Core Functionality
- **Politician Database**: Browse and search through thousands of political candidates
- **Campaign Finance Data**: View detailed financial information including receipts, contributions, and funding sources
- **Interactive Filtering**: Live-updating filters for chamber, state, party, and search terms
- **Pagination**: Efficient handling of large datasets with paginated results

### Advanced Features
- **AI-Generated Descriptions**: Dynamic politician descriptions powered by Google's Gemini AI
- **Funding Network Visualization**: Interactive D3.js graphs showing funding connections and sources
- **Real-time Filter Counts**: Live updates showing remaining options as you apply filters
- **Responsive Design**: Mobile-friendly interface built with Bootstrap 5

### Data Visualization
- **Force-Directed Graphs**: Network visualization of funding relationships
- **Funding Source Analysis**: Color-coded nodes showing individual, PAC, and party funding
- **Interactive Exploration**: Click and drag nodes to explore funding networks

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mumtahinamomo/HackHarvard.git
   cd HackHarvard
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```bash
   SECRET_KEY=your_secret_key_here
   DATABASE_URI=sqlite:///database.db
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Initialize the database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## 📊 Database Setup

The application uses SQLite for development and can be configured for other databases in production.

## 🛠️ Development

### Project Structure
```
HackHarvard/
├── flask_app/                 # Main Flask application
│   ├── templates/            # HTML templates
│   ├── static/              # CSS, JS, and assets
│   ├── graph/               # Graph visualization components
│   ├── models.py            # Database models
│   ├── routes.py            # Main routes
│   ├── politician_routes.py # Politician-specific routes
│   └── graph_api.py         # Graph API endpoints
├── migrations/              # Database migrations
├── instance/               # Database files
├── requirements.txt        # Python dependencies
└── run.py                 # Application entry point
```

### Key Components

#### Flask Routes
- `/` - Homepage
- `/list_politicians` - Politician listing with filters
- `/politician/<id>` - Individual politician details
- `/api/politicians` - JSON API for politician data
- `/generate_description/<id>` - AI description generation
- `/graph/<id>` - Network visualization for specific politician
- `/network` - Standalone network viewer

#### Database Models
- `Politician`: Main model storing candidate information, financial data, and AI-generated descriptions

#### External Integrations
- **Google Gemini AI**: For generating politician descriptions
- **D3.js**: For interactive network visualizations
- **Bootstrap 5**: For responsive UI components
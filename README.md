# Data Science Platform

> **Advanced Analytics • AI Insights • Visual Intelligence**  
> *Crafted by Hasnain & Co*

---

## Overview

A comprehensive data science platform that empowers users to upload, analyze, visualize, and gain AI-powered insights from their CSV datasets. Built with modern web technologies and powered by advanced analytics engines.

## Features

### 📊 **Data Analysis**
- Statistical summaries and distributions
- Correlation analysis
- Missing value detection
- Data quality assessment

### 📈 **Interactive Visualizations**
- **AutoViz**: Automated visualization generation
- **SweetViz**: Comprehensive EDA reports
- **Tableau Integration**: Enterprise-grade dashboards
- Custom chart builders

### 🤖 **AI-Powered Insights**
- **LangGraph Workflows**: 5 specialized analysis modes
  - Summary: Dataset overview & statistics
  - Trends: Pattern detection & variability analysis
  - Insights: Business takeaways & recommendations
  - Anomalies: Outlier detection & data quality
  - Correlations: Relationship discovery

### 🧹 **Data Preprocessing**
- Missing value imputation
- Outlier handling
- Feature scaling & normalization
- Data transformation

---

## Tech Stack

**Frontend:**
- React 18.3.1
- Framer Motion for animations
- Chart.js for visualizations
- React Router for navigation

**Backend:**
- Node.js + Express
- MongoDB for data persistence
- Python integration for analytics
- Multer for file uploads

**Analytics Engines:**
- AutoViz
- SweetViz
- LangGraph
- Pandas & NumPy

---

## Installation

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- MongoDB (optional, for data persistence)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ProjectData
   ```

2. **Install Backend Dependencies**
   ```bash
   cd backend
   npm install
   ```

3. **Install Python Dependencies**
   ```bash
   cd backend/scripts
   pip install -r requirements.txt
   ```

4. **Install Frontend Dependencies**
   ```bash
   cd ../../frontend
   npm install
   ```

5. **Configure Environment**
   
   Create `backend/.env`:
   ```env
   PORT=5000
   MONGODB_URI=mongodb://localhost:27017/datascienceplatform
   NODE_ENV=development
   ```

---

## Usage

### Start Backend Server
```bash
cd backend
npm start
```
Backend runs on `http://localhost:5000`

### Start Frontend
```bash
cd frontend
npm start
```
Frontend runs on `http://localhost:3000`

### Using the Platform

1. **Upload Data**: Drag & drop or select CSV files
2. **Analyze**: View statistical summaries and insights
3. **Visualize**: Generate automated charts and reports
4. **AI Insights**: Run LangGraph analysis in different modes
5. **Preprocess**: Clean and transform your data
6. **Export**: Download processed data and reports

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload CSV file |
| `/api/analyze` | POST | Analyze dataset |
| `/api/generate-autoviz` | POST | Generate AutoViz visualizations |
| `/api/generate-sweetviz` | POST | Generate SweetViz report |
| `/api/generate-ai-insights` | POST | Run LangGraph analysis |
| `/api/preprocess` | POST | Clean and transform data |

---

## Project Structure

```
ProjectData/
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main application
│   │   ├── App.css        # Global styles
│   │   ├── FileUpload.js  # Upload component
│   │   ├── DataAnalysis.js
│   │   ├── Visualization.js
│   │   ├── AIInsights.js
│   │   └── DataPreprocessing.js
│   └── public/
│
├── backend/               # Express backend
│   ├── server.js         # Main server
│   ├── config/           # Database config
│   ├── models/           # MongoDB models
│   └── scripts/          # Python analytics
│       ├── langgraph_analyzer.py
│       ├── autoviz_generator.py
│       └── sweetviz_generator.py
│
├── uploads/              # Temporary file storage
└── README.md            # This file
```

---

## Development

### Run Tests
```bash
# Backend tests
cd backend
npm test

# Python script tests
cd backend/scripts
python test_langgraph_modes.py
```

### Build for Production
```bash
# Frontend
cd frontend
npm run build

# Deploy build folder to your hosting service
```

---

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact: support@hasnainandco.com

---

<div align="center">
  <strong>Crafted with ❤️ by Hasnain & Co</strong>
  <br>
  <em>Empowering data-driven decisions</em>
</div>

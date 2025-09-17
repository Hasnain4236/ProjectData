# 🚀 Professional Data Science Platform# Professional Data Science Platform 🚀



A comprehensive data analysis platform with AutoViz and SweetViz integration for automated data visualization and quality assessment.[![Docker](https://img.shields.io/badge/Docker-Containerized-blue.svg)](https://docker.com)

[![React](https://img.shields.io/badge/React-18.3.1-blue.svg)](https://reactjs.org)

## ⚡ Quick Start (Local Development)[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org)

[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://mongodb.com)

### 🎯 One-Click Startup[![Python](https://img.shields.io/badge/Python-3.9+-yellow.svg)](https://python.org)

```bash

# Just double-click this file!A comprehensive, containerized data science platform featuring **AutoViz**, **SweetViz**, advanced analytics, and AI-powered insights. Built with modern technologies and production-ready Docker configuration.

run-local.bat

```## ✨ Features



### 🏃‍♂️ Quick Start (No Setup Check)### 🎯 Core Capabilities

```bash- **📊 AutoViz Integration** - Automated visualization generation with 1000+ chart types

# For experienced users- **🍭 SweetViz Reports** - Comprehensive data profiling and analysis

quick-start.bat- **🧹 Data Preprocessing** - Advanced cleaning, transformation, and quality analysis

```- **🤖 AI Insights** - Machine learning-powered recommendations and patterns

- **📈 Real-time Analytics** - Live data processing and visualization updates

### 🛑 Stop All Servers

```bash### 🏗️ Architecture

stop-servers.bat- **Frontend**: React 18.3.1 with modern hooks, Framer Motion animations

```- **Backend**: Node.js/Express 5.0 with MongoDB integration

- **Python Engine**: AutoViz, SweetViz, Pandas, NumPy, Scikit-learn

## 🌐 Access URLs- **Database**: MongoDB 7.0 with optimized schemas

- **Containerization**: Docker with multi-stage builds and orchestration

- **Frontend**: http://localhost:3000

- **Backend API**: http://localhost:5000  ### 🔧 Technical Highlights

- **Health Check**: http://localhost:5000/api/health- **Professional UI/UX** - Clean, responsive design with navigation cards

- **Multi-format Support** - CSV, JSON, XLSX, ARF file processing

## 🎯 Features- **Production Security** - Helmet.js, CORS, input validation, rate limiting

- **Health Monitoring** - Built-in health checks and error handling

- ✅ **Data Upload** - CSV file processing- **Scalable Architecture** - Microservices-ready with Docker Compose

- ✅ **AutoViz Integration** - 1000+ automated visualizations

- ✅ **SweetViz Analysis** - Comprehensive data profiling## 🚀 Quick Start (One Command!)

- ✅ **Data Preprocessing** - Quality analysis and cleaning

- ✅ **Interactive UI** - Professional React interface### Prerequisites

- ✅ **MongoDB Storage** - Data persistence- Docker & Docker Compose

- ✅ **Python Analytics** - Advanced data processing- Git



## 📋 Requirements### Production Deployment

```bash

- **Node.js** 18+ # Clone and run in one command!

- **Python** 3.8+git clone <your-repo-url>

- **MongoDB** (Atlas or local)cd ProjectData

docker-compose up -d

## 🔧 Manual Setup (if needed)```



```bash**That's it!** 🎉 

# Backend- **Frontend**: http://localhost

cd backend- **Backend API**: http://localhost:5000

npm install- **Health Check**: http://localhost/health

npm start

### Development Mode

# Frontend (in new terminal)```bash

cd frontend# For development with hot reload

npm install --legacy-peer-depsdocker-compose -f docker-compose.dev.yml up -d

npm start```

```- **Frontend**: http://localhost:3000 (hot reload)

- **Backend**: http://localhost:5000 (nodemon)

## 🚀 Coming Soon - Cloud Deployment

## 📖 Usage Guide

- **Frontend**: Vercel deployment

- **Backend**: Railway/Render deployment  ### 1. **Upload Data**

- **Database**: MongoDB Atlas (already configured)- Drag & drop CSV files up to 100MB

- Support for multiple encodings and formats

## 📊 Tech Stack- Real-time validation and preview



- **Frontend**: React 18 + Create React App### 2. **Data Analysis**

- **Backend**: Node.js + Express 5- Automatic statistical analysis

- **Database**: MongoDB + Mongoose- Missing values detection

- **Analytics**: Python (AutoViz, SweetViz, Pandas)- Data type inference and correlation analysis

- **Visualization**: Chart.js, Plotly

- **Styling**: CSS3 + Animations### 3. **Generate Visualizations**

```bash

---# AutoViz - Automated EDA

Happy Analyzing! 🎉Click "Generate AutoViz Report" → Opens professional charts

# SweetViz - Data profiling
Click "Generate SweetViz Report" → Comprehensive analysis
```

### 4. **Data Preprocessing**
- Quality metrics calculation
- Duplicate detection and removal
- Missing value imputation
- Outlier detection and treatment

### 5. **AI Insights**
- Pattern recognition
- Anomaly detection
- Automated recommendations
- Predictive insights

## 🏗️ Project Structure

```
ProjectData/
├── backend/                 # Node.js API server
│   ├── scripts/            # Python data processing
│   │   ├── autoviz_generator.py
│   │   ├── sweetviz_generator.py
│   │   └── requirements.txt
│   ├── config/             # Database configuration
│   ├── models/             # MongoDB schemas
│   ├── uploads/            # File storage
│   ├── visualizations/     # Generated reports
│   ├── Dockerfile          # Backend container
│   └── server.js           # Main server file
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── FileUpload.js   # Drag & drop upload
│   │   ├── Visualization.js # AutoViz/SweetViz integration
│   │   ├── DataPreprocessing.js # Data cleaning UI
│   │   └── App.js          # Main application
│   ├── Dockerfile          # Frontend container
│   └── nginx.conf          # Production web server
├── docker-compose.yml      # Production orchestration
├── docker-compose.dev.yml  # Development setup
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

**Backend** (`.env`):
```env
PORT=5000
NODE_ENV=production
MONGODB_URI=mongodb://admin:datascience2024@mongodb:27017/dataprocessing?authSource=admin
FRONTEND_URL=http://localhost
MAX_FILE_SIZE=104857600
```

**Frontend** (production handled by nginx proxy):
```env
REACT_APP_API_URL=http://localhost:5000
```

### Database Setup
MongoDB is automatically initialized with:
- Admin user: `admin:datascience2024`
- App user: `datauser:datapass2024`
- Optimized indexes for performance
- Health checks and replication ready

## 📊 API Endpoints

### Core Data Processing
- `POST /api/upload` - File upload with validation
- `POST /api/analyze-csv` - Statistical analysis
- `POST /api/clean-csv` - Data cleaning and preprocessing
- `GET /api/health` - Service health check

### Visualization Generation
- `POST /api/generate-autoviz` - AutoViz report creation
- `POST /api/generate-sweetviz` - SweetViz profiling
- `GET /api/visualizations/*` - Static report serving

### Data Management
- `GET /api/jobs` - Processing job history
- `GET /api/jobs/:jobId` - Specific job details
- `GET /api/download/:filename` - File downloads

## 🐳 Docker Architecture

### Multi-Stage Builds
- **Base**: System dependencies and Python environment
- **Development**: Hot reload with volume mounting
- **Production**: Optimized, security-hardened containers

### Container Security
- Non-root users in all containers
- Minimal attack surface with Alpine Linux
- Security headers and input validation
- Resource limits and health monitoring

### Orchestration Features
- **Service Dependencies** - Proper startup ordering
- **Health Checks** - Automatic restart on failure
- **Volume Management** - Persistent data storage
- **Network Isolation** - Secure inter-service communication

## 🚀 Production Deployment

### Docker Swarm (Recommended)
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml datascience

# Scale services
docker service scale datascience_backend=3
docker service scale datascience_frontend=2
```

### Kubernetes
```bash
# Convert to Kubernetes
kompose convert -f docker-compose.yml

# Deploy to cluster
kubectl apply -f .
```

### Cloud Deployment
- **AWS**: ECS/EKS with RDS MongoDB
- **Azure**: Container Instances with Cosmos DB
- **GCP**: Cloud Run with MongoDB Atlas

## 🔍 Monitoring & Logging

### Health Checks
- **Frontend**: Nginx health endpoint
- **Backend**: Express health with dependency checks
- **Database**: MongoDB ping with authentication

### Logging
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Production monitoring
docker stats
docker-compose ps
```

## 🧪 Testing

### Local Testing
```bash
# Run health checks
curl http://localhost/health
curl http://localhost:5000/api/health

# Test file upload
curl -X POST -F "file=@test.csv" http://localhost:5000/api/upload
```

### Integration Tests
```bash
# Backend tests
cd backend && npm test

# Frontend tests  
cd frontend && npm test
```

## 🛠️ Development

### Adding New Features
1. **Backend**: Add routes in `server.js`, models in `/models`
2. **Frontend**: Create components in `/src`, integrate with existing flow
3. **Python**: Add scripts in `/backend/scripts`, update requirements.txt
4. **Database**: Update schemas in `/models`, add migrations

### Hot Reload Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Code changes auto-reload:
# - Backend: nodemon restarts on file changes
# - Frontend: React hot reload for instant updates
# - Database: persistent volume for data retention
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AutoViz** - Automated visualization library
- **SweetViz** - Data profiling and comparison
- **React** - Frontend framework
- **Express.js** - Backend framework
- **MongoDB** - Database solution
- **Docker** - Containerization platform

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` folder
- **Examples**: `/examples` folder

---

**Built with ❤️ for the data science community**

*Professional Data Science Platform - Making data analysis accessible, powerful, and beautiful.*
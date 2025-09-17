# Data Processing & Analysis API Backend

A robust Node.js/Express API server for handling data processing, analysis, and AI-powered insights.

## Features

- **File Upload**: Support for CSV, JSON, XLSX, and ARF files (up to 100MB)
- **Data Processing**: Automated data cleaning and preprocessing
- **Statistical Analysis**: Comprehensive statistical computations
- **Data Visualization**: Generate chart data for various visualization types
- **AI Insights**: Automated pattern detection and recommendations
- **Security**: Helmet.js security middleware and CORS protection
- **Logging**: Morgan request logging for monitoring

## API Endpoints

### Core Endpoints

- `GET /` - API information and available endpoints
- `GET /api/health` - Health check and server status

### Data Processing

- `POST /api/upload` - Upload data files
- `POST /api/process` - Process and clean uploaded data
- `POST /api/analyze` - Perform statistical analysis
- `POST /api/visualize` - Generate visualization data
- `POST /api/insights` - Get AI-powered insights

## Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start development server:
```bash
npm run dev
```

4. Start production server:
```bash
npm start
```

## File Upload

The API accepts files via multipart/form-data:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:5000/api/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Data Processing Pipeline

1. **Upload**: Files are stored securely with validation
2. **Process**: Data cleaning, deduplication, type conversion
3. **Analyze**: Statistical analysis and correlation computation
4. **Visualize**: Chart data generation for frontend
5. **Insights**: AI-powered pattern detection and recommendations

## Security Features

- File type validation
- File size limits (100MB)
- CORS protection
- Helmet.js security headers
- Input sanitization
- Error handling middleware

## Development

- `npm run dev` - Start with nodemon for auto-restart
- `npm start` - Start production server
- `npm test` - Run tests (to be implemented)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PORT | Server port | 5000 |
| NODE_ENV | Environment | development |
| FRONTEND_URL | Frontend URL for CORS | http://localhost:3000 |
| MAX_FILE_SIZE | Maximum upload size | 104857600 (100MB) |

## Future Enhancements

- [ ] Database integration (MongoDB/PostgreSQL)
- [ ] User authentication and authorization
- [ ] Real-time processing with WebSockets
- [ ] Advanced ML model integration
- [ ] Caching with Redis
- [ ] Rate limiting
- [ ] API documentation with Swagger
- [ ] Unit and integration tests
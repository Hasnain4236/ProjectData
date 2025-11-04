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
| OPENAI_API_KEY | API key for OpenAI chat completions | — |
| GITHUB_TOKEN | GitHub token with `models` scope for GitHub Models | — |
| AZURE_OPENAI_ENDPOINT | Azure OpenAI endpoint URL | — |
| AZURE_OPENAI_KEY | Azure OpenAI API key | — |
| AZURE_OPENAI_API_VERSION | Azure OpenAI API version | 2024-02-15-preview |
| GEMINI_API_KEY | Google AI Studio (Gemini) API key | — |
| GEMINI_MODEL | Gemini model to use when Gemini is selected | gemini-1.5-flash |
| LLM_MODEL | Override model for other providers (OpenAI/Azure/GitHub) | gpt-4o |
| LLM_PROVIDER | Force provider selection (`gemini`, `openai`, `github`, `azure`) | gemini |

### LLM Question Answering

The `/api/ask-question` route uses LangGraph and LangChain to call an LLM for dataset Q&A. Provider selection follows this order:

1. Explicit `LLM_PROVIDER` value (`gemini`, `openai`, `github`, or `azure`).
2. Gemini if `GEMINI_API_KEY` is present (and `langchain-google-genai` is installed).
3. Azure OpenAI if `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` are set.
4. OpenAI if `OPENAI_API_KEY` is present.
5. GitHub Models if `GITHUB_TOKEN` is set.

> **Important:** GitHub personal access tokens must include the **`models`** permission to access GitHub Models. Tokens without this scope will trigger an unauthorized (401) response. Rotate your token if you see the error `The "models" permission is required to access this endpoint`.

If multiple providers are configured you can override the automatic selection with `LLM_PROVIDER`. Use `GEMINI_MODEL` to target a specific Gemini model (for example, `gemini-1.5-pro`), or `LLM_MODEL` for OpenAI/Azure/GitHub deployments.

#### Failure-handling

- **Rule-based answers:** Common data-quality questions (missing values, duplicate rows, row/column counts, column lists, average age) are answered immediately from metadata without hitting an external model. These responses show up with `method: "rule_based"`.
- **Provider failover:** If the preferred provider returns rate limits or internal errors, the analyzer automatically tries the next configured provider. Errors are surfaced in the response metadata (`llm_errors`) for observability.
- **Graceful degradation:** When every provider fails, the API returns a deterministic dataset summary instead of bubbling a 500 error. The response includes guidance to retry or adjust `LLM_PROVIDER`.

## Future Enhancements

- [ ] Database integration (MongoDB/PostgreSQL)
- [ ] User authentication and authorization
- [ ] Real-time processing with WebSockets
- [ ] Advanced ML model integration
- [ ] Caching with Redis
- [ ] Rate limiting
- [ ] API documentation with Swagger
- [ ] Unit and integration tests
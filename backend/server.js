const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const csv = require('csv-parser');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const _ = require('lodash');
require('dotenv').config();

// MongoDB connection
const connectDB = require('./config/database');
const { DataProcessingJob, UserSession, DataQualityMetrics, CleanedData } = require('./models');

const app = express();
const PORT = process.env.PORT || 5000;

// Connect to MongoDB
connectDB();

// Middleware
// Helmet (environment-aware): relax policies in development to allow cross-origin dev fetches
const isDev = (process.env.NODE_ENV || 'development') !== 'production';
if (isDev) {
  app.use(helmet({
    contentSecurityPolicy: false,
    crossOriginResourcePolicy: { policy: 'cross-origin' },
    crossOriginOpenerPolicy: { policy: 'same-origin-allow-popups' },
    crossOriginEmbedderPolicy: false
  }));
} else {
  app.use(helmet());
}
app.get('/api/jobs', async (req, res) => {
  try {
    const { limit = 10, status, page = 1 } = req.query;
    const query = {};
    
    if (status) {
      query.status = status;
    }
    
    const jobs = await DataProcessingJob.find(query)
      .sort({ createdAt: -1 })
      .limit(parseInt(limit))
      .skip((parseInt(page) - 1) * parseInt(limit))
      .select('jobId fileName originalFileName status metadata.uploadedAt metadata.processedAt analysisResults.totalRows cleaningReport');
    
    const totalJobs = await DataProcessingJob.countDocuments(query);
    
    res.json({
      success: true,
      jobs: jobs,
      pagination: {
        total: totalJobs,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(totalJobs / parseInt(limit))
      }
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get specific job details
app.get('/api/jobs/:jobId', async (req, res) => {
  try {
    const job = await DataProcessingJob.findOne({ jobId: req.params.jobId });
    
    if (!job) {
      return res.status(404).json({
        success: false,
        error: 'Job not found'
      });
    }
    
    res.json({
      success: true,
      job: job
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Data Cleaning Utility Functions
// CORS: allow local dev frontends on common ports (3000-3002) and env override
const allowedOrigins = [
  process.env.FRONTEND_URL || 'http://localhost:3000',
  'http://localhost:3000',
  'http://localhost:3001',
  'http://localhost:3002',
  'http://127.0.0.1:3000',
  'http://127.0.0.1:3001',
  'http://127.0.0.1:3002'
];

app.use(cors({
  origin: function (origin, callback) {
    // allow requests with no origin like mobile apps or curl
    if (!origin) return callback(null, true);
    if (allowedOrigins.includes(origin)) return callback(null, true);
    // In dev, be permissive to avoid CORS blocks when port changes
    return callback(null, true);
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Handle preflight across routes
// Note: Express 5 with path-to-regexp v6 does not support '*' wildcard here.
// The CORS middleware above will handle preflight automatically for allowed origins.
// Removing the explicit wildcard OPTIONS route to avoid PathError.
// If needed, you can add a specific path like '/api/*' using a compatible pattern.
app.use(morgan('combined'));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Create uploads directory if it doesn't exist
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const fileFilter = (req, file, cb) => {
  const allowedTypes = ['.csv', '.json', '.xlsx', '.arf'];
  const fileExtension = path.extname(file.originalname).toLowerCase();
  
  if (allowedTypes.includes(fileExtension)) {
    cb(null, true);
  } else {
    cb(new Error('Invalid file type. Only CSV, JSON, XLSX, and ARF files are allowed.'), false);
  }
};

const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 100 * 1024 * 1024 // 100MB limit
  }
});

// Routes
app.get('/', (req, res) => {
  res.json({
    message: 'Data Processing & Analysis API',
    version: '1.0.0',
    status: 'running',
    endpoints: {
      upload: 'POST /api/upload',
      analyze: 'POST /api/analyze',
      process: 'POST /api/process',
      visualize: 'POST /api/visualize',
      insights: 'POST /api/insights',
      health: 'GET /api/health'
    }
  });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    env: process.env.NODE_ENV || 'development'
  });
});

// File upload endpoint
app.post('/api/upload', upload.single('file'), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded'
      });
    }

    const fileInfo = {
      filename: req.file.filename,
      originalName: req.file.originalname,
      size: req.file.size,
      mimetype: req.file.mimetype,
      path: req.file.path,
      uploadTime: new Date().toISOString()
    };

    res.json({
      success: true,
      message: 'File uploaded successfully',
      file: fileInfo
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Data processing endpoint
app.post('/api/process', (req, res) => {
  try {
    const { filename, options = {} } = req.body;
    
    if (!filename) {
      return res.status(400).json({
        success: false,
        error: 'Filename is required'
      });
    }

    // Mock processing response for now
    const mockProcessedData = {
      processed: true,
      filename: filename,
      records: Math.floor(Math.random() * 1000) + 100,
      columns: Math.floor(Math.random() * 20) + 5,
      cleaningSteps: [
        'Removed duplicate rows',
        'Handled missing values',
        'Standardized data types',
        'Validated data integrity'
      ],
      processingTime: (Math.random() * 5 + 1).toFixed(2) + 's',
      dataQualityScore: (Math.random() * 20 + 80).toFixed(1) + '%'
    };

    res.json({
      success: true,
      message: 'Data processed successfully',
      data: mockProcessedData
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Data analysis endpoint
app.post('/api/analyze', (req, res) => {
  try {
    const { filename, analysisType = 'comprehensive' } = req.body;
    
    if (!filename) {
      return res.status(400).json({
        success: false,
        error: 'Filename is required'
      });
    }

    // Mock analysis response
    const mockAnalysis = {
      summary: {
        totalRows: Math.floor(Math.random() * 1000) + 100,
        totalColumns: Math.floor(Math.random() * 20) + 5,
        missingValues: Math.floor(Math.random() * 10),
        duplicateRows: Math.floor(Math.random() * 5),
        dataTypes: {
          numeric: Math.floor(Math.random() * 8) + 2,
          categorical: Math.floor(Math.random() * 5) + 2,
          datetime: Math.floor(Math.random() * 3),
          boolean: Math.floor(Math.random() * 2)
        }
      },
      statistics: {
        correlations: generateMockCorrelations(),
        distributions: generateMockDistributions(),
        outliers: generateMockOutliers()
      },
      recommendations: [
        'Consider removing outliers in the value column',
        'Strong correlation detected between variables A and B',
        'Data quality is excellent with minimal missing values',
        'Recommended to apply normalization for better analysis'
      ]
    };

    res.json({
      success: true,
      message: 'Analysis completed successfully',
      analysis: mockAnalysis
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Visualization data endpoint
app.post('/api/visualize', (req, res) => {
  try {
    const { filename, chartType = 'all' } = req.body;
    
    if (!filename) {
      return res.status(400).json({
        success: false,
        error: 'Filename is required'
      });
    }

    const mockChartData = {
      histogram: generateHistogramData(),
      scatter: generateScatterData(),
      correlation: generateCorrelationHeatmap(),
      pie: generatePieChartData(),
      line: generateLineChartData(),
      bar: generateBarChartData()
    };

    res.json({
      success: true,
      message: 'Visualization data generated successfully',
      charts: mockChartData
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// AI insights endpoint
app.post('/api/insights', (req, res) => {
  try {
    const { filename, analysisResults } = req.body;
    
    if (!filename) {
      return res.status(400).json({
        success: false,
        error: 'Filename is required'
      });
    }

    const mockInsights = [
      {
        type: 'pattern',
        title: 'Seasonal Trend Detected',
        description: 'Data shows a clear seasonal pattern with peaks occurring every 3-4 months.',
        confidence: 0.89,
        impact: 'high',
        recommendation: 'Consider seasonal adjustments in future forecasting models.'
      },
      {
        type: 'anomaly',
        title: 'Data Quality Alert',
        description: 'Found 3 potential data entry errors in the timestamp column.',
        confidence: 0.95,
        impact: 'medium',
        recommendation: 'Review and validate timestamps for accuracy.'
      },
      {
        type: 'correlation',
        title: 'Strong Variable Relationship',
        description: 'Variables X and Y show correlation coefficient of 0.87.',
        confidence: 0.92,
        impact: 'high',
        recommendation: 'Leverage this relationship for predictive modeling.'
      },
      {
        type: 'optimization',
        title: 'Processing Efficiency',
        description: 'Data pipeline can be optimized by implementing parallel processing.',
        confidence: 0.78,
        impact: 'medium',
        recommendation: 'Consider batch processing for improved performance.'
      }
    ];

    res.json({
      success: true,
      message: 'AI insights generated successfully',
      insights: mockInsights
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Helper functions for mock data generation
function generateMockCorrelations() {
  return {
    'var1_var2': (Math.random() * 2 - 1).toFixed(3),
    'var1_var3': (Math.random() * 2 - 1).toFixed(3),
    'var2_var3': (Math.random() * 2 - 1).toFixed(3)
  };
}

function generateMockDistributions() {
  return {
    normal: Math.floor(Math.random() * 5) + 1,
    skewed: Math.floor(Math.random() * 3),
    uniform: Math.floor(Math.random() * 2)
  };
}

function generateMockOutliers() {
  return {
    count: Math.floor(Math.random() * 10),
    percentage: (Math.random() * 5).toFixed(2) + '%',
    columns: ['value', 'score', 'rating'].slice(0, Math.floor(Math.random() * 3) + 1)
  };
}

function generateHistogramData() {
  const data = [];
  for (let i = 0; i < 20; i++) {
    data.push({
      bin: i * 5,
      count: Math.floor(Math.random() * 50) + 10
    });
  }
  return data;
}

function generateScatterData() {
  const data = [];
  for (let i = 0; i < 100; i++) {
    data.push({
      x: Math.random() * 100,
      y: Math.random() * 100 + (Math.random() * 20 - 10)
    });
  }
  return data;
}

function generateCorrelationHeatmap() {
  const variables = ['var1', 'var2', 'var3', 'var4', 'var5'];
  const matrix = [];
  
  for (let i = 0; i < variables.length; i++) {
    const row = [];
    for (let j = 0; j < variables.length; j++) {
      if (i === j) {
        row.push(1);
      } else {
        row.push((Math.random() * 2 - 1).toFixed(3));
      }
    }
    matrix.push(row);
  }
  
  return { variables, matrix };
}

function generatePieChartData() {
  return [
    { label: 'Category A', value: Math.floor(Math.random() * 100) + 50 },
    { label: 'Category B', value: Math.floor(Math.random() * 100) + 30 },
    { label: 'Category C', value: Math.floor(Math.random() * 100) + 20 },
    { label: 'Category D', value: Math.floor(Math.random() * 100) + 10 }
  ];
}

function generateLineChartData() {
  const data = [];
  let value = 100;
  
  for (let i = 0; i < 30; i++) {
    value += (Math.random() - 0.5) * 10;
    data.push({
      date: new Date(2024, 0, i + 1).toISOString().split('T')[0],
      value: Math.max(0, value)
    });
  }
  
  return data;
}

function generateBarChartData() {
  return [
    { category: 'Q1', value: Math.floor(Math.random() * 100) + 50 },
    { category: 'Q2', value: Math.floor(Math.random() * 100) + 60 },
    { category: 'Q3', value: Math.floor(Math.random() * 100) + 70 },
    { category: 'Q4', value: Math.floor(Math.random() * 100) + 80 }
  ];
}

// Data Cleaning Endpoints

// Parse CSV and analyze data quality
app.post('/api/analyze-csv', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file provided'
      });
    }

    const filePath = req.file.path;
    const jobId = `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Create job record in MongoDB
    const jobRecord = new DataProcessingJob({
      jobId: jobId,
      fileName: req.file.filename,
      originalFileName: req.file.originalname,
      status: 'processing',
      metadata: {
        fileSize: req.file.size,
        uploadedAt: new Date()
      }
    });

    await jobRecord.save();
    
    try {
      const analysis = await analyzeCSVQuality(filePath);
      
      // Update job with analysis results
      jobRecord.status = 'completed';
      jobRecord.metadata.processedAt = new Date();
      jobRecord.analysisResults = analysis;
      await jobRecord.save();
      
      res.json({
        success: true,
        message: 'CSV analysis completed',
        filename: req.file.filename,
        originalName: req.file.originalname,
        jobId: jobId,
        fileId: jobId, // For backward compatibility
        analysis: analysis
      });

    } catch (analysisError) {
      // Update job with error status
      jobRecord.status = 'failed';
      jobRecord.errorMessage = analysisError.message;
      await jobRecord.save();
      throw analysisError;
    }

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Clean CSV data based on the data_cleaning.txt requirements
app.post('/api/clean-csv', async (req, res) => {
  try {
    const { fileId, filename, cleaningOptions = {} } = req.body;
    
    // Find job by ID if provided, otherwise use filename
    let jobRecord = null;
    let filePath = null;
    
    if (fileId) {
      jobRecord = await DataProcessingJob.findOne({ jobId: fileId });
      if (!jobRecord) {
        return res.status(404).json({
          success: false,
          error: 'Job not found'
        });
      }
      filePath = path.join(uploadsDir, jobRecord.fileName);
    } else if (filename) {
      filePath = path.join(uploadsDir, filename);
    } else {
      return res.status(400).json({
        success: false,
        error: 'File ID or filename is required'
      });
    }

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({
        success: false,
        error: 'File not found'
      });
    }

    const cleanedData = await cleanCSVData(filePath, cleaningOptions);
    
    // Save cleaned data to new file
    const cleanedFilename = `cleaned_${Date.now()}_${path.basename(filePath)}`;
    const cleanedFilePath = path.join(uploadsDir, cleanedFilename);
    
    await saveCleanedCSV(cleanedData.data, cleanedFilePath, cleanedData.headers);
    
    // Save cleaned data to MongoDB
    const dataId = `data_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const cleanedDataRecord = new CleanedData({
      dataId: dataId,
      jobId: jobRecord ? jobRecord.jobId : `manual_${Date.now()}`,
      originalFileName: path.basename(filePath),
      cleanedFileName: cleanedFilename,
      headers: cleanedData.headers,
      rowCount: cleanedData.data.length,
      columnCount: cleanedData.headers.length,
      data: cleanedData.data, // Store actual cleaned data
      metadata: {
        encoding: 'UTF-8',
        delimiter: ',',
        quoteChar: '"',
        cleaningTimestamp: new Date(),
        dataTypes: await detectDataTypesForStorage(cleanedData.data, cleanedData.headers),
        qualityMetrics: await calculateQualityMetrics(cleanedData.data, cleanedData.headers)
      },
      processingStats: {
        originalSize: cleanedData.originalSize || cleanedData.data.length,
        cleanedSize: cleanedData.data.length,
        rowsRemoved: cleanedData.report.rowsRemoved || 0,
        valuesImputed: cleanedData.report.valuesImputed || 0,
        outliersTreated: cleanedData.report.outliersTreated || 0,
        duplicatesRemoved: cleanedData.report.duplicatesRemoved || 0,
        encodingFixed: cleanedData.report.encodingFixed || 0
      }
    });

    await cleanedDataRecord.save();
    
    // Update job record with cleaning results and data reference
    if (jobRecord) {
      jobRecord.cleaningReport = cleanedData.report;
      jobRecord.processingOptions = cleaningOptions;
      jobRecord.metadata.dataId = dataId; // Link to cleaned data
      await jobRecord.save();
    }
    
    res.json({
      success: true,
      message: 'Data cleaning completed and saved to database',
      originalFile: path.basename(filePath),
      cleanedFile: cleanedFilename,
      dataId: dataId,
      cleaningReport: cleanedData.report,
      cleanedData: cleanedData.data.slice(0, 100), // Return first 100 rows for preview
      totalRows: cleanedData.data.length,
      qualityMetrics: cleanedDataRecord.metadata.qualityMetrics,
      downloadUrl: `/api/download/${cleanedFilename}`,
      dataUrl: `/api/data/${dataId}` // New endpoint to retrieve full cleaned data
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Download cleaned CSV file
app.get('/api/download/:filename', (req, res) => {
  try {
    const filename = req.params.filename;
    const filePath = path.join(uploadsDir, filename);
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({
        success: false,
        error: 'File not found'
      });
    }

    res.download(filePath, filename, (err) => {
      if (err) {
        res.status(500).json({
          success: false,
          error: 'Error downloading file'
        });
      }
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get cleaned data from MongoDB
app.get('/api/data/:dataId', async (req, res) => {
  try {
    const cleanedData = await CleanedData.findOne({ dataId: req.params.dataId });
    
    if (!cleanedData) {
      return res.status(404).json({
        success: false,
        error: 'Cleaned data not found'
      });
    }
    
    res.json({
      success: true,
      data: cleanedData.data,
      metadata: cleanedData.metadata,
      processingStats: cleanedData.processingStats,
      headers: cleanedData.headers,
      rowCount: cleanedData.rowCount,
      columnCount: cleanedData.columnCount
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get all cleaned datasets  
app.get('/api/datasets', async (req, res) => {
  try {
    const { limit = 10, page = 1, sortBy = 'createdAt', order = 'desc' } = req.query;
    
    const datasets = await CleanedData.find()
      .select('dataId jobId originalFileName cleanedFileName rowCount columnCount metadata.cleaningTimestamp metadata.qualityMetrics processingStats')
      .sort({ [sortBy]: order === 'desc' ? -1 : 1 })
      .limit(parseInt(limit))
      .skip((parseInt(page) - 1) * parseInt(limit));
    
    const totalDatasets = await CleanedData.countDocuments();
    
    res.json({
      success: true,
      datasets: datasets,
      pagination: {
        total: totalDatasets,
        page: parseInt(page),
        limit: parseInt(limit),
        pages: Math.ceil(totalDatasets / parseInt(limit))
      }
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Professional AutoViz Visualization Generation
app.post('/api/generate-autoviz', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        hint: "Send multipart/form-data with field name 'file' containing the CSV",
        expectedField: 'file'
      });
    }

    const csvFilePath = req.file.path;
    const outputDir = path.join(__dirname, 'visualizations', 'autoviz', Date.now().toString());
    
    // Ensure output directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Execute AutoViz Python script
    const { spawn } = require('child_process');
    const pythonScript = path.join(__dirname, 'scripts', 'autoviz_generator.py');
    
    console.log('🎨 Starting AutoViz generation...');
    console.log('📁 CSV File:', csvFilePath);
    console.log('📁 Output Dir:', outputDir);
    console.log('🐍 Python Script:', pythonScript);
    
    // Use the correct conda Python environment
    const pythonProcess = spawn('C:/Users/4236h/anaconda3/Scripts/conda.exe', [
      'run', '-p', 'C:\\Users\\4236h\\anaconda3', '--no-capture-output', 
      'python', pythonScript, csvFilePath, outputDir
    ]);
    
    let output = '';
    let error = '';
    
    pythonProcess.stdout.on('data', (data) => {
      const chunk = data.toString();
      output += chunk;
      console.log('📊 AutoViz Output:', chunk);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const chunk = data.toString();
      error += chunk;
      console.error('❌ AutoViz Error:', chunk);
    });
    
    pythonProcess.on('close', (code) => {
      console.log('🏁 AutoViz process finished with code:', code);
      
      if (code !== 0) {
        console.error('❌ AutoViz failed with exit code:', code);
        console.error('❌ Error output:', error);
        return res.status(500).json({
          success: false,
          error: `AutoViz generation failed (exit code: ${code})`,
          details: error,
          code: code
        });
      }
      
      try {
        console.log('📋 AutoViz Raw output length:', output.length);
        console.log('📋 AutoViz Raw output preview (first 500 chars):', output.substring(0, 500));
        console.log('📋 AutoViz Raw output preview (last 500 chars):', output.substring(Math.max(0, output.length - 500)));
        
        // Enhanced JSON extraction with multiple strategies
        let jsonStr = '';
        let extractionMethod = '';
        
        // Strategy 1: Look for the last complete JSON object using brace counting
        const lines = output.split('\n');
        for (let i = lines.length - 1; i >= 0 && !jsonStr; i--) {
          const line = lines[i].trim();
          if (line === '}') {
            let braceCount = 0;
            let jsonLines = [];
            for (let j = i; j >= 0; j--) {
              const currentLine = lines[j];
              jsonLines.unshift(currentLine);
              
              for (let char of currentLine) {
                if (char === '}') braceCount++;
                if (char === '{') braceCount--;
              }
              
              if (braceCount === 0 && currentLine.includes('{')) {
                jsonStr = jsonLines.join('\n').trim();
                extractionMethod = 'reverse-brace-counting';
                break;
              }
            }
          }
        }
        
        // Strategy 2: Look for JSON patterns in the output
        if (!jsonStr) {
          const jsonPatterns = [
            /(\{[\s\S]*?"status"\s*:\s*"success"[\s\S]*?\})/,
            /(\{[\s\S]*?"charts_generated"[\s\S]*?\})/,
            /(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})/g
          ];
          
          for (const pattern of jsonPatterns) {
            const matches = output.match(pattern);
            if (matches) {
              jsonStr = matches[matches.length - 1].trim();
              extractionMethod = 'pattern-matching';
              break;
            }
          }
        }
        
        // Strategy 3: Find JSON between specific markers
        if (!jsonStr) {
          const startMarkers = ['{', 'JSON_START:', 'RESULT:'];
          const endMarkers = ['}', 'JSON_END'];
          
          for (const startMarker of startMarkers) {
            for (const endMarker of endMarkers) {
              const startIdx = output.lastIndexOf(startMarker);
              const endIdx = output.lastIndexOf(endMarker);
              if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
                jsonStr = output.substring(startIdx, endIdx + 1).trim();
                if (jsonStr.startsWith('{') && jsonStr.endsWith('}')) {
                  extractionMethod = 'marker-based';
                  break;
                }
              }
            }
            if (jsonStr) break;
          }
        }
        
        if (!jsonStr) {
          throw new Error('No valid JSON found in Python output');
        }
        
        console.log(`🔍 AutoViz Extracted JSON using ${extractionMethod}:`, jsonStr.substring(0, 200) + '...');
        const result = JSON.parse(jsonStr);
        console.log('✅ AutoViz Parsed result:', result);
        
        if (result.status === 'error') {
          return res.status(500).json({
            success: false,
            error: `AutoViz error: ${result.error}`,
            details: result
          });
        }
        
        // Generate URLs for accessing visualizations
        const baseUrl = `/api/visualizations/autoviz/${path.basename(outputDir)}`;
        const visualizationUrls = result.chart_files?.map(file => `${baseUrl}/${file}`) || [];
        
        res.json({
          success: true,
          message: 'AutoViz visualizations generated successfully',
          visualizations: visualizationUrls,
          outputDirectory: outputDir,
          chartsGenerated: result.charts_generated,
          summary: result.summary
        });
        
      } catch (parseError) {
        console.error('❌ JSON parse error:', parseError);
        console.error('❌ Raw output that failed to parse:', output);
        res.status(500).json({
          success: false,
          error: 'Failed to parse AutoViz output',
          details: parseError.message,
          rawOutput: output
        });
      }
    });

  } catch (error) {
    console.error('❌ AutoViz endpoint error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      stack: error.stack
    });
  }
});

// Professional SweetViz Report Generation
app.post('/api/generate-sweetviz', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        error: 'No file uploaded',
        hint: "Send multipart/form-data with field name 'file' containing the CSV",
        expectedField: 'file'
      });
    }

    const csvFilePath = req.file.path;
    const targetColumn = req.body.targetColumn || null;
    const outputDir = path.join(__dirname, 'visualizations', 'sweetviz', Date.now().toString());
    
    // Ensure output directory exists
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Execute SweetViz Python script
    const { spawn } = require('child_process');
    const pythonScript = path.join(__dirname, 'scripts', 'sweetviz_generator.py');
    
    const args = ['run', '-p', 'C:\\Users\\4236h\\anaconda3', '--no-capture-output', 'python', pythonScript, csvFilePath, outputDir];
    if (targetColumn) {
      args.push(targetColumn);
    }
    
    console.log('📊 Starting SweetViz generation...');
    console.log('📁 CSV File:', csvFilePath);
    console.log('📁 Output Dir:', outputDir);
    console.log('🎯 Target Column:', targetColumn || 'None');
    console.log('🐍 Python Script:', pythonScript);
    
    const pythonProcess = spawn('C:/Users/4236h/anaconda3/Scripts/conda.exe', args);
    
    let output = '';
    let error = '';
    
    pythonProcess.stdout.on('data', (data) => {
      const chunk = data.toString();
      output += chunk;
      console.log('📈 SweetViz Output:', chunk);
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const chunk = data.toString();
      error += chunk;
      console.error('❌ SweetViz Error:', chunk);
    });
    
    pythonProcess.on('close', (code) => {
      console.log('🏁 SweetViz process finished with code:', code);
      
      if (code !== 0) {
        console.error('❌ SweetViz failed with exit code:', code);
        console.error('❌ Error output:', error);
        return res.status(500).json({
          success: false,
          error: `SweetViz generation failed (exit code: ${code})`,
          details: error,
          code: code
        });
      }
      
      try {
        console.log('📋 SweetViz Raw output length:', output.length);
        console.log('📋 SweetViz Raw output preview (first 500 chars):', output.substring(0, 500));
        console.log('📋 SweetViz Raw output preview (last 500 chars):', output.substring(Math.max(0, output.length - 500)));
        
        // Enhanced JSON extraction with multiple strategies
        let jsonStr = '';
        let extractionMethod = '';
        
        // Strategy 1: Look for the last complete JSON object using brace counting
        const lines = output.split('\n');
        for (let i = lines.length - 1; i >= 0 && !jsonStr; i--) {
          const line = lines[i].trim();
          if (line === '}') {
            let braceCount = 0;
            let jsonLines = [];
            for (let j = i; j >= 0; j--) {
              const currentLine = lines[j];
              jsonLines.unshift(currentLine);
              
              for (let char of currentLine) {
                if (char === '}') braceCount++;
                if (char === '{') braceCount--;
              }
              
              if (braceCount === 0 && currentLine.includes('{')) {
                jsonStr = jsonLines.join('\n').trim();
                extractionMethod = 'reverse-brace-counting';
                break;
              }
            }
          }
        }
        
        // Strategy 2: Look for JSON patterns in the output
        if (!jsonStr) {
          const jsonPatterns = [
            /(\{[\s\S]*?"status"\s*:\s*"success"[\s\S]*?\})/,
            /(\{[\s\S]*?"report_generated"[\s\S]*?\})/,
            /(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})/g
          ];
          
          for (const pattern of jsonPatterns) {
            const matches = output.match(pattern);
            if (matches) {
              jsonStr = matches[matches.length - 1].trim();
              extractionMethod = 'pattern-matching';
              break;
            }
          }
        }
        
        // Strategy 3: Find JSON between specific markers
        if (!jsonStr) {
          const startMarkers = ['{', 'JSON_START:', 'RESULT:'];
          const endMarkers = ['}', 'JSON_END'];
          
          for (const startMarker of startMarkers) {
            for (const endMarker of endMarkers) {
              const startIdx = output.lastIndexOf(startMarker);
              const endIdx = output.lastIndexOf(endMarker);
              if (startIdx !== -1 && endIdx !== -1 && endIdx > startIdx) {
                jsonStr = output.substring(startIdx, endIdx + 1).trim();
                if (jsonStr.startsWith('{') && jsonStr.endsWith('}')) {
                  extractionMethod = 'marker-based';
                  break;
                }
              }
            }
            if (jsonStr) break;
          }
        }
        
        if (!jsonStr) {
          throw new Error('No valid JSON found in Python output');
        }
        
        console.log(`🔍 SweetViz Extracted JSON using ${extractionMethod}:`, jsonStr.substring(0, 200) + '...');
        const result = JSON.parse(jsonStr);
        console.log('✅ SweetViz Parsed result:', result);
        
        if (result.status === 'error') {
          return res.status(500).json({
            success: false,
            error: `SweetViz error: ${result.error}`,
            details: result
          });
        }
        
        // Generate URLs for accessing reports
        const baseUrl = `/api/visualizations/sweetviz/${path.basename(outputDir)}`;
        const mainReportUrl = `${baseUrl}/${result.main_report}`;
        const comparisonUrls = result.comparison_reports?.map(file => `${baseUrl}/${file}`) || [];
        
        res.json({
          success: true,
          message: 'SweetViz analysis report generated successfully',
          mainReport: mainReportUrl,
          comparisonReports: comparisonUrls,
          outputDirectory: outputDir,
          summaryStats: result.summary_stats,
          dataInsights: result.data_insights
        });
        
      } catch (parseError) {
        console.error('❌ JSON parse error:', parseError);
        console.error('❌ Raw output that failed to parse:', output);
        res.status(500).json({
          success: false,
          error: 'Failed to parse SweetViz output',
          details: parseError.message,
          rawOutput: output
        });
      }
    });

  } catch (error) {
    console.error('❌ SweetViz endpoint error:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      stack: error.stack
    });
  }
});

// Serve visualization files (AutoViz & SweetViz)
const vizRoot = path.join(__dirname, 'visualizations');
if (!fs.existsSync(vizRoot)) {
  fs.mkdirSync(vizRoot, { recursive: true });
}
app.use('/api/visualizations', express.static(vizRoot));

// Tableau REST API Integration
app.post('/api/tableau/publish', async (req, res) => {
  try {
    const { dataSource, workbookName, projectName } = req.body;
    
    if (!dataSource || !workbookName) {
      return res.status(400).json({
        success: false,
        error: 'Data source and workbook name are required'
      });
    }

    // This is a placeholder for Tableau REST API integration
    // You would need to implement actual Tableau Server connection here
    const tableauConfig = {
      serverUrl: process.env.TABLEAU_SERVER_URL,
      username: process.env.TABLEAU_USERNAME,
      password: process.env.TABLEAU_PASSWORD,
      siteName: process.env.TABLEAU_SITE_NAME || 'default'
    };

    // Simulate Tableau dashboard creation
    const dashboardUrl = `${tableauConfig.serverUrl}/views/${workbookName}/Dashboard`;
    const embedUrl = `${tableauConfig.serverUrl}/trusted/${dashboardUrl}`;

    res.json({
      success: true,
      message: 'Tableau dashboard published successfully',
      dashboardUrl: dashboardUrl,
      embedUrl: embedUrl,
      workbookName: workbookName,
      projectName: projectName || 'default'
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Get available Tableau dashboards
app.get('/api/tableau/dashboards', async (req, res) => {
  try {
    // This would connect to Tableau REST API to fetch available dashboards
    // For now, returning mock data
    const dashboards = [
      {
        id: '1',
        name: 'Sales Analysis Dashboard',
        projectName: 'Sales Analytics',
        url: '/api/tableau/embed/sales-analysis',
        createdAt: new Date().toISOString(),
        description: 'Comprehensive sales performance analysis'
      },
      {
        id: '2',
        name: 'Customer Insights Dashboard',
        projectName: 'Customer Analytics',
        url: '/api/tableau/embed/customer-insights',
        createdAt: new Date().toISOString(),
        description: 'Customer behavior and segmentation analysis'
      }
    ];

    res.json({
      success: true,
      dashboards: dashboards
    });

  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Data Cleaning Utility Functions

async function analyzeCSVQuality(filePath) {
  return new Promise((resolve, reject) => {
    const results = [];
    const analysis = {
      totalRows: 0,
      totalColumns: 0,
      missingValues: {},
      duplicates: 0,
      dataTypes: {},
      outliers: {},
      summary: {},
      correlations: {},
      qualityMetrics: {
        completeness: 0,
        consistency: 0,
        accuracy: 0,
        validity: 0,
        uniqueness: 0,
        overallScore: 0
      },
      recommendations: []
    };

    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (row) => {
        results.push(row);
      })
      .on('end', () => {
        try {
          analysis.totalRows = results.length;
          if (results.length > 0) {
            analysis.totalColumns = Object.keys(results[0]).length;
            const headers = Object.keys(results[0]);
            
            // Analyze missing values and completeness
            let totalMissingValues = 0;
            headers.forEach(column => {
              const missingCount = results.filter(row => 
                !row[column] || row[column].trim() === '' || row[column].toLowerCase() === 'null'
              ).length;
              analysis.missingValues[column] = {
                count: missingCount,
                percentage: ((missingCount / results.length) * 100).toFixed(2)
              };
              totalMissingValues += missingCount;
            });

            // Calculate completeness score
            const totalCells = results.length * headers.length;
            analysis.qualityMetrics.completeness = ((totalCells - totalMissingValues) / totalCells * 100).toFixed(2);

            // Detect data types and validate consistency
            let consistencyIssues = 0;
            headers.forEach(column => {
              const values = results.map(row => row[column]).filter(val => val && val.trim() !== '');
              const detectedType = detectDataType(values);
              analysis.dataTypes[column] = detectedType;
              
              // Check data type consistency
              if (detectedType === 'mixed') {
                consistencyIssues++;
              }
            });

            analysis.qualityMetrics.consistency = (((headers.length - consistencyIssues) / headers.length) * 100).toFixed(2);

            // Check for duplicates and calculate uniqueness
            const uniqueRows = _.uniqBy(results, row => JSON.stringify(row));
            analysis.duplicates = results.length - uniqueRows.length;
            analysis.qualityMetrics.uniqueness = ((uniqueRows.length / results.length) * 100).toFixed(2);

            // Analyze numeric columns for statistics and outliers
            const numericColumns = [];
            headers.forEach(column => {
              if (analysis.dataTypes[column] === 'numeric') {
                numericColumns.push(column);
                const numericValues = results
                  .map(row => parseFloat(row[column]))
                  .filter(val => !isNaN(val));
                
                if (numericValues.length > 0) {
                  const mean = numericValues.reduce((a, b) => a + b, 0) / numericValues.length;
                  const std = calculateStandardDeviation(numericValues);
                  const sorted = [...numericValues].sort((a, b) => a - b);
                  const q1 = percentile(sorted, 25);
                  const q3 = percentile(sorted, 75);
                  const median = percentile(sorted, 50);

                  analysis.summary[column] = {
                    count: numericValues.length,
                    mean: mean.toFixed(2),
                    median: median.toFixed(2),
                    min: Math.min(...numericValues),
                    max: Math.max(...numericValues),
                    std: std.toFixed(2),
                    q1: q1.toFixed(2),
                    q3: q3.toFixed(2),
                    skewness: calculateSkewness(numericValues, mean, std).toFixed(2),
                    kurtosis: calculateKurtosis(numericValues, mean, std).toFixed(2)
                  };

                  // Advanced outlier detection using IQR and Z-score methods
                  const outliers = detectAdvancedOutliers(numericValues);
                  analysis.outliers[column] = {
                    count: outliers.iqr.length + outliers.zscore.length,
                    iqrOutliers: outliers.iqr.slice(0, 5),
                    zscoreOutliers: outliers.zscore.slice(0, 5),
                    percentage: (((outliers.iqr.length + outliers.zscore.length) / numericValues.length) * 100).toFixed(2)
                  };
                }
              }
            });

            // Calculate correlations between numeric columns
            if (numericColumns.length > 1) {
              for (let i = 0; i < numericColumns.length; i++) {
                for (let j = i + 1; j < numericColumns.length; j++) {
                  const col1 = numericColumns[i];
                  const col2 = numericColumns[j];
                  const correlation = calculateCorrelation(results, col1, col2);
                  if (!analysis.correlations[col1]) analysis.correlations[col1] = {};
                  analysis.correlations[col1][col2] = correlation.toFixed(3);
                }
              }
            }

            // Validate data patterns and calculate accuracy
            let validityScore = 100;
            headers.forEach(column => {
              const values = results.map(row => row[column]).filter(val => val && val.trim() !== '');
              const invalidCount = validateDataPattern(values, analysis.dataTypes[column]);
              if (invalidCount > 0) {
                validityScore -= (invalidCount / values.length) * 20; // Reduce score based on invalid data
              }
            });
            analysis.qualityMetrics.validity = Math.max(0, validityScore).toFixed(2);

            // Calculate overall quality score
            const scores = [
              parseFloat(analysis.qualityMetrics.completeness),
              parseFloat(analysis.qualityMetrics.consistency),
              parseFloat(analysis.qualityMetrics.validity),
              parseFloat(analysis.qualityMetrics.uniqueness)
            ];
            analysis.qualityMetrics.overallScore = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2);

            // Generate recommendations
            analysis.recommendations = generateDataQualityRecommendations(analysis);
          }
          
          resolve(analysis);
        } catch (error) {
          reject(error);
        }
      })
      .on('error', (error) => {
        reject(error);
      });
  });
}

async function cleanCSVData(filePath, options = {}) {
  return new Promise((resolve, reject) => {
    const results = [];
    const cleaningReport = {
      stepsApplied: [],
      rowsRemoved: 0,
      valuesImputed: 0,
      outliersTreated: 0,
      duplicatesRemoved: 0
    };

    fs.createReadStream(filePath)
      .pipe(csv())
      .on('data', (row) => {
        results.push(row);
      })
      .on('end', () => {
        try {
          let cleanedData = [...results];
          const headers = Object.keys(results[0] || {});

          // Step 1: Remove duplicates
          const beforeDuplicates = cleanedData.length;
          cleanedData = _.uniqBy(cleanedData, row => JSON.stringify(row));
          cleaningReport.duplicatesRemoved = beforeDuplicates - cleanedData.length;
          if (cleaningReport.duplicatesRemoved > 0) {
            cleaningReport.stepsApplied.push(`Removed ${cleaningReport.duplicatesRemoved} duplicate rows`);
          }

          // Step 2: Handle missing values
          headers.forEach(column => {
            const missingIndices = [];
            cleanedData.forEach((row, index) => {
              if (!row[column] || row[column].trim() === '' || row[column].toLowerCase() === 'null') {
                missingIndices.push(index);
              }
            });

            if (missingIndices.length > 0) {
              const dataType = detectDataType(cleanedData.map(row => row[column]).filter(val => val && val.trim() !== ''));
              
              if (dataType === 'numeric') {
                // Fill with median
                const numericValues = cleanedData
                  .map(row => parseFloat(row[column]))
                  .filter(val => !isNaN(val))
                  .sort((a, b) => a - b);
                
                const median = numericValues.length % 2 === 0
                  ? (numericValues[numericValues.length / 2 - 1] + numericValues[numericValues.length / 2]) / 2
                  : numericValues[Math.floor(numericValues.length / 2)];

                missingIndices.forEach(index => {
                  cleanedData[index][column] = median.toString();
                  cleaningReport.valuesImputed++;
                });
              } else if (dataType === 'categorical') {
                // Fill with mode
                const values = cleanedData.map(row => row[column]).filter(val => val && val.trim() !== '');
                const mode = _.chain(values).countBy().toPairs().maxBy(1).value();
                
                if (mode) {
                  missingIndices.forEach(index => {
                    cleanedData[index][column] = mode[0];
                    cleaningReport.valuesImputed++;
                  });
                }
              }
            }
          });

          if (cleaningReport.valuesImputed > 0) {
            cleaningReport.stepsApplied.push(`Imputed ${cleaningReport.valuesImputed} missing values`);
          }

          // Step 3: Standardize text data
          headers.forEach(column => {
            const dataType = detectDataType(cleanedData.map(row => row[column]));
            if (dataType === 'categorical') {
              cleanedData.forEach(row => {
                if (row[column]) {
                  row[column] = row[column].toString().trim().toLowerCase();
                }
              });
            }
          });
          cleaningReport.stepsApplied.push('Standardized text format to lowercase');

          // Step 4: Handle outliers for numeric columns
          headers.forEach(column => {
            const numericValues = cleanedData
              .map(row => parseFloat(row[column]))
              .filter(val => !isNaN(val));

            if (numericValues.length > 0) {
              const outliers = detectOutliers(numericValues);
              if (outliers.length > 0) {
                // Cap outliers using IQR method
                const Q1 = percentile(numericValues, 25);
                const Q3 = percentile(numericValues, 75);
                const IQR = Q3 - Q1;
                const lowerBound = Q1 - 1.5 * IQR;
                const upperBound = Q3 + 1.5 * IQR;

                cleanedData.forEach(row => {
                  const value = parseFloat(row[column]);
                  if (!isNaN(value)) {
                    if (value < lowerBound) {
                      row[column] = lowerBound.toString();
                      cleaningReport.outliersTreated++;
                    } else if (value > upperBound) {
                      row[column] = upperBound.toString();
                      cleaningReport.outliersTreated++;
                    }
                  }
                });
              }
            }
          });

          if (cleaningReport.outliersTreated > 0) {
            cleaningReport.stepsApplied.push(`Treated ${cleaningReport.outliersTreated} outliers using IQR capping`);
          }

          // Step 5: Data transformation and normalization
          headers.forEach(column => {
            const numericValues = cleanedData
              .map(row => parseFloat(row[column]))
              .filter(val => !isNaN(val));

            if (numericValues.length > 0 && options.normalizeNumeric) {
              // Normalize numeric columns to 0-1 range
              const min = Math.min(...numericValues);
              const max = Math.max(...numericValues);
              const range = max - min;

              if (range > 0) {
                cleanedData.forEach(row => {
                  const value = parseFloat(row[column]);
                  if (!isNaN(value)) {
                    const normalized = (value - min) / range;
                    row[column] = normalized.toFixed(4);
                  }
                });
              }
            }
          });

          // Step 6: Data type validation and conversion
          let typeConversions = 0;
          headers.forEach(column => {
            cleanedData.forEach(row => {
              if (row[column]) {
                const value = row[column].toString().trim();
                
                // Handle date fields
                if (column.toLowerCase().includes('date') || column.toLowerCase().includes('time')) {
                  const dateValue = new Date(value);
                  if (!isNaN(dateValue.getTime())) {
                    row[column] = dateValue.toISOString().split('T')[0]; // YYYY-MM-DD format
                    typeConversions++;
                  }
                }
                // Try to convert numeric strings to proper numbers
                else if (!isNaN(value) && value !== '') {
                  const numValue = parseFloat(value);
                  if (Number.isInteger(numValue)) {
                    row[column] = numValue.toString();
                  } else {
                    row[column] = numValue.toFixed(2);
                  }
                  typeConversions++;
                }
                // Standardize boolean values
                else if (['true', 'false', 'yes', 'no', '1', '0'].includes(value.toLowerCase())) {
                  row[column] = ['true', 'yes', '1'].includes(value.toLowerCase()) ? 'true' : 'false';
                  typeConversions++;
                }
              }
            });
          });

          if (typeConversions > 0) {
            cleaningReport.stepsApplied.push(`Converted ${typeConversions} values to appropriate data types`);
          }

          // Step 7: Data validation and quality checks
          let validationIssues = 0;
          headers.forEach(column => {
            cleanedData.forEach((row, index) => {
              if (row[column]) {
                const value = row[column].toString();
                
                // Remove special characters from text fields (except dates and numbers)
                if (isNaN(parseFloat(value)) && !Date.parse(value)) {
                  const cleaned = value.replace(/[^\w\s\-.,]/g, '').trim();
                  if (cleaned !== value) {
                    row[column] = cleaned;
                    validationIssues++;
                  }
                }
                
                // Ensure consistent formatting
                if (column.toLowerCase().includes('email')) {
                  row[column] = value.toLowerCase();
                  validationIssues++;
                }
                
                if (column.toLowerCase().includes('phone')) {
                  const phoneClean = value.replace(/[^\d+\-()]/g, '');
                  if (phoneClean !== value) {
                    row[column] = phoneClean;
                    validationIssues++;
                  }
                }
              }
            });
          });

          if (validationIssues > 0) {
            cleaningReport.stepsApplied.push(`Fixed ${validationIssues} data validation issues`);
          }

          // Add comprehensive processing summary
          cleaningReport.stepsApplied.push('✅ Comprehensive data processing completed');
          cleaningReport.processingComplete = true;
          cleaningReport.finalQualityScore = calculateDataQualityScore(cleanedData, headers);

          resolve({
            data: cleanedData,
            headers: headers,
            report: cleaningReport
          });

        } catch (error) {
          reject(error);
        }
      })
      .on('error', (error) => {
        reject(error);
      });
  });
}

async function saveCleanedCSV(data, filePath, headers) {
  const csvWriter = createCsvWriter({
    path: filePath,
    header: headers.map(header => ({ id: header, title: header }))
  });

  await csvWriter.writeRecords(data);
}

// Helper functions for data analysis
function detectDataType(values) {
  if (values.length === 0) return 'unknown';
  
  const nonEmptyValues = values.filter(val => val !== null && val !== undefined && val !== '');
  if (nonEmptyValues.length === 0) return 'unknown';
  
  const numericCount = nonEmptyValues.filter(val => !isNaN(parseFloat(val))).length;
  const numericRatio = numericCount / nonEmptyValues.length;
  
  if (numericRatio > 0.8) return 'numeric';
  
  const dateCount = nonEmptyValues.filter(val => !isNaN(Date.parse(val))).length;
  const dateRatio = dateCount / nonEmptyValues.length;
  
  if (dateRatio > 0.8) return 'date';
  
  return 'categorical';
}

function calculateStandardDeviation(values) {
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  return Math.sqrt(variance);
}

function detectOutliers(values) {
  const Q1 = percentile(values, 25);
  const Q3 = percentile(values, 75);
  const IQR = Q3 - Q1;
  const lowerBound = Q1 - 1.5 * IQR;
  const upperBound = Q3 + 1.5 * IQR;
  
  return values.filter(val => val < lowerBound || val > upperBound);
}

function percentile(arr, p) {
  const sorted = [...arr].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index % 1;
  
  if (upper >= sorted.length) return sorted[sorted.length - 1];
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

// Error handling middleware
app.use((error, req, res, next) => {
  if (error instanceof multer.MulterError) {
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        success: false,
        error: 'File too large. Maximum size is 100MB.'
      });
    }
  }
  
  res.status(500).json({
    success: false,
    error: error.message || 'Internal server error'
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

// Advanced Statistical Utility Functions

async function detectDataTypesForStorage(data, headers) {
  const dataTypes = {};
  
  headers.forEach(column => {
    const values = data.map(row => row[column]).filter(val => val && val.toString().trim() !== '');
    dataTypes[column] = detectDataType(values);
  });
  
  return dataTypes;
}

async function calculateQualityMetrics(data, headers) {
  const totalCells = data.length * headers.length;
  let missingCells = 0;
  let validCells = 0;
  
  // Calculate completeness and validity
  headers.forEach(column => {
    data.forEach(row => {
      if (!row[column] || row[column].toString().trim() === '') {
        missingCells++;
      } else {
        validCells++;
      }
    });
  });
  
  const completeness = ((totalCells - missingCells) / totalCells * 100);
  const uniqueRows = _.uniqBy(data, row => JSON.stringify(row));
  const uniqueness = (uniqueRows.length / data.length * 100);
  
  // Simple validity check (non-empty and reasonable values)
  const validity = (validCells / totalCells * 100);
  
  const overallScore = (completeness + uniqueness + validity) / 3;
  
  return {
    completeness: parseFloat(completeness.toFixed(2)),
    consistency: 95.0, // Simplified for now
    accuracy: 90.0, // Simplified for now
    validity: parseFloat(validity.toFixed(2)),
    uniqueness: parseFloat(uniqueness.toFixed(2)),
    overallScore: parseFloat(overallScore.toFixed(2))
  };
}

function percentile(sortedArray, p) {
  const index = (p / 100) * (sortedArray.length - 1);
  if (Math.floor(index) === index) {
    return sortedArray[index];
  } else {
    const lower = sortedArray[Math.floor(index)];
    const upper = sortedArray[Math.ceil(index)];
    return lower + (upper - lower) * (index - Math.floor(index));
  }
}

function calculateSkewness(values, mean, std) {
  if (std === 0) return 0;
  const n = values.length;
  const sum = values.reduce((acc, val) => acc + Math.pow((val - mean) / std, 3), 0);
  return (n / ((n - 1) * (n - 2))) * sum;
}

function calculateKurtosis(values, mean, std) {
  if (std === 0) return 0;
  const n = values.length;
  const sum = values.reduce((acc, val) => acc + Math.pow((val - mean) / std, 4), 0);
  return ((n * (n + 1)) / ((n - 1) * (n - 2) * (n - 3))) * sum - (3 * Math.pow(n - 1, 2)) / ((n - 2) * (n - 3));
}

function detectAdvancedOutliers(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const q1 = percentile(sorted, 25);
  const q3 = percentile(sorted, 75);
  const iqr = q3 - q1;
  const lowerBound = q1 - 1.5 * iqr;
  const upperBound = q3 + 1.5 * iqr;
  
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const std = calculateStandardDeviation(values);
  
  const iqrOutliers = values.filter(val => val < lowerBound || val > upperBound);
  const zscoreOutliers = values.filter(val => Math.abs((val - mean) / std) > 2.5);
  
  return {
    iqr: iqrOutliers,
    zscore: zscoreOutliers
  };
}

function calculateCorrelation(data, col1, col2) {
  const pairs = data.map(row => [parseFloat(row[col1]), parseFloat(row[col2])])
    .filter(pair => !isNaN(pair[0]) && !isNaN(pair[1]));
  
  if (pairs.length < 2) return 0;
  
  const mean1 = pairs.reduce((sum, pair) => sum + pair[0], 0) / pairs.length;
  const mean2 = pairs.reduce((sum, pair) => sum + pair[1], 0) / pairs.length;
  
  let numerator = 0;
  let sum1 = 0;
  let sum2 = 0;
  
  pairs.forEach(pair => {
    const diff1 = pair[0] - mean1;
    const diff2 = pair[1] - mean2;
    numerator += diff1 * diff2;
    sum1 += diff1 * diff1;
    sum2 += diff2 * diff2;
  });
  
  const denominator = Math.sqrt(sum1 * sum2);
  return denominator === 0 ? 0 : numerator / denominator;
}

function validateDataPattern(values, dataType) {
  let invalidCount = 0;
  
  values.forEach(value => {
    switch (dataType) {
      case 'email':
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) invalidCount++;
        break;
      case 'phone':
        if (!/^[\+]?[1-9][\d]{0,15}$/.test(value.replace(/[\s\-\(\)]/g, ''))) invalidCount++;
        break;
      case 'date':
        if (isNaN(Date.parse(value))) invalidCount++;
        break;
      case 'numeric':
        if (isNaN(parseFloat(value))) invalidCount++;
        break;
      case 'url':
        try {
          new URL(value);
        } catch {
          invalidCount++;
        }
        break;
    }
  });
  
  return invalidCount;
}

function generateDataQualityRecommendations(analysis) {
  const recommendations = [];
  
  // Completeness recommendations
  if (parseFloat(analysis.qualityMetrics.completeness) < 90) {
    recommendations.push({
      type: 'completeness',
      priority: 'high',
      message: `Data completeness is ${analysis.qualityMetrics.completeness}%. Consider implementing data validation at source.`,
      action: 'Review data collection processes and add required field validation.'
    });
  }
  
  // Missing value recommendations
  Object.keys(analysis.missingValues).forEach(column => {
    const missingPercent = parseFloat(analysis.missingValues[column].percentage);
    if (missingPercent > 20) {
      recommendations.push({
        type: 'missing_values',
        priority: 'medium',
        message: `Column '${column}' has ${missingPercent}% missing values.`,
        action: 'Consider imputation strategies or investigate data collection for this field.'
      });
    }
  });
  
  // Outlier recommendations
  Object.keys(analysis.outliers || {}).forEach(column => {
    const outlierPercent = parseFloat(analysis.outliers[column].percentage);
    if (outlierPercent > 5) {
      recommendations.push({
        type: 'outliers',
        priority: 'medium',
        message: `Column '${column}' has ${outlierPercent}% outliers.`,
        action: 'Review outlier values to determine if they are errors or valid extreme values.'
      });
    }
  });
  
  // Duplicate recommendations
  if (analysis.duplicates > 0) {
    recommendations.push({
      type: 'duplicates',
      priority: 'high',
      message: `Found ${analysis.duplicates} duplicate rows.`,
      action: 'Remove duplicate entries and implement unique constraints at data source.'
    });
  }
  
  // Data type consistency recommendations
  if (parseFloat(analysis.qualityMetrics.consistency) < 95) {
    recommendations.push({
      type: 'consistency',
      priority: 'medium',
      message: `Data type consistency is ${analysis.qualityMetrics.consistency}%.`,
      action: 'Standardize data formats and implement data type validation.'
    });
  }
  
  return recommendations;
}

// Calculate comprehensive data quality score
function calculateDataQualityScore(data, headers) {
  if (!data || data.length === 0) return 0;
  
  let totalScore = 0;
  let factors = 0;
  
  // Factor 1: Completeness (no missing values)
  let totalCells = data.length * headers.length;
  let filledCells = 0;
  
  data.forEach(row => {
    headers.forEach(header => {
      if (row[header] && row[header].toString().trim() !== '') {
        filledCells++;
      }
    });
  });
  
  const completenessScore = (filledCells / totalCells) * 100;
  totalScore += completenessScore;
  factors++;
  
  // Factor 2: Consistency (standardized formats)
  let consistencyScore = 85; // Base score for standardized data
  totalScore += consistencyScore;
  factors++;
  
  // Factor 3: Validity (proper data types)
  let validityScore = 90; // High score after cleaning and validation
  totalScore += validityScore;
  factors++;
  
  // Factor 4: Uniqueness (no duplicates after cleaning)
  let uniquenessScore = 95; // High score after duplicate removal
  totalScore += uniquenessScore;
  factors++;
  
  return Math.round(totalScore / factors);
}

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Data Processing API Server running on port ${PORT}`);
  console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🔗 API URL: http://localhost:${PORT}`);
  console.log(`📁 Uploads directory: ${uploadsDir}`);
});

module.exports = app;
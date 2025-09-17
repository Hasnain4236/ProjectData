const mongoose = require('mongoose');

// Schema for storing cleaned CSV data
const cleanedDataSchema = new mongoose.Schema({
  dataId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  jobId: {
    type: String,
    required: true,
    ref: 'DataProcessingJob'
  },
  originalFileName: String,
  cleanedFileName: String,
  headers: [String],
  rowCount: Number,
  columnCount: Number,
  data: [{
    type: mongoose.Schema.Types.Mixed,
    index: false // Disable indexing for data field due to size
  }],
  metadata: {
    encoding: String,
    delimiter: String,
    quoteChar: String,
    dateFormat: String,
    cleaningTimestamp: {
      type: Date,
      default: Date.now
    },
    dataTypes: mongoose.Schema.Types.Mixed,
    qualityMetrics: {
      completeness: Number,
      consistency: Number,
      accuracy: Number,
      validity: Number,
      uniqueness: Number,
      overallScore: Number
    }
  },
  processingStats: {
    originalSize: Number,
    cleanedSize: Number,
    rowsRemoved: Number,
    valuesImputed: Number,
    outliersTreated: Number,
    duplicatesRemoved: Number,
    encodingFixed: Number
  },
  createdAt: {
    type: Date,
    default: Date.now,
    expires: 2592000 // Auto-delete after 30 days
  }
}, {
  timestamps: true
});

// Schema for storing data processing jobs
const dataProcessingJobSchema = new mongoose.Schema({
  jobId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  fileName: {
    type: String,
    required: true
  },
  originalFileName: {
    type: String,
    required: true
  },
  status: {
    type: String,
    enum: ['pending', 'processing', 'completed', 'failed'],
    default: 'pending'
  },
  metadata: {
    fileSize: Number,
    rowCount: Number,
    columnCount: Number,
    uploadedAt: {
      type: Date,
      default: Date.now
    },
    processedAt: Date
  },
  analysisResults: {
    totalRows: Number,
    totalColumns: Number,
    missingValues: mongoose.Schema.Types.Mixed,
    duplicates: Number,
    dataTypes: mongoose.Schema.Types.Mixed,
    qualityScore: Number,
    summary: mongoose.Schema.Types.Mixed
  },
  cleaningReport: {
    stepsApplied: [String],
    rowsRemoved: Number,
    valuesImputed: Number,
    outliersTreated: Number,
    duplicatesRemoved: Number,
    encodingFixed: Number
  },
  processingOptions: {
    removeDuplicates: Boolean,
    handleMissingValues: Boolean,
    treatOutliers: Boolean,
    standardizeFormats: Boolean,
    encoding: String
  },
  errorMessage: String,
  createdAt: {
    type: Date,
    default: Date.now,
    expires: 86400 // Auto-delete after 24 hours
  }
}, {
  timestamps: true
});

// Schema for storing user sessions (if needed for tracking)
const userSessionSchema = new mongoose.Schema({
  sessionId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  ipAddress: String,
  userAgent: String,
  jobsProcessed: {
    type: Number,
    default: 0
  },
  lastActivity: {
    type: Date,
    default: Date.now
  },
  createdAt: {
    type: Date,
    default: Date.now,
    expires: 3600 // Auto-delete after 1 hour
  }
}, {
  timestamps: true
});

// Schema for storing data quality metrics
const dataQualityMetricsSchema = new mongoose.Schema({
  date: {
    type: Date,
    default: Date.now
  },
  totalFilesProcessed: {
    type: Number,
    default: 0
  },
  averageQualityScore: {
    type: Number,
    default: 0
  },
  commonIssues: {
    missingValues: Number,
    duplicates: Number,
    encodingIssues: Number,
    outliers: Number
  },
  processingStats: {
    avgProcessingTime: Number,
    successRate: Number,
    errorRate: Number
  }
}, {
  timestamps: true
});

// Indexes for better performance
dataProcessingJobSchema.index({ createdAt: -1 });
dataProcessingJobSchema.index({ status: 1, createdAt: -1 });
userSessionSchema.index({ lastActivity: -1 });
cleanedDataSchema.index({ jobId: 1 });
cleanedDataSchema.index({ createdAt: -1 });

const DataProcessingJob = mongoose.model('DataProcessingJob', dataProcessingJobSchema);
const UserSession = mongoose.model('UserSession', userSessionSchema);
const DataQualityMetrics = mongoose.model('DataQualityMetrics', dataQualityMetricsSchema);
const CleanedData = mongoose.model('CleanedData', cleanedDataSchema);

module.exports = {
  DataProcessingJob,
  UserSession,
  DataQualityMetrics,
  CleanedData
};
// Initialize database and create default user
db = db.getSiblingDB('dataprocessing');

db.createUser({
  user: 'datauser',
  pwd: 'datapass2024',
  roles: [
    {
      role: 'readWrite',
      db: 'dataprocessing'
    }
  ]
});

// Create initial collections with indexes
db.createCollection('dataprocessingjobs');
db.createCollection('usersessions');
db.createCollection('dataqualitymetrics');
db.createCollection('cleaneddatas');

// Create indexes for better performance
db.dataprocessingjobs.createIndex({ "jobId": 1 }, { unique: true });
db.dataprocessingjobs.createIndex({ "status": 1 });
db.dataprocessingjobs.createIndex({ "metadata.uploadedAt": -1 });

db.usersessions.createIndex({ "sessionId": 1 }, { unique: true });
db.usersessions.createIndex({ "createdAt": -1 });

db.cleaneddatas.createIndex({ "dataId": 1 }, { unique: true });
db.cleaneddatas.createIndex({ "jobId": 1 });

print("Database initialized successfully with user and collections");
const admin = require('firebase-admin');

let firebaseApp = null;
let firestore = null;
let storageBucket = null;

function initializeFirebase() {
  if (!firebaseApp) {
    try {
      if (admin.apps.length === 0) {
        if (process.env.FIREBASE_SERVICE_ACCOUNT) {
          const serviceAccount = JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT);
          firebaseApp = admin.initializeApp({
            credential: admin.credential.cert(serviceAccount),
            projectId: process.env.FIREBASE_PROJECT_ID || serviceAccount.project_id,
            storageBucket: process.env.FIREBASE_STORAGE_BUCKET || serviceAccount.storageBucket || `${serviceAccount.project_id}.appspot.com`
          });
        } else if (process.env.FIREBASE_CLIENT_EMAIL && process.env.FIREBASE_PRIVATE_KEY) {
          firebaseApp = admin.initializeApp({
            credential: admin.credential.cert({
              projectId: process.env.FIREBASE_PROJECT_ID,
              clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
              privateKey: process.env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, '\n')
            }),
            projectId: process.env.FIREBASE_PROJECT_ID,
            storageBucket: process.env.FIREBASE_STORAGE_BUCKET
          });
        } else {
          firebaseApp = admin.initializeApp({
            credential: admin.credential.applicationDefault(),
            projectId: process.env.FIREBASE_PROJECT_ID || 'projectdata-6bbad',
            storageBucket: process.env.FIREBASE_STORAGE_BUCKET || 'projectdata-6bbad.firebasestorage.app'
          });
        }
      } else {
        firebaseApp = admin.app();
      }
      firestore = admin.firestore();
      storageBucket = admin.storage().bucket();
      console.log('🔥 Firebase initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize Firebase:', error.message);
      firebaseApp = null;
      firestore = null;
      storageBucket = null;
    }
  }

  return { admin, app: firebaseApp, firestore, storageBucket };
}

module.exports = initializeFirebase;

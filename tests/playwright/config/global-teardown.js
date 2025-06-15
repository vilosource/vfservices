// global-teardown.js

async function globalTeardown() {
  console.log('🧹 Starting global teardown for Playwright tests...');
  
  // Cleanup operations
  // Note: Docker containers will be cleaned up by docker-compose
  
  console.log('✅ Global teardown completed');
}

module.exports = globalTeardown;
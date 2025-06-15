// global-setup.js
const { chromium } = require('@playwright/test');

async function globalSetup() {
  console.log('🚀 Starting global setup for Playwright tests...');
  
  // Wait for services to be ready
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  try {
    // Health check for main services
    const services = [
      process.env.BASE_URL || 'https://vfservices.viloforge.com',
      process.env.IDENTITY_URL || 'https://identity.vfservices.viloforge.com',
    ];
    
    for (const service of services) {
      console.log(`Checking service availability: ${service}`);
      try {
        const response = await page.goto(service, { timeout: 10000 });
        if (response && response.status() < 400) {
          console.log(`✅ ${service} is available`);
        } else {
          console.log(`⚠️ ${service} returned status: ${response?.status()}`);
        }
      } catch (error) {
        console.log(`❌ ${service} is not available: ${error.message}`);
      }
    }
  } finally {
    await browser.close();
  }
  
  console.log('✅ Global setup completed');
}

module.exports = globalSetup;
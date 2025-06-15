#!/usr/bin/env node

/**
 * Comprehensive Test Results Analyzer for VF Services Playwright Tests
 * 
 * This tool analyzes Playwright test results and generates detailed reports
 * with failure categorization, trends, and actionable recommendations.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class TestResultsAnalyzer {
  constructor(runId) {
    this.runId = runId || process.env.TEST_RUN_ID;
    this.resultsDir = `/test-results/${this.runId}`;
    this.reportsDir = process.env.TEST_REPORTS_DIR || '/test-reports';
    this.analysisDir = process.env.ANALYSIS_OUTPUT_DIR || '/analysis-output';
    
    // Ensure directories exist
    [this.reportsDir, this.analysisDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  }

  async analyze() {
    console.log(`🔍 Analyzing test results for run: ${this.runId}`);
    console.log(`📁 Results directory: ${this.resultsDir}`);
    
    try {
      // Validate input
      if (!this.runId) {
        throw new Error('TEST_RUN_ID not provided');
      }
      
      if (!fs.existsSync(this.resultsDir)) {
        throw new Error(`Results directory not found: ${this.resultsDir}`);
      }

      // Load and process results
      const results = await this.loadResults();
      const analysis = await this.performAnalysis(results);
      
      // Generate outputs
      await this.saveAnalysis(analysis);
      await this.generateHtmlReport(analysis);
      await this.generateJsonReport(analysis);
      await this.generateMarkdownSummary(analysis);
      
      // Update latest symlink
      await this.updateLatestLink();
      
      console.log(`✅ Analysis completed for run: ${this.runId}`);
      console.log(`📊 Reports generated:`);
      console.log(`  - HTML: ${this.reportsDir}/${this.runId}_analysis.html`);
      console.log(`  - JSON: ${this.analysisDir}/${this.runId}_analysis.json`);
      console.log(`  - Summary: ${this.reportsDir}/${this.runId}_summary.md`);
      
      return analysis;
      
    } catch (error) {
      console.error(`❌ Analysis failed: ${error.message}`);
      process.exit(1);
    }
  }

  async loadResults() {
    console.log('📋 Loading test results...');
    
    const results = {
      tests: [],
      summary: {},
      metadata: {},
      traces: [],
      screenshots: [],
      videos: []
    };

    // Load Playwright results JSON
    const resultsJsonPath = path.join(this.resultsDir, 'results.json');
    if (fs.existsSync(resultsJsonPath)) {
      const rawResults = JSON.parse(fs.readFileSync(resultsJsonPath, 'utf8'));
      results.tests = rawResults.suites?.flatMap(suite => 
        this.extractTestsFromSuite(suite)
      ) || [];
      results.summary = rawResults.stats || {};
    }

    // Load test report JSON if available
    const reportJsonPath = path.join(this.resultsDir, 'report.json');
    if (fs.existsSync(reportJsonPath)) {
      const reportData = JSON.parse(fs.readFileSync(reportJsonPath, 'utf8'));
      results.metadata = reportData.config || {};
    }

    // Scan for additional artifacts
    results.traces = this.findFiles(this.resultsDir, '.zip');
    results.screenshots = this.findFiles(this.resultsDir, '.png');
    results.videos = this.findFiles(this.resultsDir, '.webm');

    console.log(`📊 Loaded ${results.tests.length} test results`);
    return results;
  }

  extractTestsFromSuite(suite, parentTitle = '') {
    const tests = [];
    const currentTitle = parentTitle ? `${parentTitle} > ${suite.title}` : suite.title;

    // Add tests from this suite
    if (suite.tests) {
      suite.tests.forEach(test => {
        tests.push({
          title: test.title,
          fullTitle: `${currentTitle} > ${test.title}`,
          status: test.outcome || test.status || 'unknown',
          duration: test.duration || 0,
          error: test.error,
          annotations: test.annotations || [],
          retry: test.retry || 0,
          workerIndex: test.workerIndex,
          location: test.location
        });
      });
    }

    // Recursively process child suites
    if (suite.suites) {
      suite.suites.forEach(childSuite => {
        tests.push(...this.extractTestsFromSuite(childSuite, currentTitle));
      });
    }

    return tests;
  }

  findFiles(directory, extension) {
    if (!fs.existsSync(directory)) return [];
    
    const files = [];
    const items = fs.readdirSync(directory, { withFileTypes: true });
    
    items.forEach(item => {
      const fullPath = path.join(directory, item.name);
      if (item.isDirectory()) {
        files.push(...this.findFiles(fullPath, extension));
      } else if (item.name.endsWith(extension)) {
        files.push(fullPath);
      }
    });
    
    return files;
  }

  async performAnalysis(results) {
    console.log('🧮 Performing comprehensive analysis...');
    
    const analysis = {
      runId: this.runId,
      timestamp: new Date().toISOString(),
      summary: this.generateSummary(results),
      failures: this.analyzeFailures(results),
      performance: this.analyzePerformance(results),
      coverage: this.analyzeCoverage(results),
      artifacts: this.analyzeArtifacts(results),
      trends: await this.analyzeTrends(results),
      recommendations: []
    };

    // Generate recommendations based on analysis
    analysis.recommendations = this.generateRecommendations(analysis);
    
    return analysis;
  }

  generateSummary(results) {
    const tests = results.tests || [];
    const passed = tests.filter(t => t.status === 'passed').length;
    const failed = tests.filter(t => t.status === 'failed').length;
    const skipped = tests.filter(t => t.status === 'skipped').length;
    const total = tests.length;
    
    return {
      total,
      passed,
      failed,
      skipped,
      successRate: total > 0 ? Math.round((passed / total) * 100 * 100) / 100 : 0,
      duration: tests.reduce((sum, test) => sum + (test.duration || 0), 0),
      averageTestTime: total > 0 ? Math.round((tests.reduce((sum, test) => sum + (test.duration || 0), 0) / total) * 100) / 100 : 0,
      retries: tests.reduce((sum, test) => sum + (test.retry || 0), 0)
    };
  }

  analyzeFailures(results) {
    const failures = results.tests?.filter(t => t.status === 'failed') || [];
    
    const categories = this.categorizeFailures(failures);
    const patterns = this.identifyFailurePatterns(failures);
    
    return {
      total: failures.length,
      categories,
      patterns,
      repeatOffenders: this.findRepeatFailures(failures),
      newFailures: this.identifyNewFailures(failures),
      criticalPaths: this.identifyCriticalPaths(failures)
    };
  }

  categorizeFailures(failures) {
    const categories = {
      'Browser/Infrastructure': { count: 0, tests: [], description: 'Browser launch, system dependencies' },
      'Network/CORS': { count: 0, tests: [], description: 'Network errors, CORS issues' },
      'Authentication': { count: 0, tests: [], description: 'Login, JWT, permissions' },
      'Service Unavailable': { count: 0, tests: [], description: 'Service down, timeouts' },
      'Assertion Errors': { count: 0, tests: [], description: 'Test logic, expected vs actual' },
      'Timeout': { count: 0, tests: [], description: 'Page load, element wait timeouts' },
      'Element Not Found': { count: 0, tests: [], description: 'Missing DOM elements' },
      'JavaScript Errors': { count: 0, tests: [], description: 'Runtime JS errors' },
      'Other': { count: 0, tests: [], description: 'Uncategorized failures' }
    };

    failures.forEach(failure => {
      const error = failure.error?.message || '';
      const title = failure.fullTitle || failure.title || '';
      
      let categorized = false;
      
      // Browser/Infrastructure issues
      if (error.includes('browserType.launch') || 
          error.includes('Executable doesn\'t exist') ||
          error.includes('browser') ||
          error.includes('chromium') ||
          error.includes('playwright')) {
        categories['Browser/Infrastructure'].count++;
        categories['Browser/Infrastructure'].tests.push(failure);
        categorized = true;
      }
      
      // Network/CORS issues
      else if (error.includes('CORS') || 
               error.includes('Cross-Origin') ||
               error.includes('net::ERR') ||
               error.includes('Access to fetch') ||
               error.includes('ERR_CERT_AUTHORITY_INVALID')) {
        categories['Network/CORS'].count++;
        categories['Network/CORS'].tests.push(failure);
        categorized = true;
      }
      
      // Authentication issues
      else if (error.includes('Authentication') || 
               error.includes('401') || 
               error.includes('403') ||
               error.includes('Unauthorized') ||
               error.includes('credentials were not provided')) {
        categories['Authentication'].count++;
        categories['Authentication'].tests.push(failure);
        categorized = true;
      }
      
      // Service availability
      else if (error.includes('503') || 
               error.includes('502') || 
               error.includes('ECONNREFUSED') ||
               error.includes('Service Unavailable') ||
               error.includes('Navigation to') ||
               error.includes('chrome-error://')) {
        categories['Service Unavailable'].count++;
        categories['Service Unavailable'].tests.push(failure);
        categorized = true;
      }
      
      // Timeout issues
      else if (error.includes('timeout') || 
               error.includes('Timeout') ||
               error.includes('waiting for') ||
               error.includes('exceeded') ||
               error.includes('waitFor')) {
        categories['Timeout'].count++;
        categories['Timeout'].tests.push(failure);
        categorized = true;
      }
      
      // Element not found
      else if (error.includes('locator') ||
               error.includes('element') ||
               error.includes('selector') ||
               error.includes('not found') ||
               error.includes('not visible')) {
        categories['Element Not Found'].count++;
        categories['Element Not Found'].tests.push(failure);
        categorized = true;
      }
      
      // JavaScript errors
      else if (error.includes('ReferenceError') ||
               error.includes('TypeError') ||
               error.includes('SyntaxError') ||
               error.includes('page.evaluate')) {
        categories['JavaScript Errors'].count++;
        categories['JavaScript Errors'].tests.push(failure);
        categorized = true;
      }
      
      // Assertion errors
      else if (error.includes('expect') || 
               error.includes('assertion') ||
               error.includes('toBe') ||
               error.includes('toHaveProperty') ||
               error.includes('toContain')) {
        categories['Assertion Errors'].count++;
        categories['Assertion Errors'].tests.push(failure);
        categorized = true;
      }
      
      // Everything else
      if (!categorized) {
        categories['Other'].count++;
        categories['Other'].tests.push(failure);
      }
    });

    return categories;
  }

  identifyFailurePatterns(failures) {
    const patterns = {
      'flaky_tests': [],
      'consistent_failures': [],
      'timeout_prone': [],
      'browser_specific': []
    };

    // Group by test title to identify patterns
    const testGroups = {};
    failures.forEach(failure => {
      const key = failure.fullTitle || failure.title;
      if (!testGroups[key]) testGroups[key] = [];
      testGroups[key].push(failure);
    });

    // Analyze patterns
    Object.entries(testGroups).forEach(([testTitle, testFailures]) => {
      if (testFailures.length > 1) {
        // Check if failures are similar (flaky) or different (consistently broken)
        const errorMessages = testFailures.map(f => f.error?.message || '');
        const uniqueErrors = [...new Set(errorMessages)];
        
        if (uniqueErrors.length === 1) {
          patterns.consistent_failures.push({
            test: testTitle,
            count: testFailures.length,
            error: uniqueErrors[0]
          });
        } else {
          patterns.flaky_tests.push({
            test: testTitle,
            count: testFailures.length,
            errors: uniqueErrors
          });
        }
      }
      
      // Check for timeout-prone tests
      if (testFailures.some(f => (f.error?.message || '').includes('timeout'))) {
        patterns.timeout_prone.push({
          test: testTitle,
          failures: testFailures.length
        });
      }
    });

    return patterns;
  }

  findRepeatFailures(failures) {
    const counts = {};
    failures.forEach(failure => {
      const key = failure.fullTitle || failure.title;
      counts[key] = (counts[key] || 0) + 1;
    });

    return Object.entries(counts)
      .filter(([, count]) => count > 1)
      .sort((a, b) => b[1] - a[1])
      .map(([test, count]) => ({ test, count }));
  }

  identifyNewFailures(failures) {
    // This would compare against historical data
    // For now, return all failures as potentially new
    return failures.map(f => ({
      test: f.fullTitle || f.title,
      error: f.error?.message || 'Unknown error'
    }));
  }

  identifyCriticalPaths(failures) {
    const criticalKeywords = ['login', 'auth', 'profile', 'payment', 'checkout'];
    
    return failures.filter(failure => {
      const title = (failure.fullTitle || failure.title || '').toLowerCase();
      return criticalKeywords.some(keyword => title.includes(keyword));
    }).map(failure => ({
      test: failure.fullTitle || failure.title,
      error: failure.error?.message || 'Unknown error',
      impact: 'High'
    }));
  }

  analyzePerformance(results) {
    const tests = results.tests || [];
    const durations = tests.map(t => t.duration || 0).filter(d => d > 0);
    
    if (durations.length === 0) {
      return { message: 'No performance data available' };
    }

    durations.sort((a, b) => a - b);
    
    return {
      totalDuration: durations.reduce((sum, d) => sum + d, 0),
      averageDuration: Math.round((durations.reduce((sum, d) => sum + d, 0) / durations.length) * 100) / 100,
      medianDuration: durations[Math.floor(durations.length / 2)],
      slowestTests: tests
        .filter(t => t.duration > 0)
        .sort((a, b) => (b.duration || 0) - (a.duration || 0))
        .slice(0, 10)
        .map(t => ({
          test: t.fullTitle || t.title,
          duration: t.duration
        })),
      fastestTests: tests
        .filter(t => t.duration > 0)
        .sort((a, b) => (a.duration || 0) - (b.duration || 0))
        .slice(0, 5)
        .map(t => ({
          test: t.fullTitle || t.title,
          duration: t.duration
        }))
    };
  }

  analyzeCoverage(results) {
    // Analyze test coverage across different areas
    const tests = results.tests || [];
    const areas = {
      'Authentication': 0,
      'Profile': 0,
      'CORS': 0,
      'API': 0,
      'UI': 0,
      'Integration': 0
    };

    tests.forEach(test => {
      const title = (test.fullTitle || test.title || '').toLowerCase();
      
      if (title.includes('auth') || title.includes('login') || title.includes('logout')) {
        areas.Authentication++;
      }
      if (title.includes('profile')) {
        areas.Profile++;
      }
      if (title.includes('cors') || title.includes('cross-domain')) {
        areas.CORS++;
      }
      if (title.includes('api') || title.includes('endpoint')) {
        areas.API++;
      }
      if (title.includes('ui') || title.includes('page') || title.includes('click')) {
        areas.UI++;
      }
      if (title.includes('integration') || title.includes('workflow')) {
        areas.Integration++;
      }
    });

    return {
      totalTests: tests.length,
      coverageByArea: areas,
      coverageGaps: Object.entries(areas)
        .filter(([, count]) => count === 0)
        .map(([area]) => area)
    };
  }

  analyzeArtifacts(results) {
    return {
      traces: results.traces?.length || 0,
      screenshots: results.screenshots?.length || 0,
      videos: results.videos?.length || 0,
      hasArtifacts: (results.traces?.length || 0) + (results.screenshots?.length || 0) + (results.videos?.length || 0) > 0
    };
  }

  async analyzeTrends(results) {
    // This would analyze trends over time by comparing with historical data
    // For now, return basic trend information
    return {
      message: 'Trend analysis requires historical data',
      recommendation: 'Run tests regularly to build trend analysis'
    };
  }

  generateRecommendations(analysis) {
    const recommendations = [];
    
    // Success rate recommendations
    if (analysis.summary.successRate < 50) {
      recommendations.push({
        priority: 'CRITICAL',
        category: 'Success Rate',
        message: '🚨 Critical: Success rate below 50% - immediate attention required',
        action: 'Stop development and fix infrastructure issues immediately'
      });
    } else if (analysis.summary.successRate < 80) {
      recommendations.push({
        priority: 'HIGH',
        category: 'Success Rate',
        message: '⚠️ Success rate below 80% - review test infrastructure',
        action: 'Investigate top failure categories and fix underlying issues'
      });
    } else if (analysis.summary.successRate < 95) {
      recommendations.push({
        priority: 'MEDIUM',
        category: 'Success Rate',
        message: '📈 Success rate can be improved - target 95%+',
        action: 'Review and fix remaining failing tests'
      });
    }

    // Failure category recommendations
    const categories = analysis.failures.categories;
    
    if (categories['Browser/Infrastructure'].count > 0) {
      recommendations.push({
        priority: 'HIGH',
        category: 'Infrastructure',
        message: '🖥️ Browser/infrastructure issues detected',
        action: 'Verify Playwright installation, system dependencies, and Docker configuration'
      });
    }
    
    if (categories['Service Unavailable'].count > 0) {
      recommendations.push({
        priority: 'HIGH',
        category: 'Services',
        message: '🌐 Service availability issues detected',
        action: 'Check service health, startup order, and network connectivity'
      });
    }
    
    if (categories['Network/CORS'].count > 0) {
      recommendations.push({
        priority: 'MEDIUM',
        category: 'CORS',
        message: '🔗 CORS/Network issues detected',
        action: 'Review CORS configuration and network policies'
      });
    }

    if (categories['Timeout'].count > analysis.summary.total * 0.1) {
      recommendations.push({
        priority: 'MEDIUM',
        category: 'Performance',
        message: '⏱️ High number of timeout failures',
        action: 'Increase timeout values or optimize application performance'
      });
    }

    // Performance recommendations
    if (analysis.performance.averageDuration > 30000) {
      recommendations.push({
        priority: 'MEDIUM',
        category: 'Performance',
        message: '🐌 Average test duration is high (>30s)',
        action: 'Optimize test execution and application performance'
      });
    }

    // Coverage recommendations
    if (analysis.coverage.coverageGaps.length > 0) {
      recommendations.push({
        priority: 'LOW',
        category: 'Coverage',
        message: `📊 Missing test coverage in: ${analysis.coverage.coverageGaps.join(', ')}`,
        action: 'Add tests for uncovered areas'
      });
    }

    return recommendations;
  }

  async saveAnalysis(analysis) {
    const filePath = path.join(this.analysisDir, `${this.runId}_analysis.json`);
    fs.writeFileSync(filePath, JSON.stringify(analysis, null, 2));
    console.log(`💾 Analysis saved: ${filePath}`);
  }

  async generateHtmlReport(analysis) {
    const html = this.generateHtmlTemplate(analysis);
    const filePath = path.join(this.reportsDir, `${this.runId}_analysis.html`);
    fs.writeFileSync(filePath, html);
    console.log(`📄 HTML report generated: ${filePath}`);
  }

  generateHtmlTemplate(analysis) {
    const successRateColor = analysis.summary.successRate >= 95 ? '#28a745' : 
                             analysis.summary.successRate >= 80 ? '#ffc107' : '#dc3545';
    
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Test Analysis Report - ${analysis.runId}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f8f9fa; 
        }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 2px solid #e9ecef; padding-bottom: 20px; margin-bottom: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .summary-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
        .summary-card h3 { margin: 0 0 10px 0; color: #495057; font-size: 14px; text-transform: uppercase; }
        .summary-card .value { font-size: 32px; font-weight: bold; color: #212529; margin: 0; }
        .success-rate { color: ${successRateColor} !important; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #495057; border-bottom: 1px solid #e9ecef; padding-bottom: 10px; }
        .failure-categories { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
        .category-card { background: #fff; border: 1px solid #e9ecef; padding: 15px; border-radius: 6px; }
        .category-header { display: flex; justify-content-between; align-items: center; margin-bottom: 10px; }
        .category-count { background: #dc3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 12px; }
        .recommendations { background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; }
        .recommendation { margin-bottom: 15px; padding: 15px; border-radius: 6px; }
        .recommendation.critical { background: #f8d7da; border-left: 4px solid #dc3545; }
        .recommendation.high { background: #fff3cd; border-left: 4px solid #ffc107; }
        .recommendation.medium { background: #d1ecf1; border-left: 4px solid #17a2b8; }
        .recommendation.low { background: #d4edda; border-left: 4px solid #28a745; }
        .performance-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 6px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #e9ecef; padding: 12px; text-align: left; }
        th { background-color: #f8f9fa; font-weight: 600; }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #e9ecef; color: #6c757d; }
        .artifacts { background: #e7f3ff; padding: 15px; border-radius: 6px; margin-top: 15px; }
        .trend-placeholder { background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; color: #6c757d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test Analysis Report</h1>
            <p><strong>Run ID:</strong> ${analysis.runId}</p>
            <p><strong>Generated:</strong> ${new Date(analysis.timestamp).toLocaleString()}</p>
        </div>

        <div class="section">
            <h2>📊 Summary</h2>
            <div class="summary">
                <div class="summary-card">
                    <h3>Success Rate</h3>
                    <p class="value success-rate">${analysis.summary.successRate}%</p>
                </div>
                <div class="summary-card">
                    <h3>Total Tests</h3>
                    <p class="value">${analysis.summary.total}</p>
                </div>
                <div class="summary-card">
                    <h3>Passed</h3>
                    <p class="value" style="color: #28a745;">${analysis.summary.passed}</p>
                </div>
                <div class="summary-card">
                    <h3>Failed</h3>
                    <p class="value" style="color: #dc3545;">${analysis.summary.failed}</p>
                </div>
                <div class="summary-card">
                    <h3>Duration</h3>
                    <p class="value">${Math.round(analysis.summary.duration / 1000)}s</p>
                </div>
                <div class="summary-card">
                    <h3>Avg Test Time</h3>
                    <p class="value">${Math.round(analysis.summary.averageTestTime / 1000)}s</p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>❌ Failure Analysis</h2>
            <div class="failure-categories">
                ${Object.entries(analysis.failures.categories).map(([category, data]) => `
                    <div class="category-card">
                        <div class="category-header">
                            <strong>${category}</strong>
                            <span class="category-count">${data.count}</span>
                        </div>
                        <p style="color: #6c757d; font-size: 14px; margin: 0;">${data.description}</p>
                        ${data.count > 0 ? `<p style="margin: 10px 0 0 0; font-size: 14px;">Percentage: ${Math.round((data.count / analysis.summary.failed) * 100)}%</p>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="section">
            <h2>⚡ Performance Metrics</h2>
            <div class="performance-metrics">
                <div class="metric-card">
                    <h4>Overall Performance</h4>
                    <p><strong>Total Duration:</strong> ${Math.round(analysis.performance.totalDuration / 1000)}s</p>
                    <p><strong>Average Test:</strong> ${Math.round(analysis.performance.averageDuration / 1000)}s</p>
                    <p><strong>Median Test:</strong> ${Math.round((analysis.performance.medianDuration || 0) / 1000)}s</p>
                </div>
                <div class="metric-card">
                    <h4>Slowest Tests</h4>
                    ${analysis.performance.slowestTests ? analysis.performance.slowestTests.slice(0, 3).map(test => 
                        `<p><small>${test.test.substring(0, 40)}...</small><br><strong>${Math.round(test.duration / 1000)}s</strong></p>`
                    ).join('') : '<p>No performance data available</p>'}
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📋 Recommendations</h2>
            <div class="recommendations">
                ${analysis.recommendations.map(rec => `
                    <div class="recommendation ${rec.priority.toLowerCase()}">
                        <strong>[${rec.priority}] ${rec.category}:</strong> ${rec.message}
                        <br><small><strong>Action:</strong> ${rec.action}</small>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="section">
            <h2>📁 Artifacts</h2>
            <div class="artifacts">
                <p><strong>Traces:</strong> ${analysis.artifacts.traces}</p>
                <p><strong>Screenshots:</strong> ${analysis.artifacts.screenshots}</p>
                <p><strong>Videos:</strong> ${analysis.artifacts.videos}</p>
                ${analysis.artifacts.hasArtifacts ? 
                    '<p style="color: #28a745;">✅ Debugging artifacts available for failed tests</p>' : 
                    '<p style="color: #ffc107;">⚠️ No debugging artifacts found</p>'
                }
            </div>
        </div>

        <div class="section">
            <h2>📈 Trends</h2>
            <div class="trend-placeholder">
                <p>📊 Trend analysis will be available after multiple test runs</p>
                <p>Run tests regularly to build historical comparison data</p>
            </div>
        </div>

        <div class="footer">
            <p>Generated by VF Services Test Analyzer</p>
            <p>For more details, check the JSON analysis file: <code>${analysis.runId}_analysis.json</code></p>
        </div>
    </div>
</body>
</html>`;
  }

  async generateJsonReport(analysis) {
    const filePath = path.join(this.reportsDir, `${this.runId}_analysis.json`);
    fs.writeFileSync(filePath, JSON.stringify(analysis, null, 2));
    console.log(`📄 JSON report generated: ${filePath}`);
  }

  async generateMarkdownSummary(analysis) {
    const markdown = `# Test Analysis Summary - ${analysis.runId}

**Generated:** ${new Date(analysis.timestamp).toLocaleString()}

## 📊 Quick Stats

- **Success Rate:** ${analysis.summary.successRate}%
- **Total Tests:** ${analysis.summary.total}
- **Passed:** ${analysis.summary.passed} ✅
- **Failed:** ${analysis.summary.failed} ❌
- **Duration:** ${Math.round(analysis.summary.duration / 1000)}s

## ❌ Top Failure Categories

${Object.entries(analysis.failures.categories)
  .filter(([, data]) => data.count > 0)
  .sort((a, b) => b[1].count - a[1].count)
  .map(([category, data]) => `- **${category}:** ${data.count} failures (${Math.round((data.count / analysis.summary.failed) * 100)}%)`)
  .join('\n')}

## 🎯 Key Recommendations

${analysis.recommendations.slice(0, 5).map(rec => `- **[${rec.priority}]** ${rec.message}`).join('\n')}

## 📁 Artifacts

- Traces: ${analysis.artifacts.traces}
- Screenshots: ${analysis.artifacts.screenshots}  
- Videos: ${analysis.artifacts.videos}

---
*Full analysis available in HTML report: \`${analysis.runId}_analysis.html\`*
`;

    const filePath = path.join(this.reportsDir, `${this.runId}_summary.md`);
    fs.writeFileSync(filePath, markdown);
    console.log(`📄 Markdown summary generated: ${filePath}`);
  }

  async updateLatestLink() {
    const latestLink = path.join(this.reportsDir, 'latest');
    try {
      if (fs.existsSync(latestLink)) {
        fs.unlinkSync(latestLink);
      }
      fs.symlinkSync(`${this.runId}_analysis.html`, latestLink);
      console.log(`🔗 Updated latest report link`);
    } catch (error) {
      console.warn(`⚠️ Could not create latest link: ${error.message}`);
    }
  }
}

// CLI usage
if (require.main === module) {
  const runId = process.env.TEST_RUN_ID || process.argv[2];
  
  if (!runId) {
    console.error('❌ Usage: node analyze-results.js <TEST_RUN_ID>');
    console.error('   or set TEST_RUN_ID environment variable');
    process.exit(1);
  }
  
  const analyzer = new TestResultsAnalyzer(runId);
  analyzer.analyze().catch(error => {
    console.error('❌ Analysis failed:', error.message);
    process.exit(1);
  });
}

module.exports = TestResultsAnalyzer;
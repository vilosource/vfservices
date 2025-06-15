# Docker Testing Maintenance Guide

## Overview

This document provides comprehensive maintenance procedures for the VF Services Docker-based testing infrastructure. It covers day-to-day operations, troubleshooting, performance optimization, and long-term maintenance strategies.

## Quick Reference

### 🚀 **Daily Operations**

```bash
# Run enhanced tests
make test-docker-enhanced

# Quick development tests
make test-quick

# View test status
make test-status

# View recent results
make test-list

# Start web report server
make test-web
```

### 🔧 **Maintenance Commands**

```bash
# Clean Docker environment
make test-docker-clean

# Archive old results
make test-archive

# Get help with all commands
make test-help

# Show system status
make test-status
```

## Daily Maintenance

### Morning Checklist

#### 1. **Check Test Infrastructure Health**
```bash
# Verify Docker environment
docker compose ps
docker system df

# Check test environment status
make test-status

# Review recent test runs
make test-list
```

#### 2. **Review Latest Test Results**
```bash
# Start web interface for report viewing
make test-web

# Open browser to view reports
# http://localhost:8080/reports/
# http://localhost:8080/public/

# Analyze latest run
make test-analyze TEST_RUN_ID=$(ls -t test-results | head -n1)
```

#### 3. **Monitor Success Rates**
Check key metrics:
- **Success Rate**: Target 95%+
- **Execution Time**: Target <30 minutes
- **Failure Categories**: Track trends
- **Performance**: Monitor slow tests

### Development Workflow

#### **Before Starting Development**
```bash
# Ensure clean environment
make test-docker-clean

# Run quick smoke tests
make test-quick

# If issues found, run full analysis
make test-docker-enhanced
```

#### **During Development**
```bash
# Test specific changes
make test-docker-enhanced TEST_MODE=quick

# Debug with browser UI (if needed)
make test-docker-headed

# Interactive debugging
make test-docker-debug
```

#### **Before Committing Code**
```bash
# Full test run with analysis
make test-docker-enhanced

# Review results
make test-analyze TEST_RUN_ID=$(date +%Y%m%d_%H%M%S)

# Ensure >95% success rate before commit
```

## Weekly Maintenance

### Performance Review

#### **Test Execution Analysis**
```bash
# Generate comprehensive performance report
make test-report

# Identify slow tests
make test-analyze TEST_RUN_ID=latest | grep -A 10 "slowest"

# Review container resource usage
docker stats --no-stream
```

#### **Storage Management**
```bash
# Check disk usage
du -sh test-results/ test-reports/ analysis-output/

# Archive old results (>30 days)
make test-archive

# Clean old Docker resources
make test-docker-clean
docker system prune -f --volumes
```

### Quality Metrics Review

#### **Success Rate Trends**
Monitor weekly trends:
- Compare current week vs previous week
- Identify recurring failure patterns
- Track improvement in success rates
- Review failure category distributions

#### **Performance Optimization**
- Identify consistently slow tests
- Review container startup times
- Optimize Docker layer caching
- Monitor resource utilization

## Monthly Maintenance

### Infrastructure Updates

#### **Container Image Updates**
```bash
# Update Playwright base image
cd tests/playwright/docker
vim Dockerfile.playwright.enhanced
# Update: FROM mcr.microsoft.com/playwright:v1.41.0-focal

# Rebuild containers
make test-docker-setup
```

#### **Browser Version Updates**
```bash
# Check current browser versions
make test-docker-debug
# In container: npx playwright --version

# Update browsers if needed
# (Handled automatically with container updates)
```

#### **Dependency Updates**
```bash
# Update test dependencies
cd tests
npm update
npm audit fix

# Update analyzer dependencies
cd analyzer
npm update
```

### Configuration Review

#### **Environment Configuration**
Review and update:
- `docker-compose.test.enhanced.yml`
- `Makefile.test-enhancement`
- `tests/playwright.config.js`
- `tests/playwright/config/test-environments.json`

#### **Analysis Tuning**
- Review failure categorization accuracy
- Update analysis patterns for new error types
- Enhance recommendation algorithms
- Optimize report generation

## Troubleshooting Guide

### Common Issues

#### **High Failure Rate (>20%)**

**Diagnosis:**
```bash
# Analyze recent failures
make test-analyze TEST_RUN_ID=latest

# Check service health
docker compose ps
docker compose logs traefik
docker compose logs website
docker compose logs identity-provider
```

**Common Causes & Solutions:**
1. **Service Startup Issues**
   - Increase health check timeout
   - Review service dependencies
   - Check resource constraints

2. **Network Issues**
   - Verify Docker network configuration
   - Check port conflicts
   - Review Traefik routing

3. **Browser Issues**
   - Update container images
   - Check resource limits
   - Review browser configuration

#### **Slow Test Execution (>45 minutes)**

**Diagnosis:**
```bash
# Identify slow tests
make test-analyze TEST_RUN_ID=latest | grep -A 20 "Performance"

# Check container resources
docker stats --no-stream
```

**Optimization Strategies:**
1. **Parallel Execution**
   ```bash
   # Increase parallel workers
   make test-docker-enhanced TEST_PARALLEL=6
   ```

2. **Container Optimization**
   - Review Dockerfile for efficiency
   - Optimize layer caching
   - Reduce container size

3. **Test Optimization**
   - Review slow test patterns
   - Optimize wait strategies
   - Reduce test complexity

#### **Docker Resource Issues**

**Storage Issues:**
```bash
# Check Docker disk usage
docker system df

# Clean unused resources
docker system prune -f --volumes

# Remove old test containers
docker container prune -f
```

**Memory Issues:**
```bash
# Check container memory usage
docker stats --no-stream

# Adjust container limits in docker-compose.test.enhanced.yml
services:
  playwright-runner:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### Advanced Debugging

#### **Container Debug Mode**
```bash
# Interactive debugging
make test-docker-debug

# In container:
# - Run specific tests
# - Check environment variables
# - Debug network connectivity
# - Examine file system
```

#### **Network Debugging**
```bash
# Check Docker networks
docker network ls
docker network inspect vfnet

# Test service connectivity from test container
make test-docker-debug
# In container:
curl -k https://vfservices.viloforge.com/api/status/
```

#### **Service Debugging**
```bash
# Check service logs
docker compose logs -f traefik
docker compose logs -f website
docker compose logs -f identity-provider

# Check service health
docker compose ps
```

## Performance Optimization

### Container Optimization

#### **Multi-stage Build Optimization**
```dockerfile
# Optimize Dockerfile.playwright.enhanced
FROM mcr.microsoft.com/playwright:v1.40.0-focal as base

# Use BuildKit for faster builds
# docker build --target=development .
```

#### **Layer Caching**
```bash
# Optimize build order for better caching
COPY package*.json ./
RUN npm ci --only=production
COPY . .
```

#### **Resource Limits**
```yaml
# docker-compose.test.enhanced.yml
services:
  playwright-runner:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Test Execution Optimization

#### **Parallel Execution Tuning**
```bash
# Optimal worker count (typically CPU cores)
make test-docker-enhanced TEST_PARALLEL=4

# Monitor resource usage during parallel runs
docker stats --no-stream
```

#### **Timeout Optimization**
```javascript
// playwright.config.js
module.exports = {
  timeout: 30000,  // Per test timeout
  expect: {
    timeout: 10000  // Assertion timeout
  },
  use: {
    navigationTimeout: 15000,  // Page navigation
    actionTimeout: 10000       // Element actions
  }
}
```

### Analysis Performance

#### **Report Generation Optimization**
```bash
# Optimize analysis for large result sets
make test-analyze TEST_RUN_ID=latest 2>&1 | tee analysis.log

# Monitor analysis performance
time make test-analyze TEST_RUN_ID=latest
```

#### **Storage Optimization**
```bash
# Automatic cleanup of old results
find test-results -type d -mtime +30 -exec rm -rf {} +

# Compress archived results
tar -czf archived-results-$(date +%Y%m).tar.gz test-results/
```

## Security Considerations

### Container Security

#### **Image Security**
```bash
# Scan container images for vulnerabilities
docker scan tests_playwright-runner:latest

# Use minimal base images
# Regular security updates
```

#### **Network Security**
```bash
# Verify network isolation
docker network inspect vfnet

# Check exposed ports
docker compose ps
```

### Data Security

#### **Test Data Protection**
- Automatic cleanup of sensitive test data
- Secure handling of test credentials
- Encrypted storage of test results
- Access control for test reports

#### **Credential Management**
```bash
# Use environment variables for sensitive data
export TEST_USER_PASSWORD="secure_password"

# Avoid hardcoding credentials in test files
# Use secure credential injection
```

## Monitoring and Alerting

### Automated Monitoring

#### **Test Result Monitoring**
```bash
# Real-time monitoring
make test-monitor

# Set up continuous monitoring
# (Implementation depends on monitoring system)
```

#### **Performance Monitoring**
Track key metrics:
- Test execution time trends
- Success rate over time
- Failure category distribution
- Container resource usage

### Alerting Setup

#### **Failure Rate Alerts**
Set up alerts for:
- Success rate < 90%
- Execution time > 45 minutes
- Container resource exhaustion
- Service availability issues

#### **Integration Examples**
```bash
# Example webhook for high failure rate
if [ "$SUCCESS_RATE" -lt 90 ]; then
  curl -X POST "$SLACK_WEBHOOK" \
    -d '{"text":"🚨 Test failure rate: '$SUCCESS_RATE'% - Investigation required"}'
fi
```

## Backup and Recovery

### Test Result Backup

#### **Automated Archival**
```bash
# Weekly automated backup
make test-archive

# Monthly comprehensive backup
tar -czf vf-test-backup-$(date +%Y%m).tar.gz \
  test-results/ \
  test-reports/ \
  analysis-output/ \
  docker-compose.test.enhanced.yml \
  Makefile.test-enhancement
```

#### **Recovery Procedures**
```bash
# Restore from backup
tar -xzf vf-test-backup-202412.tar.gz

# Verify restoration
make test-status
make test-list
```

### Configuration Backup

#### **Infrastructure as Code**
Maintain version control for:
- Docker configurations
- Makefile targets
- Test configurations
- Analysis scripts

#### **Environment Recreation**
```bash
# Complete environment recreation
git clone <repository>
cd vfservices
make test-setup
make test-docker-enhanced
```

## Team Collaboration

### Developer Onboarding

#### **Setup Checklist**
- [ ] Install Docker and Docker Compose
- [ ] Clone VF Services repository
- [ ] Run `make test-help` to see available commands
- [ ] Run `make test-quick` to verify setup
- [ ] Review documentation in `docs/`

#### **Training Materials**
1. **Docker Testing Overview**: Read `DOCKER_TESTING_STRATEGY.md`
2. **Daily Workflows**: Practice common testing commands
3. **Debugging Techniques**: Learn interactive debugging
4. **Best Practices**: Review coding and testing standards

### Knowledge Sharing

#### **Regular Reviews**
- Weekly test result reviews
- Monthly infrastructure updates
- Quarterly strategy assessments
- Annual technology evaluations

#### **Documentation Maintenance**
- Keep documentation current with changes
- Update troubleshooting guides
- Share debugging techniques
- Document new patterns and solutions

## Future Planning

### Scalability Considerations

#### **Infrastructure Scaling**
- Container orchestration (Kubernetes)
- Distributed test execution
- Cloud-based testing environments
- Advanced monitoring and analytics

#### **Test Suite Growth**
- Modular test organization
- Smart test selection
- Predictive failure analysis
- Automated test maintenance

### Technology Evolution

#### **Upcoming Enhancements**
- Machine learning for failure prediction
- Advanced visual regression testing
- Performance testing integration
- Enhanced accessibility testing

#### **Continuous Improvement**
- Regular technology assessments
- Performance optimization cycles
- Developer experience improvements
- Integration with emerging tools

---

This maintenance guide ensures the Docker-based testing infrastructure remains reliable, performant, and valuable for the VF Services development team. Regular adherence to these procedures will maintain the high-quality testing environment and support continuous development efforts.
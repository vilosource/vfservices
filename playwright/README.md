# Playwright Tests for VF Services

This directory contains Playwright smoke tests for the VF Services application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Running Tests

### Run all website smoke tests:
```bash
pytest website/smoke-tests/
```

### Run specific test file:
```bash
pytest website/smoke-tests/test_vfservices_access.py
```

### Run with verbose output:
```bash
pytest -v website/smoke-tests/test_vfservices_access.py
```

### Run a single test function:
```bash
python website/smoke-tests/test_vfservices_access.py
```

## Test Structure

Tests are organized by Django project:
- `website/smoke-tests/` - Tests for the main website (vfservices.viloforge.com)
- `identity-provider/smoke-tests/` - Tests for the identity provider (identity.vfservices.viloforge.com)
- `cielo-website/smoke-tests/` - Tests for the Cielo website (cielo.viloforge.com)

All tests access services through Traefik endpoints as specified in CLAUDE.md.

## Running All Tests

To run all smoke tests across services:
```bash
pytest .
```

To run tests for a specific service:
```bash
pytest website/smoke-tests/
pytest identity-provider/smoke-tests/
```

## Test Documentation

Each test directory contains its own README.md with:
- Detailed test descriptions
- Expected results
- Troubleshooting guides
- Service-specific notes
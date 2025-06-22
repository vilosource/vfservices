# Malta Central SSL Certificate Tests

This directory contains Playwright tests to verify SSL certificate configuration for www.maltacentral.com.

## Test Coverage

The SSL certificate test (`test_ssl_certificate.py`) verifies:

1. **Browser SSL Validation**
   - Tests that browsers accept the certificate as valid
   - Verifies both www.maltacentral.com and maltacentral.com
   - Ensures no SSL warnings or errors

2. **Certificate Details**
   - Validates certificate is currently valid (not expired)
   - Checks certificate validity period
   - Verifies Subject Alternative Names (SANs) include maltacentral domains
   - Shows days remaining until expiration

3. **HTTPS Redirect**
   - Confirms HTTP requests redirect to HTTPS
   - Verifies the redirect maintains the correct domain

4. **Certificate Chain**
   - Validates the complete certificate chain
   - Ensures intermediate certificates are properly served

## Prerequisites

```bash
# Install Python dependencies
pip install playwright pytest pyOpenSSL

# Install Playwright browsers
playwright install chromium
```

## Running the Tests

### Run all SSL certificate tests:
```bash
cd playwright/maltacentral-web/smoke-tests
python test_ssl_certificate.py
```

### Run with pytest for detailed output:
```bash
cd playwright/maltacentral-web/smoke-tests
pytest test_ssl_certificate.py -v
```

### Run specific test:
```bash
pytest test_ssl_certificate.py::TestMaltaCentralSSLCertificate::test_ssl_certificate_details -v
```

## Expected Results

When all tests pass, you should see:
- ✅ Browser SSL validation: PASSED
- ✅ Certificate details verification: PASSED
- ✅ HTTPS redirect test: PASSED
- ✅ Certificate chain validation: PASSED

The certificate should include these domains in its SANs:
- maltacentral.com
- www.maltacentral.com
- vfservices.viloforge.com
- *.vfservices.viloforge.com
- cielo.viloforge.com
- *.cielo.viloforge.com

## Troubleshooting

### Connection Timeout
If tests fail with connection timeout:
1. Ensure Docker services are running: `docker compose ps`
2. Check Traefik is healthy and serving HTTPS
3. Verify DNS resolution for maltacentral.com

### Certificate Errors
If certificate validation fails:
1. Check certificate is properly mounted in Traefik
2. Verify `traefik/dynamic/tls-config.yaml` points to correct certificate
3. Ensure certificate includes maltacentral.com domains: 
   ```bash
   openssl x509 -in certs/live/vfservices.viloforge.com/cert.pem -text -noout | grep -A3 "Subject Alternative Name"
   ```

### Import Errors
If you get import errors for OpenSSL:
```bash
pip install pyOpenSSL
```

## Certificate Renewal

The certificate expires every 90 days. To renew:
```bash
CLOUDFLARE_API_TOKEN=your_token LETSENCRYPT_EMAIL=your@email.com make certbot-renew
```

## Notes

- Tests use real HTTPS connections to verify certificates
- No self-signed certificates or ignore_https_errors flags are used
- Tests validate the actual certificate served by Traefik
- Certificate expiration warnings appear when < 30 days remain
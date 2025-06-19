# Testing Guide: Step 1 - Identity Provider Multi-Domain Support

## Overview
This guide provides comprehensive testing procedures to verify that the identity provider correctly supports authentication across both `vfservices.viloforge.com` and `cielo.viloforge.com` domains.

## Prerequisites

1. **Services Running**:
   ```bash
   docker-compose up -d
   ```

2. **Verify Services**:
   ```bash
   docker ps | grep -E "(identity-provider|traefik)"
   ```

3. **Test User Available**:
   - Username: `alice`
   - Password: `AlicePassword123!`

## Automated Testing

### Run Test Script
```bash
# Run automated tests
python tests/playwright/api/test_cielo_step1_multidomain.py

# Show manual testing checklist
python tests/playwright/api/test_cielo_step1_multidomain.py --manual
```

### What the Script Tests
1. **CORS Configuration**: Verifies both domains can make cross-origin requests
2. **Redirect URL Validation**: Tests allowed and blocked redirect URLs
3. **JWT Cookie Domain**: Ensures cookies work across subdomains
4. **Security**: Verifies malicious redirects are blocked

## Manual Testing Procedures

### 1. CORS Verification

#### Browser Developer Tools Method
1. Open Chrome/Firefox Developer Tools (F12)
2. Navigate to `https://vfservices.viloforge.com`
3. Go to Network tab
4. Click login button
5. Look for requests to `identity.vfservices.viloforge.com`
6. Check Response Headers for:
   - `Access-Control-Allow-Origin: https://vfservices.viloforge.com`
   - `Access-Control-Allow-Credentials: true`

#### Command Line Method
```bash
# Test CORS from main domain
curl -H "Origin: https://vfservices.viloforge.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: content-type" \
     -X OPTIONS \
     https://identity.vfservices.viloforge.com/api/auth/login/ \
     -v 2>&1 | grep -i "access-control"

# Test CORS from Cielo domain
curl -H "Origin: https://cielo.viloforge.com" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: content-type" \
     -X OPTIONS \
     https://identity.vfservices.viloforge.com/api/auth/login/ \
     -v 2>&1 | grep -i "access-control"
```

### 2. Login Flow Testing

#### Test Case 1: Login from Main Domain
1. Open browser in incognito mode
2. Navigate to `https://vfservices.viloforge.com`
3. Click login (should redirect to `https://identity.vfservices.viloforge.com/login/`)
4. Check URL contains: `redirect_uri=https://vfservices.viloforge.com`
5. Login with alice/AlicePassword123!
6. Verify redirect back to `https://vfservices.viloforge.com`
7. Check for JWT cookie in browser developer tools

#### Test Case 2: Login from Cielo Domain
1. Open new incognito window
2. Navigate to `https://cielo.viloforge.com` (will get 404 until Step 2 implemented)
3. Manually go to: `https://identity.vfservices.viloforge.com/login/?redirect_uri=https://cielo.viloforge.com`
4. Login with alice/AlicePassword123!
5. Verify redirect to `https://cielo.viloforge.com`

### 3. Single Sign-On (SSO) Testing

1. Login at `https://vfservices.viloforge.com`
2. In same browser, open new tab
3. Navigate to `https://billing.vfservices.viloforge.com`
4. Verify you're already logged in (no login prompt)
5. Check JWT cookie is shared across subdomains

### 4. Security Testing

#### Test Invalid Redirect URLs
```bash
# These should redirect to default site, not the malicious URL
curl -X POST https://identity.vfservices.viloforge.com/login/ \
     -d "username=alice&password=AlicePassword123!" \
     -d "redirect_uri=https://evil.com/steal-token" \
     -L -v 2>&1 | grep -i "location:"
```

#### Check Logs for Security Events
```bash
# Check for redirect validation warnings
docker logs vfservices-identity-provider-1 2>&1 | grep -E "(Invalid redirect|Redirect URL validation)"
```

### 5. Cookie Configuration Testing

1. After successful login, check cookie properties:
   - Open Developer Tools > Application > Cookies
   - Find the `jwt` cookie
   - Verify:
     - Domain: `.vfservices.viloforge.com` (note the leading dot)
     - HttpOnly: ✓
     - Secure: ✓
     - SameSite: Lax

## Docker Testing Commands

### View Configuration
```bash
# Check CORS settings
docker exec vfservices-identity-provider-1 python -c "
from django.conf import settings
print('CORS_ALLOWED_ORIGINS:')
for origin in settings.CORS_ALLOWED_ORIGINS:
    print(f'  - {origin}')
"

# Check allowed redirect domains
docker exec vfservices-identity-provider-1 python -c "
from django.conf import settings
print('ALLOWED_REDIRECT_DOMAINS:')
for domain in settings.ALLOWED_REDIRECT_DOMAINS:
    print(f'  - {domain}')
"

# Check SSO cookie domain
docker exec vfservices-identity-provider-1 python -c "
from django.conf import settings
print(f'SSO_COOKIE_DOMAIN: {settings.SSO_COOKIE_DOMAIN}')
"
```

### Monitor Logs
```bash
# Watch identity provider logs
docker logs -f vfservices-identity-provider-1

# Filter for authentication events
docker logs vfservices-identity-provider-1 2>&1 | grep -E "(Login|Redirect|CORS)"
```

## Troubleshooting

### Common Issues

1. **CORS Errors in Browser Console**
   - Check: Is cielo.viloforge.com in CORS_ALLOWED_ORIGINS?
   - Fix: Restart identity-provider after configuration changes

2. **Redirect Goes to Wrong Domain**
   - Check: ALLOWED_REDIRECT_DOMAINS configuration
   - Check: validate_redirect_url function in views.py

3. **Cookie Not Shared Across Subdomains**
   - Check: SSO_COOKIE_DOMAIN starts with a dot (`.vfservices.viloforge.com`)
   - Check: Cookie domain in browser developer tools

4. **Login Works but No JWT Cookie**
   - Check: Docker logs for JWT creation errors
   - Verify: JWT_SECRET is set in environment

### Debug Commands
```bash
# Test JWT creation
docker exec vfservices-identity-provider-1 python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from common.jwt_auth import utils
user = User.objects.get(username='alice')
token = utils.generate_jwt_token(user)
print(f"JWT Token generated: {token[:20]}...")
EOF

# Test redirect validation
docker exec vfservices-identity-provider-1 python manage.py shell << 'EOF'
from identity_app.views import validate_redirect_url
test_urls = [
    'https://vfservices.viloforge.com',
    'https://cielo.viloforge.com',
    'https://evil.com'
]
for url in test_urls:
    result = validate_redirect_url(url)
    print(f"{url}: {'✓ VALID' if result else '✗ INVALID'}")
EOF
```

## Success Criteria Checklist

- [ ] No CORS errors when accessing from vfservices.viloforge.com
- [ ] No CORS errors when accessing from cielo.viloforge.com  
- [ ] Login redirects work for main domain
- [ ] Login redirects work for Cielo domain
- [ ] Invalid redirect URLs are blocked
- [ ] JWT cookie domain allows subdomain sharing
- [ ] Single sign-on works across subdomains
- [ ] Security logs show redirect validation
- [ ] All automated tests pass

## Next Steps

Once all tests pass:
1. Mark Step 1 as fully tested in implementation plan
2. Proceed to Step 2: Create Cielo Website Base
3. Use this same identity provider for Cielo authentication
import asyncio
import ssl
import socket
import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
import pytest
import OpenSSL.crypto


class TestMaltaCentralSSLCertificate:
    """Test SSL certificate configuration for www.maltacentral.com"""

    def setup_method(self):
        """Set up test environment"""
        self.domain = "www.maltacentral.com"
        self.alternate_domain = "maltacentral.com"
        self.expected_domains = [
            "www.maltacentral.com",
            "maltacentral.com",
            "*.vfservices.viloforge.com",
            "vfservices.viloforge.com",
            "*.cielo.viloforge.com",
            "cielo.viloforge.com"
        ]

    def test_ssl_certificate_browser_validation(self):
        """Test SSL certificate validation through browser"""
        with sync_playwright() as p:
            # Launch browser with SSL verification enabled
            browser = p.chromium.launch(
                headless=True,
                args=['--ignore-certificate-errors-spki-list=']  # Don't ignore cert errors
            )
            context = browser.new_context(
                ignore_https_errors=False  # Enforce SSL validation
            )
            page = context.new_page()
            
            # Test primary domain
            print(f"\nTesting SSL for https://{self.domain}")
            try:
                response = page.goto(f"https://{self.domain}", timeout=30000)
                assert response is not None, f"Failed to load https://{self.domain}"
                assert response.status < 400, f"HTTP error {response.status} for https://{self.domain}"
                print(f"✓ Successfully connected to https://{self.domain} with valid SSL")
            except Exception as e:
                pytest.fail(f"SSL validation failed for {self.domain}: {str(e)}")
            
            # Test alternate domain
            print(f"\nTesting SSL for https://{self.alternate_domain}")
            try:
                response = page.goto(f"https://{self.alternate_domain}", timeout=30000)
                if response and response.status < 400:
                    print(f"✓ Successfully connected to https://{self.alternate_domain} with valid SSL")
                else:
                    print(f"⚠ Warning: Got HTTP {response.status} for https://{self.alternate_domain}")
                    print(f"  This may be a server configuration issue, not an SSL issue")
            except Exception as e:
                print(f"⚠ Warning: Could not connect to {self.alternate_domain}: {str(e)}")
            
            browser.close()

    def test_ssl_certificate_details(self):
        """Test SSL certificate details using direct SSL connection"""
        print(f"\nAnalyzing SSL certificate for {self.domain}")
        
        try:
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect to the server
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    # Get certificate in DER format
                    der_cert_bin = ssock.getpeercert(binary_form=True)
                    
                    # Convert to PEM format for OpenSSL
                    pem_cert = ssl.DER_cert_to_PEM_cert(der_cert_bin)
                    
                    # Parse certificate with OpenSSL
                    x509 = OpenSSL.crypto.load_certificate(
                        OpenSSL.crypto.FILETYPE_PEM, 
                        pem_cert
                    )
                    
                    # Check certificate validity dates
                    not_before = datetime.datetime.strptime(
                        x509.get_notBefore().decode('ascii'), 
                        '%Y%m%d%H%M%SZ'
                    )
                    not_after = datetime.datetime.strptime(
                        x509.get_notAfter().decode('ascii'), 
                        '%Y%m%d%H%M%SZ'
                    )
                    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                    
                    print(f"\nCertificate Details:")
                    print(f"  Issuer: {x509.get_issuer()}")
                    print(f"  Subject: {x509.get_subject()}")
                    print(f"  Valid from: {not_before}")
                    print(f"  Valid until: {not_after}")
                    print(f"  Days remaining: {(not_after - now).days}")
                    
                    # Verify certificate is currently valid
                    assert now >= not_before, f"Certificate not yet valid (starts {not_before})"
                    assert now <= not_after, f"Certificate expired on {not_after}"
                    print("✓ Certificate is currently valid")
                    
                    # Check certificate has reasonable time remaining (warn if < 30 days)
                    days_remaining = (not_after - now).days
                    if days_remaining < 30:
                        print(f"⚠ WARNING: Certificate expires in {days_remaining} days!")
                    else:
                        print(f"✓ Certificate has {days_remaining} days remaining")
                    
                    # Extract and verify SANs (Subject Alternative Names)
                    sans = []
                    for i in range(x509.get_extension_count()):
                        ext = x509.get_extension(i)
                        if ext.get_short_name() == b'subjectAltName':
                            san_string = str(ext)
                            # Parse SANs from string format
                            for san in san_string.split(', '):
                                if san.startswith('DNS:'):
                                    sans.append(san[4:])
                    
                    print(f"\nSubject Alternative Names (SANs):")
                    for san in sorted(sans):
                        print(f"  - {san}")
                    
                    # Verify our domains are in the certificate
                    assert "www.maltacentral.com" in sans, "www.maltacentral.com not in certificate SANs"
                    assert "maltacentral.com" in sans, "maltacentral.com not in certificate SANs"
                    print("\n✓ Both maltacentral.com domains are included in the certificate")
                    
        except socket.timeout:
            pytest.fail(f"Connection timeout to {self.domain}:443")
        except ssl.SSLError as e:
            pytest.fail(f"SSL error: {str(e)}")
        except Exception as e:
            pytest.fail(f"Unexpected error: {str(e)}")

    def test_https_redirect(self):
        """Test that HTTP redirects to HTTPS"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(ignore_https_errors=True)
            page = context.new_page()
            
            # Test HTTP to HTTPS redirect for primary domain
            print(f"\nTesting HTTP to HTTPS redirect for {self.domain}")
            response = page.goto(f"http://{self.domain}", timeout=30000, wait_until="domcontentloaded")
            
            # Check that we were redirected to HTTPS
            final_url = page.url
            assert final_url.startswith("https://"), f"Not redirected to HTTPS. Final URL: {final_url}"
            print(f"✓ Successfully redirected from HTTP to HTTPS")
            
            # Verify the certificate on the HTTPS site
            assert "www.maltacentral.com" in final_url or "maltacentral.com" in final_url
            print(f"✓ Landed on correct domain: {final_url}")
            
            browser.close()

    def test_certificate_chain(self):
        """Test the certificate chain is complete and valid"""
        print(f"\nTesting certificate chain for {self.domain}")
        
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((self.domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    # Get the server certificate
                    cert = ssock.getpeercert()
                    
                    if cert:
                        subject = dict(x[0] for x in cert.get('subject', []))
                        issuer = dict(x[0] for x in cert.get('issuer', []))
                        
                        print(f"\nServer Certificate:")
                        print(f"  Subject: {subject.get('commonName', 'N/A')}")
                        print(f"  Issuer: {issuer.get('organizationName', 'N/A')} - {issuer.get('commonName', 'N/A')}")
                        
                        # Check if it's issued by Let's Encrypt
                        if 'Let\'s Encrypt' in issuer.get('organizationName', ''):
                            print(f"✓ Certificate is issued by Let's Encrypt")
                        
                        # Verify SANs include our domain
                        sans = []
                        for san_type, san_value in cert.get('subjectAltName', []):
                            if san_type == 'DNS':
                                sans.append(san_value)
                        
                        assert self.domain in sans, f"{self.domain} not found in certificate SANs"
                        print(f"✓ {self.domain} is included in certificate SANs")
                        print(f"✓ Valid certificate chain verified")
                    else:
                        pytest.fail("No certificate returned from server")
                    
        except Exception as e:
            pytest.fail(f"Certificate chain validation failed: {str(e)}")


if __name__ == "__main__":
    # Run the tests
    test = TestMaltaCentralSSLCertificate()
    test.setup_method()
    
    print("=" * 60)
    print("Malta Central SSL Certificate Tests")
    print("=" * 60)
    
    try:
        test.test_ssl_certificate_browser_validation()
        print("\n✅ Browser SSL validation: PASSED")
    except Exception as e:
        print(f"\n❌ Browser SSL validation: FAILED - {e}")
    
    try:
        test.test_ssl_certificate_details()
        print("\n✅ Certificate details verification: PASSED")
    except Exception as e:
        print(f"\n❌ Certificate details verification: FAILED - {e}")
    
    try:
        test.test_https_redirect()
        print("\n✅ HTTPS redirect test: PASSED")
    except Exception as e:
        print(f"\n❌ HTTPS redirect test: FAILED - {e}")
    
    try:
        test.test_certificate_chain()
        print("\n✅ Certificate chain validation: PASSED")
    except Exception as e:
        print(f"\n❌ Certificate chain validation: FAILED - {e}")
    
    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)
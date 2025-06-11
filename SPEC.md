Implementing JWT-Based SSO in Viloforge
Viloforge uses a centralized authentication system across multiple subdomains. In this guide, we’ll implement a step-by-step solution where a central Identity Provider (IdP) issues JWT tokens after login, and other services (website and APIs) consume and verify these tokens for Single Sign-On (SSO). We will also address cross-domain cookies, CSRF protection, and containerization details.
Overview of the Architecture
Viloforge’s platform is divided into multiple domains (or subdomains):
Identity Provider (IdP) – hosts the login page and authentication logic
(Production: login.viloforge.com; Development: login.<project_name>.viloforge.com)*
Frontend Website – the main user-facing site that requires SSO login
(Production: website.viloforge.com; Development: website.<project_name>.viloforge.com)*
Backend API Services – e.g., Billing and Inventory microservices, providing JSON APIs
(Production: billing-api.viloforge.com, inventory-api.viloforge.com;
Development: billing-api.<project_name>.viloforge.com, inventory-api.<project_name>.viloforge.com)*
All these services will trust JWT tokens issued by the IdP. The JWT will be stored in a secure, HttpOnly cookie scoped to the parent domain (.viloforge.com) so that it’s automatically shared with subdomains
blog.stackademic.com
. This allows a user to authenticate once and access all services across the Viloforge suite without re-login. Key points in the workflow:
Unauthenticated users on the frontend are redirected to the IdP login page. The IdP issues a JWT upon successful login.
The JWT is set in a cross-subdomain cookie (domain .viloforge.com) with Secure, HttpOnly, and SameSite=Lax attributes for security.
The browser is redirected back to the original site; the cookie is sent along (thanks to the shared parent domain and SameSite policy)
stackoverflow.com
.
The frontend JavaScript can retrieve the JWT from the cookie (if not HttpOnly) or rely on the browser to send it, and include it in Authorization: Bearer <token> headers for AJAX calls to the backend APIs.
Each service (website, billing API, inventory API) verifies incoming JWTs (via a shared secret or key) using custom JWT Authentication middleware, and populates request.user for Django as if the user was logged in
blog.stackademic.com
blog.stackademic.com
.
Standard Django features like @login_required decorators can be used in these services, since the middleware will ensure request.user.is_authenticated is True for valid tokens.
We will maintain strong security practices: always use HTTPS, secure cookies, short token lifetimes with optional refresh tokens, and proper CORS/CSRF protections
blog.stackademic.com
.
Below, we expand each part of the implementation in detail.
1. Project Structure Setup (Monorepo)
First, set up a monorepo directory structure as described. Each Django project (IdP, website, billing-api, inventory-api) will be a standalone Django site with its own settings, running in its own container. A common module will hold shared code (like JWT utils and middleware). Directory layout:
php
Copy
viloforge-monorepo/
├── identity-provider/
│   ├── manage.py
│   ├── main/                 # Django project (settings, wsgi)
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── identity_app/         # Django app for IdP functionality (views, models)
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       └── templates/
├── website/
│   ├── manage.py
│   ├── main/                 # Django project for website
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── webapp/               # Django app for website features
│       ├── views.py
│       ├── models.py
│       ├── urls.py
│       ├── templates/        # e.g., using Bootstrap for admin UI
│       └── static/
├── billing-api/
│   ├── manage.py
│   ├── main/                 # Django project for billing service
│   ├── billing/              # Django app for billing API
│   │   ├── views.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── ...
├── inventory-api/
│   ├── manage.py
│   ├── main/                 # Django project for inventory service
│   ├── inventory/            # Django app for inventory API
│   │   ├── views.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   └── urls.py
│   └── ...
└── common/
    └── jwt_auth/
        ├── middleware.py     # JWT authentication middleware shared by services
        ├── utils.py          # Helper functions for JWT (encode/decode)
        └── exceptions.py
Steps to create the projects:
Create each Django project using django-admin startproject. For example, in the identity-provider directory, run:
bash
Copy
django-admin startproject main .
This creates a main/ folder with Django settings for the IdP. Repeat for website, billing-api, and inventory-api directories.
In each project, create a Django app for the core functionality:
For IdP, create an app (e.g., identity_app):
bash
Copy
python manage.py startapp identity_app
This will hold views for login, JWT issuance, etc.
For the website, create webapp similarly.
For each API service, create apps billing and inventory respectively (these may use Django REST Framework or simple JSON views).
Add the new app to INSTALLED_APPS in the respective main/settings.py for each project. Also include common.jwt_auth in INSTALLED_APPS or ensure the common directory is on the Python path so its middleware can be imported.
In the common/jwt_auth package, we will implement shared JWT logic. Make sure each Django project knows about the common directory (you can do this by adding the path in PYTHONPATH or by using a monorepo approach where the common folder is treated as a local package).
Set up a shared secret key for JWT signing. In a real setup, use a strong random secret (or a key pair if using RSA). You can define an environment variable like JWT_SECRET and ensure all services use the same value to encode/decode tokens. For now, store it in Django settings (e.g., settings.JWT_SECRET = 'your-256-bit-secret') for simplicity during development.
User model considerations: The IdP will host the user database (likely using Django’s default User). Other services won’t have users logging in directly, but they need to recognize the JWT’s username/email. For simplicity, you can use Django’s built-in User model on the IdP and either:
Share the user database with other services (not typical in microservices, but possible if they connect to the same DB for auth), or
Create a user object on-the-fly in the JWT auth middleware when a valid token is received (not persisting it, just for request scope). We’ll follow the second approach to avoid cross-service DB calls: the JWT will carry user info and each service will treat that as authoritative.
With the projects created, proceed to implement the central authentication logic.
2. Identity Provider – Login and JWT Generation
The Identity Provider (login.viloforge.com) is responsible for authenticating users and issuing JWTs for SSO. We’ll set up a simple Django view to handle login submissions, create a token, and redirect users back. Key steps:
User Authentication: Use Django’s standard authentication (username & password check via django.contrib.auth.authenticate).
JWT Creation: On successful login, generate a JWT containing necessary claims (like username, email, issued-at, expiration).
Cookie Setup: Send the JWT to the browser in a cookie scoped to .viloforge.com so that all subdomains can receive it
blog.stackademic.com
docs.djangoproject.com
. The cookie must be Secure (HTTPS only) and HttpOnly (not accessible to JavaScript) to guard against XSS
docs.djangoproject.com
. We use SameSite=Lax so that the cookie is included on top-level navigations between subdomains (our redirect flow) but not for third-party cross-site contexts, adding CSRF protection in general
docs.djangoproject.com
.
Redirect Back: After setting the cookie, redirect the user to the original application (website.viloforge.com) using the redirect_uri provided.
Let’s write the login view (identity_app/views.py):
python
Copy
# identity_app/views.py (in Identity Provider service)
import datetime
import jwt  # PyJWT library
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect, HttpResponseForbidden

def login_user(request):
    # If GET, render login form (template not shown for brevity)
    if request.method == 'GET':
        # (You would typically render a template with a username/password form)
        return render(request, 'login_form.html')
    
    # If POST, process the login form
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user is None:
        # Invalid credentials
        return HttpResponseForbidden("Invalid login")  # or redirect to login with error
    
    # User is authenticated, create JWT payload
    payload = {
        'username': user.username,
        'email': user.email,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # token valid 1 hour
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256')
    
    # Prepare redirect response to return to original site
    redirect_url = request.GET.get('redirect_uri', settings.DEFAULT_REDIRECT_URL)
    response = HttpResponseRedirect(redirect_url)
    
    # Set JWT as cookie for .viloforge.com domain
    response.set_cookie(
        'jwt', token,
        domain=settings.SSO_COOKIE_DOMAIN,   # e.g., '.viloforge.com' in production
        secure=True, httponly=True, samesite='Lax',  # secure cookie settings:contentReference[oaicite:9]{index=9}:contentReference[oaicite:10]{index=10}
        max_age=3600  # 1 hour for example, must align with 'exp'
    )
    return response
A few notes on the above code:
We use jwt.encode from the PyJWT library to generate the token. settings.JWT_SECRET is a shared secret across services. Algorithm HS256 (HMAC-SHA256) is used here for simplicity (symmetric key), but you could use RS256 with a private/public key pair for higher security.
redirect_uri is expected as a query parameter when the user was sent to login. For example, the website might redirect to:
https://login.viloforge.com?redirect_uri=https://website.viloforge.com/path_after_login. We default to some safe page if not provided.
We set response.set_cookie('jwt', ...) with the domain .viloforge.com. Django’s set_cookie allows cross-domain cookies if the domain is a suffix of the current host
docs.djangoproject.com
. Since the IdP is login.viloforge.com, setting domain .viloforge.com is allowed and will make the cookie accessible on all subdomains under viloforge.com. In development, we will use SSO_COOKIE_DOMAIN = ".<project_name>.viloforge.com" (for example, .vlservices.viloforge.com) so that dev subdomains share the cookie.
We marked the cookie HttpOnly and Secure. HttpOnly ensures JavaScript on the client side cannot directly read the cookie’s value, mitigating XSS exfiltration
blog.stackademic.com
. Secure ensures the cookie only travels over HTTPS. We use SameSite=Lax, which means the cookie will automatically be sent on navigations from one subdomain to another (like our redirect), but will not be sent on cross-site subrequests like iframes or AJAX from an external site
stackoverflow.com
. This behavior helps reduce CSRF risk by not automatically sending the JWT cookie in third-party contexts. (All Viloforge services share the same eTLD+1 “viloforge.com”, so they are considered same-site with each other
stackoverflow.com
. The Lax setting primarily guards against other sites.)
The cookie’s max_age is set to match the token expiration (here 1 hour). In practice, you might use shorter access token lifespan (15 minutes, etc.) and use a refresh token mechanism to keep users logged in without re-entering credentials
blog.stackademic.com
blog.stackademic.com
. For this tutorial, we focus on access tokens, but be aware of implementing a refresh token in a secure, HttpOnly cookie as well for production if needed.
Configuring URLs: In identity_app/urls.py, map a route to this view (e.g., path '' or /login to login_user). Include these URLs in the IdP’s main urls.py. Template: Implement a simple login_form.html with fields for username and password, posting to the same URL (the IdP can handle the form display and submission on one endpoint for simplicity). Ensure that if a redirect_uri query param exists, it’s preserved (e.g., include it in a hidden form field or the form action). Optional: Implement a logout view that deletes the JWT cookie (set it with an expired time) on .viloforge.com domain. This would log the user out of all services (since the cookie is shared). Keep in mind JWT is stateless; “logout” on the client just means removing the token. If you need to forcibly invalidate a token server-side, you’d need a token blacklist or short expiry approach
ianlondon.github.io
ianlondon.github.io
. Now the IdP is ready to authenticate and issue tokens. Next, we handle how the other services use these tokens.
3. JWT Authentication Middleware (Shared)
To avoid duplicating logic in each Django service, we create a middleware in common/jwt_auth/middleware.py that will:
Read the JWT from incoming requests (either from the Authorization header or from the cookie).
Verify and decode the JWT. If invalid or expired, treat the user as unauthenticated.
If valid, populate request.user with a user object that Django views and decorators can recognize as an authenticated user.
By doing this at the middleware level, it integrates with Django’s authentication system seamlessly. We can continue to use @login_required and request.user in views without special handling in each view. Implementing the middleware:
python
Copy
# common/jwt_auth/middleware.py
import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin

class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Authenticate the user via JWT on each request (if token is provided).
        """
        token = None
        # 1. Check Authorization header for a Bearer token
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header:
            # Expected format: "Bearer <token>"
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
        # 2. If not in header, check cookie (user might rely on cookie auth)
        if token is None:
            token = request.COOKIES.get('jwt')
        
        if token:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                # Token has expired - treat as anonymous (could also force re-login)
                request.user = AnonymousUser()
                return
            except jwt.InvalidTokenError:
                # Token invalid - also anonymous
                request.user = AnonymousUser()
                return
            
            # Token is valid here. Create a user-like object for this request:
            username = payload.get('username')
            email = payload.get('email')
            # Option 1: If using shared DB and user exists locally
            # try:
            #     user = User.objects.get(username=username)
            # except User.DoesNotExist:
            #     user = None
            # Option 2: Create a dummy user object
            from django.contrib.auth.models import User
            user = User(username=username, email=email)
            user.is_active = True
            # Mark the user as authenticated
            user.backend = 'django.contrib.auth.backends.ModelBackend'  # nominal backend
            # (Alternatively, define a custom User class or SimpleLazyObject if desired)
            request.user = user
        else:
            # No token provided, ensure this is treated as an anonymous user
            request.user = AnonymousUser()
Add this middleware to each service’s settings. In main/settings.py of website, billing-api, and inventory-api, include:
python
Copy
MIDDLEWARE = [
    # ... (Django’s default middlewares like SecurityMiddleware, SessionMiddleware, etc.)
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # default auth middleware
    'common.jwt_auth.middleware.JWTAuthenticationMiddleware',   # our JWT middleware
    # ... (possibly other middlewares like CSRF, etc.)
]
We place our middleware after Django’s AuthenticationMiddleware. By default, AuthenticationMiddleware populates request.user using session data. However, since we are not using session auth for APIs, one might consider putting our JWT middleware before it. But because AuthenticationMiddleware will find no session and leave an AnonymousUser (and doesn’t override an existing request.user if set), the order can be either. To be safe, placing JWT middleware after ensures that if a session login exists (e.g., admin site or other fallback), it wouldn’t get overwritten by JWT logic. Now, how this works: On each request, if a JWT is present (header or cookie), we decode it. If valid, we attach a User object to request.user. Here we simply instantiate a Django User without hitting the database (note: we did not call save()). This user instance will have is_authenticated = True by virtue of not being an AnonymousUser. We also set a backend attribute to satisfy some authentication system internals (some parts of Django might look for user.backend to identify how the user was authenticated, especially if you call login(), but here we aren’t using Django’s login, so this is mostly informational). Important: The above approach trusts the JWT completely. In a real setup, if you want to enforce user permissions or roles, you might include those in the token or look up the user in the database to fetch permissions. For basic SSO, the token itself is proof of authentication. We ensure the token is signed with our secret, so only our IdP could have issued it. By using this middleware, any Django view that checks request.user.is_authenticated will see a valid user if a correct token is present. This means:
In the website service, we can use @login_required on views to force authentication.
In the API services, we can similarly protect endpoints by checking request.user or using DRF’s IsAuthenticated if integrating with Django REST Framework.
Edge cases: If the token is expired or invalid, we leave request.user as AnonymousUser. The view or a decorator can then redirect to login or return 401 as appropriate. For example, we’ll configure the website to redirect to the IdP if no valid login.
4. Frontend Website – Enforcing Login and Using the JWT
The frontend website (website.viloforge.com) is a Django app that likely serves HTML pages (and maybe provides some AJAX endpoints to fetch data from the APIs). We want to ensure that if a user isn’t authenticated (no valid JWT), they get sent to the IdP login. Enforcing SSO login on the website: There are a couple of ways to do this:
Use Django’s authentication system directly: set LOGIN_URL in settings to the IdP URL. For example:
python
Copy
LOGIN_URL = "https://login.viloforge.com"
But we also need to pass ?redirect_uri= so the IdP knows where to return. Django’s login_required decorator will append next= param to LOGIN_URL automatically if it’s on the same site. However, since this is an external domain, that might not carry over smoothly. Instead, we can manage redirects manually in our view.
Manually check in each protected view if request.user.is_authenticated is False, and do a redirect.
A simple approach: define a custom mixin or decorator for the website that handles redirect. But for clarity, we’ll just illustrate it in a view. For example, assume the homepage of the website should be accessible only to logged-in users. In webapp/views.py:
python
Copy
from django.shortcuts import redirect, render

def home(request):
    # If user not authenticated, send to IdP login
    if not request.user or not request.user.is_authenticated:
        # Construct IdP login URL with redirect back to this page
        target = request.build_absolute_uri()  # current page URL
        login_url = f"https://login.viloforge.com?redirect_uri={target}"
        return redirect(login_url)
    # If authenticated, render the home page
    return render(request, "home.html", {"user": request.user})
We can apply a similar check to any view that requires login, or use Django’s @login_required decorator on views if we set LOGIN_URL appropriately. For instance:
python
Copy
from django.contrib.auth.decorators import login_required

@login_required(login_url="https://login.viloforge.com")
def dashboard(request):
    # Only reached if JWT was valid and user is authenticated
    return render(request, "dashboard.html", {"user": request.user})
However, using login_required might try to append a next parameter. Our manual approach using redirect_uri covers it more explicitly. Both can work; just ensure the IdP view reads redirect_uri and uses that as done in the earlier step. Using the JWT in JavaScript (Frontend side): Once the user is logged in, the JWT cookie (named 'jwt') is available for use. If it’s HttpOnly (as we set), JavaScript cannot directly read it via document.cookie. This is good for security
ianlondon.github.io
, but it means we need a strategy to call APIs:
Option A: Rely on cookies in AJAX – If the cookie is set for .viloforge.com, and if our API calls are going to subdomains under viloforge.com, the browser can send the cookie automatically provided we configure CORS to allow it. This requires using fetch or XHR with credentials: 'include' and setting Access-Control-Allow-Credentials on the server
blog.stackademic.com
blog.stackademic.com
. We also need SameSite=None for the cookie in this case, because an XHR is considered a cross-site request (even if the domain is a sibling subdomain). In our case, SameSite=Lax would not send the cookie for an AJAX from website.viloforge.com to billing-api.viloforge.com because that’s a cross-site (not top-level navigation) context
stackoverflow.com
. So, to use cookies in XHR, we’d have to set SameSite=None on the JWT cookie (and Secure, since None requires Secure). This is a possible approach if we want truly HttpOnly tokens used automatically by the browser.
Option B: Expose the token to JS and send in headers – This is what the initial spec hints at by retrieving the token and including in Authorization: Bearer ... headers on fetch calls. To do this, we cannot have the cookie as HttpOnly. We could set a second cookie (same value) without HttpOnly or use another mechanism to pass the token to the frontend script (some apps do a one-time injection of the JWT into a global JS variable on page load, then immediately clear the cookie). Security trade-off: If the JWT is accessible via JS, an XSS attack on the website could steal it and impersonate the user elsewhere
ianlondon.github.io
. In a trusted internal app, this might be acceptable, but ideally we keep HttpOnly. For our educational implementation, we’ll demonstrate the header approach for clarity, but note the security implications.
Using Authorization header (preferred for APIs): We’ll have the website JavaScript read the token and send it. Since we set HttpOnly=True, our current cookie can’t be read by JS. To work around this in development or simplified environment, you might set HttpOnly=False. Alternatively, the IdP after login could redirect with the token in a URL fragment (e.g., website.viloforge.com/#token=<JWT>), which the website’s script can capture and then store (e.g., in localStorage or a non-HttpOnly cookie). For brevity, assume we allowed reading the cookie. For example, on home.html (the website’s homepage template), include a script to make an API call:
html
Copy
<script>
  // Example: Fetch user’s invoices from the billing API
  const token = getCookie('jwt');  // assume a JS function to get cookie value
  if(token) {
      fetch('https://billing-api.viloforge.com/invoices', {
          method: 'GET',
          headers: {
              'Authorization': 'Bearer ' + token
          }
          // If we were using cookies via credentials: include, we would add:
          // credentials: 'include'
      })
      .then(response => {
          if (!response.ok) { throw new Error(response.statusText); }
          return response.json();
      })
      .then(data => {
          console.log("Invoices data:", data);
          // render the invoices on the page, etc.
      })
      .catch(err => {
          console.error("API error or not authorized", err);
      });
  }
</script>
This JavaScript snippet demonstrates how the JWT can be attached in the Authorization header for a cross-domain API call. On the server side, our JWTAuthenticationMiddleware in the billing service will see the Authorization header and authenticate the user. Cross-Origin Resource Sharing (CORS): Because website.viloforge.com is a different origin from billing-api.viloforge.com, the browser will only allow this AJAX request if the billing API sets the appropriate CORS headers. We must configure CORS on each API service to allow the website origin. We’ll cover that in the next section. CSRF considerations on the website: The website is a normal Django app, likely using Django’s CSRF protection for forms. The presence of the JWT cookie doesn’t directly affect Django’s CSRF tokens, because Django’s CSRF middleware looks at the csrftoken cookie and X-CSRFToken header for POST forms. We should not disable CSRF protection on the website, especially if it has forms that cause state changes. Since we are not using the JWT cookie as a session cookie, a cross-site attacker cannot automatically use the JWT to perform actions via form posts thanks to SameSite=Lax and missing credentials. But if you have forms (e.g., a profile update form on the website), keep using the {% csrf_token %} in templates and Django will manage a CSRF cookie/token pair. That CSRF cookie is separate and has no HttpOnly so that JS can read it if needed (for AJAX form submissions), and is limited to the website.viloforge.com domain. In summary: The website uses the JWT primarily to call other APIs or to identify the user. For its own forms, it can rely on standard session or CSRF tokens as needed (even if the session is not used for auth, you can still use Django’s session for flash messages or other state if needed without impacting SSO). Now that the website can get the token and call APIs, let’s implement the APIs to respond accordingly.
5. Protecting API Endpoints (Billing & Inventory Services)
For each backend service (e.g., billing-api and inventory-api), we will:
Install the JWTAuthenticationMiddleware (already covered in Step 3 by adding to settings).
Possibly use Django REST Framework (DRF) for convenience in building JSON APIs, or just use Django’s HttpResponse/JsonResponse.
Ensure CORS is configured to allow the frontend domain to access.
Example: Billing API view (protected):
python
Copy
# billing/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET
# No need for @login_required if we manually check request.user

@require_GET
def list_invoices(request):
    user = request.user
    if not user or not user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    # In a real app, filter invoices by user info (e.g., user ID or username)
    # Here we’ll just return a dummy response
    data = [
        {"invoice_id": 1, "amount": 100, "user": user.username},
        {"invoice_id": 2, "amount": 250, "user": user.username}
    ]
    return JsonResponse(data, safe=False)
We can map this view in billing/urls.py to a path like /invoices. Because we used request.user.is_authenticated, this will be True if the JWT was valid (middleware set the user) or False if no token. We return 401 Unauthorized for the latter, which the frontend can detect and perhaps redirect to login. If using Django REST Framework (DRF), we could integrate JWT by writing a custom authentication class or simply rely on the middleware and use DRF’s IsAuthenticated permission. For example, using DRF:
python
Copy
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_invoices(request):
    # DRF will have already checked authentication via our middleware populating request.user
    # (Might also need to set DEFAULT_AUTHENTICATION_CLASSES to an appropriate class that looks at header or session.
    # We can create a DRF Authentication class that simply returns (request.user, None) if request.user is authenticated by middleware.)
    invoices = [...]  # fetch from database
    serializer = InvoiceSerializer(invoices, many=True)
    return Response(serializer.data)
This assumes DRF sees a non-Anonymous user. If you want to be strict, you could create a small DRF Authentication class that reads the Authorization header and verifies JWT (similar to our middleware). But since we already did it in middleware, it may be redundant. The key is to ensure DRF doesn’t override or ignore our request.user. By default, DRF’s TokenAuthentication or SessionAuthentication might run. You can disable DRF’s default auth and rely on the middleware by setting in settings:
python
Copy
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': []
}
and just use our middleware + normal Django IsAuthenticated. Another approach is to integrate as a custom auth backend. For brevity, continuing with the simpler function-based view is fine. Configure CORS on APIs: To allow the website’s domain to call the API, enable CORS. The simplest way is to use the django-cors-headers library. Install it and add to INSTALLED_APPS. Then in each API service’s settings.py:
python
Copy
INSTALLED_APPS = [
    ...,
    'corsheaders',
    ...
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # put it near top, before CommonMiddleware
    ...,
    'common.jwt_auth.middleware.JWTAuthenticationMiddleware',
    ...
]
CORS_ALLOW_CREDENTIALS = True  # allow cookies/Authorization headers to be sent
CORS_ALLOWED_ORIGINS = [
    "https://website.viloforge.com",
    # and the dev domain:
    "https://website.<project_name>.viloforge.com"
]
# If you want to allow all subdomains of viloforge.com you could use regex:
# CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://website\..*\.viloforge\.com$"]
CORS_ALLOW_HEADERS = list(default_headers) + ["Authorization"]
This configuration will produce the appropriate Access-Control-Allow-Origin for the website domain and allow credentials
blog.stackademic.com
. With CORS_ALLOW_CREDENTIALS=True, the header Access-Control-Allow-Credentials: true will be sent, which is required if the request includes credentials (like cookies or auth headers)
blog.stackademic.com
. We also explicitly allow the Authorization header to be sent from the browser
blog.stackademic.com
. Now, the billing API (and similarly inventory API) will accept requests from the website. The flow will be:
Browser JS (on website) makes a GET to billing-api.viloforge.com/invoices with the JWT in the header.
The browser sends a preflight OPTIONS request (because of cross-origin and custom header Authorization). Our CORS middleware will respond allowing it.
Then the GET is sent, with Authorization: Bearer <token>.
JWT middleware on billing service verifies token, sets user.
View returns JSON data, Django sends response with CORS headers (Access-Control-Allow-Origin: https://website.viloforge.com, etc.).
Browser receives data, JS displays the invoices.
At this point, we have a working SSO: one login gives access to website and its API calls.
6. Security Checks: CSRF and JWT Together
It’s crucial to ensure CSRF protection is not accidentally broken by our JWT approach:
API calls (billing, inventory): We use JWT in Authorization header, which is a bearer token. Such requests are not automatically accompanied by cookies (unless we explicitly allowed it). Since we configured the system to use Authorization headers, an attacker site cannot trigger a user’s browser to send this header (because of CORS, an attacker JavaScript from another origin cannot read or send requests to our API without our API allowing that origin, which it won’t). Thus, API endpoints using JWT headers are inherently protected from CSRF. (CSRF mainly targets cookie-based auth because browsers send cookies automatically to the target domain.) As an extra layer, we allowed SameSite=Lax on the JWT cookie, which means if an attacker tries to use the cookie by causing a form submission or image load to an API endpoint, those are not top-level navigations and the cookie would not be sent
stackoverflow.com
. So even if an API endpoint mistakenly relied on the cookie alone, the Lax policy helps mitigate that scenario.
Web forms on the website: The website might have normal forms (for example, a support contact form or profile update). Because the website uses Django templates and presumably has CSRF middleware enabled by default, those forms are protected by CSRF tokens. Our implementation should not disable Django’s CSRF middleware on the website. The JWT cookie does not replace CSRF tokens. In fact, Django’s CSRF middleware will by default ignore requests that come with an Authorization header, considering them AJAX, unless configured otherwise. This is because DRF, for instance, exempted such requests by default in older versions
stackoverflow.com
. However, since our state-changing operations on the website likely go through form posts with session or (in the future) might call APIs, we should still include CSRF tokens in forms.
Login CSRF: Our login form at the IdP should include a CSRF token if we use Django’s form (because it’s a POST to our own domain). This is easy by adding {% csrf_token %} in the form and ensuring django.middleware.csrf.CsrfViewMiddleware is active for the IdP. Because the login page is a top-level page on the IdP domain, SameSite does not interfere with the CSRF cookie there.
In summary, keep CSRF middleware enabled for any site that has forms or session cookie usage (like the website and IdP). The cross-domain JWT cookie with SameSite=Lax provides additional CSRF safety by not being sent in third-party contexts, but it’s not a substitute for Django’s built-in CSRF protections
docs.djangoproject.com
.
7. Docker and Development Environment
Each Django project will be containerized separately, and we’ll use docker-compose to run them together. We will also handle HTTPS in development to simulate the production-like environment with subdomains. Dockerfile for each service: Create a Dockerfile in each project folder (identity-provider, website, billing-api, inventory-api). They will look similar, for example:
dockerfile
Copy
# Base image
FROM python:3.11-slim

WORKDIR /app
# Copy the code
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose the port (if we run directly, though we might use gunicorn or runserver_plus)
EXPOSE 8000

# Command to run the development server (use runserver_plus for HTTPS support)
CMD ["python", "manage.py", "runserver_plus", "0.0.0.0:8000", "--cert-file", "/app/certs/dev.cert", "--key-file", "/app/certs/dev.key"]
We will include the use of runserver_plus (from django-extensions) to easily serve HTTPS in dev. Note the CMD above references certificate files; we will generate those next. docker-compose.yml (sketch): In the root viloforge-monorepo directory, compose file might include:
yaml
Copy
version: '3.8'
services:
  identity:
    build: ./identity-provider
    container_name: viloforge_identity
    hostname: login.vlservices.viloforge.com
    # ... map volumes if needed, etc.
    ports:
      - "8443:8000"
  website:
    build: ./website
    container_name: viloforge_website
    hostname: website.vlservices.viloforge.com
    ports:
      - "8444:8000"
  billing:
    build: ./billing-api
    container_name: viloforge_billing
    hostname: billing-api.vlservices.viloforge.com
    ports:
      - "8445:8000"
  inventory:
    build: ./inventory-api
    container_name: viloforge_inventory
    hostname: inventory-api.vlservices.viloforge.com
    ports:
      - "8446:8000"
Networking: Each container is on the same Docker network by default, and each is being exposed on a different host port (8443, 8444, ...). We set hostname in container to simulate DNS names, but to actually reach them by those names from your host browser, you have to ensure those names resolve to your localhost (127.0.0.1). In development, you can edit your hosts file to add entries:
pgsql
Copy
127.0.0.1 login.vlservices.viloforge.com 
127.0.0.1 website.vlservices.viloforge.com 
127.0.0.1 billing-api.vlservices.viloforge.com 
127.0.0.1 inventory-api.vlservices.viloforge.com
Then, you can open https://website.vlservices.viloforge.com:8444 in your browser (the port is needed because we mapped 8444->container 8000). The cookie domain should be set as .vlservices.viloforge.com in dev, which covers all these subdomains. The browser will consider them all under the registrable domain vlservices.viloforge.com (which is our project’s dev domain). HTTPS Certificates in Dev: We want valid HTTPS on these custom domains. As described, we’ll obtain certificates from Let’s Encrypt using a DNS-01 challenge (since these dev domains might not be accessible via HTTP). Using Cloudflare DNS API to prove domain ownership is the plan:
Ensure the <project_name>.viloforge.com subdomains are configured in Cloudflare DNS (could be wildcard CNAME to your dev machine, or specific A records to your IP).
Use a tool like Certbot with the Cloudflare plugin to request a wildcard certificate. For example, a wildcard for *.vlservices.viloforge.com. The DNS-01 challenge will create a TXT record via Cloudflare API
gist.github.com
.
Automate this via a Makefile target and a script:
Create a file cloudflare.ini with your Cloudflare API token (with permissions to edit DNS)
gist.github.com
.
Run Certbot in a lightweight container or directly. For example:
bash
Copy
certbot certonly --dns-cloudflare --dns-cloudflare-credentials cloudflare.ini \
  -d "*.vlservices.viloforge.com" -d "vlservices.viloforge.com"
Include the base domain if needed (for cookie domain, though we won’t serve it, but just in case). Certbot will output the cert files (fullchain.pem and privkey.pem).
The script can place these in a shared volume or copy into each container’s certs/ directory (as referenced in the Dockerfile CMD).
Alternatively, use a single reverse-proxy container (like Nginx or Traefik) to handle TLS termination using that certificate and route to the services. In that case, each Django app can run on HTTP internally. This is a more production-like setup. However, since the question hints at using runserver_plus with certs, we presented that route.
For simplicity, you might also use self-signed certificates in dev (django-extensions can generate one). But using a real cert from Let’s Encrypt avoids having to configure your browser to trust a self-signed authority. Makefile example:
makefile
Copy
dev-cert:
    # Obtain dev wildcard cert using Cloudflare DNS challenge
    docker run --rm -v $(PWD)/certs:/etc/letsencrypt \
        -v $(PWD)/cloudflare.ini:/cloudflare.ini \
        certbot/dns-cloudflare certonly \
        --dns-cloudflare-credentials /cloudflare.ini \
        -d "*.vlservices.viloforge.com" -d "vlservices.viloforge.com" \
        --agree-tos --no-eff-email -m "your-email@domain.com" --non-interactive

up:
    docker-compose up --build

In the above snippet, dev-cert uses the official Certbot image with the Cloudflare plugin. It mounts a volume certs to store certificates and an ini file with secrets. It requests the wildcard domain certificates
gist.github.com
gist.github.com
. After running this, the certificate and key will be in certs/live/vlservices.viloforge.com/. You would then configure either the Django dev servers to use them (as we did with runserver_plus) or copy them into an Nginx container. We mentioned a --cert-file and --key-file for runserver_plus in the Dockerfile CMD. You’ll need to copy the generated fullchain.pem and privkey.pem into each image (perhaps during build or by mounting at runtime). Alternatively, runserver_plus has an option to generate a self-signed cert on the fly, but that wouldn’t be trusted by default. Note: For an actual development team, using a reverse proxy with a single certificate might be easier. But using multiple runserver_plus instances with the same wildcard cert also works. After everything is up, developers can:
Run make dev-cert (once) to get certificates.
Run make up to build and start all containers.
Access the site at https://website.vlservices.viloforge.com:8444 (for example). The certificate will be valid (because it’s issued for that domain). The login redirect will go to https://login.vlservices.viloforge.com:8443, also covered by the wildcard cert.
Now you have a fully functional dev environment with SSO and HTTPS.
8. Summary and Next Steps
We built a JWT-based SSO system for Viloforge with the following flow:
Central Login: A user authenticates at the IdP and receives a JWT in a secure cookie
blog.stackademic.com
.
Token Sharing: The JWT cookie is scoped to the parent domain so that all subdomains (website, APIs) receive it
stackoverflow.com
blog.stackademic.com
.
Token Usage: The website (and potentially other frontends) use the JWT for authorizing API calls, either via automatic cookie inclusion or by adding it to request headers. We chose to send it in the Authorization header for clarity.
Verification: Every service validates the token using a shared secret and uses middleware to treat the user as logged-in
blog.stackademic.com
blog.stackademic.com
.
Security: We enforced HTTPS and used HttpOnly cookies to protect tokens from XSS
blog.stackademic.com
, SameSite and CSRF tokens to mitigate CSRF, and recommended short token lifetimes and refresh tokens for production readiness
blog.stackademic.com
blog.stackademic.com
. We also configured CORS properly to allow our domains to communicate while blocking others
blog.stackademic.com
blog.stackademic.com
.
By following this guide, a developer can implement a Single Sign-On mechanism where multiple Django applications (in separate containers or servers) accept a centralized login. This setup can be adapted to specific project needs – for instance, using longer-lived refresh tokens, integrating user roles/permissions in the JWT, or using OpenID Connect for a more standardized solution. Always adapt the code and configurations to your actual environment and test thoroughly, especially around security (token leakage, expiration, logout, etc.).






Sources







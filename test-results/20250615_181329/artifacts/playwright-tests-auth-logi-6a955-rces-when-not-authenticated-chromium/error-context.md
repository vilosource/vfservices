# Page snapshot

```yaml
- navigation "navbar":
  - link "Django REST framework":
    - /url: https://www.django-rest-framework.org/
  - list
- list:
  - listitem:
    - link "Home":
      - /url: /
- main "content":
  - group:
    - link "GET":
      - /url: /
    - button
  - button "OPTIONS"
  - main "main content":
    - heading "Home" [level=1]
    - paragraph: Home endpoint providing API information.
    - text: "GET / HTTP 200 OK Allow: OPTIONS, GET Content-Type: application/json Vary: Accept { \"message\": \"Welcome to the Billing API\", \"service\": \"billing-api\", \"version\": \"1.0.0\", \"timestamp\": \"2025-06-15T15:18:15.645761+00:00\", \"endpoints\": { \"health\": \"/health/ - Health check endpoint\", \"private\": \"/private/ - Private endpoint (requires authentication)\", \"home\": \"/ - This endpoint\" }, \"documentation\": \"/docs/ - API documentation (if available)\", \"status\": \"operational\" }"
```
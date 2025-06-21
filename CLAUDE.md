# Project Guidelines

## identity-provider
- The identity provider URL is https://identity.vfservices.viloforge.com (NOT identity-provider)
- When integrating with the identity-provider always get the api schema /api/schema from the traefik endpoint of the identity-provider

## Changelog
- 2025-01-21T15:45:00Z: Added correct identity provider URL (identity.vfservices.viloforge.com)
- 2025-01-21T10:30:00Z: Reorganized and made more concise while preserving all context

## Testing
- Always use Traefik endpoints for testing (e.g., https://website.vfservices.viloforge.com)
- Write Playwright smoke tests for all Django views in `playwright/<Django Project Name>/smoke-tests/`
- Include README.md for each test with instructions
- Test passwords: `<USERNAME>123!#QWERT`

## Development
- Use `docker compose` (not `docker-compose`)
- Common library is in project root directory
- Identity Provider has no web views - only API endpoints
- HTML content is populated via JavaScript API calls

## Documentation
- Add changelog to markdown files: `<DATETIME_TIMESTAMP>: Reason for update`

## Git Commits
- Do NOT include: `🤖 Generated with [Claude Code]` or `Claude <noreply@anthropic.com>`

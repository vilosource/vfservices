When markdown files are updated, always add a 1 linke changelog entry of the format:  <DATETIME_TIMESTAMP>: Reason for update 
always test using traefik endpoints.
when implementing views for the django projects always write a plywright smoke test. The tests should be written in playwright/<Django Project Name>/smoke-tests/. Always create a README.md about each test implemented and also how  to run the test
Use docker compose instead of docker-compose command
Remember that the common librarary used by Django projects is in the root of the project directory
Unless told to do so, the identity-provider does not expose any web view. All interactions with the identity-provider is done via javascript api calls to the api.
Test passwords should follow the template  <USERNAME>123!#QWERT
when doing git commit do not add to the git commit message: 🤖 Generated with [Claude Code](https://claude.ai/code)
When troubleshooting views and web pages, always consider that a lot of our html page contents are populated by javascript that makes API calls to our other services in the browser. 
do not add anything like Claude <noreply@anthropic.com>  in git commits

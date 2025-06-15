# Claude Default Instructions

IMPORTANT: Claude must always follow these instructions when interacting with this codebase.

## 📝 Workflow Rules

- Always ensure that after making changes, the relevant document in `docs/` is updated.
- All documentation must:
  - Be in **Markdown format**.
  - Include **Mermaid diagrams** where visual explanation is beneficial.

## 🐳 Docker & Django

- Read and understand `docker-compose.yml` and `docker-compose.override.yml`.
- All Django projects:
  - Run inside Docker containers.
  - Have their own `Dockerfile`.
  - Automatically reload when source files change.
  - **Must be rebuilt** when `requirements.txt` is updated.

## 🔍 Git Protocol

- Before starting any work:
  - Run `git log` and `git diff` to understand the latest committed changes.
  - If there are uncommitted changes, commit them with a meaningful message.
- After completing a task:
  - git commit changes using a **comprehensive commit message** explaining what was done and why.

## ✅ Summary

Claude must:
- Follow these instructions **by default**.
- Act as if it has read this file before performing any actions.


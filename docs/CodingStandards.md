# Kisan Mitra AI - Coding Standards

This document establishes the code quality gates, style requirements, type linting patterns, and formatting rules for contributors to **Kisan Mitra AI**.

---

## 1. Python (Backend) Coding Standards

### 1.1 Type Safety & Annotations
* All function signatures **MUST** contain strict type annotations for parameters and return types.
* Avoid using `Any`. Use `Union`, `Optional`, or specific generic types when possible.
* Use `mypy` for static analysis and validation.

### 1.2 Tooling Configuration
* **Code Formatting**: Handled strictly via **Black** (line length limit: `88`).
* **Linter & Style Rules**: Managed via **Ruff**. It replaces flake8, pyflakes, and pyupgrade.
* **Import Sorting**: Configured using **isort** options built directly into Ruff.
* Before committing, developers should run:
  ```bash
  ruff check . --fix
  black .
  mypy .
  ```

---

## 2. Frontend Coding Standards

### 2.1 Next.js & React
* Use **TypeScript** strictly for state interfaces, component props, and API request schemas.
* Follow the **App Router** layout. Server components should be the default; specify `"use client"` only for client-side interactive sub-components.
* Place API communication logic inside `frontend/services/` rather than embedded directly in UI pages.

### 2.2 Styling
* Use **Tailwind CSS** classes. Avoid custom inline styles.
* Group Tailwind classes cleanly. Use `clsx` and `tailwind-merge` (through `cn` utility) for conditional classes.

### 2.3 Formatting & Linting
* **Prettier** is used for layout structure and syntax styling.
* Prettier rules:
  - Single Quotes: `true`
  - Tab Width: `2`
  - Semicolons: `true`
  - Trailing Commas: `es5`
* Prettier formatting must not conflict with Next.js default **ESLint** rules.

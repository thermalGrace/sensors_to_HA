# Thermal Grace — Version, Releases, Contributing & Tests

> **Manage&Control KPIs Implementation**

**Author:** Artur Kraskov  
**Course:** ICT & OL, Delta — Fontys 2025-2026  

---

## Overview

This document describes the implementation of project management and control infrastructure for the **Thermal Grace** system. It covers version management, release automation, teamwork support, and automated testing for both hardware and software systems.

### Key Points

| Aspect | Summary |
|--------|---------|
| **Version Management** | Semantic versioning via `VERSION` file |
| **Release Management** | GitHub Actions automated releases on tag push |
| **Teamwork Support** | `CONTRIBUTING.md` + Pull Request templates |
| **Automated Testing** | CI pipelines for C++, Python, and MicroPython |

---

## Table of Contents

1. [Introduction](#introduction)
2. [Background](#background)
3. [What Was Implemented](#what-was-implemented)
4. [KPI Reflection](#kpi-reflection)
5. [Conclusion](#conclusion)
6. [References](#references)

---

## Introduction

This document details the development environment and project management infrastructure created to meet the Manage&Control KPIs. It ensures that all code changes are validated, releases are automated, and contributors have clear guidelines to follow.

### Background

The project follows a phased development approach:

| Phase | Description | Deliverables |
|-------|-------------|--------------|
| **Analysis & Advice** | Project plan, requirements gathering | Project Plan [1], Requirements [2] |
| **Design** | System architecture, C4 diagrams | C4 diagrams, Hardware Architecture [3] |
| **Realization** | Implementation, testing, deployment | Source code, CI/CD pipelines |

This document focuses on the **Realization** phase, specifically the infrastructure supporting code quality and release management.

---

## What Was Implemented

### Version Management

| Item | Description |
|------|-------------|
| `VERSION` file | Tracks current version (`0.1.0-alpha`) in repo root |
| Semantic Versioning | Format: `MAJOR.MINOR.PATCH[-label]` |

**Why:** Provides a single source of truth for the project version, enabling consistent versioning across documentation, releases, and code.

---

### Release Management

| Item | Description |
|------|-------------|
| `.github/workflows/release.yml` | GitHub Action triggered on `v*` tags |
| Auto-generated release notes | Uses GitHub's native release note generation |
| Explicit permissions | `contents: write` granted for release creation |

**How it works:** When a tag like `v1.0.0` is pushed, the workflow automatically creates a GitHub Release with generated release notes from commit history.

**Verification:** Successfully tested with tag `v0.1.0-test` — release was created automatically.

---

### Teamwork Support

| Item | Description |
|------|-------------|
| `CONTRIBUTING.md` | Guidelines for contributing (forking, branching, testing, PRs) |
| `.github/PULL_REQUEST_TEMPLATE.md` | Standard checklist for all pull requests |

**Why:** Ensures consistent contribution practices and facilitates code review by providing structure to pull requests.

---

### Automated Testing

Automated build and test pipelines were created for all major components of the system:

#### C++ Firmware (PlatformIO)

| Aspect | Details |
|--------|---------|
| **Workflow** | `.github/workflows/cpp_build.yml` |
| **Projects** | `MTP40-F_CO2_sensor/MTP40-F`, `MTP40-F_CO2_sensor/MTP40F_MQTT` |
| **Validation** | Compilation check via `pio run` |

#### Python/Streamlit Dashboard

| Aspect | Details |
|--------|---------|
| **Workflow** | `.github/workflows/python_tests.yml` |
| **Testing** | `pytest` for thermal comfort model and core logic tests |
| **Test Files** | `test.py`, `test_multi_user.py`, `tests/test_logic.py` |
| **Linting** | `flake8` style and syntax checks |

**Test Coverage:** Unit tests verify:
- Comfort calculation (`estimate_met`, `estimate_clo`, `compute_comfort`)
- MQTT payload parsing (`parse_env_from_payload`)
- State-to-CSV mapping (`snapshot_to_row`)
- LLM prompt building (`build_prompt_from_snapshot`, `build_multi_user_prompt`)

#### MicroPython Firmware

| Aspect | Details |
|--------|---------|
| **Workflow** | `.github/workflows/micropython_lint.yml` |
| **Linting** | `ruff` for syntax and import checks |
| **Directories** | `air_quality_mmWave_mqtt`, `bme680_air_quality_pi_pico_2_w`, `mmWave_pico_2_w`, `AMG_8833_Grid_eye` |

**Fixes Applied:** Resolved 24 linting errors including:
- Unused imports removed
- Multiple imports on one line split
- Unnecessary semicolons removed
- Star imports replaced with explicit imports

---

## KPI Reflection

### Manage&Control-H3.1

> "Set up and make use of: version management, release management, teamwork support, automated testing for hard- and software systems."

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Version management | `VERSION` file + semantic versioning | ✅ Met |
| Release management | Automated GitHub Releases via Actions | ✅ Met |
| Teamwork support | `CONTRIBUTING.md` + PR template | ✅ Met |
| Automated testing (HW) | C++ build validation in CI | ✅ Met |
| Automated testing (SW) | Python tests + linting in CI | ✅ Met |

---

### Manage&Control-S3.2

> "Organise a development environment with automated build and test infrastructure."

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Development environment | `requirements.txt` + `requirements.py` | ✅ Met |
| Automated build | GitHub Actions for all firmware types | ✅ Met |
| Automated test infrastructure | `pytest`, `flake8`, `ruff` in CI | ✅ Met |

---

## Conclusion

The project management infrastructure meets all requirements for the Manage&Control KPIs:

- **Versioned:** Clear semantic versioning with a central `VERSION` file
- **Automated:** Releases and testing triggered on every push/PR
- **Collaborative:** Contribution guidelines and PR templates in place
- **Quality-assured:** All code validated via linting and compilation checks

---

## References

1. Kraskov A., Kaszuba B., (2025), *Vitality HUB Perceived Thermal Comfort | Project Plan*, Thermal Comfort-as-a-Service (CaaS) IoT system, FHICT Delta.
2. Kraskov A., Kaszuba B., (2025), *Vitality HUB Perceived Thermal Comfort | Requirements*, Thermal Comfort-as-a-Service (CaaS) IoT system, FHICT Delta.
3. Kraskov A., (2025), *Thermal Grace — Hardware Architecture*, Technical Specification.

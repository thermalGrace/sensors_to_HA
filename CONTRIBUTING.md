# Contributing to Thermal Grace

Thank you for your interest in contributing to the Thermal Grace project! This project aims to provide a "Comfort-as-a-Service" platform using Pico sensor nodes, MQTT, and a Streamlit dashboard.

## How to Contribute

1.  **Fork the repository** on GitHub.
2.  **Create a new branch** for your feature or bugfix: `git checkout -b feature/your-feature-name`.
3.  **Implement your changes**.
4.  **Run tests and linting**:
    - For Python: `pip install -r requirements.txt` then `pytest` and `flake8 .`.
    - For C++ Firmware: Use PlatformIO to build the project.
5.  **Commit your changes** with descriptive commit messages.
6.  **Push to your fork** and **submit a Pull Request**.

## Automated Checks

We use GitHub Actions to run automated tests and linting on every Pull Request:
- **C++ Build Check**: Ensures firmware compiles.
- **Python Tests & Linting**: Runs `pytest` and checks code style.
- **MicroPython Linting**: Checks MicroPython firmware for syntax errors.

## Release Management

Versions are tracked in the `VERSION` file. Automated releases are created when a tag starting with `v` is pushed to the repository.

# SeleniumHub Pro: Enterprise-Grade, Data-Driven E-Commerce Test Automation

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/selenium-4.x-green.svg)](https://www.selenium.dev/)
[![Pytest](https://img.shields.io/badge/pytest-8.x%2F9.x-orange.svg)](https://pytest.org/)
[![Reporting](https://img.shields.io/badge/reports-HTML%20%7C%20PDF%20%7C%20TXT-purple.svg)](reports/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SeleniumHub Pro** is a production-grade, enterprise-ready end-to-end test automation framework built in Python using **Selenium WebDriver (W3C)**, **Pytest**, and the **Page Object Model (POM)** design pattern. It automates a complete e-commerce customer purchase journey across multiple storefronts with zero code changes, supporting data-driven execution via both **Excel (.xlsx)** and **JSON**, and delivering executive-ready **PDF**, **HTML**, and **pure text** test reports.

---

## 🌟 Key Highlights & Architectural Strengths

- **Strict Page Object Model (POM)**: 100% decoupling between test logic, locators, page actions, and test data.
- **Data-Driven Testing (DDT)**: Dual-source data repository supporting **Excel** (`openpyxl`) and **JSON**, switchable via configuration or CLI flag.
- **Multi-Format Reporting**:
  - **`output.pdf`**: Standalone executive test execution report with KPIs, results matrix, sanitized milestone viewports, console logs, and SDET sign-off.
  - **`latest_execution_report.html`**: Interactive, self-contained HTML report with environment metadata, duration metrics, and failure diagnostics.
  - **`test_output_only.txt`**: Clean, stream-oriented plain-text output file for CI/CD pipe consumption.
- **Symbol & Vendor Masking Engine**: Automated DOM JavaScript element hiding and Pillow image sanitization removing AUT logos/banners from milestone screenshots.
- **Robust Synchronization**: Exclusively utilizes **Explicit Waits** (`WebDriverWait` and Expected Conditions). Zero arbitrary `time.sleep()` calls.
- **Dynamic Cart Adjustment**: Handles both editable inputs and static badge shopping carts, seamlessly recalculating item totals (`Total = Unit Price × Quantity`).
- **Auto-Registration Fallback**: If a test user does not exist on the target AUT, the framework automatically initiates signup with test dataset credentials and proceeds seamlessly.
- **Resilient Pop-up & Overlay Handling**: Automatic handling of JavaScript alerts, confirmation dialogs, modal popups, and Google AdSense overlays/vignettes.
- **CI/CD & Containerization**: Ready-to-run GitHub Actions workflow (`.github/workflows/tests.yml`) and containerized execution via `Dockerfile`.

---

## 📋 10 Mandatory Requirements Traceability Matrix

| # | Mandatory Requirement | Implementation Details | Verification Evidence |
|---|-----------------------|------------------------|-----------------------|
| **1** | **Launch Browser** | `conftest.py` initializes Chrome or Firefox with WebDriverManager; maximizes window; enforces `implicitly_wait(0)` with explicit waits. | `base_page.py`, `conftest.py` |
| **2** | **Login to Application** | `LoginPage.login_or_register()` authenticates with test data; auto-registers if account does not exist; asserts `"Logged in as Alexander Wright"`. | `pages/login_page.py` |
| **3** | **Search Product** | `ProductPage.search_product()` enters product name from dataset (`"Blue Top"`) and verifies search results display. | `pages/product_page.py` |
| **4** | **Add Product to Cart** | `ProductPage.add_to_cart()` adds product; handles confirmation modal dialog (`#cartModal`). | `pages/product_page.py` |
| **5** | **Update Quantity** | `CartPage.update_quantity()` adjusts quantity from 1 to 3; handles static badge carts via detail replenishment. | `pages/cart_page.py` |
| **6** | **Verify Cart Details** | `CartPage.verify_cart_details()` asserts: Product name (`"Blue Top"`), quantity (`3`), unit price (`Rs. 500`), and math (`Rs. 1500 = Rs. 500 × 3`). | `pages/cart_page.py` |
| **7** | **Capture Screenshots** | Captured at every milestone (`01_after_login`, `02_after_search_results`, `03_after_add_to_cart`, `04_after_quantity_update`, `05_after_cart_verification`) with symbol masking, plus automated failure hook screenshots. | `screenshots/`, `pages/base_page.py` |
| **8** | **Read Test Data from Excel / JSON** | Validated with both `DATA_SOURCE=excel` and `DATA_SOURCE=json`. Dynamic parameterization via `pytest_generate_tests`. | `utilities/data_loader.py` |
| **9** | **Handle Popups / Alerts** | `BasePage.handle_alert()`, `dismiss_common_overlays()`, and modal selectors safely dismiss consent banners and Google AdSense vignettes. | `pages/base_page.py` |
| **10** | **Generate Execution Report** | Generates executive `output.pdf`, `reports/latest_execution_report.html`, and `test_output_only.txt`. | `reports/`, `utilities/pdf_report_generator.py` |

---

## 📂 Project Directory Structure

```text
SeleniumHub_Pro/
├── .github/
│   └── workflows/
│       └── tests.yml          # GitHub Actions CI/CD matrix pipeline
├── config/
│   ├── __init__.py
│   ├── config.py              # Centralized runtime configuration & env overrides
│   └── settings.json          # Standalone JSON configuration file
├── pages/
│   ├── __init__.py
│   ├── base_page.py           # BasePage: explicit waits, clicks, screenshots, DOM sanitization
│   ├── home_page.py           # HomePage: navigation, consent banners, session checks
│   ├── login_page.py          # LoginPage: login, auto-registration fallback, assertions
│   ├── product_page.py        # ProductPage: search, details, quantity, cart modal
│   └── cart_page.py           # CartPage: quantity updates, item details, math assertions
├── test_data/
│   ├── test_data.xlsx         # Formatted Excel test dataset (openpyxl)
│   └── test_data.json         # Structured JSON test dataset
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures, driver factory, failure hooks, report generators
│   └── test_e2e_purchase.py   # Main E2E purchase flow covering all 10 requirements
├── utilities/
│   ├── __init__.py
│   ├── excel_reader.py        # openpyxl-based Excel dataset reader
│   ├── json_reader.py         # JSON dataset reader
│   ├── data_loader.py         # Unified data repository with source switching
│   ├── logger.py              # Sensitive data masking & rotating file/console logger
│   ├── pdf_report_generator.py # Executive PDF report builder with ReportLab
│   ├── sanitize_reports.py    # Report sanitization engine enforcing clean outputs
│   ├── report_helper.py       # Timestamped directory and file path coordinator
│   └── create_excel_data.py   # Utility to generate/refresh formatted Excel test data
├── reports/                   # Generated reports (HTML, PDF, Output Text)
│   ├── output.pdf             # Executive PDF report with embedded screenshots & metrics
│   ├── latest_execution_report.pdf
│   ├── latest_execution_report.html
│   └── test_output_only.txt
├── screenshots/               # Sanitized milestone screenshots
├── logs/                      # Rotating execution log files
├── output.pdf                 # Root deliverable copy of executive PDF report
├── test_output_only.txt       # Root deliverable copy of pure test output
├── requirements.txt           # Pinned production dependencies
├── pytest.ini                 # Pytest runner, markers, and logging configuration
├── Dockerfile                 # Reproducible containerized execution
├── ARCHITECTURE.md            # Detailed architecture, design patterns, & requirement matrix
└── README.md                  # This file
```

---

## 🚀 Quick Start & Prerequisites

### 1. System Requirements
- **Python**: Version 3.11, 3.12, 3.13, or 3.14
- **Google Chrome** or **Mozilla Firefox** installed locally
- **Operating System**: Windows, Linux, or macOS

### 2. Installation
Clone the repository and install the pinned dependencies:

```bash
# Clone the repository
git clone https://github.com/abir1010200/E-COMMERCE_selenium.git
cd E-COMMERCE_selenium

# Install required dependencies
pip install -r requirements.txt
```

---

## 💻 Running the Test Suite

All drivers are managed automatically by `webdriver-manager`—no manual driver downloads required.

### 1. Run Complete Test Suite (Headless Mode)
```bash
python -m pytest tests/test_e2e_purchase.py --headless
```

### 2. Run Specific Test Case (e.g. TC_E2E_01)
```bash
python -m pytest tests/test_e2e_purchase.py -k "TC_E2E_01" --headless
```

### 3. Switch Test Data Source (Excel vs. JSON)
You can toggle between Excel and JSON test data without changing any test code:

```bash
# Using CLI option
python -m pytest tests/test_e2e_purchase.py --data-source=json --headless
python -m pytest tests/test_e2e_purchase.py --data-source=excel --headless

# Using Environment Variable (PowerShell)
$env:DATA_SOURCE="json"; python -m pytest tests/test_e2e_purchase.py --headless
```

### 4. Switch Browser Engine (Chrome vs. Firefox)
```bash
# Run on Firefox
python -m pytest tests/test_e2e_purchase.py --browser=firefox --headless

# Run on Chrome
python -m pytest tests/test_e2e_purchase.py --browser=chrome --headless
```

### 5. Multi-Storefront (AUT) Switching
The framework supports multiple e-commerce storefronts via configuration alone:
```bash
# Windows PowerShell
$env:AUT_NAME="automationexercise"; python -m pytest tests/test_e2e_purchase.py --headless
$env:AUT_NAME="tutorialsninja"; python -m pytest tests/test_e2e_purchase.py --headless
```

### 6. Parallel Execution (pytest-xdist)
Run tests across multiple CPU cores simultaneously:
```bash
python -m pytest tests/test_e2e_purchase.py -n auto --headless
```

---

## 📊 Deliverable Reports & Artifacts

After execution, the following deliverable reports are available:

1. **`output.pdf`**:
   - Executive-ready summary table and KPIs (Passed, Failed, Success Rate, Execution Time).
   - Test Results Matrix with quantities, unit prices, and financial totals.
   - Clean, sanitized milestone screenshots (zero vendor logos or carousel banners).
   - Detailed console execution output stream.
   - QA sign-off and requirement compliance audit block.

2. **`latest_execution_report.html`**:
   - Interactive pytest-html report with filterable test statuses and environment metadata.

3. **`test_output_only.txt`**:
   - Stream-oriented pure console output log with zero vendor mentions.

4. **`screenshots/`**:
   - Milestone captures verifying login, search, add-to-cart, quantity modification, and cart table calculations.

---

## 🐳 Docker Execution

Run tests inside a clean, reproducible containerized environment:

```bash
# Build Docker image
docker build -t seleniumhub-pro .

# Run test container
docker run --rm -v ${PWD}/reports:/app/reports -v ${PWD}/screenshots:/app/screenshots seleniumhub-pro
```

---

## 🛠️ SDET Design Patterns & Best Practices

1. **Explicit Synchronization**: All page interactions employ `WebDriverWait` with conditions such as `element_to_be_clickable`, `visibility_of_element_located`, and `presence_of_element_located`.
2. **Resilient Interception Handling**: Clicks intercepted by overlays or animations trigger automatic scroll-to-element and JavaScript execution fallbacks.
3. **Data Security**: Sensitive credentials (passwords, tokens) are filtered and masked in all log outputs using custom `SensitiveDataFilter`.
4. **Autonomous Account Provisioning**: Self-healing login workflow automatically signs up missing users without requiring manual database seeding.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

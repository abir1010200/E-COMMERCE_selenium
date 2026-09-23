# Capstone Assignment 1: E-Commerce Web Application Automation

A clean, basic, and complete Selenium WebDriver with Python test automation project adhering to the Page Object Model (POM) pattern.

## 📋 Business Scenario & 10 Mandatory Requirements

A customer wants to purchase a product from an E-Commerce site (`https://automationexercise.com/`). The automation accomplishes:

| # | Requirement | Implementation in Project |
|---|-------------|----------------------------|
| 1 | **Launch browser** | `tests/conftest.py` configures Chrome / Firefox via `webdriver-manager` with explicit waits |
| 2 | **Login to application** | `pages/login_page.py` authenticates using test credentials (with auto-registration fallback) |
| 3 | **Search product** | `pages/product_page.py` searches for product from test data and verifies search results |
| 4 | **Add product to cart** | `pages/product_page.py` adds product to shopping cart and handles confirmation modal |
| 5 | **Update quantity** | `pages/cart_page.py` updates product quantity |
| 6 | **Verify cart details** | `pages/cart_page.py` verifies product name, quantity, unit price, and total price calculation ($Total = Unit \times Qty$) |
| 7 | **Capture screenshots** | Captured at every key milestone in `screenshots/` directory + automated failure screenshot capture |
| 8 | **Read test data from Excel / JSON** | Reads test cases from `test_data/test_data.xlsx` or `test_data/test_data.json` |
| 9 | **Handle popup / alerts if available** | Handled in `pages/base_page.py` (overlays, modals, consent dialogs, alerts) |
| 10 | **Generate execution report** | Generates clean, interactive HTML test execution report at `reports/report.html` |

---

## 📁 Project Directory Structure

```text
Selenium/
├── config/
│   ├── config.py              # Centralized configuration (timeouts, browser, AUT URL)
│   └── settings.json          # Configuration parameters
├── pages/
│   ├── base_page.py           # Base Page Object with reusable helper methods
│   ├── home_page.py           # Home page elements and actions
│   ├── login_page.py          # Login and registration actions
│   ├── product_page.py        # Product search and add-to-cart actions
│   └── cart_page.py           # Cart verification and quantity update actions
├── reports/
│   └── report.html            # Test execution report (HTML format)
├── screenshots/               # Step-by-step and failure screenshots
├── test_data/
│   ├── test_data.xlsx         # Excel test dataset (openpyxl)
│   └── test_data.json         # JSON test dataset
├── tests/
│   ├── conftest.py            # Pytest fixtures and browser lifecycle
│   └── test_e2e_purchase.py   # E2E test covering the 10 requirements
├── utilities/
│   ├── data_loader.py         # Data loader supporting Excel and JSON
│   ├── excel_reader.py        # Excel file reader
│   ├── json_reader.py         # JSON file reader
│   ├── logger.py              # Centralized logging setup
│   └── report_helper.py       # Screenshot path helper
├── pytest.ini                 # Pytest configuration and HTML report settings
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Run Test Suite
To run the complete automated test suite:
```powershell
python -m pytest
```

### 3. Run in Headless Mode
```powershell
python -m pytest --headless
```

### 4. Run with JSON Test Data (Instead of Excel)
```powershell
python -m pytest --data-source=json
```

### 5. View Test Execution Report
After execution, open the self-contained execution report in your browser:
```text
reports/report.html
```

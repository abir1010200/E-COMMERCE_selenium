# Capstone Project: E-Commerce Web Automation

An automated end-to-end testing suite for an e-commerce platform using **Python** and **Selenium WebDriver**.

This project automates a complete customer purchasing workflow on [Automation Exercise](https://automationexercise.com/), from user login to cart verification and price calculation assertions.

---

## 🎯 Project Overview & Workflow

The automated script covers the full purchase lifecycle:

1. **Launch Browser**: Initializes Google Chrome WebDriver with custom options (`eager` page loading to avoid renderer timeouts from third-party ads).
2. **Handle Popups**: Automatically detects and dismisses cookie consent banners and overlays.
3. **User Authentication**: Logs in with test credentials (with automatic signup and profile creation fallback if the user is not found).
4. **Cart Cleanup**: Clears any previous session items to ensure accurate quantity testing.
5. **Product Search**: Searches for the target product (`Blue Top`) from the catalog.
6. **Product Detail & Quantity**: Navigates to the product detail page and sets the quantity to `3`.
7. **Add to Cart & Modal Handling**: Adds the product to the shopping cart and interacts with the confirmation modal.
8. **Cart Verification**:
   - Asserts product name contains `Blue Top`.
   - Asserts quantity equals `3`.
   - Asserts financial calculation: $\text{Total Price} = \text{Unit Price} \times \text{Quantity}$.
9. **Milestone Screenshot**: Captures and saves a full viewport verification image as `screenshot.png`.
10. **Browser Teardown**: Closes the browser cleanly upon completion.

---

## 📁 Project Structure

```text
Selenium/
├── main.py              # Consolidated single-file automation script with step comments
├── screenshot.png       # Captured milestone execution screenshot
├── requirements.txt     # Python project dependencies
├── pytest.ini           # Optional Pytest test runner configuration
└── README.md            # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+ installed
- Google Chrome browser installed

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run the Automation Script

Run the consolidated single-file script:
```powershell
python main.py
```

Or run via Pytest:
```powershell
python -m pytest main.py
```

### 4. Output & Verification
Upon execution, the terminal outputs step-by-step progress and verification confirmation:
```text
Logged in successfully!
Searched for 'Blue Top'
Opened product detail: https://automationexercise.com/product_details/1
Added product to cart with quantity 3
Navigated to Cart page
ALL ASSERTIONS PASSED: Name: 'Blue Top' | Qty: 3 | Unit: Rs. 500.0 | Total: Rs. 1500.0
Saved screenshot to screenshot.png
```
A visual proof of test execution is saved in `screenshot.png`.

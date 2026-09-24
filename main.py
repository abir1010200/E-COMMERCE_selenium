import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def safe_click(driver, element):
    """Safely click an element, falling back to JavaScript click if an overlay intercepts it."""
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)

def run_test():
    # --------------------------------------------------------------------------
    # 1. Launch Browser & Driver Configuration
    # --------------------------------------------------------------------------
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.page_load_strategy = "eager"
    # options.add_argument("--headless")  # Uncomment to run without browser window

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        # ----------------------------------------------------------------------
        # 2. Navigate to Application Homepage
        # ----------------------------------------------------------------------
        driver.get("https://automationexercise.com")

        # ----------------------------------------------------------------------
        # 3. Handle Cookie Consent Popups if Present
        # ----------------------------------------------------------------------
        try:
            consent_buttons = driver.find_elements(By.CSS_SELECTOR, "p.fc-button-headline, button.fc-cta-consent, .fc-button")
            if consent_buttons:
                safe_click(driver, consent_buttons[0])
        except Exception:
            pass

        # ----------------------------------------------------------------------
        # 4. User Login & Auto-Registration Fallback
        # ----------------------------------------------------------------------
        driver.get("https://automationexercise.com/login")
        email = "alexander.wright.test@example.com"
        password = "SecurePassword123!"

        # Enter login credentials
        driver.find_element(By.CSS_SELECTOR, "input[data-qa='login-email']").send_keys(email)
        driver.find_element(By.CSS_SELECTOR, "input[data-qa='login-password']").send_keys(password)
        safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[data-qa='login-button']"))

        # If user does not exist, perform automatic signup
        if driver.find_elements(By.XPATH, "//div[contains(@class, 'login-form')]//p[contains(@style, 'red')]"):
            driver.find_element(By.CSS_SELECTOR, "input[data-qa='signup-name']").send_keys("Alexander Wright")
            driver.find_element(By.CSS_SELECTOR, "input[data-qa='signup-email']").send_keys(email)
            safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[data-qa='signup-button']"))

            if not driver.find_elements(By.XPATH, "//form[contains(@action, 'signup')]//p[contains(@style, 'red')]"):
                safe_click(driver, wait.until(EC.presence_of_element_located((By.ID, "id_gender1"))))
                driver.find_element(By.ID, "password").send_keys(password)
                driver.find_element(By.ID, "first_name").send_keys("Alexander")
                driver.find_element(By.ID, "last_name").send_keys("Wright")
                driver.find_element(By.ID, "address1").send_keys("742 Evergreen Terrace")
                driver.find_element(By.ID, "state").send_keys("California")
                driver.find_element(By.ID, "city").send_keys("Springfield")
                driver.find_element(By.ID, "zipcode").send_keys("97477")
                driver.find_element(By.ID, "mobile_number").send_keys("15550198234")
                safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button[data-qa='create-account']"))
                safe_click(driver, wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-qa='continue-button']"))))

        # Verify user is logged in
        wait.until(EC.presence_of_element_located((By.XPATH, "//header//a[contains(., 'Logged in as')]")))
        print("Logged in successfully!")

        # ----------------------------------------------------------------------
        # 5. Clear Any Existing Cart Items from Previous Runs
        # ----------------------------------------------------------------------
        driver.get("https://automationexercise.com/view_cart")
        delete_buttons = driver.find_elements(By.CSS_SELECTOR, "a.cart_quantity_delete")
        for btn in delete_buttons:
            safe_click(driver, btn)
        time.sleep(1)

        # ----------------------------------------------------------------------
        # 6. Search for Product
        # ----------------------------------------------------------------------
        driver.get("https://automationexercise.com/products")
        search_input = wait.until(EC.presence_of_element_located((By.ID, "search_product")))
        search_input.send_keys("Blue Top", Keys.ENTER)
        print("Searched for 'Blue Top'")

        # ----------------------------------------------------------------------
        # 7. Open Product Details Page
        # ----------------------------------------------------------------------
        detail_link = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/product_details/')]")))
        detail_url = detail_link.get_attribute("href")
        driver.get(detail_url)
        print(f"Opened product detail: {detail_url}")

        # ----------------------------------------------------------------------
        # 8. Set Quantity & Add to Cart
        # ----------------------------------------------------------------------
        qty_input = wait.until(EC.visibility_of_element_located((By.ID, "quantity")))
        driver.execute_script("arguments[0].value = '';", qty_input)
        qty_input.send_keys("3")

        safe_click(driver, driver.find_element(By.CSS_SELECTOR, "button.cart"))
        print("Added product to cart with quantity 3")

        # ----------------------------------------------------------------------
        # 9. Handle Add to Cart Modal Popup & Open Cart
        # ----------------------------------------------------------------------
        try:
            modal_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='cartModal']//a[contains(@href, '/view_cart')] | //div[@id='cartModal']//u[contains(text(), 'View Cart')]")))
            safe_click(driver, modal_btn)
        except Exception:
            pass

        # Fallback to direct navigation if modal click did not change page
        if "view_cart" not in driver.current_url:
            driver.get("https://automationexercise.com/view_cart")
        print("Navigated to Cart page")

        # ----------------------------------------------------------------------
        # 10. Verify Cart Details (Name, Quantity, Unit Price, Total Price)
        # ----------------------------------------------------------------------
        wait.until(EC.presence_of_element_located((By.ID, "cart_info_table")))

        product_name = driver.find_element(By.CSS_SELECTOR, "td.cart_description h4 a").text
        price_text = driver.find_element(By.CSS_SELECTOR, "td.cart_price p").text
        qty_text = driver.find_element(By.CSS_SELECTOR, "td.cart_quantity button").text
        total_text = driver.find_element(By.CSS_SELECTOR, "td.cart_total p.cart_total_price").text

        # Parse numeric amounts
        unit_price = float(re.search(r"(\d+(?:\.\d+)?)", price_text.replace(",", "")).group(1))
        quantity = int(qty_text)
        total_price = float(re.search(r"(\d+(?:\.\d+)?)", total_text.replace(",", "")).group(1))

        # Assertions
        assert "Blue Top" in product_name, f"Expected 'Blue Top' in '{product_name}'"
        assert quantity == 3, f"Expected quantity 3, found {quantity}"
        assert abs(total_price - (unit_price * quantity)) < 0.01, f"Total price mismatch: {total_price} != {unit_price * quantity}"

        print(f"ALL ASSERTIONS PASSED: Name: '{product_name}' | Qty: {quantity} | Unit: Rs. {unit_price} | Total: Rs. {total_price}")

        # ----------------------------------------------------------------------
        # 11. Capture Milestone Screenshot
        # ----------------------------------------------------------------------
        driver.save_screenshot("screenshot.png")
        print("Saved screenshot to screenshot.png")

    finally:
        # ----------------------------------------------------------------------
        # 12. Teardown / Close Browser
        # ----------------------------------------------------------------------
        driver.quit()

# Support running directly with Pytest
def test_ecommerce_flow():
    run_test()

# Support running directly with Python
if __name__ == "__main__":
    run_test()

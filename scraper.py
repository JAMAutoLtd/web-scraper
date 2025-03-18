from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import random

# -------------------- Setup --------------------

# Path to your Edge WebDriver
driver_path = r"C:\Users\justi\OneDrive\Documents\1JAM\edgedriver_win64\msedgedriver.exe"

# Initialize Edge options (optional)
options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")  # Start maximized
# Uncomment the next line to run in headless mode
# options.add_argument('--headless')

# Initialize the Edge driver
service = Service(driver_path)
driver = webdriver.Edge(service=service, options=options)

# Initialize WebDriverWaits
wait_long = WebDriverWait(driver, 30)   # For elements that may take longer
wait_short = WebDriverWait(driver, 10)  # For faster interactions

# -------------------- Utility Functions --------------------

def sanitize_step_name(step_name):
    """
    Replaces problematic characters in step_name to create valid file paths.
    """
    return step_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_') \
                    .replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_') \
                    .replace('|', '_')

def capture_debug_info(step_name):
    """
    Captures the current page's HTML source and a screenshot for debugging purposes.
    Only captures debug info on failures to speed up the script.
    """
    try:
        # Sanitize the step_name to prevent invalid file paths
        safe_step_name = sanitize_step_name(step_name)
        
        # Ensure the debug_info directory exists
        if not os.path.exists("debug_info"):
            os.makedirs("debug_info")
        
        # Capture the page source
        with open(f"debug_info/page_source_{safe_step_name}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Capture a screenshot
        driver.save_screenshot(f"debug_info/screenshot_{safe_step_name}.png")
        print(f"Captured debug info for: {safe_step_name}")
    
    except Exception as e:
        print(f"Failed to capture debug info for '{step_name}': {e}")

def wait_for_page_load():
    """
    Waits until the page is fully loaded.
    """
    try:
        wait_long.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        print("Page loaded successfully.")
    except Exception as e:
        print(f"Error waiting for page to load: {e}")

def interact_with_dropdown(identifying_text, option_text, need_to_open=True, parent_element=None):
    """
    Interacts with a dropdown by locating it based on placeholder or title,
    clicking to open if needed, and selecting the desired option.

    :param identifying_text: The placeholder text or the title text of the dropdown.
    :param option_text: The visible text of the option to select.
    :param need_to_open: Boolean indicating whether to click to open the dropdown.
    :param parent_element: The parent WebElement to scope the search (optional).
    :return: Boolean indicating success or failure
    """
    try:
        print(f"Interacting with dropdown: '{identifying_text}' to select '{option_text}'")
        
        # Define the context for searching elements
        context = parent_element if parent_element else driver

        dropdown_toggle = None

        # Attempt to locate an input field with the given placeholder
        try:
            dropdown_toggle = wait_short.until(EC.element_to_be_clickable((
                By.XPATH, f".//input[@placeholder='{identifying_text}']"
            )))
            print(f"Found input-based dropdown for: '{identifying_text}'")
        except:
            # If not found, attempt to locate a div-based dropdown with h3.title
            try:
                dropdown_toggle = wait_short.until(EC.element_to_be_clickable((
                    By.XPATH, f".//div[contains(@class, 'dropbox') and .//h3[@class='title' and normalize-space(text())='{identifying_text}']]"
                )))
                print(f"Found div-based dropdown for: '{identifying_text}'")
            except:
                # Dropdown toggle not found; possibly already open or not present
                print(f"Dropdown toggle for '{identifying_text}' not found; assuming dropdown is already open or not present.")
        
        if need_to_open and dropdown_toggle:
            # Scroll the toggle into view
            driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_toggle)
            
            # Click the dropdown toggle using JavaScript to ensure reliability
            driver.execute_script("arguments[0].click();", dropdown_toggle)
            print(f"Clicked on dropdown: '{identifying_text}' using JavaScript")
            
            # Wait until the dropdown options are visible instead of using sleep
            if identifying_text == "Make/Model/Year":
                wait_short.until(EC.visibility_of_element_located((
                    By.XPATH, f".//following-sibling::div[contains(@class, 'dropbox') and .//h3[@class='title' and text()='Make']]/ul"
                )))
            elif identifying_text == "Model":
                wait_short.until(EC.visibility_of_element_located((
                    By.XPATH, f".//div[contains(@class, 'dropbox') and .//h3[@class='title' and text()='Model']]/ul"
                )))
            elif identifying_text == "Year":
                wait_short.until(EC.visibility_of_element_located((
                    By.XPATH, f".//div[contains(@class, 'dropbox') and .//h3[@class='title' and text()='Year']]/ul"
                )))
        
        # Now, locate the dropdown options
        dropdown_ul = None
        if identifying_text == "Make/Model/Year":
            # For the first level, options are in sibling divs
            dropdown_ul = wait_short.until(EC.visibility_of_element_located((
                By.XPATH, f".//following-sibling::div[contains(@class, 'dropbox') and .//h3[@class='title' and text()='Make']]/ul"
            )))
        elif identifying_text == "Model":
            # For the Model dropdown, locate the ul within the Model dropbox
            dropdown_ul = wait_short.until(EC.visibility_of_element_located((
                By.XPATH, f".//div[contains(@class, 'dropbox') and .//h3[@class='title' and text()='Model']]/ul"
            )))
        elif identifying_text == "Year":
            # For the Year dropdown, locate the ul within the Year dropbox
            dropdown_ul = wait_short.until(EC.visibility_of_element_located((
                By.XPATH, f".//div[contains(@class, 'dropbox') and .//h3[@class='title' and text()='Year']]/ul"
            )))
        else:
            # Default locator if not specifically handled
            dropdown_ul = wait_short.until(EC.visibility_of_element_located((
                By.XPATH, f".//div[contains(@class, 'dropbox_wrap')]/div[contains(@class, 'dropbox') and not(contains(@style, 'display: none'))]/ul"
            )))
        
        print(f"Dropdown options are now visible for: '{identifying_text}'")
        
        # Locate the desired option within the dropdown
        desired_option = dropdown_ul.find_element(By.XPATH, f".//li[normalize-space(text())='{option_text}']")
        
        # Scroll the desired option into view (optional)
        driver.execute_script("arguments[0].scrollIntoView(true);", desired_option)
        
        # Click the desired option using JavaScript to ensure reliability
        driver.execute_script("arguments[0].click();", desired_option)
        print(f"Selected option '{option_text}' in dropdown '{identifying_text}' using JavaScript click")
        return True

    except Exception as e:
        print(f"Failed to interact with dropdown '{identifying_text}': {e}")
        capture_debug_info(f"{identifying_text}_error")
        return False

def interact_with_multilevel_dropdown(level_placeholders_options):
    """
    Interacts with multi-level dropdowns sequentially.

    :param level_placeholders_options: A list of tuples containing (placeholder, option_text, need_to_open) for each level
    """
    for item in level_placeholders_options:
        if len(item) == 3:
            placeholder, option_text, need_to_open = item
        elif len(item) == 2:
            placeholder, option_text = item
            need_to_open = True  # Default to True
        else:
            raise ValueError("Each tuple must have 2 or 3 elements: (placeholder, option_text, [need_to_open])")
        
        success = interact_with_dropdown(placeholder, option_text, need_to_open=need_to_open)
        if not success:
            print(f"Stopping script due to failure in '{placeholder}' dropdown.")
            driver.quit()
            exit()
        # No sleep; rely on explicit waits

# -------------------- Main Script --------------------

try:
    # Step 1: Open the URL
    driver.get("https://www.maxisysadas.com/getCoverage.jspx")
    capture_debug_info("step1_open_url")
    wait_for_page_load()
    # Minimal additional wait
    time.sleep(2)  # Reduced from 5 seconds
    
    # -------------------- Interact with Dropdowns --------------------
    
    # Step 2: Interact with 'Product type' Dropdown
    success = interact_with_dropdown("Product type", "MA600", need_to_open=True)
    if not success:
        print("Stopping script due to failure in 'Product type' dropdown.")
        driver.quit()
        exit()
    time.sleep(random.uniform(1, 3))  # Wait between interactions
    
    # Step 3: Interact with 'Make/Model/Year' Dropdown (Multi-Level)
    # Define the sequence of placeholders, options, and whether to open the dropdown
    multilevel_levels = [
        ("Make/Model/Year", "Acura(CANADA)", True),  # Need to open
        ("Model", "Acura ILX", False),              # Already open
        ("Year", "2022", False)                     # Already open
    ]
    interact_with_multilevel_dropdown(multilevel_levels)
    # Removed sleep
        
    # Step 4: Interact with 'System' Dropdown
    success = interact_with_dropdown("System", "ACC", need_to_open=True)
    if not success:
        print("Stopping script due to failure in 'System' dropdown.")
        driver.quit()
        exit()
    time.sleep(random.uniform(1, 3))  # Wait between interactions
    # Removed sleep
    
    # -------------------- Data Extraction --------------------
    # After selecting all dropdown options, proceed to extract the required data.
    # This part depends on how the data is presented on the page after selections.
    # Example:
    
    # Wait for the data to load (adjust the wait condition as needed)
    # data_element = wait_short.until(EC.visibility_of_element_located((By.XPATH, "//div[@id='desired_data_element']")))
    
    # Extract the data
    # extracted_data = data_element.text
    # print(f"Extracted Data: {extracted_data}")
    
    # For demonstration, let's capture a screenshot of the final state
    capture_debug_info("final_state")
    print("Data extraction step is pending based on specific requirements.")
    
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    capture_debug_info("unexpected_error")

finally:
    # Cleanup: Close the browser
    driver.quit()
    print("Browser closed.")

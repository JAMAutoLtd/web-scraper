from playwright.async_api import async_playwright
import asyncio
import os
import random
from datetime import datetime
import logging
import re
import json
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("model_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelYearScraper:
    # Define make mappings
    MAKE_MAPPINGS = {
        'ACURA': 'Acura(CANADA)',
        'ALFA ROMEO': 'Alfa',
        'AUDI': 'Audi',
        'BENTLEY': 'Bentley',
        'BMW': 'BMW',
        'BUICK': 'Buick',
        'CADILLAC': 'Cadillac',
        'CHEVROLET': 'Chevrolet',
        'CHRYSLER': 'Chrysler',
        'DODGE': 'Dodge',
        'FIAT': 'Fiat',
        'FORD': 'Ford',
        'GENESIS': 'Genesis(Canada)',
        'GMC': 'GMC',
        'HONDA': 'Honda(CANADA)',
        'HYUNDAI': 'Hyundai(Canada)',
        'INFINITI': 'Infiniti(North America)',
        'JAGUAR': 'Jaguar',
        'JEEP': 'Jeep',
        'KIA': 'Kia(USA)',
        'LAMBORGHINI': 'Lamborghini',
        'LAND ROVER': 'Land Rover',
        'LEXUS': 'LEXUS(USA)',
        'LINCOLN': 'Lincoln',
        'MASERATI': 'Maserati',
        'MAZDA': 'Mazda',
        'MERCEDES-BENZ': 'Mercedes Benz',
        'MINI': 'MINI',
        'MITSUBISHI': 'Mitsubishi',
        'NISSAN': 'Nissan(North America)',
        'PORSCHE': 'Porsche',
        'RAM': 'RAM',
        'SUBARU': 'Subaru(US)',
        'TESLA': 'Tesla',
        'TOYOTA': 'Toyota(USA)',
        'VOLKSWAGEN': 'Volkswagen',
        'VOLVO': 'Volvo'
    }

    # Special handling configurations
    CHASSIS_BASED_MANUFACTURERS = {'BMW', 'MINI'}
    MODEL_DESIGNATION_MANUFACTURERS = {
        'MERCEDES-BENZ'  # Removed LAMBORGHINI since it uses years like Audi
    }

    # Manufacturers that use year ranges in their model names
    YEAR_RANGE_MANUFACTURERS = {'AUDI', 'BENTLEY', 'LAMBORGHINI'}  # Added LAMBORGHINI since it uses model-attached ranges

    # Manufacturers that use special year range formats (e.g., "2021~" or "~2020", "2021-", "2018-2019")
    YEAR_RANGE_FORMAT_MANUFACTURERS = {'TESLA', 'JAGUAR', 'LAND ROVER'}  # Added LAND ROVER

    # Manufacturers that don't use years (only models with their ranges in the model name)
    NO_YEAR_MANUFACTURERS = {'PORSCHE', 'MERCEDES-BENZ'}

    # Special models that use model codes instead of years
    MODEL_CODE_MODELS = {
        'LEXUS': {
            'IS500': 'model_code',
            'LC500': 'model_code',
            'LC500c': 'model_code'
        }
    }

    # List of manufacturers to scrape
    MANUFACTURERS = [
        'ACURA', 'ALFA ROMEO', 'AUDI', 'BENTLEY', 'BMW',
        'BUICK', 'CADILLAC', 'CHEVROLET', 'CHRYSLER', 'DODGE', 'FIAT',
        'FORD', 'GENESIS', 'GMC', 'HONDA', 'HYUNDAI', 'INFINITI', 'JAGUAR', 'JEEP',
        'KIA', 'LAMBORGHINI', 'LAND ROVER', 'LEXUS', 'LINCOLN', 'MASERATI',
        'MAZDA', 'MERCEDES-BENZ', 'MINI', 'MITSUBISHI', 'NISSAN',
        'PORSCHE', 'RAM', 'SUBARU', 'TESLA', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO'
    ]

    # Preferred regions in order of priority
    PREFERRED_REGIONS = [
        'CANADA', 'USA', 'North America', 'MMNA', 
        'GENERAL', 'US', 'EU', 'JP'
    ]
    
    # Region designations to exclude
    EXCLUDED_REGIONS = [
        'Japan', 'Europe', 'Korea', 'Asia', 'Africa', 'Oceania', 
        'South America', 'Far East', 'EUR', 'EXP', 'JAPAN', 'MMAL', 
        'LD', 'EU', 'JP', 'CN', 'EN', 'TH', 'IN'
    ]

    def __init__(self):
        self.debug_dir = "model_scraper_debug"
        self.results_dir = "model_scraper_results"
        self.results = {}
        self.ensure_directories()
        self.browser = None
        self.context = None
        self.page = None
        
    def ensure_directories(self):
        """Ensure the debug and results directories exist."""
        directories = [self.debug_dir, self.results_dir]
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

    async def capture_debug_info(self, page, step_name):
        """Capture debug information including screenshot and HTML."""
        try:
            safe_step_name = self.sanitize_step_name(step_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Capture screenshot
            screenshot_path = os.path.join(self.debug_dir, f"screenshot_{safe_step_name}_{timestamp}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Capture HTML
            html_path = os.path.join(self.debug_dir, f"page_source_{safe_step_name}_{timestamp}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(await page.content())
            
            logger.info(f"Captured debug info for: {safe_step_name}")
        except Exception as e:
            logger.error(f"Failed to capture debug info for '{step_name}': {e}")

    @staticmethod
    def sanitize_step_name(step_name):
        """Sanitize step name for file system use."""
        return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in step_name)

    def get_website_make(self, database_make):
        """Convert database make to website-specific make format."""
        website_make = self.MAKE_MAPPINGS.get(database_make)
        if not website_make:
            logger.error(f"Unsupported make: {database_make}")
            return None
        logger.info(f"Converted database make '{database_make}' to website make '{website_make}'")
        return website_make

    async def select_make(self, page, make):
        """Select a make from the dropdown."""
        try:
            # Click the main Make/Model/Year input to open the panel
            main_dropdown = await page.wait_for_selector("input[placeholder='Make/Model/Year']", timeout=3000)
            await main_dropdown.click()
            
            # Handle Make selection
            logger.info(f"Selecting Make: {make}")
            
            # For Mercedes-Benz, use a more precise selector
            if make == 'Mercedes Benz':
                # Try multiple selectors for Mercedes Benz
                selectors = [
                    "//li[text()='Mercedes Benz']",  # Exact match for Mercedes Benz
                    "//li[normalize-space(text())='Mercedes Benz']",  # Normalized space match
                    "//li[contains(text(), 'Mercedes') and not(contains(text(), 'LD'))]"  # Contains Mercedes but not LD
                ]
                
                make_element = None
                for selector in selectors:
                    try:
                        logger.info(f"Trying Mercedes Benz selector: {selector}")
                        make_element = await page.wait_for_selector(selector, timeout=2000)
                        if make_element:
                            logger.info(f"Found Mercedes Benz element with selector: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue
                
                if not make_element:
                    # If no selector worked, try to find all visible makes to help debug
                    visible_makes = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('li'))
                            .filter(el => el.offsetParent !== null)
                            .map(el => el.textContent.trim())
                            .filter(text => text.includes('Mercedes'));
                    }""")
                    logger.error(f"Could not find Mercedes Benz make. Visible Mercedes options: {visible_makes}")
                    return False
            else:
                make_selector = f"text={make}"
                make_element = await page.wait_for_selector(make_selector, timeout=3000)
            
            if not make_element:
                logger.error(f"Could not find Make option: {make}")
                return False
            
            # Click the make element
            await make_element.click()
            logger.info(f"Clicked on make: {make}")
            
            # Wait for the model dropdown to appear using a more reliable selector
            try:
                # Wait for either the model dropdown or model list to be visible
                model_visible = await page.wait_for_selector("""
                    .dropbox.level2:visible, 
                    .model-list:visible, 
                    .model-column:visible
                """, timeout=2000)  # Reduced timeout since this should appear quickly after make selection
                
                if model_visible:
                    logger.info("Model dropdown/list is visible")
                    return True
                
            except Exception as e:
                logger.warning(f"Initial model dropdown check failed: {e}")
            
            # If we reach here, the dropdown might need a moment to load
            await page.wait_for_timeout(500)  # Reduced from 1000ms to 500ms
            
            # One final check before giving up
            is_visible = await page.evaluate("""() => {
                const modelElements = [
                    document.querySelector('.dropbox.level2'),
                    document.querySelector('.model-list'),
                    document.querySelector('.model-column')
                ].filter(el => el !== null);
                
                return modelElements.some(el => 
                    window.getComputedStyle(el).display !== 'none' &&
                    el.offsetParent !== null
                );
            }""")
            
            if is_visible:
                logger.info("Model selection area found on final check")
                return True
            
            logger.error("Model dropdown/list not visible after all attempts")
            await self.capture_debug_info(page, f"make_selection_error_{make}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to select make '{make}': {e}")
            await self.capture_debug_info(page, f"make_selection_error_{make}")
            return False

    async def get_available_models(self, page, manufacturer):
        """Get all available models for a manufacturer."""
        try:
            logger.info(f"Getting models for: {manufacturer}")
            
            # FIRST APPROACH: Check if models are displayed in a table format
            logger.info("Checking if models are displayed in table format...")
            
            # Look specifically for the Models column/section
            table_models = await page.evaluate("""() => {
                // Look specifically for the Models column/section
                const modelSection = document.querySelector('.model-column, .model-list, table.models-table');
                if (!modelSection) {
                    // Try more specific selectors based on the HTML structure
                    const modelHeading = Array.from(document.querySelectorAll('h3.title'))
                        .find(el => el.textContent.trim() === 'Model');
                    
                    if (modelHeading) {
                        // Get the parent container that holds models
                        const container = modelHeading.closest('.dropbox') || 
                                          modelHeading.nextElementSibling;
                        
                        if (container) {
                            return Array.from(container.querySelectorAll('li'))
                                .map(el => el.textContent.trim())
                                .filter(text => text.length > 0);
                        }
                    }
                } else {
                    return Array.from(modelSection.querySelectorAll('li, td'))
                        .map(el => el.textContent.trim())
                        .filter(text => text.length > 0);
                }
                
                return [];
            }""")
            
            logger.info(f"Found {len(table_models)} potential models in table format: {table_models}")
            
            if table_models and len(table_models) > 0:
                logger.info("Using models from table format instead of dropdown")
                
                # Filter out any non-model items that might have been picked up
                filtered_models = []
                for model in table_models:
                    # Skip common non-model text
                    if any(skip in model.upper() for skip in ['SUPPORT', 'VIDEO', 'DOWNLOADS', 'CONTACT', 'PRODUCTS']):
                        continue
                    
                    # For Audi and Volkswagen, only include models with USA/CAN in their name
                    if manufacturer in {'AUDI', 'VOLKSWAGEN'}:
                        if not ('USA' in model or 'CAN' in model):
                            logger.debug(f"Skipping non-USA/CAN {manufacturer} model: {model}")
                            continue
                    
                    # For Mercedes-Benz, skip models from Mercedes-Benz LD
                    if manufacturer == 'MERCEDES-BENZ' and 'LD' in model:
                        logger.debug(f"Skipping Mercedes-Benz LD model: {model}")
                        continue
                    
                    # For Jeep, Ram, Dodge, and Chrysler, skip models with parentheses
                    if manufacturer in {'JEEP', 'RAM', 'DODGE', 'CHRYSLER'}:
                        if '(' in model and ')' in model:
                            logger.debug(f"Skipping {manufacturer} model with parentheses: {model}")
                            continue
                    
                    # For regular models, check if it matches common patterns
                    if (re.match(r'^[A-Z0-9].*', model) and  # Starts with letter or number
                          len(model) >= 2):  # At least 2 characters long
                        filtered_models.append(model)
                
                if filtered_models:
                    logger.info(f"Filtered to {len(filtered_models)} models: {filtered_models}")
                    return filtered_models
            
            # SECOND APPROACH: If we didn't find models in table format, check for dropdown
            logger.info("Table format not found or no valid models. Checking dropdown format...")
            
            # First, check if the dropdown exists
            dropdown_exists = await page.evaluate("""() => {
                return document.querySelector('.dropbox.level2') !== null;
            }""")
            
            if not dropdown_exists:
                logger.error("Models dropdown (.dropbox.level2) does not exist in the DOM")
                await self.capture_debug_info(page, f"{manufacturer}_models_dropdown_missing")
                return []
            
            # Wait for the dropdown to be visible
            try:
                is_visible = await page.evaluate("""() => {
                    const dropdown = document.querySelector('.dropbox.level2');
                    if (!dropdown) return false;
                    return dropdown.offsetParent !== null && 
                           window.getComputedStyle(dropdown).display !== 'none' &&
                           window.getComputedStyle(dropdown).visibility !== 'hidden';
                }""")
                
                logger.info(f"Models dropdown visible: {is_visible}")
                
                if not is_visible:
                    logger.info("Waiting for models to appear...")
                    await page.wait_for_timeout(5000)
                    
                    # Try to find model list items directly
                    model_items_exist = await page.evaluate("""() => {
                        const modelList = document.querySelector('.dropbox.level2 ul');
                        return modelList && modelList.querySelectorAll('li').length > 0;
                    }""")
                    
                    logger.info(f"Model list items exist: {model_items_exist}")
                    
                    if not model_items_exist:
                        logger.warning("Model dropdown may be present but has no items")
                        await self.capture_debug_info(page, f"{manufacturer}_models_empty")
            except Exception as e:
                logger.warning(f"Error checking model dropdown visibility: {e}")
            
            # Get all visible model options - specifically from the level2 dropdown
            # Adjust the query to work even if the dropdown isn't fully visible
            models = await page.evaluate("""() => {
                // First try to get the dropdown
                const modelsDropdown = document.querySelector('.dropbox.level2');
                if (!modelsDropdown) return [];
                
                // Get the UL element that's a direct child of the level2 dropdown
                const modelList = modelsDropdown.querySelector('ul');
                if (!modelList) return [];
                
                // Get all LI elements, even if they might not be visible
                return Array.from(modelList.querySelectorAll('li'))
                    .map(el => ({
                        text: el.textContent.trim(),
                        isVisible: el.offsetParent !== null
                    }))
                    .filter(item => 
                        item.text.length > 0 && 
                        !item.text.includes('PRODUCTS') && 
                        !item.text.includes('Contact Us')
                    )
                    .map(item => item.text);
            }""")
            
            logger.info(f"Raw models found (may include hidden items): {len(models)}")
            
            # Filter models based on manufacturer
            filtered_models = []
            for model in models:
                # Skip common non-model text
                if any(skip in model.upper() for skip in ['SUPPORT', 'VIDEO', 'DOWNLOADS', 'CONTACT', 'PRODUCTS']):
                    continue
                
                # For Audi and Volkswagen, only include models with USA/CAN in their name
                if manufacturer in {'AUDI', 'VOLKSWAGEN'}:
                    if not ('USA' in model or 'CAN' in model):
                        logger.debug(f"Skipping non-USA/CAN {manufacturer} model: {model}")
                        continue
                
                # For Jeep, Ram, Dodge, and Chrysler, skip models with parentheses
                if manufacturer in {'JEEP', 'RAM', 'DODGE', 'CHRYSLER'}:
                    if '(' in model and ')' in model:
                        logger.debug(f"Skipping {manufacturer} model with parentheses: {model}")
                        continue
                
                filtered_models.append(model)
            
            if filtered_models:
                logger.info(f"Found {len(filtered_models)} models for {manufacturer}")
                for model in filtered_models:
                    logger.info(f"- {model}")
                return filtered_models
            else:
                logger.warning(f"No models found for {manufacturer}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting models for {manufacturer}: {e}")
            await self.capture_debug_info(page, f"{manufacturer}_get_models_error")
            return []

    async def select_model(self, page, model):
        """Select a model from the list."""
        try:
            logger.info(f"Selecting model: {model}")
            
            # First, check if we're already in a table view with models visible
            is_table_view = await page.evaluate("""(modelName) => {
                // Check if there's a table or list of models visible
                const tableElements = document.querySelectorAll('table td, div.model-list li, .model-column li');
                
                if (tableElements.length > 0) {
                    // For MINI, find the second instance since the first is the manufacturer
                    if (modelName === 'MINI') {
                        const miniElements = Array.from(tableElements)
                            .filter(el => el.textContent.trim() === modelName);
                        return miniElements.length >= 2;  // We need at least 2 MINI elements
                    }
                    
                    // For other manufacturers, look for exact match
                    for (const el of tableElements) {
                        if (el.textContent.trim() === modelName) {
                            return true;
                        }
                    }
                }
                
                return false;
            }""", model)
            
            logger.info(f"Is table view with models: {is_table_view}")
            
            if is_table_view:
                # Try clicking on the model in the table view
                logger.info("Using table view mode to select model")
                
                # For MINI, use specific handling to click the second instance
                if model == 'MINI':
                    clicked = await page.evaluate("""() => {
                        const miniElements = Array.from(document.querySelectorAll('table td, div.model-list li, .model-column li'))
                            .filter(el => el.textContent.trim() === 'MINI' && 
                                        !el.closest('.manufacturer') &&
                                        !el.closest('.make-list'));
                        
                        if (miniElements.length >= 1) {
                            // Click the last MINI element (should be the model, not the make)
                            miniElements[miniElements.length - 1].click();
                            return true;
                        }
                        return false;
                    }""")
                    
                    if clicked:
                        logger.info("Successfully clicked MINI model")
                        await page.wait_for_timeout(2000)
                        return True
                    else:
                        logger.warning("Could not find MINI model to click")
                        return False
                
                # For other manufacturers, use the existing logic
                selectors = [
                    f"table td:has-text('{model}')",
                    f"div.model-list li:has-text('{model}')",
                    f".model-column li:has-text('{model}')",
                    f"//td[contains(text(), '{model}')]",
                    f"//li[contains(text(), '{model}')]",
                    f"//*[text()='{model}']"
                ]
                
                clicked = False
                for selector in selectors:
                    try:
                        logger.info(f"Trying to click model with selector: {selector}")
                        # Only wait 1 second for each selector to avoid long timeouts
                        element = page.locator(selector).first
                        if await element.count() > 0:
                            await element.click()
                            logger.info(f"Successfully clicked model {model} in table view")
                            clicked = True
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                
                if not clicked:
                    # Try JavaScript click as a last resort
                    logger.info("Trying JavaScript click on model")
                    clicked = await page.evaluate("""(modelName) => {
                        // For MINI, find the first model element that's not a manufacturer
                        if (modelName === 'MINI') {
                            const elements = Array.from(document.querySelectorAll('li'))
                                .filter(el => 
                                    el.textContent.trim() === modelName && 
                                    !el.closest('.manufacturer') &&
                                    !el.closest('.make-list')
                                );
                            
                            if (elements.length > 0) {
                                elements[0].click();
                                return true;
                            }
                            return false;
                        }
                        
                        // For other manufacturers, find exact match
                        const elements = Array.from(document.querySelectorAll('*'))
                            .filter(el => el.textContent.trim() === modelName);
                            
                        if (elements.length > 0) {
                            elements[0].click();
                            return true;
                        }
                        return false;
                    }""", model)
                    
                    if clicked:
                        logger.info(f"Successfully clicked model {model} with JavaScript")
                    else:
                        logger.warning(f"Could not click model {model} in table view")
                
                await page.wait_for_timeout(2000)  # Wait for model selection to take effect
                return True
            
            # SECOND APPROACH: Try the dropdown selector
            logger.info("Trying dropdown selector for model")
            
            # Update selector to be more specific - target li elements that are children of ul inside .dropbox.level2
            selector = f".dropbox.level2 > ul > li:has-text('{model}')"
            logger.info(f"Using selector: {selector}")
            
            # Wait for the element to be visible
            try:
                await page.wait_for_selector(selector, timeout=5000)
                await page.click(selector)
                logger.info(f"Successfully clicked model {model} in dropdown")
                await page.wait_for_timeout(2000)  # Wait for Year/Chassis panel to appear
                return True
            except Exception as e:
                logger.warning(f"Failed to click model with dropdown selector: {e}")
                
                # Try a more general selector as fallback
                try:
                    logger.info("Trying more general selector as fallback")
                    await page.click(f"text={model}")
                    logger.info(f"Successfully clicked model {model} with text selector")
                    await page.wait_for_timeout(2000)
                    return True
                except Exception as e2:
                    logger.error(f"Failed to select model '{model}' with all methods: {e2}")
                    return False
        except Exception as e:
            logger.error(f"Failed to select model '{model}': {e}")
            await self.capture_debug_info(page, f"model_selection_error_{model}")
            return False

    async def extract_years_from_model(self, model):
        """Extract years from model name for manufacturers that include year ranges."""
        try:
            # Extract year patterns from model name
            # Patterns like "2019>", "2013-2020", "2008-", "-2020"
            year_patterns = [
                r'(\d{4})\s*>', # "2019>"
                r'(\d{4})\s*-\s*(\d{4})', # "2013-2020"
                r'(\d{4})\s*-', # "2008-"
                r'-\s*(\d{4})', # "-2020"
                r'(\d{4})' # Just a year
            ]
            
            years = []
            for pattern in year_patterns:
                matches = re.finditer(pattern, model)
                for match in matches:
                    # Get all capturing groups from the match
                    found_years = [int(y) for y in match.groups() if y]
                    years.extend(found_years)
            
            if years:
                # Remove duplicates and sort in descending order
                years = sorted(list(set(years)), reverse=True)
                logger.info(f"Extracted years from model {model}: {years}")
                return [str(year) for year in years]
            
            return []
        except Exception as e:
            logger.error(f"Error extracting years from model {model}: {e}")
            return []

    async def get_years_or_chassis(self, page, manufacturer, model):
        """Get all available years or chassis for a model."""
        try:
            logger.info(f"Getting years/chassis for {manufacturer} - {model}")
            
            # Check if this is a special Lexus model that uses model codes
            if manufacturer == 'LEXUS' and model in self.MODEL_CODE_MODELS['LEXUS']:
                logger.info(f"Special Lexus model {model} detected - looking for model code instead of year")
                try:
                    # Click the Year/System dropdown as we still need to open it
                    year_system_selector = "input[placeholder='Year/System']"
                    year_system_element = await page.wait_for_selector(year_system_selector, timeout=5000)
                    if year_system_element:
                        await year_system_element.click()
                        logger.info("Clicked Year/System dropdown")
                        await page.wait_for_timeout(1000)  # Wait for dropdown to open
                    
                    # Look for three-letter model codes
                    model_codes = await page.evaluate("""() => {
                        const elements = document.querySelectorAll('.dropbox.level3 li, table td');
                        return Array.from(elements)
                            .map(el => el.textContent.trim())
                            .filter(text => /^[A-Z]{3}$/.test(text));  // Match exactly three uppercase letters
                    }""")
                    
                    if model_codes:
                        logger.info(f"Found model codes for {model}: {model_codes}")
                        return model_codes
                    else:
                        logger.warning(f"No model codes found for Lexus {model}")
                        return []
                except Exception as e:
                    logger.error(f"Error getting model code for Lexus {model}: {e}")
                    return []
            
            # If manufacturer doesn't use years, return empty list
            if manufacturer in self.NO_YEAR_MANUFACTURERS:
                logger.info(f"Skipping year/chassis for {manufacturer} as it doesn't use years")
                return []
            
            # For Toyota and Lexus, we need to click the Year/System dropdown first
            if manufacturer in {'TOYOTA', 'LEXUS'}:
                try:
                    # Click the Year/System dropdown
                    year_system_selector = "input[placeholder='Year/System']"
                    year_system_element = await page.wait_for_selector(year_system_selector, timeout=5000)
                    if year_system_element:
                        await year_system_element.click()
                        logger.info("Clicked Year/System dropdown")
                        await page.wait_for_timeout(1000)  # Wait for dropdown to open
                except Exception as e:
                    logger.error(f"Failed to click Year/System dropdown: {e}")
            
            # Determine what type of data we're looking for based on manufacturer
            is_chassis_based = manufacturer in self.CHASSIS_BASED_MANUFACTURERS
            is_model_designation = manufacturer in self.MODEL_DESIGNATION_MANUFACTURERS
            is_year_range_format = manufacturer in self.YEAR_RANGE_FORMAT_MANUFACTURERS
            
            data_type = "chassis" if is_chassis_based else "model designation" if is_model_designation else "year"
            logger.info(f"Looking for {data_type} data")
            
            # FIRST APPROACH: Check if data is displayed in a table format
            logger.info(f"Checking if {data_type} is displayed in table format...")
            
            # Look for elements based on the data type
            table_data = await page.evaluate("""(dataType) => {
                // First try to find the specific section by heading
                const headings = Array.from(document.querySelectorAll('h3.title, th, td:first-child'))
                    .filter(el => el.textContent.trim().toUpperCase() === dataType.toUpperCase());
                
                let container = null;
                
                if (headings.length > 0) {
                    // Get the parent or next element that contains the data
                    container = headings[0].closest('.dropbox') || 
                              headings[0].closest('table') ||
                              headings[0].nextElementSibling;
                } else {
                    // If no heading found, try common containers
                    container = document.querySelector('.dropbox.level3') ||
                              document.querySelector('table') ||
                              document.querySelector('.model-list');
                }
                
                if (!container) return [];
                
                // Get all potential data elements
                const elements = container.querySelectorAll('li, td');
                return Array.from(elements)
                    .map(el => el.textContent.trim())
                    .filter(text => text.length > 0);
            }""", data_type)
            
            logger.info(f"Found {len(table_data)} potential {data_type} entries in table format: {table_data}")
            
            if table_data and len(table_data) > 0:
                logger.info(f"Using {data_type} from table format")
                
                # Filter based on the type of data we're looking for
                filtered_data = []
                for item in table_data:
                    if is_chassis_based:
                        # For BMW/MINI chassis codes (e.g., F30, G20)
                        if re.match(r'^[A-Z][0-9]{2}$', item):
                            filtered_data.append(item)
                    elif is_model_designation:
                        # For model designations (e.g., "2017-2023", "2020>", etc.)
                        if (re.match(r'^(19|20)\d{2}[-~]\d{4}$', item) or  # Year range
                            re.match(r'^(19|20)\d{2}[>~]?$', item) or      # Single year with optional >
                            re.match(r'^[~<]?(19|20)\d{2}$', item) or      # Single year with optional <
                            re.match(r'^.*\((19|20)\d{2}.*\)$', item)):    # Year in parentheses
                            filtered_data.append(item)
                    elif is_year_range_format:
                        # For Tesla/Land Rover/Jaguar-style year ranges
                        if manufacturer in {'TESLA', 'LAND ROVER'}:
                            if (re.match(r'^(19|20)\d{2}[-~]$', item) or      # "2021-" or "2021~" format
                                re.match(r'^[-~](19|20)\d{2}$', item) or      # "-2020" or "~2020" format
                                re.match(r'^(19|20)\d{2}-(19|20)\d{2}$', item)):  # "2017-2019" format
                                filtered_data.append(item)
                        elif manufacturer == 'JAGUAR':
                            if (re.match(r'^(19|20)\d{2}-$', item) or          # "2021-" format
                                re.match(r'^(19|20)\d{2}-(19|20)\d{2}$', item) or  # "2018-2019" format
                                re.match(r'^(19|20)\d{2}$', item)):            # Single year
                                filtered_data.append(item)
                    else:
                        # For regular years (4 digits between 1900-2100)
                        year_match = re.match(r'^(19|20)\d{2}(?:\s*\([A-Z]\))?$', item)
                        if year_match and not re.search(r'(SUPPORT|VIDEO|DOWNLOADS)', item.upper()):
                            filtered_data.append(item)
                
                logger.info(f"Filtered to {len(filtered_data)} valid {data_type} entries: {filtered_data}")
                
                # Sort years in descending order if they're numeric
                if filtered_data and not is_chassis_based:
                    if is_year_range_format:
                        if manufacturer in {'TESLA', 'LAND ROVER'}:
                            # Sort Tesla/Land Rover-style year ranges with "later" years first
                            filtered_data.sort(key=lambda x: (
                                int(re.search(r'(19|20)\d{2}', x).group(0)),  # Extract year
                                '-' in x or '~' in x  # Put ranges first
                            ), reverse=True)
                        elif manufacturer == 'JAGUAR':
                            # Sort Jaguar-style year ranges
                            filtered_data.sort(key=lambda x: (
                                int(re.search(r'(19|20)\d{2}', x).group(0)),  # Extract first year
                                '-' in x  # Put ranges first
                            ), reverse=True)
                    else:
                        # Sort by the year part
                        filtered_data.sort(key=lambda x: int(re.match(r'^(19|20\d{2})', x).group(0)), reverse=True)
                    logger.info(f"Sorted years in descending order: {filtered_data}")
                
                return filtered_data
            
            # SECOND APPROACH: If we didn't find data in table format, check for dropdown
            logger.info(f"Table format not found or no valid {data_type}. Checking dropdown format...")
            
            # First try to check if the dropdown exists
            dropdown_exists = await page.evaluate("""() => {
                return document.querySelector('.dropbox.level3') !== null;
            }""")
            
            if not dropdown_exists:
                logger.error(f"{data_type} dropdown (.dropbox.level3) does not exist in the DOM")
                await self.capture_debug_info(page, f"{manufacturer}_{model}_{data_type}_dropdown_missing")
                return []
            
            # Give it a moment to stabilize
            await page.wait_for_timeout(2000)
            
            # Wait for the dropdown to be visible
            try:
                is_visible = await page.evaluate("""() => {
                    const dropdown = document.querySelector('.dropbox.level3');
                    if (!dropdown) return false;
                    return dropdown.offsetParent !== null && 
                           window.getComputedStyle(dropdown).display !== 'none' &&
                           window.getComputedStyle(dropdown).visibility !== 'hidden';
                }""")
                
                logger.info(f"{data_type} dropdown visible: {is_visible}")
                
                if not is_visible:
                    logger.info(f"Waiting for {data_type} to appear...")
                    await page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"Error checking {data_type} dropdown visibility: {e}")
            
            # Get all options from the dropdown
            options = await page.evaluate("""() => {
                const dropdown = document.querySelector('.dropbox.level3');
                if (!dropdown) return [];
                
                // Try to find all year elements
                const yearElements = dropdown.querySelectorAll('li');
                return Array.from(yearElements)
                    .map(el => el.textContent.trim())
                    .filter(text => text.length > 0 && /^(19|20)\d{2}/.test(text));
            }""")
            
            # Filter and sort the years
            filtered_options = []
            for item in options:
                if re.match(r'^(19|20)\d{2}', item) and not re.search(r'(SUPPORT|VIDEO|DOWNLOADS)', item.upper()):
                    filtered_options.append(item)
            
            if filtered_options:
                # Sort years in descending order
                filtered_options.sort(reverse=True)
                logger.info(f"Found {len(filtered_options)} valid years for {manufacturer} - {model}")
                for option in filtered_options:
                    logger.info(f"- {option}")
                return filtered_options
            else:
                logger.warning(f"No valid years found for {manufacturer} - {model}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting years for {manufacturer} - {model}: {e}")
            await self.capture_debug_info(page, f"{manufacturer}_{model}_get_years_error")
            return []

    async def interact_with_dropdown(self, page, identifying_text, option_text, need_to_open=True):
        """Interact with a dropdown element."""
        try:
            logger.info(f"Interacting with dropdown: '{identifying_text}' to select '{option_text}'")
            
            # Wait for and click the dropdown toggle
            dropdown_selector = f"input[placeholder='{identifying_text}']"
            dropdown = await page.wait_for_selector(dropdown_selector, timeout=10000)
            
            if need_to_open:
                await dropdown.click()
                await page.wait_for_timeout(1000)  # Wait for dropdown to open
            
            # First, wait for the dropdown list to be visible
            try:
                # Wait for any dropdown list container to appear
                await page.wait_for_selector("ul:visible, .dropbox ul:visible, .dropdown ul:visible", timeout=5000)
                logger.info("Dropdown list container is visible")
            except Exception as e:
                logger.error(f"Could not find visible dropdown list: {e}")
            
            # Try different selectors for the option, prioritizing li elements
            selectors = [
                f"//ul//li[normalize-space(text())='{option_text}']",  # Exact match within ul
                f"//ul//li[contains(text(), '{option_text}')]",        # Contains match within ul
                f"//div[contains(@class, 'dropbox')]//li[contains(text(), '{option_text}')]"  # Backup selector
            ]
            
            option_found = False
            for selector in selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # Verify this is the correct element before clicking
                        element_info = await page.evaluate("""(element) => {
                            return {
                                tagName: element.tagName,
                                textContent: element.textContent.trim(),
                                className: element.className,
                                id: element.id,
                                isVisible: element.offsetParent !== null,
                                parentElement: {
                                    tagName: element.parentElement ? element.parentElement.tagName : '',
                                    className: element.parentElement ? element.parentElement.className : '',
                                    id: element.parentElement ? element.parentElement.id : ''
                                }
                            }
                        }""", element)
                        
                        # Only proceed if this is actually a list item with the exact text we want
                        if (element_info['tagName'] == 'LI' and 
                            element_info['textContent'] == option_text and 
                            element_info['isVisible']):
                            
                            logger.info(f"Found matching element:")
                            logger.info(f"- Tag: {element_info['tagName']}")
                            logger.info(f"- Text: {element_info['textContent']}")
                            logger.info(f"- Class: {element_info['className']}")
                            logger.info(f"- Parent: {element_info['parentElement']['tagName']} (class: {element_info['parentElement']['className']})")
                            
                            # Ensure element is in view and click it
                            await element.scroll_into_view_if_needed()
                            await element.click()
                            option_found = True
                            logger.info(f"Successfully clicked option using selector: {selector}")
                            break
                        else:
                            logger.info(f"Found element but it doesn't match our criteria: {element_info}")
                            continue
                            
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not option_found:
                # If no selector worked, try to get all visible text to help debug
                visible_text = await page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('ul li'))
                        .filter(el => el.offsetParent !== null)
                        .map(el => ({
                            tag: el.tagName,
                            text: el.textContent.trim(),
                            class: el.className,
                            id: el.id,
                            parentTag: el.parentElement ? el.parentElement.tagName : ''
                        }))
                        .filter(item => item.text.length > 0);
                }""")
                logger.info("Visible list items on page:")
                for item in visible_text:
                    logger.info(f"- {item['tag']} in {item['parentTag']}: {item['text']} (class: {item['class']}, id: {item['id']})")
                
                raise Exception(f"Could not find option '{option_text}' with any selector")
            
            # Wait for selection to be applied
            await page.wait_for_timeout(1000)
            return True
            
        except Exception as e:
            logger.error(f"Failed to interact with dropdown '{identifying_text}': {e}")
            await self.capture_debug_info(page, f"dropdown_error_{identifying_text}")
            return False

    async def process_manufacturer(self, manufacturer):
        """Process all models and years for a specific manufacturer."""
        logger.info(f"===== Processing Manufacturer: {manufacturer} =====")
        
        try:
            # Check if we already have results for this manufacturer
            results_file = os.path.join(self.results_dir, f"{manufacturer}_results.json")
            existing_results = {}
            if os.path.exists(results_file):
                try:
                    with open(results_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if manufacturer in existing_data:
                            existing_results = existing_data[manufacturer]
                            logger.info(f"Found existing results for {manufacturer}")
                except Exception as e:
                    logger.warning(f"Error reading existing results for {manufacturer}: {e}")
            
            # Convert manufacturer name to website format
            website_make = self.get_website_make(manufacturer)
            if not website_make:
                logger.error(f"Unsupported manufacturer: {manufacturer}")
                return
            
            # Launch a new browser for each manufacturer
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(headless=False)
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                
                try:
                    # Navigate to the target URL
                    await self.page.goto("https://www.maxisysadas.com/getCoverage.jspx")
                    await self.capture_debug_info(self.page, f"{manufacturer}_initial_page_load")
                    
                    # Wait for page to be fully loaded
                    await self.page.wait_for_load_state("networkidle")
                    
                    # Select Product type using the interact_with_dropdown method
                    if not await self.interact_with_dropdown(self.page, "Product type", "MA600", True):
                        logger.error("Failed to select product type MA600")
                        return
                    
                    # Select the manufacturer
                    if not await self.select_make(self.page, website_make):
                        logger.error(f"Failed to select make: {website_make}")
                        return
                    
                    # Get all available models
                    models = await self.get_available_models(self.page, manufacturer)
                    
                    # Initialize manufacturer data in results, preserving existing data
                    if manufacturer not in self.results:
                        self.results[manufacturer] = {"models": {}}
                    if existing_results and "models" in existing_results:
                        self.results[manufacturer]["models"].update(existing_results["models"])
                    
                    logger.info(f"Processing {len(models)} models for {manufacturer}")
                    
                    # For each model, get years/chassis
                    for model_index, model in enumerate(models):
                        # Skip if we already have data for this model and it's not empty
                        if (model in self.results[manufacturer]["models"] and 
                            self.results[manufacturer]["models"][model] and 
                            (("years" in self.results[manufacturer]["models"][model] and 
                              self.results[manufacturer]["models"][model]["years"]) or
                             ("chassis" in self.results[manufacturer]["models"][model] and 
                              self.results[manufacturer]["models"][model]["chassis"]) or
                             ("model_designation" in self.results[manufacturer]["models"][model] and 
                              self.results[manufacturer]["models"][model]["model_designation"]))):
                            logger.info(f"Skipping model {model} - already have data")
                            continue
                        
                        logger.info(f"Processing model {model_index+1}/{len(models)}: {model}")
                        
                        try:
                            # Create a new page for each model to ensure a clean state
                            model_page = await self.context.new_page()
                            await model_page.goto("https://www.maxisysadas.com/getCoverage.jspx")
                            await model_page.wait_for_load_state("networkidle")
                            
                            # Select Product type again using the interact_with_dropdown method
                            if not await self.interact_with_dropdown(model_page, "Product type", "MA600", True):
                                logger.error(f"Failed to select product type MA600 for model {model}")
                                continue
                            
                            # Select the manufacturer again
                            if not await self.select_make(model_page, website_make):
                                logger.error(f"Failed to select make for model {model}")
                                continue
                            
                            # Select the model
                            if not await self.select_model(model_page, model):
                                logger.error(f"Failed to select model: {model}")
                                continue
                            
                            # Get years or chassis
                            data = await self.get_years_or_chassis(model_page, manufacturer, model)
                            
                            # Determine the data type based on manufacturer
                            if manufacturer in self.CHASSIS_BASED_MANUFACTURERS:
                                data_type = "chassis"
                            elif manufacturer in self.MODEL_DESIGNATION_MANUFACTURERS:
                                data_type = "model_designation"
                            else:
                                data_type = "years"
                            
                            # Store in results - even if empty, so we know we processed it
                            self.results[manufacturer]["models"][model] = {
                                data_type: data
                            }
                            
                            logger.info(f"Successfully stored {len(data)} {data_type} for model {model}")
                            
                            # Clean up
                            await model_page.close()
                            
                            # Save interim results after each model to avoid losing data
                            if model_index % 5 == 0 or model_index == len(models) - 1:
                                self.save_results(manufacturer)
                                logger.info(f"Saved interim results for {manufacturer} after processing {model_index+1}/{len(models)} models")
                            
                            # Add a small delay to avoid overwhelming the server
                            await asyncio.sleep(1)
                        except Exception as model_err:
                            logger.error(f"Error processing model {model}: {model_err}")
                            continue
                    
                    # Save final results for this manufacturer
                    self.save_results(manufacturer)
                    logger.info(f"Completed processing {manufacturer} with {len(self.results[manufacturer]['models'])} models")
                except Exception as e:
                    logger.error(f"Error processing manufacturer {manufacturer}: {e}")
                    await self.capture_debug_info(self.page, f"{manufacturer}_error")
                    # Save whatever results we have so far
                    if manufacturer in self.results and "models" in self.results[manufacturer]:
                        logger.info(f"Saving partial results for {manufacturer} with {len(self.results[manufacturer]['models'])} models")
                        self.save_results(manufacturer)
                finally:
                    # Clean up
                    if self.page:
                        await self.page.close()
                    if self.context:
                        await self.context.close()
                    if self.browser:
                        await self.browser.close()
        except Exception as e:
            logger.error(f"Fatal error processing manufacturer {manufacturer}: {e}")
            # Try to save any partial results
            if manufacturer in self.results:
                self.save_results(manufacturer)

    def save_results(self, manufacturer=None):
        """Save the results to a JSON file."""
        try:
            if manufacturer:
                # Save manufacturer-specific results
                if manufacturer in self.results:
                    filename = os.path.join(self.results_dir, f"{manufacturer}_results.json")
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump({manufacturer: self.results[manufacturer]}, f, indent=2)
                    logger.info(f"Saved results for {manufacturer} to {filename}")
            else:
                # Save all results
                filename = os.path.join(self.results_dir, "all_results.json")
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, indent=2)
                logger.info(f"Saved all results to {filename}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    async def run(self):
        """Run the scraper for all manufacturers."""
        start_time = time.time()
        logger.info("Starting Model/Year scraper")
        
        # Process each manufacturer
        for manufacturer in self.MANUFACTURERS:
            try:
                await self.process_manufacturer(manufacturer)
            except Exception as e:
                logger.error(f"Failed to process manufacturer {manufacturer}: {e}")
        
        # Save all results at the end
        self.save_results()
        
        end_time = time.time()
        logger.info(f"Scraping completed in {end_time - start_time:.2f} seconds")

async def main():
    scraper = ModelYearScraper()
    await scraper.run()

if __name__ == "__main__":
    asyncio.run(main()) 
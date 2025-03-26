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
        'ALFA ROMEO': 'Alfa Romeo',
        'ASTON MARTIN': 'Aston Martin',
        'AUDI': 'Audi',
        'BENTLEY': 'Bentley',
        'BMW': 'BMW',
        'BUICK': 'Buick',
        'CADILLAC': 'Cadillac',
        'CHEVROLET': 'Chevrolet',
        'CHRYSLER': 'Chrysler',
        'DODGE': 'Dodge',
        'FERRARI': 'Ferrari',
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
        'LOTUS': 'Lotus',
        'MASERATI': 'Maserati',
        'MAZDA': 'Mazda(North America)',
        'MERCEDES-BENZ': 'Mercedes-Benz',
        'MINI': 'MINI',
        'MITSUBISHI': 'Mitsubishi',
        'NISSAN': 'Nissan(North America)',
        'PORSCHE': 'Porsche',
        'RAM': 'RAM',
        'ROLLS-ROYCE': 'Rolls-Royce',
        'SUBARU': 'Subaru(US)',
        'TESLA': 'Tesla',
        'TOYOTA': 'Toyota(USA)',
        'VOLKSWAGEN': 'Volkswagen',
        'VOLVO': 'Volvo'
    }

    # List of manufacturers to scrape
    MANUFACTURERS = [
        'ACURA', 'ALFA ROMEO', 'ASTON MARTIN', 'AUDI', 'BENTLEY', 'BMW',
        'BUICK', 'CADILLAC', 'CHEVROLET', 'CHRYSLER', 'DODGE', 'FERRARI', 'FIAT',
        'FORD', 'GENESIS', 'GMC', 'HONDA', 'HYUNDAI', 'INFINITI', 'JAGUAR', 'JEEP',
        'KIA', 'LAMBORGHINI', 'LAND ROVER', 'LEXUS', 'LINCOLN', 'LOTUS', 'MASERATI',
        'MAZDA', 'MERCEDES-BENZ', 'MINI', 'MITSUBISHI', 'NISSAN',
        'PORSCHE', 'RAM', 'ROLLS-ROYCE', 'SUBARU', 'TESLA', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO'
    ]

    # Preferred regions in order of priority
    PREFERRED_REGIONS = [
        'CANADA', 'USA', 'North America', 'MMNA', 
        'GENERAL', 'US', 'EU', 'JP'
    ]
    
    # Region designations to exclude
    EXCLUDED_REGIONS = [
        'Japan', 'Europe', 'Korea', 'Asia', 'Africa', 'Oceania', 
        'South America', 'Far East', 'EUR', 'EXP', 'JAPAN', 'MMAL', 'MMNA', 
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
            main_dropdown = await page.wait_for_selector("input[placeholder='Make/Model/Year']", timeout=10000)
            await main_dropdown.click()
            await page.wait_for_timeout(1000)  # Wait for panel to open
            
            # Handle Make selection
            logger.info(f"Selecting Make: {make}")
            make_selector = f"text={make}"
            make_element = await page.wait_for_selector(make_selector, timeout=10000)
            if not make_element:
                logger.error(f"Could not find Make option: {make}")
                return False
            
            await make_element.click()
            logger.info(f"Clicked on make: {make}")
            
            # Wait longer for the model panel to appear and stabilize
            await page.wait_for_timeout(3000)
            
            # Check if the model dropdown is visible
            is_model_visible = await page.evaluate("""() => {
                const modelDropdown = document.querySelector('.dropbox.level2');
                return modelDropdown && 
                       window.getComputedStyle(modelDropdown).display !== 'none' &&
                       modelDropdown.offsetParent !== null;
            }""")
            
            logger.info(f"Model dropdown visible after make selection: {is_model_visible}")
            
            if not is_model_visible:
                logger.info("Model dropdown not visible. Trying to click make again.")
                await make_element.click()
                await page.wait_for_timeout(2000)
            
            return True
        except Exception as e:
            logger.error(f"Failed to select make '{make}': {e}")
            await self.capture_debug_info(page, f"make_selection_error_{make}")
            return False

    async def get_available_models(self, page, manufacturer):
        """Get all available models for a manufacturer."""
        try:
            logger.info(f"Getting models for: {manufacturer}")
            
            # FIRST APPROACH: Check if models are displayed in a table format (as seen in the screenshot)
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
                    # Check if this looks like a real model name (e.g., "Acura ILX", "MDX", etc.)
                    if ((" ILX" in model or " MDX" in model or " RDX" in model or " RLX" in model or 
                         " TLX" in model or " ZDX" in model or model in ["ILX", "MDX", "RDX", "RLX", "TLX", "ZDX"]) or
                        # More general model name pattern
                        re.match(r'^[A-Z][a-zA-Z0-9]+([ -][A-Z][a-zA-Z0-9]+)*$', model)):
                        filtered_models.append(model)
                
                if filtered_models:
                    logger.info(f"Filtered to {len(filtered_models)} models: {filtered_models}")
                    return filtered_models
            
            # SECOND APPROACH: If we didn't find models in table format, check for dropdown
            logger.info("Table format not found or no valid models. Checking dropdown format...")
            
            # First, check if the models dropdown exists at all
            dropdown_exists = await page.evaluate("""() => {
                return document.querySelector('.dropbox.level2') !== null;
            }""")
            
            if not dropdown_exists:
                logger.error("Models dropdown (.dropbox.level2) does not exist in the DOM")
                await self.capture_debug_info(page, f"{manufacturer}_models_dropdown_missing")
                return []
            
            # Wait for the models dropdown to be visible with a different approach
            try:
                # First, check if it's immediately visible
                is_visible = await page.evaluate("""() => {
                    const dropdown = document.querySelector('.dropbox.level2');
                    if (!dropdown) return false;
                    return dropdown.offsetParent !== null && 
                           window.getComputedStyle(dropdown).display !== 'none' &&
                           window.getComputedStyle(dropdown).visibility !== 'hidden';
                }""")
                
                logger.info(f"Models dropdown initially visible: {is_visible}")
                
                if not is_visible:
                    # If not visible immediately, wait a bit longer and look for any model list
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
            
            # Get the base manufacturer name without region
            base_manufacturer = manufacturer.split('(')[0] if '(' in manufacturer else manufacturer
            
            # Organize models by region for better selection
            models_by_region = {}
            no_region_models = []
            
            for model in models:
                if '(' in model:
                    # Extract the region part
                    region_start = model.find('(')
                    region_end = model.find(')')
                    if region_start > 0 and region_end > region_start:
                        region = model[region_start+1:region_end]
                        if region not in models_by_region:
                            models_by_region[region] = []
                        models_by_region[region].append(model)
                else:
                    no_region_models.append(model)
            
            # First, check for preferred regions in order
            filtered_models = []
            
            # Start with models that have no region specified
            if no_region_models:
                logger.info(f"Found {len(no_region_models)} models without region specification")
                filtered_models.extend(no_region_models)
            
            # Add models from preferred regions in order of priority
            for region in self.PREFERRED_REGIONS:
                if region in models_by_region:
                    logger.info(f"Adding {len(models_by_region[region])} models from region {region}")
                    filtered_models.extend(models_by_region[region])
            
            # If we still don't have any models, add any that aren't in excluded regions
            if not filtered_models:
                for region, region_models in models_by_region.items():
                    if region not in self.EXCLUDED_REGIONS:
                        logger.info(f"Adding {len(region_models)} models from non-excluded region {region}")
                        filtered_models.extend(region_models)
            
            # Final fallback: if we still have nothing, take all models
            if not filtered_models and models:
                logger.warning(f"No preferred regions found, using all {len(models)} available models")
                filtered_models = models
            
            # Log the models found
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
                    // If there's a specific element with this model, return true - we're in table view
                    for (const el of tableElements) {
                        if (el.textContent.trim() === modelName) {
                            return true;
                        }
                    }
                }
                
                // If no exact match, look for any element containing this model
                const anyModelElement = Array.from(document.querySelectorAll('*'))
                    .find(el => el.textContent.trim() === modelName);
                    
                return !!anyModelElement;
            }""", model)
            
            logger.info(f"Is table view with models: {is_table_view}")
            
            if is_table_view:
                # Try clicking on the model in the table view
                logger.info("Using table view mode to select model")
                
                # Try multiple selectors to find and click the model
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
                        // Find any element with exact model text
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

    async def get_years_or_chassis(self, page, manufacturer, model):
        """Get all available years or chassis for a model."""
        try:
            logger.info(f"Getting years/chassis for {manufacturer} - {model}")
            
            # FIRST APPROACH: Check if years are displayed in a table format
            logger.info("Checking if years/chassis are displayed in table format...")
            
            # Look specifically for year elements under a "Year" heading or with year-related classes
            table_years = await page.evaluate("""() => {
                // First, try to find the Year section specifically
                const yearHeading = Array.from(document.querySelectorAll('h3.title'))
                    .find(el => el.textContent.trim() === 'Year');
                
                if (yearHeading) {
                    // Get the parent or next element that contains the years
                    const yearContainer = yearHeading.closest('.dropbox') || 
                                         yearHeading.nextElementSibling;
                    
                    if (yearContainer) {
                        // Get all year elements from the container
                        return Array.from(yearContainer.querySelectorAll('li'))
                            .map(el => el.textContent.trim())
                            .filter(text => text.length > 0);
                    }
                }
                
                // If we didn't find a clear Year section, try looking for elements with year classes
                const yearElements = document.querySelectorAll('.year, li[class^="20"], li[class*="year"]');
                if (yearElements.length > 0) {
                    return Array.from(yearElements)
                        .map(el => el.textContent.trim())
                        .filter(text => text.length > 0);
                }
                
                // Final fallback: look for elements that match year patterns (4 digits)
                return Array.from(document.querySelectorAll('li, td'))
                    .map(el => el.textContent.trim())
                    .filter(text => 
                        // Only keep items that look like valid years or chassis codes
                        text.length > 0 && 
                        (
                            // Year pattern (4 digits between 1900-2100)
                            /^(19|20)\d{2}$/.test(text) || 
                            // Chassis pattern for BMW (alphanumeric with possible special chars)
                            /^[A-Z][0-9]{2}$/.test(text)
                        )
                    );
            }""")
            
            logger.info(f"Found {len(table_years)} potential years/chassis in table format: {table_years}")
            
            if table_years and len(table_years) > 0:
                logger.info("Using years/chassis from table format")
                
                # Filter to ensure we only have valid years or chassis codes
                filtered_years = []
                for year in table_years:
                    # Keep only valid years (4 digits between 1900-2100) or BMW chassis codes
                    if re.match(r'^(19|20)\d{2}$', year) or (manufacturer == "BMW" and re.match(r'^[A-Z][0-9]{2}$', year)):
                        filtered_years.append(year)
                
                logger.info(f"Filtered to {len(filtered_years)} valid years/chassis: {filtered_years}")
                
                # Sort years in descending order (newest first) if they're numeric
                if filtered_years and all(y.isdigit() for y in filtered_years):
                    filtered_years.sort(reverse=True)
                    logger.info(f"Sorted years in descending order: {filtered_years}")
                
                return filtered_years
            
            # SECOND APPROACH: If we didn't find years in table format, check for dropdown
            logger.info("Table format not found or no valid years. Checking dropdown format...")
            
            # First try to check if the years dropdown exists
            dropdown_exists = await page.evaluate("""() => {
                return document.querySelector('.dropbox.level3') !== null;
            }""")
            
            if not dropdown_exists:
                logger.error("Years/chassis dropdown (.dropbox.level3) does not exist in the DOM")
                await self.capture_debug_info(page, f"{manufacturer}_{model}_years_dropdown_missing")
                return []
            
            # Give it a moment to stabilize
            await page.wait_for_timeout(2000)
            
            # Wait for the years dropdown to be visible with a more robust approach
            try:
                # Check if it's visible
                is_visible = await page.evaluate("""() => {
                    const dropdown = document.querySelector('.dropbox.level3');
                    if (!dropdown) return false;
                    return dropdown.offsetParent !== null && 
                           window.getComputedStyle(dropdown).display !== 'none' &&
                           window.getComputedStyle(dropdown).visibility !== 'hidden';
                }""")
                
                logger.info(f"Years/chassis dropdown visible: {is_visible}")
                
                if not is_visible:
                    logger.info("Waiting for years/chassis to appear...")
                    await page.wait_for_timeout(3000)
            except Exception as e:
                logger.warning(f"Error checking years dropdown visibility: {e}")
            
            # Get all years/chassis options from the dropdown, specifically focusing on year elements
            options = await page.evaluate("""() => {
                // First try to find the year heading within the dropdown
                const yearHeading = Array.from(document.querySelectorAll('.dropbox.level3 h3.title'))
                    .find(el => el.textContent.trim() === 'Year');
                
                let yearsList;
                
                if (yearHeading) {
                    // Get the UL that follows the year heading
                    yearsList = yearHeading.nextElementSibling;
                    if (yearsList && yearsList.tagName !== 'UL') {
                        yearsList = yearsList.querySelector('ul');
                    }
                } else {
                    // If no heading, just get the UL within the level3 dropdown
                    yearsList = document.querySelector('.dropbox.level3 > ul');
                }
                
                if (!yearsList) return [];
                
                // Get all LI elements and filter for valid years/chassis
                return Array.from(yearsList.querySelectorAll('li'))
                    .map(el => el.textContent.trim())
                    .filter(text => 
                        text.length > 0 && 
                        (
                            // Year pattern (4 digits between 1900-2100)
                            /^(19|20)\\d{2}$/.test(text) || 
                            // Chassis pattern for BMW (alphanumeric with possible special chars)
                            /^[A-Z][0-9]{2}$/.test(text)
                        )
                    );
            }""")
            
            # Sort years in descending order if they're numeric
            if options and all(opt.isdigit() for opt in options):
                options.sort(key=int, reverse=True)
            
            if options:
                logger.info(f"Found {len(options)} valid years/chassis for {manufacturer} - {model}")
                for option in options:
                    logger.info(f"- {option}")
                return options
            else:
                logger.warning(f"No valid years/chassis found for {manufacturer} - {model}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting years/chassis for {manufacturer} - {model}: {e}")
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
                    
                    # Select Product type using the interact_with_dropdown method from original scraper
                    if not await self.interact_with_dropdown(self.page, "Product type", "MA600", True):
                        logger.error("Failed to select product type MA600")
                        return
                    
                    # Select the manufacturer
                    if not await self.select_make(self.page, website_make):
                        logger.error(f"Failed to select make: {website_make}")
                        return
                    
                    # Get all available models
                    models = await self.get_available_models(self.page, manufacturer)
                    
                    # Initialize manufacturer data in results
                    self.results[manufacturer] = {"models": {}}
                    logger.info(f"Processing {len(models)} models for {manufacturer}")
                    
                    # For each model, get years/chassis
                    for model_index, model in enumerate(models):
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
                            years_or_chassis = await self.get_years_or_chassis(model_page, manufacturer, model)
                            
                            # Store in results - even if empty, so we know we processed it
                            data_type = "chassis" if manufacturer == "BMW" else "years"
                            self.results[manufacturer]["models"][model] = {
                                data_type: years_or_chassis
                            }
                            
                            logger.info(f"Successfully stored {len(years_or_chassis)} {data_type} for model {model}")
                            
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
                            # Continue with next model even if this one fails
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
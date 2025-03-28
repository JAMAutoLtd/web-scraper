from playwright.async_api import async_playwright
import asyncio
import os
import random
from datetime import datetime
import logging
import pytesseract
from PIL import Image
import re

# Set Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MaxiSysScraper:
    # Define make mappings
    MAKE_MAPPINGS = {
        'ACURA': 'Acura(CANADA)',
        'GENESIS': 'Genesis(Canada)',
        'HYUNDAI': 'Hyundai(Canada)',
        'KIA': 'Kia(USA)',
        'LEXUS': 'LEXUS(USA)',
        'NISSAN': 'Nissan(North America)',
        'INFINITI': 'Infiniti(North America)',
        'SUBARU': 'Subaru(US)',
        'TOYOTA': 'Toyota(USA)',
        'VOLKSWAGEN': 'Volkswagen',  # No special suffix for Volkswagen
        'AUDI': 'Audi'  # No special suffix for Audi
    }

    # Makes that require Engine/vehicle configuration selection
    MAKES_WITH_VEHICLE_CONFIG = ['VOLKSWAGEN', 'AUDI']

    # Volkswagen model mapping system
    # Maps user input models to possible website models with their earliest year
    VW_MODEL_MAPPINGS = {
        # Format: 'INPUT_MODEL': [('CODE_PATTERN', 'WEBSITE_MODEL', EARLIEST_YEAR), ...]
        'ATLAS': [
            ('CA/CM', 'Atlas', 2018),  # Atlas 2018+
        ],
        'ATLAS CROSS SPORT': [
            ('CA/CM', 'Atlas', 2018),  # Atlas range includes Cross Sport
        ],
        'BEETLE': [
            ('5C', 'Beetle', 2012),    # Beetle 2012+
        ],
        'GOLF': [
            ('CD/CG', 'Golf', 2022),   # Golf 2022+
            ('AU/BE/BX', 'Golf', 2013) # Golf 2013-2021
        ],
        'GOLF GTI': [
            ('CD/CG', 'Golf', 2022),   # Golf 2022+ includes GTI
            ('AU/BE/BX', 'Golf', 2013) # Golf 2013-2021 includes GTI
        ],
        'GOLF R': [
            ('CD/CG', 'Golf', 2022),   # Golf 2022+ includes R
            ('AU/BE/BX', 'Golf', 2013) # Golf 2013-2021 includes R
        ],
        'GOLF ALLTRACK': [
            ('AU/BE/BX', 'Golf', 2013) # Golf 2013-2021 includes Alltrack
        ],
        'GOLF SPORTWAGEN': [
            ('AU/BE/BX', 'Golf', 2013) # Golf 2013-2021 includes SportWagen
        ],
        'ID.4': [
            ('E4', 'ID.4 X', 2021),    # ID.4 X 2021+
            ('E8', 'ID.4 USA/CAN', 2021)  # ID.4 USA/CAN 2021+
        ],
        'ID.BUZZ': [
            ('EB', 'ID.Buzz', 2022),   # ID.Buzz 2022+
        ],
        'JETTA': [
            ('BU', 'Jetta', 2018),     # Jetta 2018+
            ('16', 'Jetta', 2011)      # Jetta 2011-2017
        ],
        'JETTA GLI': [
            ('BU', 'Jetta', 2018),     # Jetta 2018+ includes GLI
            ('16', 'Jetta', 2011)      # Jetta 2011-2017 includes GLI
        ],
        'PASSAT': [
            ('3G/CB', 'Passat', 2015), # Passat 2015+
            ('36', 'Passat', 2011),    # Passat 2011-2014
            ('35', 'Passat CC', 2009), # Passat CC 2009+
            ('3C', 'Passat', 2006)     # Passat 2006-2008
        ],
        'ARTEON': [
            ('3H', 'Arteon', 2017)     # Arteon 2017+
        ],
        'TAOS': [
            ('CL', 'Taos', 2021)       # Taos 2021+
        ],
        'TIGUAN': [
            ('BW', 'Tiguan', 2018),    # Tiguan 2018+
            ('5T', 'Tiguan', 2016),    # Tiguan 2016-2017
            ('5N', 'Tiguan', 2008)     # Tiguan 2008-2015
        ],
        'TOUAREG': [
            ('CR/QT', 'Touareg MF', 2018), # Touareg MF 2018+
            ('7P', 'Touareg', 2010),   # Touareg 2010-2017
            ('7L', 'Touareg', 2003)    # Touareg 2003-2009
        ],
        'T-ROC': [
            ('A1/AC', 'T-Roc', 2018)   # T-Roc 2018+
        ],
        'T-CROSS': [
            ('AW/C1', 'T-Cross', 2019) # T-Cross 2019+
        ],
        'POLO': [
            ('AW', 'Polo', 2018),      # Polo 2018+
            ('6C', 'Polo', 2014),      # Polo 2014-2017
            ('CK', 'Polo', 2020)       # Polo 2020+ (another model code variant)
        ],
        'TOURAN': [
            ('5T', 'Touran', 2016),    # Touran 2016+
            ('1T', 'Touran', 2011)     # Touran 2011-2015
        ],
        'VIRTUS': [
            ('BZ', 'Polo/Virtus', 2018), # Polo/Virtus 2018+
            ('CY', 'Virtus', 2022)     # Virtus 2022+
        ],
        'NIVUS': [
            ('CH', 'Nivus', 2020)      # Nivus 2020+
        ],
        'TAYRON': [
            ('RM', 'Tayron', 2024)     # Tayron 2024+
        ],
        'TAREK': [
            ('CP', 'Tarek', 2021)      # Tarek 2021+
        ],
        'TERAMONT': [
            ('CA/CM', 'Atlas', 2018)   # Atlas/Teramont share platform
        ],
        'PHIDEON': [
            ('3E', 'Phideon', 2017)    # Phideon 2017+
        ]
    }

    def __init__(self):
        self.debug_dir = "debug_info"
        self.ensure_debug_directory()
        self.browser = None
        self.context = None
        self.page = None
        
    def ensure_debug_directory(self):
        """Ensure the debug directory exists."""
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)

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

    async def interact_with_multilevel_dropdown(self, page, level_placeholders_options):
        """Interact with multi-level dropdowns sequentially."""
        try:
            # Click the main Make/Model/Year input to open the panel
            main_dropdown = await page.wait_for_selector("input[placeholder='Make/Model/Year']", timeout=10000)
            await main_dropdown.click()
            await page.wait_for_timeout(1000)  # Wait for panel to open

            # Get the make, model, and year from the input
            make = level_placeholders_options[0][1]
            model = level_placeholders_options[1][1]
            year = level_placeholders_options[2][1]
            
            # Handle Make selection
            logger.info(f"Selecting Make: {make}")
            make_selector = f"text={make}"
            make_element = await page.wait_for_selector(make_selector, timeout=10000)
            if not make_element:
                raise Exception(f"Could not find Make option: {make}")
            await make_element.click()
            await page.wait_for_timeout(2000)  # Wait for Model panel to appear

            # Special handling for Volkswagen based on YMM
            database_make = level_placeholders_options[0][1].split('(')[0].strip().upper()
            if database_make == "VOLKSWAGEN":
                await self.select_volkswagen_model(page, model, year)
            else:
                # Regular model selection
                logger.info(f"Selecting Model: {model}")
                # Try different selectors for the model
                model_selectors = [
                    f"li:has-text('{model}')",
                    f"text={model}",
                    f"//li[contains(text(), '{model}')]"
                ]
                
                model_found = False
                for selector in model_selectors:
                    try:
                        logger.info(f"Trying model selector: {selector}")
                        model_element = await page.wait_for_selector(selector, timeout=5000)
                        if model_element:
                            # Log the element we found
                            element_info = await page.evaluate("""(element) => {
                                return {
                                    tagName: element.tagName,
                                    textContent: element.textContent.trim(),
                                    className: element.className,
                                    id: element.id,
                                    parentElement: {
                                        className: element.parentElement ? element.parentElement.className : '',
                                        id: element.parentElement ? element.parentElement.id : ''
                                    }
                                }
                            }""", model_element)
                            logger.info(f"Found model element:")
                            logger.info(f"- Tag: {element_info['tagName']}")
                            logger.info(f"- Text: {element_info['textContent']}")
                            logger.info(f"- Class: {element_info['className']}")
                            logger.info(f"- Parent class: {element_info['parentElement']['className']}")
                            
                            await model_element.click()
                            model_found = True
                            logger.info(f"Successfully clicked model option")
                            break
                    except Exception as e:
                        logger.debug(f"Model selector {selector} failed: {e}")
                        continue
                
                if not model_found:
                    # If we couldn't find the model, let's log all visible elements to help debug
                    visible_text = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('li'))
                            .filter(el => el.offsetParent !== null)
                            .map(el => ({
                                tag: el.tagName,
                                text: el.textContent.trim(),
                                class: el.className,
                                id: el.id
                            }))
                            .filter(item => item.text.length > 0);
                    }""")
                    logger.info("Visible list items after Make selection:")
                    for item in visible_text:
                        logger.info(f"- {item['tag']}: {item['text']} (class: {item['class']}, id: {item['id']})")
                    raise Exception(f"Could not find Model option: {model}")

            await page.wait_for_timeout(2000)  # Wait for Year panel to appear

            # Handle Year selection
            logger.info(f"Selecting Year: {year}")
            # For Volkswagen, years may have suffixes like (S), (R), etc.
            if make == "Volkswagen":
                # Try to find the year with any suffix
                year_selectors = [
                    f"text={year} (", # Year with any suffix
                    f"text={year}"    # Just the year as fallback
                ]
                
                year_found = False
                for selector in year_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            text = await element.text_content()
                            logger.info(f"Found potential year element: {text}")
                            
                            # Verify it's a year with optional suffix
                            if re.match(f"{year} \\([A-Z]\\)|{year}$", text):
                                await element.click()
                                year_found = True
                                logger.info(f"Selected year: {text}")
                                break
                        
                        if year_found:
                            break
                    except Exception as e:
                        logger.debug(f"Year selector {selector} failed: {e}")
                        continue
                
                if not year_found:
                    # Log all visible year options
                    visible_years = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('li'))
                            .filter(el => el.offsetParent !== null)
                            .map(el => el.textContent.trim())
                            .filter(text => /\\d{4}/.test(text));
                    }""")
                    logger.info("Available year options:")
                    for y in visible_years:
                        logger.info(f"- {y}")
                    
                    # Try to select the best matching year
                    if visible_years:
                        # Sort years to find closest match
                        exact_matches = [y for y in visible_years if y.startswith(year)]
                        if exact_matches:
                            best_year = exact_matches[0]
                            logger.info(f"Selecting best matching year: {best_year}")
                            await page.click(f"text={best_year}")
                        else:
                            # Just click the first year
                            logger.info(f"No exact match found, selecting first year: {visible_years[0]}")
                            await page.click(f"text={visible_years[0]}")
                    else:
                        raise Exception(f"Could not find any year options")
            else:
                # Regular year selection
                year_selector = f"text={year}"
                year_element = await page.wait_for_selector(year_selector, timeout=10000)
                if not year_element:
                    raise Exception(f"Could not find Year option: {year}")
                await year_element.click()
            
            # After selecting Year, handle Engine/vehicle configuration for VW and Audi
            database_make = level_placeholders_options[0][1].split('(')[0].strip().upper()
            if database_make in self.MAKES_WITH_VEHICLE_CONFIG:
                logger.info(f"Handling Engine/vehicle configuration for {database_make}")
                await self.select_vehicle_configuration(page)
            
            return True

        except Exception as e:
            logger.error(f"Failed in multilevel dropdown interaction: {e}")
            await self.capture_debug_info(page, "multilevel_dropdown_error")
            return False

    async def select_volkswagen_model(self, page, model_name, model_year):
        """Special handling for Volkswagen models based on YMM."""
        try:
            # Normalize the model name to uppercase for matching
            normalized_model = model_name.upper()
            logger.info(f"Selecting Volkswagen model: {normalized_model}, Year: {model_year}")
            
            # Find the mapping for this model
            best_mapping = None
            
            # Check if we have a direct match
            if normalized_model in self.VW_MODEL_MAPPINGS:
                model_options = self.VW_MODEL_MAPPINGS[normalized_model]
            else:
                # If not, check for partial matches (e.g., "GOLF R" should match with "GOLF")
                potential_matches = []
                for key in self.VW_MODEL_MAPPINGS.keys():
                    # If the input model starts with a mapping key (like GOLF GTI starts with GOLF)
                    if normalized_model.startswith(key):
                        potential_matches.append((key, len(key)))
                    # If a mapping key starts with the input model (like GOLF starts with the input GOLF)
                    elif key.startswith(normalized_model):
                        potential_matches.append((key, len(normalized_model)))
                
                # Sort by match length (longer matches first)
                potential_matches.sort(key=lambda x: x[1], reverse=True)
                
                if potential_matches:
                    best_match = potential_matches[0][0]
                    logger.info(f"No exact match found for '{normalized_model}', using best match: '{best_match}'")
                    model_options = self.VW_MODEL_MAPPINGS[best_match]
                else:
                    # No match found, log error
                    logger.error(f"No mapping found for Volkswagen model: {normalized_model}")
                    # Get all available model options to help debug
                    model_options = await page.evaluate("""() => {
                        return Array.from(document.querySelectorAll('li'))
                            .filter(el => el.offsetParent !== null)
                            .map(el => el.textContent.trim())
                            .filter(text => text.includes(' - ') && text.includes('USA/CAN'));
                    }""")
                    
                    logger.info(f"Available Volkswagen model options:")
                    for option in model_options:
                        logger.info(f"- {option}")
                        
                    # Just take the first USA/CAN option
                    if model_options and isinstance(model_options, list) and len(model_options) > 0:
                        logger.info(f"No mapping found, selecting first available USA/CAN option")
                        await page.click(f"text={model_options[0]}")
                        return True
                    return False
            
            # Find the most appropriate model range based on year
            year = int(model_year)
            appropriate_options = []
            
            for code_pattern, model, earliest_year in model_options:
                # Check if the model year is in range for this option (assuming no upper limit)
                if year >= earliest_year:
                    appropriate_options.append((code_pattern, model, earliest_year))
            
            # Sort by year (descending) to get the newest range that's still applicable
            appropriate_options.sort(key=lambda x: x[2], reverse=True)
            
            # If we don't have any appropriate options, log error and return
            if not appropriate_options:
                logger.error(f"No appropriate model range found for {normalized_model} year {year}")
                return False
            
            # Select the first (newest) appropriate option
            best_option = appropriate_options[0]
            code_pattern, model, earliest_year = best_option
            
            logger.info(f"Selected model range: {code_pattern} - {model} {earliest_year} USA/CAN")
            
            # Get all visible model options from the page
            model_options = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('li'))
                    .filter(el => el.offsetParent !== null)
                    .map(el => el.textContent.trim())
                    .filter(text => text.includes(' - ') && text.includes('USA/CAN'));
            }""")
            
            logger.info(f"Available Volkswagen model options on page:")
            for option in model_options:
                logger.info(f"- {option}")
            
            # Find the option that matches our criteria
            selected_option = None
            for option in model_options:
                # Look for code pattern match, model match, and USA/CAN
                if (code_pattern in option and 
                    f" - {model} " in option and 
                    "USA/CAN" in option):
                    selected_option = option
                    break
            
            # If we didn't find an exact match, look for a close match
            if not selected_option:
                for option in model_options:
                    # Just match the code pattern and USA/CAN
                    if code_pattern in option and "USA/CAN" in option:
                        selected_option = option
                        break
            
            # If we still don't have a match, try just matching the code pattern
            if not selected_option:
                for option in model_options:
                    if code_pattern in option:
                        selected_option = option
                        break
            
            # If we found an option, click it
            if selected_option:
                logger.info(f"Selected Volkswagen model option: {selected_option}")
                await page.click(f"text={selected_option}")
                return True
            else:
                logger.error(f"Could not find matching model option for {code_pattern} - {model} {earliest_year}")
                return False
                
        except Exception as e:
            logger.error(f"Error selecting Volkswagen model: {e}")
            return False

    async def get_calibration_type(self, page):
        """Detect whether the calibration type is Static or Dynamic."""
        try:
            logger.info("Detecting calibration type...")
            
            # Wait for either Static or Dynamic calibration text to appear
            selectors = [
                "text=Static Calibration",
                "text=Dynamic Calibration"
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        text = await element.text_content()
                        logger.info(f"Found calibration type: {text}")
                        return text
                except Exception:
                    continue
            
            # If we get here, we didn't find either type
            logger.error("Could not determine calibration type")
            return None
            
        except Exception as e:
            logger.error(f"Error detecting calibration type: {e}")
            return None

    async def get_csc_model(self, page):
        """Extract CSC model number from the calibration diagram using OCR."""
        try:
            # Log all images on the page for debugging
            images = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('img')).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    class: img.className,
                    id: img.id,
                    isVisible: img.offsetParent !== null
                }));
            }""")
            logger.info("Found images on page:")
            for img in images:
                logger.info(f"Image: src={img['src']}, alt={img['alt']}, class={img['class']}, visible={img['isVisible']}")

            # Try multiple selectors to find the calibration diagram
            selectors = [
                '.swiper-slide img[src*="download1.auteltech.net"]',  # Target the specific domain
                '.swiper-container img',  # Any image in the swiper container
                '.swiper-slide:has-text("Static Calibration") img',  # Image in slide with Static Calibration text
                '//div[contains(@class, "swiper-slide")]//img',  # XPath for any image in swiper slides
                'img[src*="adas-filter/image"]'  # Images from the adas-filter directory
            ]

            diagram = None
            for selector in selectors:
                try:
                    logger.info(f"Trying selector: {selector}")
                    # Use waitForSelector instead of locator for better error handling
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # Verify this is the correct image
                        src = await element.get_attribute('src')
                        logger.info(f"Found image with src: {src}")
                        if 'adas-filter/image' in src:
                            logger.info(f"Found element with selector: {selector}")
                            diagram = element
                            break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            if not diagram:
                # Try an alternative approach - look for the text directly
                logger.info("Could not find diagram, trying to find text directly...")
                text_selectors = [
                    '.swiper-slide:has-text("CSC")',
                    'text="AUTEL-CSC0800"',
                    'text="AUTEL-CSC0802/01"',
                    '.swiper-slide .header:has-text("Static Calibration")'
                ]
                
                for selector in text_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            text = await element.text_content()
                            logger.info(f"Found text content: {text}")
                            # Look for CSC model patterns
                            csc_pattern = r'(?:AUTEL-)?CSC0[80][0-9]{2}(?:/\d+)?'
                            matches = re.findall(csc_pattern, text)
                            if matches:
                                return matches[0]
                    except Exception as e:
                        logger.debug(f"Text selector {selector} failed: {e}")
                        continue
                        
                logger.error("Could not find calibration diagram or text")
                return None
            
            # Take a screenshot of just the diagram
            screenshot_path = os.path.join(self.debug_dir, "calibration_diagram.png")
            await diagram.screenshot(path=screenshot_path)
            logger.info(f"Saved diagram screenshot to {screenshot_path}")
            
            # Use pytesseract to extract text
            img = Image.open(screenshot_path)
            text = pytesseract.image_to_string(img)
            logger.info(f"Extracted text from image: {text}")
            
            # Look for CSC model patterns
            csc_pattern = r'(?:AUTEL-)?CSC0[80][0-9]{2}(?:/\d+)?'
            matches = re.findall(csc_pattern, text)
            
            if matches:
                csc_model = matches[0]
                logger.info(f"Found CSC model: {csc_model}")
                return csc_model
            else:
                # If no match found, try to find the text directly on the page
                logger.info("No CSC model found in image, trying to find text on page...")
                
                # Get all text content from the page
                page_text = await page.evaluate("""() => {
                    return document.body.innerText;
                }""")
                
                # Look for CSC model in page text
                matches = re.findall(csc_pattern, page_text)
                if matches:
                    csc_model = matches[0]
                    logger.info(f"Found CSC model in page text: {csc_model}")
                    return csc_model
                
                logger.warning("No CSC model found in image or page text")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting CSC model: {e}")
            return None

    def get_website_make(self, database_make):
        """Convert database make to website-specific make format."""
        website_make = self.MAKE_MAPPINGS.get(database_make.upper())
        if not website_make:
            logger.error(f"Unsupported make: {database_make}")
            raise ValueError(f"Make '{database_make}' is not supported")
        logger.info(f"Converted database make '{database_make}' to website make '{website_make}'")
        return website_make

    async def select_vehicle_configuration(self, page):
        """Handle Engine/vehicle configuration dropdown for VW and Audi."""
        try:
            # Wait for any pending loading indicators to disappear
            await page.wait_for_timeout(2000)
            
            # Look for the Engine/vehicle configuration dropdown
            logger.info("Looking for Engine/vehicle configuration dropdown")
            config_selector = "input[placeholder='Engine/vehicle configuration/System']"
            
            try:
                config_dropdown = await page.wait_for_selector(config_selector, timeout=10000)
                logger.info("Found Engine/vehicle configuration dropdown, clicking it")
                await config_dropdown.click()
                await page.wait_for_timeout(2000)  # Wait for dropdown to open
            except Exception as e:
                logger.error(f"Could not find Engine/vehicle configuration dropdown: {e}")
                await self.capture_debug_info(page, "vehicle_config_error")
                return False
            
            # The configuration options we want to find (in order of preference)
            config_options = ["Sedan", "Saloon", "SUV", "Coupe", "Avant", "Roadster", "Sportback"]
            
            logger.info(f"Looking for vehicle configuration options in order: {', '.join(config_options)}")
            
            # Get all visible list items
            list_items = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('li'))
                    .filter(el => el.offsetParent !== null)  // Only visible elements
                    .map(el => el.textContent.trim());
            }""")
            
            logger.info(f"Found {len(list_items)} visible items")
            
            # Find the first matching option in our preferred order
            selected = False
            for option in config_options:
                if option in list_items:
                    logger.info(f"Found preferred option: '{option}', clicking it")
                    await page.click(f"li:text('{option}')")
                    selected = True
                    break
            
            if not selected:
                logger.error("None of the preferred configuration options were found")
                await self.capture_debug_info(page, "vehicle_config_error")
                return False
                
            await page.wait_for_timeout(2000)  # Wait for selection to apply
            return True
                
        except Exception as e:
            logger.error(f"Error selecting vehicle configuration: {e}")
            await self.capture_debug_info(page, "vehicle_config_error")
            return False

    async def scrape(self):
        """Main scraping function."""
        try:
            async with async_playwright() as p:
                # Launch browser
                self.browser = await p.chromium.launch(headless=False)
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                
                # Navigate to the target URL
                await self.page.goto("https://www.maxisysadas.com/getCoverage.jspx")
                await self.capture_debug_info(self.page, "initial_page_load")
                
                # Wait for page to be fully loaded
                await self.page.wait_for_load_state("networkidle")
                
                # Interact with dropdowns
                # Product type dropdown
                success = await self.interact_with_dropdown(self.page, "Product type", "MA600", True)
                if not success:
                    raise Exception("Failed to select product type")
                
                # Example database input (to be replaced with actual database call later)
                database_make = "VOLKSWAGEN"  # This will come from the database
                database_model = "Atlas Cross Sport"  # This will come from the database
                database_year = "2020"  # This will come from the database
                
                # Convert database make to website format
                website_make = self.get_website_make(database_make)
                
                # Multi-level dropdown interaction with converted make
                multilevel_levels = [
                    ("Make/Model/Year", website_make, True),
                    ("Model", database_model, False),  # For VW, this will be handled differently
                    ("Year", database_year, False)
                ]
                
                # VIN is no longer needed - everything uses YMM
                await self.interact_with_multilevel_dropdown(self.page, multilevel_levels)
                
                # Note: Engine/vehicle configuration is now handled in interact_with_multilevel_dropdown
                # for Volkswagen and Audi
                
                # System dropdown
                if database_make.upper() not in self.MAKES_WITH_VEHICLE_CONFIG:
                    # Only need to select system separately for makes that don't have Engine/vehicle configuration
                    success = await self.interact_with_dropdown(self.page, "System", "ACC", True)
                    if not success:
                        raise Exception("Failed to select system")
                else:
                    # For VW and Audi, the system dropdown is already handled in the vehicle configuration
                    logger.info("System already selected as part of vehicle configuration")
                
                # Wait for content to load after all selections
                await self.page.wait_for_load_state("networkidle")
                await self.page.wait_for_timeout(2000)  # Additional wait for dynamic content
                
                # Get calibration type
                calibration_type = await self.get_calibration_type(self.page)
                if calibration_type:
                    logger.info(f"Calibration Type: {calibration_type}")
                else:
                    logger.error("Failed to determine calibration type")
                
                # Get CSC model
                csc_model = await self.get_csc_model(self.page)
                if csc_model:
                    logger.info(f"CSC Model: {csc_model}")
                else:
                    logger.warning("Failed to determine CSC model")
                
                # Capture final state
                await self.capture_debug_info(self.page, "final_state")
                
                # Keep browser open for inspection
                logger.info("Scraping completed. Browser will remain open for inspection.")
                logger.info("Press Ctrl+C to close the browser and exit.")
                
                # Keep the script running
                while True:
                    await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Closing browser...")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            await self.capture_debug_info(self.page, "unexpected_error")
            logger.info("Browser will remain open for inspection.")
            logger.info("Press Ctrl+C to close the browser and exit.")
            while True:
                await asyncio.sleep(1)
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    scraper = MaxiSysScraper()
    await scraper.scrape()

if __name__ == "__main__":
    asyncio.run(main()) 
import asyncio
import aiohttp
import json
from datetime import datetime
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from VehicleSelect.tsx
ALLOWED_MAKES = {
    'ACURA', 'ALFA ROMEO', 'ASTON MARTIN', 'AUDI', 'BENTLEY', 'BMW',
    'BUICK', 'CADILLAC', 'CHEVROLET', 'CHRYSLER', 'DODGE', 'FERRARI', 'FIAT',
    'FORD', 'GENESIS', 'GMC', 'HONDA', 'HYUNDAI', 'INFINITI', 'JAGUAR', 'JEEP',
    'KIA', 'LAMBORGHINI', 'LAND ROVER', 'LEXUS', 'LINCOLN', 'LOTUS', 'MASERATI',
    'MAZDA', 'MERCEDES-BENZ', 'MINI', 'MITSUBISHI', 'NISSAN',
    'PORSCHE', 'RAM', 'ROLLS-ROYCE', 'SUBARU', 'TESLA', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO'
}

EXCLUDED_KEYWORDS = [
    'CHASSIS', 'CAB', 'COMMERCIAL', 'MEDIUM DUTY', 'HEAVY DUTY',
    'STRIPPED', 'INCOMPLETE', 'MOTORHOME', 'RV', 'BUS', 'TRACTOR',
    'MOTORCYCLE', 'SCOOTER', 'ATV', 'TRAILER', 'VAN CAMPER', 'MOTOR COACH',
    # Volvo specific exclusions
    'FH', 'FM', 'FMX', 'NH', 'VHD', 'VNL', 'VNM', 'VNR', 'VNX', 'VT'
]

# Allowed model patterns (for models that start with letters followed by numbers)
ALLOWED_MODEL_PATTERNS = [
    r'^[A-Z]\d{1,2}$',  # Matches Q50, G35, etc.
    r'^[A-Z][A-Z]\d{1,2}$',  # Matches QX50, GX460, etc.
    r'^[A-Z]\d{3}[a-zA-Z]*$',  # Matches M340i, S560e, etc.
]

# Special cases for specific makes
SPECIAL_CASES = {
    'MERCEDES-BENZ': ['SPRINTER'],
}

class VehicleOptionsGenerator:
    def __init__(self):
        self.results = {}
        self.current_year = datetime.now().year
        self.start_year = 1995

    async def fetch_data(self, session, url):
        try:
            async with session.get(url) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching data from {url}: {e}")
            return None

    def is_valid_model(self, model: str, make: str) -> bool:
        upper_model = model.upper()
        
        # Check special cases
        if make in SPECIAL_CASES and upper_model in SPECIAL_CASES[make]:
            return True

        # For Volvo, exclude models that contain only letters
        if make.upper() == 'VOLVO' and re.match(r'^[A-Z]+$', upper_model):
            return False

        # Check if model matches any of our allowed patterns
        is_allowed_pattern = any(re.match(pattern, model) for pattern in ALLOWED_MODEL_PATTERNS)

        return (
            is_allowed_pattern or
            (not any(keyword in upper_model for keyword in EXCLUDED_KEYWORDS) and
             not re.match(r'^[A-Z]\d{4,}', model) and
             model.strip())
        )

    async def fetch_models_for_make_year(self, session, make: str, year: str):
        vehicle_types = ['passenger car', 'multipurpose passenger vehicle (mpv)', 'truck']
        models = set()

        for vehicle_type in vehicle_types:
            url = f'https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/{make}/modelyear/{year}/vehicletype/{vehicle_type}?format=json'
            data = await self.fetch_data(session, url)
            
            if data and 'Results' in data:
                valid_models = [
                    model['Model_Name']
                    for model in data['Results']
                    if self.is_valid_model(model['Model_Name'], make)
                ]
                models.update(valid_models)

        # Add "Other" if we found any models
        if models:
            models.add('Other')
        
        return sorted(list(models))

    async def fetch_makes_for_year(self, session, year: str):
        vehicle_types = ['passenger car', 'multipurpose passenger vehicle (mpv)', 'truck']
        makes = set()

        for vehicle_type in vehicle_types:
            url = f'https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/{vehicle_type}?year={year}&format=json'
            data = await self.fetch_data(session, url)
            
            if data and 'Results' in data:
                valid_makes = [
                    make['MakeName']
                    for make in data['Results']
                    if make['MakeName'].upper() in ALLOWED_MAKES
                ]
                makes.update(valid_makes)

        return sorted(list(makes))

    async def generate_options(self):
        async with aiohttp.ClientSession() as session:
            for year in range(self.current_year, self.start_year - 1, -1):
                year_str = str(year)
                logger.info(f"Processing year {year_str}")
                
                makes = await self.fetch_makes_for_year(session, year_str)
                if not makes:
                    logger.warning(f"No makes found for year {year_str}")
                    continue

                self.results[year_str] = {}
                
                for make in makes:
                    logger.info(f"Processing {year_str} {make}")
                    models = await self.fetch_models_for_make_year(session, make, year_str)
                    
                    if models:
                        self.results[year_str][make] = models
                    else:
                        logger.warning(f"No models found for {year_str} {make}")

    def save_results(self):
        output_file = 'vehicle_options.json'
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results saved to {output_file}")

async def main():
    generator = VehicleOptionsGenerator()
    await generator.generate_options()
    generator.save_results()

if __name__ == "__main__":
    asyncio.run(main()) 
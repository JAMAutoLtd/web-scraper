"use client";

import { useState, useEffect } from "react";

interface VehicleSelectProps {
  onVehicleSelect: (vehicle: { year: string; make: string; model: string }) => void;
}

interface VehicleData {
  year: string;
  make: string;
  model: string;
}

const VehicleSelect: React.FC<VehicleSelectProps> = ({ onVehicleSelect }) => {
  const [years, setYears] = useState<string[]>([]);
  const [makes, setMakes] = useState<string[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedData, setSelectedData] = useState<VehicleData>({
    year: '',
    make: '',
    model: ''
  });

  // Fetch available years (from current year back to 1995)
  useEffect(() => {
    const currentYear = new Date().getFullYear();
    const yearsList = Array.from(
      { length: currentYear - 1995 + 1 },
      (_, i) => (currentYear - i).toString()
    );
    setYears(yearsList);
  }, []);

  // Fetch makes for selected year
  const fetchMakes = async (year: string) => {
    setLoading(true);
    setError(null);
    try {
      // Fetch passenger cars, MPVs/SUVs, and light trucks
      const [carsResponse, mpvResponse, trucksResponse] = await Promise.all([
        fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/passenger car?year=${year}&format=json`),
        fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/multipurpose passenger vehicle (mpv)?year=${year}&format=json`),
        fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/truck?year=${year}&format=json`)
      ]);

      const [carsData, mpvData, trucksData] = await Promise.all([
        carsResponse.json(),
        mpvResponse.json(),
        trucksResponse.json()
      ]);

      console.log('Cars data:', carsData);
      console.log('MPV data:', mpvData);
      console.log('Trucks data:', trucksData);

      // List of allowed consumer vehicle manufacturers
      const allowedMakes = new Set([
        'ACURA', 'ALFA ROMEO', 'ASTON MARTIN', 'AUDI', 'BENTLEY', 'BMW',
        'BUICK', 'CADILLAC', 'CHEVROLET', 'CHRYSLER', 'DODGE', 'FERRARI', 'FIAT',
        'FORD', 'GENESIS', 'GMC', 'HONDA', 'HYUNDAI', 'INFINITI', 'JAGUAR', 'JEEP',
        'KIA', 'LAMBORGHINI', 'LAND ROVER', 'LEXUS', 'LINCOLN', 'LOTUS', 'MASERATI',
        'MAZDA', 'MERCEDES-BENZ', 'MINI', 'MITSUBISHI', 'NISSAN',
        'PORSCHE', 'RAM', 'ROLLS-ROYCE', 'SUBARU', 'TESLA', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO'
      ]);

      // Combine results from all endpoints and filter
      const allMakes = [...carsData.Results, ...mpvData.Results, ...trucksData.Results]
        .map((make: any) => make.MakeName as string)
        .filter((make: string) => allowedMakes.has(make.toUpperCase()));

      // Remove duplicates and sort
      const uniqueMakes = [...new Set(allMakes)].sort() as string[];

      if (uniqueMakes.length === 0) {
        setError("No vehicle makes found for the selected year");
        setMakes([]);
      } else {
        setMakes(uniqueMakes);
      }
      setModels([]);
      setSelectedData(prev => ({ ...prev, year, make: '', model: '' }));
    } catch (err) {
      setError("Failed to load vehicle makes");
      console.error("Error fetching makes:", err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch models for selected make and year
  const fetchModels = async (year: string, make: string) => {
    setLoading(true);
    setError(null);
    try {
      // Fetch passenger cars, MPVs/SUVs, and light trucks
      const [carsResponse, mpvResponse, trucksResponse] = await Promise.all([
        fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/${make}/modelyear/${year}/vehicletype/passenger car?format=json`),
        fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/${make}/modelyear/${year}/vehicletype/multipurpose passenger vehicle (mpv)?format=json`),
        fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeYear/make/${make}/modelyear/${year}/vehicletype/truck?format=json`)
      ]);

      const [carsData, mpvData, trucksData] = await Promise.all([
        carsResponse.json(),
        mpvResponse.json(),
        trucksResponse.json()
      ]);

      console.log('Cars models:', carsData);
      console.log('MPV models:', mpvData);
      console.log('Truck models:', trucksData);
      
      // Filter out unwanted vehicle types and models
      const excludedKeywords = [
        'CHASSIS', 'CAB', 'COMMERCIAL', 'MEDIUM DUTY', 'HEAVY DUTY',
        'STRIPPED', 'INCOMPLETE', 'MOTORHOME', 'RV', 'BUS', 'TRACTOR',
        'MOTORCYCLE', 'SCOOTER', 'ATV', 'TRAILER', 'VAN CAMPER', 'MOTOR COACH',
        // Volvo specific exclusions
        'FH', 'FM', 'FMX', 'NH', 'VHD', 'VNL', 'VNM', 'VNR', 'VNX', 'VT'
      ];

      // List of allowed model patterns (for models that start with letters followed by numbers)
      const allowedModelPatterns = [
        /^[A-Z]\d{1,2}$/,  // Matches Q50, G35, etc.
        /^[A-Z][A-Z]\d{1,2}$/,  // Matches QX50, GX460, etc.
        /^[A-Z]\d{3}[a-zA-Z]*$/,  // Matches M340i, S560e, etc.
      ];

      // Special cases for specific makes
      const specialCases: Record<string, string[]> = {
        'MERCEDES-BENZ': ['SPRINTER'],
        // Add other special cases here if needed
      };
      
      // Combine and filter models from all endpoints
      const allModels = [...carsData.Results, ...mpvData.Results, ...trucksData.Results]
        .map((model: any) => model.Model_Name as string)
        .filter((model: string) => {
          const upperModel = model.toUpperCase();
          
          // Check if it's a special case for the current make
          if (specialCases[make] && specialCases[make].includes(upperModel)) {
            return true;
          }

          // For Volvo, exclude models that contain only letters
          if (make.toUpperCase() === 'VOLVO' && /^[A-Z]+$/.test(upperModel)) {
            return false;
          }
          
          // Check if model matches any of our allowed patterns
          const isAllowedPattern = allowedModelPatterns.some(pattern => pattern.test(model));
          
          return (
            // Allow models that match our patterns
            isAllowedPattern ||
            // Or models that don't contain excluded keywords and don't match unwanted patterns
            (!excludedKeywords.some(keyword => upperModel.includes(keyword)) &&
             !/^[A-Z]\d{4,}/.test(model) && // Excludes models with very long numbers
             model.trim().length > 0) // Excludes empty model names
          );
        });

      // Remove duplicates, sort, and add "Other" option
      const filteredModels = [...new Set(allModels)].sort() as string[];
      filteredModels.push('Other');

      if (filteredModels.length === 1 && filteredModels[0] === 'Other') {
        setError("No specific models found for the selected make and year");
      }
      setModels(filteredModels);
      setSelectedData(prev => ({ ...prev, make, model: '' }));
    } catch (err) {
      setError("Failed to load vehicle models");
      console.error("Error fetching models:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const year = e.target.value;
    if (year) {
      fetchMakes(year);
    } else {
      setMakes([]);
      setModels([]);
      setSelectedData({ year: '', make: '', model: '' });
    }
  };

  const handleMakeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const make = e.target.value;
    if (make && selectedData.year) {
      fetchModels(selectedData.year, make);
    } else {
      setModels([]);
      setSelectedData(prev => ({ ...prev, make: '', model: '' }));
    }
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const model = e.target.value;
    setSelectedData(prev => {
      const newData = { ...prev, model };
      onVehicleSelect(newData);
      return newData;
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label htmlFor="year" className="block text-sm font-medium text-gray-700 mb-1">
          Year
        </label>
        <select
          id="year"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={selectedData.year}
          onChange={handleYearChange}
          disabled={loading}
        >
          <option value="">Select Year</option>
          {years.map(year => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="make" className="block text-sm font-medium text-gray-700 mb-1">
          Make
        </label>
        <select
          id="make"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={selectedData.make}
          onChange={handleMakeChange}
          disabled={!selectedData.year || loading}
        >
          <option value="">Select Make</option>
          {makes.map(make => (
            <option key={make} value={make}>{make}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-1">
          Model
        </label>
        <select
          id="model"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={selectedData.model}
          onChange={handleModelChange}
          disabled={!selectedData.make || loading}
        >
          <option value="">Select Model</option>
          {models.map(model => (
            <option key={model} value={model}>{model}</option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="col-span-3 text-center text-sm text-gray-500">
          Loading vehicle data...
        </div>
      )}
      {error && (
        <div className="col-span-3 text-center text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
};

export default VehicleSelect; 
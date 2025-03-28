import re

# Read the file
with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the process_adas_systems method
# Target the problematic line with the indentation error
pattern1 = r'(if not system_options or system_options\[0\] == "N/A":\s+logger\.info\(f"Skipping \{system_type\} for \{manufacturer\} - marked as N/A"\))\s+continue'
replacement1 = r'\1\n                continue'

# Apply the fix
fixed_content = re.sub(pattern1, replacement1, content)

# Write the fixed content back
with open('scraper_models_years.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Fixed indentation in process_adas_systems method")

# Fix the save_results method
with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation in the save_results method's except clause
pattern2 = r'(logger\.info\(f"Saved all results to \{filename\}"\))\s+except Exception as e:'
replacement2 = r'\1\n        except Exception as e:'

# Apply the fix
fixed_content = re.sub(pattern2, replacement2, content)

# Write the fixed content back
with open('scraper_models_years.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Fixed indentation in save_results method")

# Fix the process_manufacturer method
with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the indentation in the process_manufacturer method
# This pattern targets the misaligned try-except-finally block
pattern3 = r'(logger\.info\(f"Completed processing \{manufacturer\}"\)\s*)\n(\s+?)except Exception as e:'
replacement3 = r'\1\n                except Exception as e:'

# Apply the fix
fixed_content = re.sub(pattern3, replacement3, content)

# Fix the next level of indentation
pattern4 = r'(self\.save_results\(manufacturer\)\s*)\n(\s+?)finally:'
replacement4 = r'\1\n                finally:'

# Apply the fix
fixed_content = re.sub(pattern4, replacement4, fixed_content)

# Write the fixed content back
with open('scraper_models_years.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("Fixed indentation in process_manufacturer method")

# Run a test to make sure the fixes worked
try:
    import ast
    with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print("✅ File now has valid Python syntax!")
except SyntaxError as e:
    print(f"❌ Syntax error still exists: {e}")
    
    # If still error, let's show the specific area causing problems
    if hasattr(e, 'lineno'):
        line_no = e.lineno
        with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Print a few lines around the error for context
        start = max(0, line_no - 5)
        end = min(len(lines), line_no + 5)
        
        print("Context around error:")
        for i in range(start, end):
            prefix = "→ " if i+1 == line_no else "  "
            print(f"{prefix}{i+1}: {lines[i].rstrip()}") 
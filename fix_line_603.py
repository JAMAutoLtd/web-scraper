with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 603 (0-based index is 602)
if len(lines) > 602:
    if r'\d' in lines[602]:
        print(f"Found invalid escape sequence in line 603: {lines[602].strip()}")
        lines[602] = lines[602].replace(r'\d', r'[0-9]')
        print(f"Fixed to: {lines[602].strip()}")
        
        # Save the file
        with open('scraper_models_years.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("File updated.")
    else:
        print(f"Line 603 does not contain \\d: {lines[602].strip()}")
else:
    print(f"File only has {len(lines)} lines")
    
# Check the entire file for any remaining \d
with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Check if there are any raw Python regex patterns with \d
raw_regex_patterns = 0
for i, line in enumerate(lines):
    if "r'" in line and r'\d' in line:
        print(f"Line {i+1} has \\d in raw regex: {line.strip()}")
        raw_regex_patterns += 1
        
print(f"Found {raw_regex_patterns} lines with raw regex containing \\d")

# Count all instances of \d in the file
all_instances = content.count(r'\d')
print(f"Total instances of '\\d' in the file: {all_instances}") 
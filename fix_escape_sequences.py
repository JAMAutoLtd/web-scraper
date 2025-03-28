import re

# Read the file
with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Get all JavaScript sections inside triple quotes
js_sections = re.findall(r'"""(.*?)"""', content, re.DOTALL)

# Find all instances of \d in the JavaScript code and fix them
for js_section in js_sections:
    if r'\d' in js_section:
        fixed_js = js_section.replace(r'\d', r'\\d')
        content = content.replace(js_section, fixed_js)

# Also fix Python regex patterns
content = re.sub(r'csc_pattern = r\'.*?\'', "csc_pattern = r'(?:AUTEL-)?CSC0[80][0-9]{2}(?:/[0-9]+)?'", content)

# Fix YEAR_PATTERN regex
content = re.sub(r'(YEAR_PATTERN = r\'.*?)\\d(.*?\')', r'\1[0-9]\2', content)

# Fix any remaining patterns
content = re.sub(r'r\'.*?\\d.*?\'', lambda m: m.group(0).replace(r'\d', r'[0-9]'), content)

# Write the fixed content back
with open('scraper_models_years.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all invalid escape sequences in JavaScript regex patterns and Python regex")

# Run a test to verify the fix
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
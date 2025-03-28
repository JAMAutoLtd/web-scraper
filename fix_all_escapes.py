import re

with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all triple-quoted strings that might contain JavaScript
triple_quotes = re.findall(r'"""(.*?)"""', content, re.DOTALL)

for block in triple_quotes:
    if '/\\d' in block:
        fixed_block = block.replace('/\\d', '/[0-9]')
        content = content.replace(block, fixed_block)

# Write the fixed content
with open('scraper_models_years.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed JavaScript regex patterns in triple-quoted strings.")

# Run a syntax check
import ast
try:
    ast.parse(content)
    print("✅ No syntax errors!")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")

# More direct fix - just replace all JavaScript regex patterns with \d
with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all instances of /\d in JavaScript regex patterns
for pattern in [r'/\^?(19\|20)\\d', r'/\^?\\d', r'\\d\{']:
    content = content.replace(pattern, pattern.replace('\\d', '[0-9]'))

# Write the fixed content
with open('scraper_models_years.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Additional fixes applied.")

# Check for any remaining instances of \d
with open('scraper_models_years.py', 'r') as f:
    content = f.read()
    
all_instances = content.count(r'\d')
print(f"Total instances of '\\d' remaining in the file: {all_instances}")

# If there are still instances, do a line-by-line check
if all_instances > 0:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if r'\d' in line:
            print(f"Line {i+1}: {line.strip()}") 
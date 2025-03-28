with open('scraper_models_years.py', 'r') as f:
    lines = f.readlines()

# Lines with \d to fix directly (0-indexed)
problem_lines = [607, 609, 914, 1459, 1461, 1513, 1515]

# Fix each line
for line_idx in problem_lines:
    if line_idx < len(lines):
        # Replace \d with [0-9] in JavaScript regex patterns
        lines[line_idx] = lines[line_idx].replace('/\\d', '/[0-9]')
        print(f"Fixed line {line_idx+1}: {lines[line_idx].strip()}")

# Write the fixed content
with open('scraper_models_years.py', 'w') as f:
    f.writelines(lines)

print("Fixed specific lines with \\d in JavaScript regex patterns.")

# Verify fixes
with open('scraper_models_years.py', 'r') as f:
    content = f.read()
    
all_instances = content.count('/\\d')
print(f"Remaining instances of '/\\d' in the file: {all_instances}")

if all_instances > 0:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '/\\d' in line:
            print(f"Line {i+1} still has /\\d: {line.strip()}")

# Run final syntax check
import ast
try:
    ast.parse(content)
    print("✅ No syntax errors!")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}") 
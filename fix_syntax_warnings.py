with open('scraper_models_years.py', 'r') as f:
    lines = f.readlines()

# Find all lines with \d that might be causing warnings
problem_lines = []
for i, line in enumerate(lines):
    if r'\d' in line:
        problem_lines.append(i)
        print(f"Line {i+1} has \\d: {line.strip()}")

print(f"Found {len(problem_lines)} lines with \\d")

# Fix each line by replacing \d with [0-9] in JavaScript string context
# and with \\d in Python regex context
for line_idx in problem_lines:
    if line_idx < len(lines):
        # Check if this is a JavaScript context
        if '"""' in lines[line_idx] and ('return' in lines[line_idx] or '.filter' in lines[line_idx]):
            # JavaScript context: replace /\d with /[0-9]
            lines[line_idx] = lines[line_idx].replace('/\\d', '/[0-9]')
            print(f"Fixed JavaScript line {line_idx+1}")
        else:
            # Python regex context: replace \d with \\d
            lines[line_idx] = lines[line_idx].replace('\\d', '[0-9]')
            print(f"Fixed Python line {line_idx+1}")

# Write the fixed content
with open('scraper_models_years.py', 'w') as f:
    f.writelines(lines)

print("Fixed lines with \\d escape sequences.")

# Run final syntax check
import ast
try:
    ast.parse(''.join(lines))
    print("✅ No syntax errors!")
except SyntaxError as e:
    print(f"❌ Syntax error at line {e.lineno}: {e.msg}")

# Additional check for warnings
import subprocess
try:
    result = subprocess.run(['python', '-c', 'import scraper_models_years'], 
                           stderr=subprocess.PIPE, text=True)
    if 'SyntaxWarning' in result.stderr:
        print("❌ SyntaxWarnings still exist:")
        print(result.stderr)
    else:
        print("✅ No SyntaxWarnings!")
except Exception as e:
    print(f"Error running import check: {e}") 
import ast
import sys

try:
    with open('scraper_models_years.py', 'r', encoding='utf-8') as f:
        source = f.read()
        lines = source.splitlines()
    
    # First check for basic syntax errors
    try:
        ast.parse(source)
        print("✅ Basic syntax check passed")
    except SyntaxError as e:
        line_no = e.lineno
        print(f"❌ Syntax error at line {line_no}: {e}")
        
        # Print a few lines around the error for context
        start = max(0, line_no - 3)
        end = min(len(lines), line_no + 2)
        
        for i in range(start, end):
            prefix = "→ " if i+1 == line_no else "  "
            print(f"{prefix}{i+1}: {lines[i]}")
        sys.exit(1)
    
    # Check for try-except blocks that might be incomplete
    in_try = False
    try_line = 0
    try_indent = 0
    
    for i, line in enumerate(lines):
        if in_try:
            stripped = line.lstrip()
            if stripped.startswith('try:'):
                print(f"⚠️ Nested try at line {i+1} inside try from line {try_line}")
            elif stripped.startswith('except') or stripped.startswith('finally:'):
                indent = len(line) - len(line.lstrip())
                if indent == try_indent:
                    in_try = False
        elif 'try:' in line and not line.strip().startswith('#'):
            in_try = True
            try_line = i+1
            try_indent = len(line) - len(line.lstrip())
    
    if in_try:
        print(f"⚠️ Unclosed try block starting at line {try_line}")
        
    # Check for potentially problematic indentation
    prev_indent = 0
    for i, line in enumerate(lines):
        if not line.strip() or line.strip().startswith('#'):
            continue
        
        indent = len(line) - len(line.lstrip())
        if indent > prev_indent + 4 and prev_indent > 0:
            print(f"⚠️ Suspicious indentation jump at line {i+1}: {indent} spaces (previous: {prev_indent})")
            print(f"  {i+1}: {line}")
        
        prev_indent = indent
            
    print("✅ File check completed")
        
except Exception as e:
    print(f"Error checking file: {e}") 
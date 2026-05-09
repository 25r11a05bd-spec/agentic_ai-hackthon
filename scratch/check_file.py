import os

path = 'backend/app/tools/ai_agent.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '\t' in line:
        print(f"Tab found on line {i+1}")
    if line.rstrip() == "    except Exception as e:":
        print(f"Old style except found on line {i+1}")
    if line.rstrip() == "    try:":
        print(f"Try found on line {i+1}")

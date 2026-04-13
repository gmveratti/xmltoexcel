import os
import re

replacements = {
    'shared.': 'shared.',
    'from shared': 'from shared',
    'import shared': 'import shared',
    'shared.base_parser': 'shared.base_parser',
    'cte.parser': 'cte.parser',
    'cte.event_parser': 'cte.event_parser',
    'nfe.parser': 'nfe.parser',
    'nfe.event_parser': 'nfe.event_parser',
    'from shared import': 'from shared import'
}

for root, _, files in os.walk('.'):
    if '.venv' in root or '.git' in root or '.pytest_cache' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content
            for old, new in replacements.items():
                new_content = new_content.replace(old, new)
                
            if new_content != content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Updated {path}')

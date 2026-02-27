import re

with open('docs/source/index.rst', 'r') as f:
    content = f.read()

# Insert evaluation after concepts/index
content = re.sub(
    r'(concepts/index\n)',
    r'\1   evaluation\n',
    content
)

with open('docs/source/index.rst', 'w') as f:
    f.write(content)

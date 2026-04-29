from pathlib import Path
text = Path('dist/assets/index-o93a1SHb.js').read_text(encoding='utf-8', errors='ignore')
needle = 'Forgot Password?'
idx = text.find(needle)
print('found' if idx >= 0 else 'not found')
if idx >= 0:
    print(text[max(0, idx-100):idx+len(needle)+100])

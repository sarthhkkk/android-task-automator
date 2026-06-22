import uiautomator2 as u2
d = u2.connect('b145b040')
xml = d.dump_hierarchy()
import re
texts = re.findall(r'text="([^"]*)"', xml)
texts = [t for t in texts if t.strip()]
print('\n'.join(texts))
print("---")
# Also check content-desc
descs = re.findall(r'content-desc="([^"]*)"', xml)
descs = [t for t in descs if t.strip()]
print('\n'.join(descs))

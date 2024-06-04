import requests
from datetime import datetime

# GitHub URLs of list files
list_urls = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/QuantumultX/Gemini/Gemini.list",
    'https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/QuantumultX/OpenAI/OpenAI.list',
    'https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/QuantumultX/Claude/Claude.list',
    'https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/QuantumultX/Copilot/Copilot.list'，
    'https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/QuantumultX/Bing/Bing.list',
    # Add more URLs here
]

# Custom websites to add
custom_websites = [
    "HOST,perplexity.ai,Copilot",
]

# Fetch list files and merge contents
merged_list = set()
for url in list_urls:
    response = requests.get(url)
    merged_list.update(response.text.split("\n"))

# Add custom websites
merged_list.update(custom_websites)

# Write merged list to file
filename = f"merged-list.txt"
with open(filename, "w") as f:
    f.write("\n".join(merged_list))

# Commit changes to GitHub repository
# (Requires Git setup and authentication)
import subprocess
subprocess.run(["git", "add", filename])
subprocess.run(["git", "commit", "-m", f"Updated merged list: {now}"])
subprocess.run(["git", "push"])

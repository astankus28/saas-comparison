import json
import itertools

# 1. Load your data
with open('tools.json', 'r') as f:
    tools = json.load(f)

# 2. Define the HTML Template (Simplified version of what we built)
template = """
<!DOCTYPE html>
<html>
<head><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-50 p-10">
    <div class="max-w-4xl mx-auto bg-white p-8 rounded-xl shadow">
        <h1 class="text-4xl font-bold text-center">{name1} vs {name2}</h1>
        <div class="grid grid-cols-2 gap-10 mt-10 text-center">
            <div class="p-4 border rounded">
                <h2 class="text-xl font-bold">{name1}</h2>
                <p>Price: ${price1}/mo</p>
                <p>Best For: {bestFor1}</p>
                <a href="{link1}" class="block mt-4 bg-blue-600 text-white py-2 rounded">Try {name1}</a>
            </div>
            <div class="p-4 border rounded">
                <h2 class="text-xl font-bold">{name2}</h2>
                <p>Price: ${price2}/mo</p>
                <p>Best For: {bestFor2}</p>
                <a href="{link2}" class="block mt-4 bg-green-600 text-white py-2 rounded">Try {name2}</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

# 3. Generate every combination
for tool1, tool2 in itertools.combinations(tools, 2):
    filename = f"{tool1['id']}-vs-{tool2['id']}.html"
    content = template.format(
        name1=tool1['name'], price1=tool1['price'], bestFor1=tool1['bestFor'], link1=tool1['link'],
        name2=tool2['name'], price2=tool2['price'], bestFor2=tool2['bestFor'], link2=tool2['link']
    )
    
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Generated: {filename}")

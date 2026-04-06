import json
import itertools

# 1. Load the data
with open('tools.json', 'r') as f:
    tools = json.load(f)

generated_links = []

# 2. Template for Comparison Pages
page_template = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <title>{name1} vs {name2} | 2026 Comparison</title>
</head>
<body class="bg-slate-50 p-8 text-slate-900 font-sans">
    <div class="max-w-4xl mx-auto bg-white p-10 rounded-3xl shadow-xl border border-slate-100">
        <h1 class="text-4xl font-black mb-4 text-center">{name1} <span class="text-slate-300">vs</span> {name2}</h1>
        <p class="text-center text-slate-500 mb-10">Detailed 2026 analysis for {bestFor1} and {bestFor2}.</p>
        
        <div class="grid md:grid-cols-2 gap-8 mb-10">
            <div class="p-6 border rounded-2xl bg-blue-50">
                <h2 class="text-2xl font-bold mb-2">{name1}</h2>
                <p class="text-sm font-bold text-blue-600 mb-4">{price1}</p>
                <p class="text-slate-600 mb-4"><strong>Pros:</strong> {pros1}</p>
                <a href="{link1}" class="block text-center bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition">Get Started &rarr;</a>
            </div>
            <div class="p-6 border rounded-2xl bg-slate-50">
                <h2 class="text-2xl font-bold mb-2">{name2}</h2>
                <p class="text-sm font-bold text-slate-600 mb-4">{price2}</p>
                <p class="text-slate-600 mb-4"><strong>Pros:</strong> {pros2}</p>
                <a href="{link2}" class="block text-center bg-slate-800 text-white py-3 rounded-lg font-bold hover:bg-slate-900 transition">View Pricing &rarr;</a>
            </div>
        </div>

        <div class="border-t pt-10">
            <h3 class="text-xl font-bold mb-4 italic text-blue-600">The Final Verdict</h3>
            <p class="text-lg text-slate-700 leading-relaxed mb-6">{name1} is {verdict1} Meanwhile, {name2} is {verdict2}</p>
            <div class="bg-slate-900 text-white p-6 rounded-xl">
                <p class="text-sm"><strong>Our Advice:</strong> Use <strong>{name1}</strong> if you need <strong>{bestFor1}</strong>. Choose <strong>{name2}</strong> if you prioritize <strong>{bestFor2}</strong>.</p>
            </div>
        </div>
        <div class="mt-10 text-center"><a href="index.html" class="text-slate-400 hover:text-blue-600">&larr; Back to all comparisons</a></div>
    </div>
</body>
</html>
"""

# 3. Generate all comparison pairs
for tool1, tool2 in itertools.combinations(tools, 2):
    filename = f"{tool1['id']}-vs-{tool2['id']}.html"
    content = page_template.format(
        name1=tool1['name'], price1=tool1['price'], bestFor1=tool1['bestFor'], link1=tool1['link'], pros1=tool1['pros'], verdict1=tool1['verdict'],
        name2=tool2['name'], price2=tool2['price'], bestFor2=tool2['bestFor'], link2=tool2['link'], pros2=tool2['pros'], verdict2=tool2['verdict']
    )
    with open(filename, 'w') as f:
        f.write(content)
    
    # Save link for the index page
    generated_links.append(f'<a href="{filename}" class="block p-4 bg-white border rounded-xl hover:shadow-md transition font-bold text-slate-700 hover:text-blue-600">{tool1["name"]} vs {tool2["name"]}</a>')

# 4. Generate the NEW Index.html
index_template = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <title>SaaS Scouter | Expert Tool Comparisons</title>
</head>
<body class="bg-slate-50 font-sans">
    <div class="max-w-6xl mx-auto p-12">
        <header class="text-center mb-16">
            <h1 class="text-6xl font-black text-slate-900 mb-4 tracking-tighter">SaaS<span class="text-blue-600">Scouter</span></h1>
            <p class="text-xl text-slate-500">Expertly scouting the best tech stacks for your business.</p>
        </header>
        
        <h2 class="text-2xl font-bold mb-8 border-l-4 border-blue-600 pl-4">All Comparisons</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {"".join(generated_links)}
        </div>
    </div>
</body>
</html>
"""
with open('index.html', 'w') as f:
    f.write(index_template)

print(f"Successfully built {len(generated_links)} pages and updated index.html")

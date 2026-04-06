import json
import itertools

# 1. Load the data
with open('tools.json', 'r') as f:
    tools = json.load(f)

generated_links = []

# 2. Re-designed Comparison Template (v3.0)
page_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>{name1} vs {name2} | SaaS Scouter 2026</title>
</head>
<body class="bg-slate-50 text-slate-900 font-sans antialiased">
    <nav class="bg-white border-b border-slate-200 p-4 sticky top-0 z-50">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
            <a href="index.html" class="font-black text-2xl tracking-tighter italic">SaaS<span class="text-blue-600">Scouter</span></a>
            <a href="index.html" class="text-sm font-bold text-slate-500 hover:text-blue-600">&larr; All Comparisons</a>
        </div>
    </nav>

    <main class="max-w-5xl mx-auto px-6 py-12">
        <div class="text-center mb-16">
            <div class="inline-block px-4 py-1.5 mb-6 text-xs font-bold tracking-widest text-blue-700 uppercase bg-blue-50 rounded-full">2026 Expert Analysis</div>
            <h1 class="text-4xl md:text-6xl font-black tracking-tight mb-4">{name1} <span class="text-slate-300 italic">vs</span> {name2}</h1>
            <p class="text-xl text-slate-500 max-w-2xl mx-auto">One is {verdict1} while the other {verdict2}</p>
        </div>

        <div class="grid md:grid-cols-2 gap-8 relative">
            <div class="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm hover:shadow-md transition">
                <div class="flex justify-between items-start mb-6">
                    <h2 class="text-3xl font-bold">{name1}</h2>
                    <span class="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-bold uppercase">{price1}</span>
                </div>
                <div class="space-y-4 mb-8">
                    <p class="text-sm font-bold text-slate-400 uppercase tracking-widest">Top Advantage</p>
                    <div class="bg-green-50 text-green-700 p-4 rounded-xl border border-green-100 italic">"{pros1}"</div>
                </div>
                <a href="{link1}" target="_blank" class="block w-full text-center py-4 bg-blue-600 text-white font-black rounded-2xl hover:bg-blue-700 transition shadow-lg shadow-blue-200">Get {name1} Now &rarr;</a>
            </div>

            <div class="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm hover:shadow-md transition">
                <div class="flex justify-between items-start mb-6">
                    <h2 class="text-3xl font-bold">{name2}</h2>
                    <span class="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-bold uppercase">{price2}</span>
                </div>
                <div class="space-y-4 mb-8">
                    <p class="text-sm font-bold text-slate-400 uppercase tracking-widest">Top Advantage</p>
                    <div class="bg-blue-50 text-blue-700 p-4 rounded-xl border border-blue-100 italic">"{pros2}"</div>
                </div>
                <a href="{link2}" target="_blank" class="block w-full text-center py-4 bg-slate-900 text-white font-black rounded-2xl hover:bg-black transition">Get {name2} Now &rarr;</a>
            </div>
        </div>

        <div class="mt-20 max-w-3xl mx-auto text-center">
            <h3 class="text-2xl font-black mb-6">Which one should you choose?</h3>
            <div class="bg-slate-100 p-10 rounded-3xl border-2 border-dashed border-slate-200">
                <p class="text-lg leading-relaxed text-slate-700 mb-0">
                    If your primary focus is <strong>{bestFor1}</strong>, then <strong>{name1}</strong> is clearly {verdict1} 
                    However, if you prioritize <strong>{bestFor2}</strong>, <strong>{name2}</strong> is the superior choice.
                </p>
            </div>
        </div>
    </main>

    <footer class="mt-20 border-t border-slate-200 py-12 text-center text-slate-400 text-sm">
        <p>© 2026 Andrew Stankus | SaaS Scouter</p>
    </footer>
</body>
</html>
"""

# 3. Generate pages (Same logic as before)
for tool1, tool2 in itertools.combinations(tools, 2):
    filename = f"{tool1['id']}-vs-{tool2['id']}.html"
    content = page_template.format(
        name1=tool1['name'], price1=tool1['price'], bestFor1=tool1['bestFor'], link1=tool1['link'], pros1=tool1['pros'], verdict1=tool1['verdict'],
        name2=tool2['name'], price2=tool2['price'], bestFor2=tool2['bestFor'], link2=tool2['link'], pros2=tool2['pros'], verdict2=tool2['verdict']
    )
    with open(filename, 'w') as f:
        f.write(content)
    
    generated_links.append(f'''
        <a href="{filename}" class="group bg-white border border-slate-200 p-6 rounded-2xl hover:border-blue-500 hover:shadow-xl transition-all">
            <div class="text-xs font-bold text-blue-600 mb-2 uppercase tracking-tighter">Comparison</div>
            <div class="font-black text-xl text-slate-900 group-hover:text-blue-600">{tool1["name"]} <span class="text-slate-300">vs</span> {tool2["name"]}</div>
        </a>
    ''')

# 4. Generate the NEW Index.html (v3.0)
index_template = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <title>SaaS Scouter | The Ultimate Tool Comparison Engine</title>
</head>
<body class="bg-slate-50 text-slate-900 font-sans antialiased">
    <div class="max-w-6xl mx-auto px-6 py-20">
        <header class="text-center mb-20">
            <div class="inline-block px-4 py-1 mb-6 text-xs font-black tracking-widest text-blue-600 uppercase bg-blue-50 rounded-full">Scouting the best tech since 2026</div>
            <h1 class="text-7xl font-black tracking-tighter mb-4 italic">SaaS<span class="text-blue-600 underline decoration-8 decoration-blue-100">Scouter</span></h1>
            <p class="text-xl text-slate-500 max-w-xl mx-auto font-medium leading-relaxed">Stop overpaying for software. We scout the 50+ top tech pairings to build your perfect stack.</p>
        </header>
        
        <div class="flex justify-between items-center mb-10">
            <h2 class="text-2xl font-black uppercase tracking-tight">Browse the Scout Files</h2>
            <span class="text-sm font-bold text-slate-400">{len(generated_links)} Comparisons Live</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {"".join(generated_links)}
        </div>
    </div>
</body>
</html>
"""
with open('index.html', 'w') as f:
    f.write(index_template)

import json
import itertools

with open('tools.json', 'r') as f:
    tools = json.load(f)

generated_links = []

# Page Template: Minimalist High-Contrast
page_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <title>{name1} vs {name2} | SaaS Scouter</title>
</head>
<body class="bg-white text-slate-800 font-sans antialiased">
    <nav class="p-6 max-w-6xl mx-auto flex justify-between items-center">
        <a href="index.html" class="text-xl font-bold tracking-tight text-slate-900 uppercase">SaaS<span class="text-blue-600">Scouter</span></a>
        <a href="index.html" class="text-xs font-medium text-slate-400 hover:text-slate-900 transition underline underline-offset-4">Back to Scout Files</a>
    </nav>

    <main class="max-w-4xl mx-auto px-6 py-20">
        <header class="mb-24">
            <h1 class="text-5xl font-light tracking-tight text-slate-900 mb-6">{name1} <span class="text-slate-300">/</span> {name2}</h1>
            <p class="text-lg text-slate-500 leading-relaxed max-w-xl">{name1} is {verdict1} whereas {name2} is {verdict2}</p>
        </header>

        <div class="space-y-32">
            <div class="grid md:grid-cols-2 gap-16 border-t border-slate-100 pt-12">
                <div>
                    <h2 class="text-2xl font-semibold mb-4">{name1}</h2>
                    <p class="text-slate-500 mb-8 leading-relaxed">{pros1}</p>
                    <a href="{link1}" target="_blank" class="inline-flex items-center gap-2 text-blue-600 font-semibold hover:gap-4 transition-all">
                        Try {name1} <span>&rarr;</span>
                    </a>
                </div>
                <div>
                    <h2 class="text-2xl font-semibold mb-4">{name2}</h2>
                    <p class="text-slate-500 mb-8 leading-relaxed">{pros2}</p>
                    <a href="{link2}" target="_blank" class="inline-flex items-center gap-2 text-blue-600 font-semibold hover:gap-4 transition-all">
                        Explore {name2} <span>&rarr;</span>
                    </a>
                </div>
            </div>

            <div class="bg-slate-50 p-12 rounded-2xl">
                <h3 class="text-xs font-bold uppercase tracking-widest text-slate-400 mb-6">The Scouting Report</h3>
                <p class="text-xl text-slate-800 leading-snug font-medium">
                    Choose <span class="text-blue-600">{name1}</span> if you need <span class="lowercase">{bestFor1}</span>. Choose <span class="text-blue-600">{name2}</span> if you prioritize <span class="lowercase">{bestFor2}</span>.
                </p>
            </div>
        </div>
    </main>

    <footer class="py-20 text-center border-t border-slate-50">
        <p class="text-xs text-slate-300 font-medium">© 2026 SaaS Scouter | Andrew Stankus</p>
    </footer>
</body>
</html>
"""

# Generate pages
for tool1, tool2 in itertools.combinations(tools, 2):
    filename = f"{tool1['id']}-vs-{tool2['id']}.html"
    content = page_template.format(
        name1=tool1['name'], price1=tool1['price'], bestFor1=tool1['bestFor'], link1=tool1['link'], pros1=tool1['pros'], verdict1=tool1['verdict'],
        name2=tool2['name'], price2=tool2['price'], bestFor2=tool2['bestFor'], link2=tool2['link'], pros2=tool2['pros'], verdict2=tool2['verdict']
    )
    with open(filename, 'w') as f:
        f.write(content)
    
    generated_links.append(f'''
        <a href="{filename}" class="py-4 border-b border-slate-100 flex justify-between items-center group">
            <span class="text-slate-600 group-hover:text-blue-600 transition font-medium">{tool1["name"]} vs {tool2["name"]}</span>
            <span class="text-slate-200 group-hover:text-blue-600 transition">&rarr;</span>
        </a>
    ''')

# Index Template: The "Clean List"
index_template = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <title>SaaS Scouter | 2026 Comparisons</title>
</head>
<body class="bg-white text-slate-900 font-sans antialiased">
    <div class="max-w-3xl mx-auto px-6 py-32">
        <header class="mb-24">
            <h1 class="text-xs font-bold tracking-[0.2em] uppercase text-blue-600 mb-8">SaaS Scouter</h1>
            <p class="text-4xl font-light tracking-tight text-slate-900 leading-tight">
                An objective guide to the <span class="italic text-slate-400">top 50+</span> software stacks for founders and agencies.
            </p>
        </header>
        
        <div class="space-y-1">
            <h2 class="text-xs font-bold uppercase text-slate-300 mb-6 tracking-widest">Index of Scout Files</h2>
            {"".join(generated_links)}
        </div>
    </div>
</body>
</html>
"""
with open('index.html', 'w') as f:
    f.write(index_template)

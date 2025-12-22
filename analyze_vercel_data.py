import json

with open('vercel_data.json', 'r') as f:
    games = json.load(f)

keyword = "ルネサンス"
found = []
for g in games:
    text = (
        (g.get('title') or '') + 
        (g.get('title_ja') or '') + 
        (g.get('title_en') or '') + 
        (g.get('summary') or '') + 
        (g.get('description') or '') + 
        (g.get('rules_content') or '')
    ).lower()
    if keyword in text:
        found.append(g['title'])

print(f"Total games: {len(games)}")
print(f"Games with '{keyword}':")
for title in found:
    print(f"- {title}")

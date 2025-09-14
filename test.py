import ansiconv

with open('logs/log_all.log', 'r', encoding='utf-8') as file:
    ansi = file.read()

print(f"Ansi: {ansi}")

plain = ansiconv.to_plain(ansi)

html = ansiconv.to_html(ansi)

print(f"Convert Plain: {plain}")

print(f"Convert HTML: {html}")
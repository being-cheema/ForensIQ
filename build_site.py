"""
build_site.py
=============
Embeds site/data.json into site/index.template.html and writes the self-contained site/index.html.
Run after export_site_data.py:  python build_site.py
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(BASE, "site")
data = open(os.path.join(SITE, "data.json"), encoding="utf-8").read().replace("</", "<\\/")
tpl = open(os.path.join(SITE, "index.template.html"), encoding="utf-8").read()
out = tpl.replace("/*__DATA__*/", data)


def ascii_safe(doc):
    """Escape non-ASCII so the page renders the same whatever charset the host assumes."""
    head, _, rest = doc.partition('<script>\n(function')
    js, sep, tail = rest.partition('</script>')
    esc_html = lambda t: "".join(c if ord(c) < 128 else f"&#x{ord(c):X};" for c in t)
    esc_js = lambda t: "".join(c if ord(c) < 128 else f"\\u{ord(c):04x}" for c in t)
    return esc_html(head) + '<script>\n(function' + esc_js(js) + sep + esc_html(tail)


out = ascii_safe(out)
with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
    f.write(out)
print("[+] wrote site/index.html", len(out) // 1024, "KB")

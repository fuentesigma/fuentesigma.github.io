#!/usr/bin/env python3
"""
Turn Markdown entries into pages of the site, and rebuild the landing page.

An entry is a directory holding either index.md or a hand-written index.html.
Directories with an index.md are generated from it. Directories with only an
index.html are left exactly as they are, so the two kinds live side by side.

    python3 build.py            build everything, rewrite the index
    python3 build.py frames     build one entry, rewrite the index
    python3 build.py --check    report what would change, write nothing

Nothing is installed and nothing is imported beyond the standard library.
"""

import html as _html
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {"template", ".git", ".github", "figures"}

# ---------------------------------------------------------------- front matter

def split_front_matter(text):
    """Return (dict, body). The block is `key: value` lines between --- fences."""
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            text = text[end + 4 :]
    return meta, text.lstrip("\n")


# ---------------------------------------------------------------- inline pass

def inline(text, math, eqnums):
    """Inline markdown to HTML. Maths is lifted out before anything else runs,
    so that underscores and asterisks inside it are never read as emphasis."""
    def lift(m):
        math.append(m.group(1))
        return "\x00M%d\x00" % (len(math) - 1)

    text = re.sub(r"(?<!\\)\$(.+?)(?<!\\)\$", lift, text, flags=re.S)
    text = re.sub(r"`([^`]+)`", lambda m: "\x00C%s\x00" % _html.escape(m.group(1)), text)

    text = _html.escape(text, quote=False)

    # @eq:label -> the number that equation carries
    text = re.sub(r"@eq:([A-Za-z0-9_-]+)",
                  lambda m: "eq.&nbsp;%s" % eqnums.get(m.group(1), "?"), text)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = text.replace("---", "&mdash;").replace("--", "&ndash;")

    text = re.sub(r"\x00C(.*?)\x00", r"<code>\1</code>", text, flags=re.S)
    for i, m in enumerate(math):
        text = text.replace("\x00M%d\x00" % i,
                            "\\(" + m.replace("<", "&lt;").replace(">", "&gt;") + "\\)")
    return " ".join(text.split())


# ---------------------------------------------------------------- block pass

def number_equations(body):
    """Assign numbers to $$...$$ blocks and map {#eq:label} to them."""
    eqnums, n = {}, 0
    for m in re.finditer(r"^\$\$(.*?)\$\$([^\n]*)$", body, re.S | re.M):
        trailer = m.group(2)
        if "{-}" in trailer:
            continue
        n += 1
        lab = re.search(r"\{#eq:([A-Za-z0-9_-]+)\}", trailer)
        if lab:
            eqnums[lab.group(1)] = n
    return eqnums


def render_blocks(body, eqnums):
    """Markdown blocks to the constructions style.css provides."""
    out, math, eqn = [], [], 0
    blocks = re.split(r"\n\s*\n", body)
    i = 0
    while i < len(blocks):
        b = blocks[i].strip()
        i += 1
        if not b:
            continue

        # display equation
        m = re.match(r"^\$\$(.*?)\$\$([^\n]*)$", b, re.S)
        if m:
            tex = m.group(1).strip().replace("<", "&lt;").replace(">", "&gt;")
            if "{-}" in m.group(2):
                tag = ""
            else:
                eqn += 1
                tag = '<span class="tag">eq. %d</span>' % eqn
            out.append('      <div class="eq">%s\n        \\[ %s \\]\n      </div>' % (tag, tex))
            continue

        # aside
        if b.startswith(">"):
            txt = " ".join(l.lstrip("> ").rstrip() for l in b.split("\n"))
            out.append('      <div class="note">\n        <p>%s</p>\n      </div>'
                       % inline(txt, math, eqnums))
            continue

        # code excerpt
        if b.startswith("```"):
            first, _, rest = b.partition("\n")
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', first))
            code = rest.rsplit("```", 1)[0].rstrip("\n")
            if attrs.get("file"):
                out.append('      <div class="file"><span>%s</span><span>%s</span></div>'
                           % (_html.escape(attrs["file"]), _html.escape(attrs.get("role", ""))))
            out.append("<pre><code>%s</code></pre>" % _html.escape(code))
            continue

        # figure
        m = re.match(r"^!\[(.*?)\]\((.*?)\)(.*)$", b, re.S)
        if m:
            cap, src, attrs = m.group(1), m.group(2), m.group(3)
            a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
            out.append(
                '      <figure>\n'
                '        <img src="%s" alt="%s" width="%s" height="%s" loading="lazy">\n'
                '        <figcaption class="caption"><span class="n">Fig. %s</span>'
                '<span>%s</span></figcaption>\n      </figure>'
                % (_html.escape(src), _html.escape(a.get("alt", cap)),
                   a.get("width", "560"), a.get("height", "280"),
                   a.get("n", str(len([o for o in out if "<figure>" in o]) + 1)),
                   inline(cap, math, eqnums)))
            continue

        # table
        if b.startswith("|"):
            rows = [r for r in b.split("\n") if r.strip().startswith("|")]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head, data = cells[0], cells[2:] if len(cells) > 2 else []
            t = ['      <div class="table-wrap">', "        <table>", "          <thead><tr>"]
            t += ["<th>%s</th>" % inline(c, math, eqnums) for c in head]
            t += ["</tr></thead>", "          <tbody>"]
            for r in data:
                t.append("            <tr>" + "".join(
                    '<td%s>%s</td>' % (' class="num"' if re.fullmatch(r"[-\d.,eE+]+", c) else "",
                                       inline(c, math, eqnums)) for c in r) + "</tr>")
            t += ["          </tbody>", "        </table>", "      </div>"]
            out.append("\n".join(t))
            continue

        # lists
        if re.match(r"^(\d+\.|[-*])\s", b):
            ordered = bool(re.match(r"^\d+\.", b))
            items = re.split(r"\n(?=(?:\d+\.|[-*])\s)", b)
            tag = "ol" if ordered else "ul"
            cls = ' class="refs"' if ordered and getattr(render_blocks, "_in_refs", False) else ""
            lis = "".join("        <li>%s</li>\n"
                          % inline(re.sub(r"^(?:\d+\.|[-*])\s*", "", it.strip()), math, eqnums)
                          for it in items)
            out.append("      <%s%s>\n%s      </%s>" % (tag, cls, lis, tag))
            continue

        out.append("      <p>%s</p>" % inline(b, math, eqnums))
    return "\n\n".join(out)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def build_sections(body, eqnums):
    """Split on ## headings, wrap each in the row/body scaffold, build the toc."""
    parts = re.split(r"^##\s+(.+)$", body, flags=re.M)
    lead, secs = parts[0], [(parts[i], parts[i + 1]) for i in range(1, len(parts), 2)]
    toc, html_secs = [], []
    for n, (title, content) in enumerate(secs, 1):
        m = re.search(r"\{#([A-Za-z0-9_-]+)\}", title)
        sid = m.group(1) if m else slugify(title)
        title = re.sub(r"\s*\{#[A-Za-z0-9_-]+\}", "", title).strip()
        render_blocks._in_refs = title.lower().startswith("reference")
        toc.append('        <li><a href="#%s"><span class="n">%02d</span>'
                   '<span class="t">%s</span></a></li>' % (sid, n, _html.escape(title)))
        html_secs.append(
            '<!-- ============================================== %02d -->\n'
            '<section id="%s">\n  <div class="row">\n    <div class="body">\n'
            '      <h2>%s</h2>\n\n%s\n    </div>\n  </div>\n</section>'
            % (n, sid, _html.escape(title), render_blocks(content.strip(), eqnums)))
    return lead.strip(), toc, html_secs


PAGE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="J. Fuentes Aguilar">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:url" content="https://fuentesigma.github.io/{slug}/">
<link rel="canonical" href="https://fuentesigma.github.io/{slug}/">
<meta name="twitter:card" content="summary">

<link rel="stylesheet" href="../style.css">

<!-- KaTeX: math rendering, no build step. Pinned version. -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css">
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js"></script>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js"></script>
<script>
  document.addEventListener("DOMContentLoaded", function () {{
    renderMathInElement(document.body, {{
      delimiters: [
        {{ left: "\\\\[", right: "\\\\]", display: true }},
        {{ left: "\\\\(", right: "\\\\)", display: false }}
      ],
      ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code"],
      throwOnError: false
    }});
  }});
</script>
</head>
<body class="flow">

<header class="bar">
  <a class="home" href="../"><span class="dot"></span>J. Fuentes Aguilar<span class="sep">/</span>notes</a>
</header>

<main id="top">

<!-- ============================================== HERO -->
<div class="hero">
  <div class="row wide">
    <div class="body">
      <h1>{title}</h1>
      <div class="year">{year}</div>
      <p class="lede">{lede}</p>
    </div>
  </div>
</div>

<!-- ============================================== TOC -->
<section style="padding-top:2.2rem">
  <div class="row wide">
    <div class="body">
      <ol class="toc">
{toc}
      </ol>
    </div>
  </div>
</section>

{sections}

</main>

<footer>
  <div class="row wide">
    <div class="body">
      Written by J. Fuentes Aguilar &ndash;&ndash; j.fuentesaquilar [at] gmail [dot] com <br>
      Last updated {updated}
    </div>
  </div>
</footer>

</body>
</html>
'''


def build_entry(slug):
    src = os.path.join(ROOT, slug, "index.md")
    meta, body = split_front_matter(open(src, encoding="utf-8").read())
    eqnums = number_equations(body)
    lede, toc, secs = build_sections(body, eqnums)
    math = []
    page = PAGE.format(
        title=_html.escape(meta.get("title", slug)),
        desc=_html.escape(meta.get("description", "")),
        slug=slug,
        year=_html.escape(meta.get("year", "")),
        lede=inline(lede, math, eqnums),
        toc="\n".join(toc),
        sections="\n\n".join(secs),
        updated=_html.escape(meta.get("updated", "")),
    )
    return page


# ---------------------------------------------------------------- landing page
#
# The landing page is hand-curated. Its blurbs are shorter than the ledes, and
# its titles and years do not always match the entry pages. So nothing here is
# generated from an entry's body. A Markdown entry supplies its own landing
# block through `summary:` in the front matter, and entries without an index.md
# are never touched.


def end_year(y):
    ns = re.findall(r"\b(1[89]\d\d|20\d\d)\b", y)
    if ns:
        return max(int(n) for n in ns)
    roman = re.search(r"\bM[MCDXLIVX]*\b", y)
    if roman:
        vals = {"M": 1000, "D": 500, "C": 100, "L": 50, "X": 10, "V": 5, "I": 1}
        t, prev = 0, 0
        for ch in reversed(roman.group(0)):
            v = vals.get(ch, 0)
            t += -v if v < prev else v
            prev = max(prev, v)
        return t
    return 0


LI = re.compile(r'        <li>\n          <a class="entry" href="([^/"]+)/">.*?\n        </li>\n',
                re.S)


def make_li(slug, meta):
    return ('        <li>\n          <a class="entry" href="%s/">\n'
            '            <h2>%s</h2>\n            <div class="year">%s</div>\n'
            '            <p>%s</p>\n          </a>\n        </li>\n'
            % (slug, meta.get("title", slug), meta.get("year", ""),
               meta.get("summary", "")))


def upsert_index(updates):
    """Insert or refresh the landing block of each Markdown entry. Every other
    block is copied through byte for byte."""
    p = os.path.join(ROOT, "index.html")
    s = open(p, encoding="utf-8").read()
    head, _, rest = s.partition('<ul class="entries">\n')
    listing, _, tail = rest.rpartition("      </ul>")

    blocks = []          # (slug, text)
    for m in LI.finditer(listing):
        blocks.append([m.group(1), m.group(0)])

    for slug, meta in updates.items():
        li = make_li(slug, meta)
        for b in blocks:
            if b[0] == slug:
                b[1] = li
                break
        else:
            yr = end_year(meta.get("year", ""))
            pos = len(blocks)
            for i, b in enumerate(blocks):
                m = re.search(r'<div class="year">(.*?)</div>', b[1], re.S)
                if yr > end_year(m.group(1) if m else ""):
                    pos = i
                    break
            blocks.insert(pos, [slug, li])

    listing_new = "\n" + "\n".join(b[1] for b in blocks) + "\n"
    return p, head + '<ul class="entries">\n' + listing_new + "      </ul>" + tail, \
           [b[0] for b in blocks]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    targets = args or sorted(
        d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d)) and d not in SKIP
        and os.path.exists(os.path.join(ROOT, d, "index.md")))

    changed = []
    for slug in targets:
        if not os.path.exists(os.path.join(ROOT, slug, "index.md")):
            print("  %-10s no index.md, left alone" % slug)
            continue
        page = build_entry(slug)
        dest = os.path.join(ROOT, slug, "index.html")
        old = open(dest, encoding="utf-8").read() if os.path.exists(dest) else ""
        if page != old:
            changed.append(slug)
            if not check:
                open(dest, "w", encoding="utf-8").write(page)
        print("  %-10s %s" % (slug, "would change" if check and page != old
                              else "built" if page != old else "unchanged"))

    updates = {}
    for slug in targets:
        src = os.path.join(ROOT, slug, "index.md")
        if os.path.exists(src):
            meta, _ = split_front_matter(open(src, encoding="utf-8").read())
            if meta.get("summary"):
                updates[slug] = meta
    p, new, order = upsert_index(updates)
    old = open(p, encoding="utf-8").read()
    if new != old:
        changed.append("index.html")
        if not check:
            open(p, "w", encoding="utf-8").write(new)
    print("  %-10s %s" % ("index.html",
                          "would change" if check and new != old
                          else "updated" if new != old else "unchanged"))
    print("  order: " + " ".join(order))
    if check and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()

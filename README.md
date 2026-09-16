# fuentesigma.github.io

Static site served by GitHub Pages at <https://fuentesigma.github.io/>. No build
step, no generator, no dependencies. `.nojekyll` tells Pages to serve the files
exactly as they are.

```
index.html          landing page, the list of entries
style.css           the whole design system, shared by every page
template/           skeleton for a new entry, not linked from anywhere
psidm/              Schrodinger-Poisson solver for wave dark matter
lion/               quantum machine learning with canonical variables
```

## Adding an entry

Four steps. Nothing else in the repository needs to change.

**1. Copy the skeleton.**

```sh
cp -r template <slug>
mkdir <slug>/figures
```

Pick a short lowercase slug with no spaces. It becomes the URL,
`https://fuentesigma.github.io/<slug>/`.

**2. Give the entry an accent colour.**

In `style.css`, under `SITE LEVEL`, add one line to each of the two lists:

```css
html[data-entry="<slug>"]         { --accent: #rrggbb; }
.entries > li[data-entry="<slug>"] { --accent: #rrggbb; }
```

The first colours the entry page, the second colours its row on the landing
page while the pointer is over it. The rest of the palette is fixed and is not
overridden per entry.

**3. Write the page.** Open `<slug>/index.html` and resolve every `REPLACE`
marker. The skeleton carries one example of each construction the design
system provides.

| construction | markup |
| --- | --- |
| section with a rail label | `<section id>` holding `.row` > `.label` + `.body` |
| continuation row | `.row` with an empty `.label` |
| numbered equation | `.eq` with a hand-written `.tag` |
| code excerpt | `.file` bar followed immediately by `<pre><code>` |
| figure | `<figure>` with `<img>` and `figcaption.caption` |
| two figures side by side | wrap them in `.fig-pair` |
| table | wrap in `.table-wrap` |
| aside | `.note` |
| references | `ol.refs`, numbered automatically |

Syntax highlighting inside `<pre>` is manual, with `<span class="k">` for
keywords, `<span class="s">` for strings and `<span class="c">` for comments.
Mathematics is rendered by KaTeX from a pinned CDN build, with `\(...\)` inline
and `\[...\]` displayed. Equation numbers are written by hand because KaTeX does
not number.

Every `<img>` needs `width`, `height`, `alt` and `loading="lazy"`. The
dimensions prevent the page from reflowing while the figures load.

**4. List it on the landing page.** Add one `<li data-entry="<slug>">` block to
`ul.entries` in the root `index.html`, copying the shape of an existing one.
Newest first. An entry with no page yet is listed with `class="entry soon"` on a
`<div>` instead of an `<a>`, which greys the row and removes the link.

## Figures

Figures are generated in the project directory that owns the data, never here.
Each project keeps its own script, and the output is copied into
`<slug>/figures/`. Line plots go in as SVG, images and animations as PNG or
WebP.

Converting a figure out of a LaTeX paper:

```sh
pdftoppm -png -r 200 -singlefile figure1.pdf <slug>/figures/figure1
```

## Before pushing

- Check the page at 1280 px and at 400 px.
- Confirm `og:image` is an absolute URL. Relative ones do not resolve in link
  previews.
- Confirm the footer date.
- Open the page with JavaScript disabled once. Everything except the
  mathematics should still read.

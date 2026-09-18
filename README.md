# fuentesigma.github.io

Static site served by GitHub Pages at <https://fuentesigma.github.io/>.

```
index.html          landing page, the list of entries
style.css           the whole design system, shared by every page
template/           skeleton for a new entry, not linked from anywhere
psidm/              Schrodinger-Poisson solver for wave dark matter
stokes/             non-abelian Stokes law for permutation-valued connections
lion/               quantum machine learning with canonical variables
frames/             on frames of reference
build.py            turns an entry written in Markdown into its page
```

## Adding an entry

This is for me to remember each time...

**1. Copy the skeleton.**

```sh
cp -r template <slug>
mkdir <slug>/figures
```

Pick a short lowercase slug with no spaces. It becomes the URL,
`https://fuentesigma.github.io/<slug>/`.

**2. Write the page.** Open `<slug>/index.html` and resolve every `REPLACE`
marker. The skeleton carries one example of each construction the design
system provides.

Every entry page is one column of a single width, set once as `--column` in
`:root`. `<body class="flow">` is what applies it, and it governs everything
on the page, the bar at the top, the title, the abstract, the text, the
equations, the figures and the footer. No element sets a width of its own, and
an equation too wide for the column scrolls inside its own box rather than
widening the page. There are no section numbers, no section subtitles and no
menu. The only navigation is the link back to the index in the top left
corner, and the table of contents under the abstract.

| construction | markup |
| --- | --- |
| section | `<section id>` holding `.row` > `.body`, with the `<h2>` first inside `.body` |
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

**3. List it on the landing page.** Add one `<li>` block to `ul.entries` in the
root `index.html`, copying the shape of an existing one. Each block is a title,
a `.year` line under it, and the abstract. An entry with no page yet is listed
with `class="entry soon"` on a `<div>` instead of an `<a>`, which greys the row
and removes the link.

There is one accent colour for the whole site, set once as `--accent` in
`:root`. Entry pages do not recolour themselves.

## Writing an entry in Markdown

An entry may be written either way. A directory holding an `index.html` and
nothing else is hand-written and is never touched by anything. A directory
holding an `index.md` has its `index.html` generated from it, and the file is
committed alongside the source so that Pages keeps serving files exactly as
they are.

```sh
mkdir <slug> && $EDITOR <slug>/index.md
python3 build.py <slug>        # or let the Action do it on push
```

`summary` is separate from the lede on purpose. The landing page is curated
and its blurbs are shorter than the openings of the entries they point at.
An entry without a `summary` is built but is not listed, and the landing
blocks of hand-written entries are copied through untouched.

The text before the first `##` becomes the lede. Every `##` becomes a section
and the table of contents is assembled from them, with the anchor taken from
the heading or written as `## Title {#anchor}`.

| construction | markup |
| --- | --- |
| section | `## Title`, or `## Title {#anchor}` |
| numbered equation | `$$ ... $$`, numbered in order of appearance |
| labelled equation | `$$ ... $$ {#eq:name}` |
| unnumbered equation | `$$ ... $$ {-}` |
| reference to one | `@eq:name`, which resolves to its number |
| inline mathematics | `$ ... $` |
| aside | `> a blockquote` |
| code excerpt | a fence carrying `file="path" role="what it is"` |
| figure | `![caption](figures/x.svg){width="560" height="280" alt="..."}` |
| table | an ordinary pipe table |
| references | a numbered list under a `## References` heading |

Equation numbers are assigned at build time, so inserting an equation
renumbers the ones after it and every `@eq:` reference follows. This is the
one thing the hand-written pages have to keep in order themselves.

`python3 build.py --check` builds nothing and exits non-zero if any page is
out of date with its source.


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
- Confirm `og:image` is an absolute URL. Relative ones do not resolve in link previews.
- Open the page with JavaScript disabled once. Everything except the
  mathematics should still read.

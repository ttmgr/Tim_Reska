"""Build the static blog from Markdown posts.

Reads every ``blog/posts/*.md`` file and writes:

* ``blog/<slug>/index.html``: one page per post.
* ``blog/index.html``: the list of posts, newest first.
* ``blog/feed.xml``: an RSS 2.0 feed.
* The "Latest posts" block and the "Blog" menu link in ``index.html``,
  between the ``BLOG:BEGIN/END`` and ``BLOG-NAV:BEGIN/END`` markers.
* The blog entries in ``sitemap.xml``, between the ``BLOG:BEGIN/END`` markers.

A post file starts with a small header, then Markdown::

    ---
    title: AI News Radar, week of 12 October 2026
    date: 2026-10-16
    series: AI News Radar
    summary: One or two sentences for the list and the feed.
    ---
    ## A heading
    A paragraph with **bold**, *italic*, `code` and [a link](https://...).

    - A list item

Only that subset of Markdown is supported, on purpose: no extra packages.

Usage::

    python3 scripts/build_blog.py                 # build everything
    python3 scripts/build_blog.py --preview FILE  # render one draft for review
"""

from __future__ import annotations

import argparse
import html
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import format_datetime
from pathlib import Path

log = logging.getLogger("build_blog")

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog"
POSTS = BLOG / "posts"
DRAFTS = BLOG / "_drafts_data_do_not_touch_if_not_prompted"
SITE_URL = "https://ttmgr.github.io/Tim_Reska/"
LATEST_ON_HOME = 3


@dataclass
class Post:
    """One blog post parsed from a Markdown file."""

    slug: str
    title: str
    day: date
    series: str
    summary: str
    body_md: str

    @property
    def url(self) -> str:
        """Absolute URL of the post page."""
        return f"{SITE_URL}blog/{self.slug}/"


# ---------------------------------------------------------------- Markdown


def _inline(text: str) -> str:
    """Convert inline Markdown (code, links, bold, italic) to HTML.

    Args:
        text: One line or paragraph of Markdown.

    Returns:
        The HTML string, with all other text escaped.
    """
    parts: list[str] = []
    # Split out code spans first so nothing inside them is converted.
    for i, chunk in enumerate(re.split(r"`([^`]+)`", text)):
        if i % 2:
            parts.append(f"<code>{html.escape(chunk)}</code>")
            continue
        chunk = html.escape(chunk, quote=False)
        chunk = re.sub(
            r"\[([^\]]+)\]\(([^)\s]+)\)",
            lambda m: f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">{m.group(1)}</a>'
            if m.group(2).startswith("http")
            else f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>',
            chunk,
        )
        chunk = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", chunk)
        chunk = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", chunk)
        parts.append(chunk)
    return "".join(parts)


def markdown_to_html(md: str) -> str:
    """Convert the supported Markdown subset to HTML.

    Supports ``##``/``###`` headings, paragraphs, ``-`` lists (one level,
    with indented continuation lines) and ``>`` quotes.

    Args:
        md: The Markdown body of a post.

    Returns:
        The HTML body.
    """
    out: list[str] = []
    para: list[str] = []
    items: list[str] = []
    quote: list[str] = []

    def flush() -> None:
        if para:
            out.append(f"<p>{_inline(' '.join(para))}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in items) + "</ul>")
            items.clear()
        if quote:
            out.append(f"<blockquote><p>{_inline(' '.join(quote))}</p></blockquote>")
            quote.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush()
        elif stripped.startswith("### "):
            flush()
            out.append(f"<h3>{_inline(stripped[4:])}</h3>")
        elif stripped.startswith("## "):
            flush()
            out.append(f"<h2>{_inline(stripped[3:])}</h2>")
        elif line.startswith("- "):
            if para or quote:
                flush()
            items.append(stripped[2:])
        elif stripped.startswith("> "):
            if para or items:
                flush()
            quote.append(stripped[2:])
        elif items and line.startswith("  "):
            items[-1] += " " + stripped
        else:
            if items or quote:
                flush()
            para.append(stripped)
    flush()
    return "\n".join(out)


# ---------------------------------------------------------------- Posts


def parse_post(path: Path) -> Post:
    """Read a post file and its header.

    Args:
        path: Path to a ``.md`` post.

    Returns:
        The parsed post.

    Raises:
        ValueError: If the header is missing or incomplete.
    """
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: missing '---' header")
    meta = dict(
        (k.strip(), v.strip())
        for k, v in (ln.split(":", 1) for ln in m.group(1).splitlines() if ":" in ln)
    )
    missing = [k for k in ("title", "date", "summary") if not meta.get(k)]
    if missing:
        raise ValueError(f"{path.name}: header is missing {', '.join(missing)}")
    return Post(
        slug=path.stem,
        title=meta["title"],
        day=date.fromisoformat(meta["date"]),
        series=meta.get("series", ""),
        summary=meta["summary"],
        body_md=m.group(2),
    )


def load_posts() -> list[Post]:
    """Load all published posts, newest first."""
    posts = [parse_post(p) for p in sorted(POSTS.glob("*.md"))]
    return sorted(posts, key=lambda p: (p.day, p.slug), reverse=True)


def nice_date(d: date) -> str:
    """Format a date as '16 October 2026'."""
    return f"{d.day} {d.strftime('%B %Y')}"


# ---------------------------------------------------------------- Pages


def page(title: str, description: str, body: str, up: str, canonical: str) -> str:
    """Wrap page content in the shared blog layout.

    Args:
        title: The ``<title>`` text.
        description: The meta description.
        body: HTML for inside ``<main>``.
        up: Relative path from this page to the site root, e.g. ``"../../"``.
        canonical: Absolute URL of this page.

    Returns:
        A complete HTML document.
    """
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <meta name="theme-color" content="#14223A">
    <title>{e(title)}</title>
    <meta name="description" content="{e(description)}">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(description)}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{e(canonical)}">
    <link rel="canonical" href="{e(canonical)}">
    <link rel="icon" type="image/svg+xml" href="{up}favicon.svg">
    <link rel="alternate" type="application/rss+xml" title="Tim Reska, blog" href="{up}blog/feed.xml">
    <link rel="stylesheet" href="{up}assets/css/fonts.css">
    <link rel="stylesheet" href="{up}assets/css/tokens.css">
    <link rel="stylesheet" href="{up}blog/blog.css">
    <link rel="stylesheet" href="{up}assets/css/theme-navy.css">
</head>
<body>
    <header class="topbar">
        <div class="wrap">
            <a class="home" href="{up}">Tim Reska</a>
            <nav aria-label="Sections">
                <ul>
                    <li><a href="{up}#research">Research</a></li>
                    <li><a href="{up}#benchmark">AI benchmark</a></li>
                    <li><a href="{up}#projects">Projects</a></li>
                    <li><a href="{up}blog/" aria-current="page">Blog</a></li>
                    <li><a href="{up}#timeline">Timeline</a></li>
                    <li><a href="{up}#contact">Contact</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <main class="wrap">
{body}
    </main>
    <footer>
        <div class="wrap">
            <ul>
                <li><a href="mailto:timreska@gmail.com">Email</a></li>
                <li><a href="https://linkedin.com/in/tim-r-ai" target="_blank" rel="noopener">LinkedIn</a></li>
                <li><a href="https://github.com/ttmgr" target="_blank" rel="noopener">GitHub</a></li>
                <li><a href="{up}blog/feed.xml">RSS feed</a></li>
            </ul>
            <small>Dr. rer. nat. Tim Reska</small>
        </div>
    </footer>
</body>
</html>
"""


def render_post(post: Post, up: str) -> str:
    """Render one post page."""
    e = html.escape
    meta = nice_date(post.day) + (f", {e(post.series)}" if post.series else "")
    body = f"""        <div class="head">
            <h1>{e(post.title)}</h1>
            <p class="meta"><time datetime="{post.day.isoformat()}">{meta}</time></p>
            <p class="summary">{_inline(post.summary)}</p>
            <hr class="rule">
        </div>
        <article class="post">
{markdown_to_html(post.body_md)}
        </article>
        <p class="back"><a href="{up}blog/">All posts</a></p>"""
    return page(f"{post.title} | Tim Reska", post.summary, body, up, post.url)


def render_index(posts: list[Post]) -> str:
    """Render the blog index page."""
    e = html.escape
    if posts:
        rows = "\n".join(
            f"""                <li>
                    <div class="date"><time datetime="{p.day.isoformat()}">{nice_date(p.day)}</time></div>
                    <div>
                        <p class="title"><a href="./{p.slug}/">{e(p.title)}</a></p>
                        {f'<p class="series">{e(p.series)}</p>' if p.series else ''}
                        <p class="sum">{_inline(p.summary)}</p>
                    </div>
                </li>"""
            for p in posts
        )
        listing = f'            <ul class="posts">\n{rows}\n            </ul>'
    else:
        listing = '            <p class="empty">No posts yet.</p>'
    body = f"""        <div class="head">
            <h1>Blog</h1>
            <p class="summary">Two news radars, one on AI coding tools and one on nanopore sequencing and metagenomics, plus occasional longer posts.</p>
            <hr class="rule">
        </div>
{listing}"""
    return page("Blog | Tim Reska", "News radars on AI coding tools and on nanopore sequencing and metagenomics, by Tim Reska.", body, "../", f"{SITE_URL}blog/")


def render_feed(posts: list[Post]) -> str:
    """Render the RSS 2.0 feed."""
    e = html.escape
    items = "\n".join(
        f"""    <item>
      <title>{e(p.title)}</title>
      <link>{p.url}</link>
      <guid isPermaLink="true">{p.url}</guid>
      <pubDate>{format_datetime(datetime(p.day.year, p.day.month, p.day.day, 8, tzinfo=timezone.utc))}</pubDate>
      <description>{e(p.summary)}</description>
    </item>"""
        for p in posts
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tim Reska, blog</title>
    <link>{SITE_URL}blog/</link>
    <description>Two news radars, one on AI coding tools and one on nanopore sequencing and metagenomics, plus occasional longer posts.</description>
    <language>en</language>
{items}
  </channel>
</rss>
"""


# ---------------------------------------------------------------- Homepage and sitemap


def replace_between(text: str, name: str, new: str, path: Path) -> str:
    """Replace the text between ``<!-- NAME:BEGIN -->`` and ``<!-- NAME:END -->``.

    Raises:
        ValueError: If the markers are missing.
    """
    pattern = re.compile(rf"(<!-- {name}:BEGIN -->)(.*?)([ \t]*<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"{path.name}: markers {name}:BEGIN/END not found")
    return pattern.sub(lambda m: m.group(1) + new + m.group(3), text, count=1)


def update_home(posts: list[Post]) -> None:
    """Write the 'Latest posts' block and the 'Blog' menu link on the homepage."""
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    e = html.escape
    nav = "\n                    <li><a href=\"./blog/\">Blog</a></li>\n" if posts else "\n"
    if posts:
        rows = "\n".join(
            f'                        <li><div class="when">{nice_date(p.day)}</div>'
            f'<div><h3><a href="./blog/{p.slug}/">{e(p.title)}</a></h3><p>{_inline(p.summary)}</p></div></li>'
            for p in posts[:LATEST_ON_HOME]
        )
        block = f"""
    <section id="blog">
        <div class="wrap row">
            <div>
                <h2>Blog</h2>
                <ul class="tl posts-home">
{rows}
                </ul>
                <p class="links"><a href="./blog/">All posts</a> <a href="./blog/feed.xml">RSS feed</a></p>
            </div>
        </div>
    </section>
"""
    else:
        block = "\n"
    text = replace_between(text, "BLOG-NAV", nav, path)
    text = replace_between(text, "BLOG", block, path)
    path.write_text(text, encoding="utf-8")


def update_sitemap(posts: list[Post]) -> None:
    """Write the blog URLs into sitemap.xml."""
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    urls = [(f"{SITE_URL}blog/", posts[0].day if posts else None)] + [(p.url, p.day) for p in posts]
    entries = "".join(
        f"\n  <url>\n    <loc>{u}</loc>\n    <lastmod>{d.isoformat()}</lastmod>\n  </url>" for u, d in urls if d
    )
    text = replace_between(text, "BLOG", entries + "\n", path)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- Main


def build() -> None:
    """Build every blog page, the feed, and the homepage and sitemap entries."""
    posts = load_posts()
    BLOG.mkdir(exist_ok=True)
    for post in posts:
        out = BLOG / post.slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_post(post, "../../"), encoding="utf-8")
        log.info("wrote %s", out.relative_to(ROOT))
    (BLOG / "index.html").write_text(render_index(posts), encoding="utf-8")
    (BLOG / "feed.xml").write_text(render_feed(posts), encoding="utf-8")
    update_home(posts)
    update_sitemap(posts)
    log.info("built %d post(s), index, feed, homepage block, sitemap", len(posts))


def preview(path: Path) -> Path:
    """Render one draft into the drafts folder for review. Publishes nothing.

    Args:
        path: The draft ``.md`` file.

    Returns:
        Path of the rendered preview page.
    """
    post = parse_post(path)
    out = DRAFTS / "preview" / post.slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_post(post, "../../../../"), encoding="utf-8")
    log.info("preview: %s", out.relative_to(ROOT))
    return out


def main() -> None:
    """Command-line entry point."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--preview", type=Path, help="render one draft for review instead of building")
    args = parser.parse_args()
    if args.preview:
        preview(args.preview)
    else:
        build()


if __name__ == "__main__":
    main()

Add a new piece of content (case study, tutorial, or blog post) from a Google Docs HTML export and accompanying images.

The user will provide:
- Path to the HTML file (Google Docs export)
- Path to the images directory
- Content type: `case-studies`, `tutorials`, or `blog`
- Slug (URL-safe identifier, e.g. `spatial-accessibility-public-healthcare`)

## Step 1 — Read the source HTML

Read the HTML file in full. Extract all text content and note each image reference (`images/image1.png`, etc.) alongside its figure caption or surrounding text so you can give each image a meaningful filename later.

Do not summarize or condense the source text. Every paragraph, sentence, table, and section heading from the HTML must appear in the final markdown.

## Step 2 — Determine directory structure and paths

**Case studies** (`content/case-studies/<slug>/`):
- Content file: `content/case-studies/<slug>/index.md`
- Images: `content/case-studies/<slug>/img/`
- `thumbnail`: `"<slug>/img/<image>.webp"`
- `og_image`: `"case-studies/<slug>/img/<image>.webp"`
- `subtitle`: use the document's own subtitle or a short descriptor (e.g. `"District-scale study"`, `"Regional scale study"`, `"Community-driven mapping"`)

**Tutorials** (`content/tutorials/<slug>/`):
- Content file: `content/tutorials/<slug>/index.md`
- Images: `content/tutorials/<slug>/img/`
- `thumbnail`: `"<slug>/img/<image>.webp"`
- `og_image`: `"tutorials/<slug>/img/<image>.webp"`
- `subtitle`: `"Step-by-step guides by the community"`

**Blog** (`content/blog/`):
- Content file: `content/blog/<slug>.md` (flat file, not a bundle)
- Images: `content/blog/img/<slug>/`
- `thumbnail`: `"./img/<slug>/<image>.webp"`
- `og_image`: `"blog/img/<slug>/<image>.webp"`
- `subtitle`: `"Tips, resources, and articles for QGIS users"`
- Add `author` field with the author's name

## Step 3 — Convert images

Create the target images directory, then convert every PNG to webp using `cwebp`. If `cwebp` is not available, prompt the user to install it and help with the install.

```bash
mkdir -p <target-img-dir>
cwebp <source>/image1.png -o <target-img-dir>/<descriptive-name>.webp
```

Name each webp file descriptively based on the figure caption or subject (e.g. `study_area_map.webp`, `buffer_analysis.webp`), not `image1.webp`. Map the original filenames to your chosen names as you go — you will need this mapping when writing the markdown.

## Step 4 — Write the frontmatter

Use today's date for `date`. Choose the thumbnail image that best represents the content (a map or key figure, not a screenshot of a UI).

```yaml
---
type: "page"
title: "<full title from document>"
subtitle: "<per content type, see above>"
draft: false
date: <YYYY-MM-DD>
sidebar: true
thumbnail: "<path per content type>"
og_image: "<path per content type>"
---
```

Blog posts also include:
```yaml
author: "<Author Name>"
```

## Step 5 — Write the markdown content

Open with the Hugo shortcode, then the H1 title:

```
{{< content-start >}}

# <title>
```

Then convert the full HTML body to markdown, following these rules:

**Faithfulness** — reproduce every paragraph word-for-word. Do not paraphrase, condense, or omit any content. Include all in-text citations, footnotes, acknowledgements, funding statements, and reference lists.

**Section headings** — use `##` for top-level sections (Introduction, Study Area, Conclusion, etc.) and `###` for subsections.

**Images** — replace each `<img src="images/imageN.png">` with the figure block below, using the descriptive webp filename you assigned:

```html
<p align="center">
  <img src="img/<descriptive-name>.webp" alt="<alt text from caption>">
</p>
<p align="center"><em>Fig. N. <caption text></em></p>
```

For blog posts the path is `img/<slug>/<descriptive-name>.webp`.

**Tables** — convert HTML tables to GFM markdown tables.

**Bold/italic** — preserve emphasis from the original.

**Links** — preserve all hyperlinks. Google Docs export wraps links in redirect URLs (`https://www.google.com/url?q=...`); extract the actual `q=` target URL and use that directly.

**References** — reproduce the full reference list including DOIs as plain text (not hyperlinks). Keep the exact author lists; do not collapse to "et al." unless the original does.

Close with:

```
{{< content-end >}}
```

## Step 6 — Verify

After writing the file:
1. Confirm all images referenced in the markdown exist in the target img directory.
2. Confirm the thumbnail image path is one of the converted images.
3. Check that no HTML from the source was skipped (cross-check section headings in the HTML against the markdown).

## Notes

- `cwebp` is available at `/opt/local/bin/cwebp`
- The source images from Google Docs exports are named `image1.png`, `image2.png`, etc. — always rename them to something descriptive
- If the user later provides updated source images, reconvert only the changed files: check modification timestamps or ask which images changed
- The `date` field controls ordering on listing pages (newest first); always set it to today for new content
- Do not add a `date` to `_index.md` section index files

# Codex prompt: portfolio source fixes + ENPH 353 project page

You are editing the GitHub Pages/Jekyll repository `EzraKlukas/ezraklukas.github.io`.

## Goals

1. Fix project-page image scaling so markdown images, project-card thumbnails, project header images, and inline videos render sensibly on desktop and mobile.
2. Enable LaTeX math rendering for inline `$...$` and display `$$...$$` math, as well as `\(...\)` and `\[...\]` if already used in posts.
3. Add a new ENPH 353 project page under `_projects/enph353_autonomous_robot/`, using the provided `index.md`, extracted images, final report PDF, and optional video snippets.
4. Extract the useful images from the provided ENPH 353 final report PDF if the image files are not already provided.
5. Configure local mp4 snippets from the Google Drive video link referenced in the report, so they embed cleanly in markdown.

## Existing context

The site uses a Jekyll `projects` collection with `permalink: /projects/:path/`. Existing project pages live under `_projects/<project-name>/index.md`, and project assets are generally stored in the same directory as the corresponding `index.md`.

The current CSS has these issues:

- `.project-card img` forces `aspect-ratio: 3/1` and `object-fit: cover`, which crops many images too aggressively.
- `.post-view .summary img` also forces `aspect-ratio: 3/1`, `height: 100%`, and `object-fit: cover`, so project header images are cropped rather than displayed intentionally.
- There is no general rule for normal markdown images inside `.post-view .content`, so large images can render at awkward intrinsic sizes or behave inconsistently.
- There is no consistent styling for `<figure>`, `<figcaption>`, or local `<video>` embeds in project posts.
- Math is currently emitted as raw `$...$`, `$$...$$`, `\(...\)`, or `\[...\]` text because no MathJax/KaTeX script is loaded.

## Task 1: CSS image/video scaling fixes

Edit `css/styles.css`. Preserve the overall visual style, but patch the project image rules. Search for the existing project-card, post summary, image-gallery, and youtube styles. Replace or augment them with rules equivalent to the following.

```css
/* Project cards on the home/projects grids */
.project-card img {
  width: 100%;
  max-width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
  border-radius: 6px;
  margin-bottom: 10px;
  background: var(--light-background-color);
}

/* Main image at the top of a project post */
.post-view .summary img {
  width: 100%;
  max-height: 420px;
  height: auto;
  object-fit: contain;
  border-radius: 6px;
  margin-bottom: 10px;
  background: var(--light-background-color);
}

/* Normal markdown images inside project posts */
.post-view .content img {
  display: block;
  max-width: 100%;
  width: auto;
  height: auto;
  max-height: 80vh;
  object-fit: contain;
  margin: 1.25rem auto;
  border-radius: 6px;
}

/* Optional wrappers for images that should intentionally fill the text column */
.post-view .content .wide-img img,
.post-view .content img.wide-img {
  width: 100%;
  max-width: 100%;
}

.post-view .content figure {
  margin: 1.5rem auto;
  text-align: center;
}

.post-view .content figure img {
  margin-bottom: 0.5rem;
}

.post-view .content figcaption {
  color: var(--text-color);
  opacity: 0.8;
  font-size: calc(8px + 0.45vw);
  line-height: 1.4;
}

/* Local video embeds */
.video-container {
  width: 100%;
  max-width: 960px;
  margin: 1.5rem auto;
}

.post-video,
.video-container video {
  display: block;
  width: 100%;
  height: auto;
  max-height: 80vh;
  border-radius: 8px;
  background: #000;
}

.youtube-container {
  width: 100%;
  max-width: 960px;
  margin: 1.5rem auto;
  padding: 0;
}
```

In the mobile media query, keep the post padding small, but do not force images smaller than the content column. Add this if needed:

```css
@media (max-width: 768px) {
  .post-view .content img {
    max-height: none;
  }

  .post-view .summary img {
    max-height: 260px;
  }

  .video-container {
    margin: 1rem auto;
  }
}
```

Do not edit files under `_site/`; only source files should be changed.

## Task 2: enable LaTeX rendering

Add MathJax globally. The simplest robust approach is to create `_includes/mathjax.html`:

```html
<script>
  window.MathJax = {
    tex: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    }
  };
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
```

Then include it once in `_layouts/wrapper.html`, preferably after `{{content}}` and before the footer include, or at the end of the file if that is easiest:

```liquid
{% include mathjax.html %}
```

Verify locally that math in the motor control post renders for both display math and inline math.

## Task 3: add the ENPH 353 project page

Create:

```text
_projects/enph353_autonomous_robot/
  index.md
  final_report.pdf
  competition_surface.png
  software_architecture.png
  driving_masks.png
  npc_masks.png
  hill_cnn_input.png
  side_camera_views.png
  plate_pipeline.png
  text_mask_weakening.png
  character_distribution.png
  driving_cnn_loss.png
  character_cnn_loss.png
  model_size_comparison.png
  kappa_gui.png
```

Use the provided `index.md` for the page content.

If the images are not already provided, extract them from `Final Report.pdf` using PyMuPDF or `pdfimages`. Suggested names:

- Figure 1/course map -> `competition_surface.png`
- Figure 2/software diagram -> `software_architecture.png`
- Figure 3/driving masks -> `driving_masks.png` (stitch the three masks into one image if extracted separately)
- Figure 4/NPC masks -> `npc_masks.png` (stitch the three masks into one image if extracted separately)
- Figure 5/sample hill input -> `hill_cnn_input.png`
- Figure 6/character extraction steps -> `plate_pipeline.png` (stitch the intermediate images into one horizontal image if extracted separately)
- Figure 7/side camera views -> `side_camera_views.png`
- Figure 8/text mask weakening -> `text_mask_weakening.png`
- Figure 9/character frequency histogram -> `character_distribution.png`
- Figure 10/kappa GUI -> `kappa_gui.png`
- Figure 11/driving CNN loss -> `driving_cnn_loss.png`
- Figure 12/character CNN loss -> `character_cnn_loss.png`
- Figure 13/model size comparison -> `model_size_comparison.png`

A workable extraction script:

```python
from pathlib import Path
from PIL import Image
import fitz
import shutil

pdf_path = Path('Final Report.pdf')
out = Path('_projects/enph353_autonomous_robot')
out.mkdir(parents=True, exist_ok=True)

doc = fitz.open(pdf_path)
raw = out / '_raw_extracted'
raw.mkdir(exist_ok=True)

for pno, page in enumerate(doc, start=1):
    for ino, img in enumerate(page.get_images(full=True), start=1):
        xref = img[0]
        pix = fitz.Pixmap(doc, xref)
        if pix.n - pix.alpha > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        pix.save(raw / f'p{pno:02d}_img{ino:02d}.png')

# Rename/copy the obvious single-image figures based on the report layout.
mapping = {
    'p03_img01.png': 'competition_surface.png',
    'p04_img01.png': 'software_architecture.png',
    'p07_img01.png': 'hill_cnn_input.png',
    'p08_img06.png': 'side_camera_views.png',
    'p09_img01.png': 'text_mask_weakening.png',
    'p10_img01.png': 'character_distribution.png',
    'p11_img01.png': 'kappa_gui.png',
    'p15_img01.png': 'driving_cnn_loss.png',
    'p15_img02.png': 'character_cnn_loss.png',
    'p16_img01.png': 'model_size_comparison.png',
}
for src_name, dest_name in mapping.items():
    shutil.copy(raw / src_name, out / dest_name)

def concat_horizontal(src_names, dest_name, pad=6):
    imgs = [Image.open(raw / name).convert('RGB') for name in src_names]
    max_h = max(img.height for img in imgs)
    total_w = sum(img.width for img in imgs) + pad * (len(imgs) - 1)
    canvas = Image.new('RGB', (total_w, max_h), 'white')
    x = 0
    for img in imgs:
        canvas.paste(img, (x, (max_h - img.height) // 2))
        x += img.width + pad
    canvas.save(out / dest_name)

concat_horizontal(['p05_img01.png', 'p05_img02.png', 'p05_img03.png'], 'driving_masks.png')
concat_horizontal(['p06_img01.png', 'p06_img02.png', 'p06_img03.png'], 'npc_masks.png')
concat_horizontal(['p08_img01.png', 'p08_img02.png', 'p08_img03.png', 'p08_img04.png', 'p08_img05.png'], 'plate_pipeline.png', pad=4)
```

## Task 4: video snippets

The final report links to a Google Drive video of four uncut expected-performance runs. Download it manually or with `yt-dlp`/`gdown` if permissions allow.

The report timestamps are:

- Run 1: `0:00-1:47`, 37 points
- Run 2: `2:34-4:15`, 49 points
- Run 3: `4:43-5:56`, 28 points, cut short
- Run 4: `6:29-8:17`, 50 points, with note about forgotten respawn penalty

Save the downloaded source video outside the repo, then create local web-friendly snippets. Example commands:

```bash
mkdir -p _projects/enph353_autonomous_robot

# Best full-run demonstration, from the report timestamps.
ffmpeg -ss 00:06:29 -to 00:08:17 -i full_expected_runs.mp4 \
  -vf "scale='min(1280,iw)':-2" -c:v libx264 -crf 24 -preset medium \
  -c:a aac -b:a 128k -movflags +faststart \
  _projects/enph353_autonomous_robot/expected_run_4.mp4

# Optional shorter clip from the first run. Adjust the exact time after viewing the source.
ffmpeg -ss 00:00:00 -to 00:00:35 -i full_expected_runs.mp4 \
  -vf "scale='min(1280,iw)':-2" -c:v libx264 -crf 24 -preset medium \
  -c:a aac -b:a 128k -movflags +faststart \
  _projects/enph353_autonomous_robot/sign_reading_clip.mp4
```

If the `sign_reading_clip.mp4` segment does not actually show sign reading clearly, pick a better 10-20 second segment from the same video and keep the output filename the same so the markdown link works.

Keep each mp4 reasonably small. If a file is too large for the repo, reduce resolution to 720p and/or increase CRF to 28.

## Task 5: verify locally

Run:

```bash
bundle exec jekyll serve
```

Then check:

- `/projects/motor_control_circuit/index/`: math renders and existing images still look good.
- `/projects/ubckin/index/`: long equations render and images stay within the text column.
- `/projects/enph353_autonomous_robot/index/`: images render, videos load if present, and the project appears on the home/projects grid.
- Mobile viewport: project cards do not crop absurdly, post images do not overflow, and videos scale to the content column.

Commit only source files and final assets. Do not commit `_site/`, temporary extracted image folders, downloaded full-length videos, or build artifacts.

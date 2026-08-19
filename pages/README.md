# Spectrometer Projects — GitHub Pages

This is a static website generated from the four folders in `pages.zip`. The Python code files were intentionally left out for now so the markdown content and images stay prominent.

## Publish on GitHub Pages

1. Create a new GitHub repository.
2. Upload everything in this folder to the **root** of the repository.
3. Commit/push the files.
4. In GitHub, open **Settings → Pages**.
5. Under **Build and deployment**, choose **Deploy from a branch**.
6. Select your main branch (usually `main`) and the `/ (root)` folder, then save.
7. GitHub will show the public Pages URL after deployment finishes.

## Structure

- `index.html` — intentionally empty main page, with navigation only
- `diy.html` — DIY folder markdown + images
- `freeform.html` — Freeform folder markdown + images
- `overviews.html` — combines the three Overviews markdown documents + image
- `solex.html` — SolEx markdown + images
- `assets/` — copied images
- `styles.css` — shared responsive styling

To change text later, edit the corresponding HTML page. To add code content later, you can add a new section to each page without changing the site structure.

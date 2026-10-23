"""Reconstruct occupancy-grid maps from the figures of Li, Li & Dai (Sensors 2024, 24, 6929).

The paper does not release its maps.  Every map figure is a MATLAB grid plot whose axes
frame spans exactly N x N cells, obstacles are dark-grey cells, start = red dot and
goal = green dot.  This module:
  1. renders a PDF page at high resolution (PyMuPDF),
  2. locates each sub-plot frame (largest connected non-white regions),
  3. samples the centre of every cell and classifies it as obstacle (dark grey),
  4. detects the start/goal dots (red/green blobs),
  5. merges the sub-figures of one map (Fig. 8a-e show the same map five times)
     by majority vote, which removes artefacts from the drawn paths.

Convention used everywhere in this project
  grid[r, c]  with r = 0 the BOTTOM row (paper y = 1) and c = 0 the LEFT column (paper x = 1)
  value 1 = obstacle, 0 = free.  Points are (c, r) = (paper_x - 1, paper_y - 1).
"""
from __future__ import annotations
import numpy as np
import cv2

try:
    import pymupdf as fitz
except ImportError:          # older PyMuPDF
    import fitz


# --------------------------------------------------------------------------- rendering
def render_page(pdf_path: str, page_number: int, dpi: int = 800) -> np.ndarray:
    """Render 1-indexed page to an RGB uint8 array."""
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    doc.close()
    return img[:, :, :3].copy()


# --------------------------------------------------------------------------- frames
def find_plot_frames(img: np.ndarray, min_frac: float = 0.10):
    """Return bounding boxes (x, y, w, h) of sub-plot frames, sorted row-major."""
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    mask = (gray < 245).astype(np.uint8)
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    H, W = gray.shape
    boxes = [tuple(int(v) for v in s[:4]) for s in stats[1:]
             if s[2] > min_frac * W and s[3] > min_frac * W * 0.6]
    row_tol = 0.05 * H
    boxes.sort(key=lambda b: (round(b[1] / row_tol), b[0]))
    return boxes


def refine_frame(img: np.ndarray, box, margin: int = 6):
    """Tighten a box to the dark axis lines (the frame is darker than the grid lines)."""
    x, y, w, h = box
    sub = cv2.cvtColor(img[y:y + h, x:x + w], cv2.COLOR_RGB2GRAY).astype(float)
    dark = sub < 200
    cols = dark.mean(axis=0); rows = dark.mean(axis=1)
    def edge(profile, from_start):
        idx = range(len(profile)) if from_start else range(len(profile) - 1, -1, -1)
        for i in idx:
            if profile[i] > 0.5:
                return i
        return 0 if from_start else len(profile) - 1
    l, r = edge(cols, True), edge(cols, False)
    t, b = edge(rows, True), edge(rows, False)
    # accept refinement only when it is a small adjustment
    if l < margin and t < margin and (w - 1 - r) < margin and (h - 1 - b) < margin:
        return (x + l, y + t, r - l + 1, b - t + 1)
    return box


# --------------------------------------------------------------------------- classification
def _cell_slices(box, n, inner=0.5):
    x, y, w, h = box
    cw, ch = w / n, h / n
    for r in range(n):              # r = 0 is the bottom row
        y1 = y + h - (r + 1) * ch
        for c in range(n):
            x1 = x + c * cw
            pad_x, pad_y = cw * (1 - inner) / 2, ch * (1 - inner) / 2
            yield r, c, (int(round(y1 + pad_y)), int(round(y1 + ch - pad_y)),
                         int(round(x1 + pad_x)), int(round(x1 + cw - pad_x)))


def classify_cells(img, box, n, grey_lo=35, grey_hi=120, sat_max=40, thresh=0.5):
    """Return (grid, obstacle_fraction) for one sub-plot."""
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    obstacle_px = (gray >= grey_lo) & (gray <= grey_hi) & (hsv[:, :, 1] <= sat_max)
    grid = np.zeros((n, n), dtype=np.uint8)
    frac = np.zeros((n, n), dtype=float)
    for r, c, (ya, yb, xa, xb) in _cell_slices(box, n):
        patch = obstacle_px[ya:yb, xa:xb]
        f = float(patch.mean()) if patch.size else 0.0
        frac[r, c] = f
        grid[r, c] = 1 if f >= thresh else 0
    return grid, frac


def detect_marker(img, box, n, colour):
    """Cell (c, r) of the red (start) or green (goal) dot, or None."""
    x, y, w, h = box
    sub = img[y:y + h, x:x + w].astype(int)
    R, G, B = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
    if colour == "red":
        m = (R > 190) & (G < 90) & (B < 90)
    else:
        m = (G > 170) & (R < 110) & (B < 110)
    m = m.astype(np.uint8)
    k, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    if k <= 1:
        return None
    best, best_score = None, 0
    for i in range(1, k):
        bw, bh, area = st[i, 2], st[i, 3], st[i, 4]
        if area < 8:
            continue
        fill = area / float(bw * bh)            # a filled dot is compact; spline strokes are not
        score = area * fill * min(bw, bh) / max(bw, bh)
        if score > best_score:
            best, best_score = cen[i], score
    if best is None:
        return None
    cx, cy = best
    c = int(np.clip(cx / (w / n), 0, n - 1))
    r = int(np.clip((h - cy) / (h / n), 0, n - 1))
    return (c, r)


# --------------------------------------------------------------------------- consensus
def consensus(grids):
    stack = np.stack(grids)
    votes = stack.sum(axis=0)
    merged = (votes * 2 > len(grids)).astype(np.uint8)
    agreement = (stack == merged).mean()
    disputed = np.argwhere((votes > 0) & (votes < len(grids)))
    return merged, float(agreement), disputed, votes


def mode_point(points):
    pts = [p for p in points if p is not None]
    if not pts:
        return None
    vals, counts = np.unique(np.array(pts), axis=0, return_counts=True)
    return tuple(int(v) for v in vals[counts.argmax()])

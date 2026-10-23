"""Grid map container used by every planner in this project."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json
import numpy as np


@dataclass
class GridMap:
    name: str
    grid: np.ndarray                 # (n, n) uint8, grid[r, c], r=0 bottom row, 1 = obstacle
    start: tuple                     # (c, r)
    goal: tuple                      # (c, r)
    source: str = ""
    meta: dict = field(default_factory=dict)

    @property
    def size(self) -> int:
        return int(self.grid.shape[0])

    @property
    def density(self) -> float:
        return float(self.grid.mean())

    def is_free(self, c: int, r: int) -> bool:
        n = self.size
        return 0 <= c < n and 0 <= r < n and self.grid[r, c] == 0

    def to_paper_xy(self, p):
        """(c, r) -> paper coordinates of the cell centre (x, y), 1-indexed lines."""
        return (p[0] + 1.5, p[1] + 1.5)

    # ------------------------------------------------------------------ I/O
    def save(self, folder) -> Path:
        folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
        rows = ["".join(str(v) for v in row) for row in self.grid[::-1]]     # top row first
        (folder / f"{self.name}.txt").write_text("\n".join(rows) + "\n")
        info = {"name": self.name, "size": self.size, "start": list(self.start),
                "goal": list(self.goal), "density": round(self.density, 4),
                "source": self.source, "convention": "grid[r,c], r=0 bottom; points (c,r); txt top row first",
                **self.meta}
        (folder / f"{self.name}.json").write_text(json.dumps(info, indent=2))
        return folder / f"{self.name}.txt"

    @classmethod
    def load(cls, folder, name) -> "GridMap":
        folder = Path(folder)
        rows = (folder / f"{name}.txt").read_text().split()
        grid = np.array([[int(ch) for ch in row] for row in rows], dtype=np.uint8)[::-1].copy()
        info = json.loads((folder / f"{name}.json").read_text())
        meta = {k: v for k, v in info.items()
                if k not in ("name", "size", "start", "goal", "density", "source", "convention")}
        return cls(name, grid, tuple(info["start"]), tuple(info["goal"]), info.get("source", ""), meta)


def plot_map(ax, m: GridMap, title=None, path=None):
    n = m.size
    ax.imshow(1 - m.grid, cmap="gray", origin="lower", vmin=0, vmax=1,
              extent=(1, n + 1, 1, n + 1), interpolation="nearest")
    if n <= 40:
        ax.set_xticks(range(1, n + 2, max(1, n // 10))); ax.set_yticks(range(1, n + 2, max(1, n // 10)))
        ax.grid(color="#cccccc", lw=0.3)
    sx, sy = m.to_paper_xy(m.start); gx, gy = m.to_paper_xy(m.goal)
    if path is not None:
        p = np.array([m.to_paper_xy(q) for q in path]); ax.plot(p[:, 0], p[:, 1], "b-", lw=1.2)
    ax.plot(sx, sy, "o", color="red", ms=6, label="start")
    ax.plot(gx, gy, "o", color="lime", mec="k", ms=6, label="goal")
    ax.set_title(title or f"{m.name} ({n}x{n})"); ax.set_aspect("equal")

"""Render every scene (in parallel) and stitch the film together.

    python build.py            # preview pass, 480p15
    python build.py -q h       # the real thing, 1080p60
    python build.py -q h -s S07Solve S08Reynolds   # just those two
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "out"
PY = ROOT / ".venv" / "bin" / "manim"

# the running order of the film
FILM = [
    ("scenes_intro.py", "S01Title"),
    ("scenes_intro.py", "S02Field"),
    ("scenes_intro.py", "S03Newton"),
    ("scenes_terms.py", "S04Acceleration"),
    ("scenes_terms.py", "S05Forces"),
    ("scenes_terms.py", "S06Assemble"),
    ("scenes_sim.py", "S07Solve"),
    ("scenes_sim.py", "S08Reynolds"),
    ("scenes_open.py", "S09Chaos"),
    ("scenes_open.py", "S10Prize"),
    ("scenes_open.py", "S11Outro"),
]

QUALITY = {"l": ("-ql", "480p15"), "m": ("-qm", "720p30"),
           "h": ("-qh", "1080p60"), "k": ("-qk", "2160p60")}


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def render(job, flag, folder, force):
    module, scene = job
    target = ROOT / "media" / "videos" / Path(module).stem / folder / f"{scene}.mp4"
    if target.exists() and not force:
        return scene, target, 0.0, True
    env = dict(os.environ)
    env["PATH"] = "/Library/TeX/texbin:" + env.get("PATH", "")
    env["OMP_NUM_THREADS"] = "1"
    t0 = time.time()
    proc = subprocess.run(
        [str(PY), flag, "--disable_caching", module, scene],
        cwd=ROOT, env=env, capture_output=True, text=True)
    if proc.returncode != 0 or not target.exists():
        tail = (proc.stderr or proc.stdout)[-2500:]
        raise RuntimeError(f"{scene} failed:\n{tail}")
    return scene, target, time.time() - t0, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-q", "--quality", default="l", choices=list(QUALITY))
    ap.add_argument("-s", "--scenes", nargs="*", default=None)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    ap.add_argument("-f", "--force", action="store_true")
    ap.add_argument("--no-concat", action="store_true")
    args = ap.parse_args()

    flag, folder = QUALITY[args.quality]
    jobs = [j for j in FILM if args.scenes is None or j[1] in args.scenes]
    if not jobs:
        sys.exit(f"no scenes matched {args.scenes}")

    OUT.mkdir(exist_ok=True)
    print(f"rendering {len(jobs)} scene(s) at {folder}, {args.jobs} at a time\n")

    results, t0 = {}, time.time()
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {pool.submit(render, j, flag, folder, args.force): j[1] for j in jobs}
        for fut in cf.as_completed(futures):
            scene, path, secs, cached = fut.result()
            results[scene] = path
            tag = "cached" if cached else f"{secs:6.0f}s"
            print(f"  {scene:<18} {tag}   {duration(path):6.1f}s of film", flush=True)
    print(f"\nrendered in {time.time()-t0:.0f}s")

    if args.no_concat or args.scenes is not None:
        return

    order = [ROOT / "media" / "videos" / Path(m).stem / folder / f"{s}.mp4"
             for m, s in FILM]
    missing = [p for p in order if not p.exists()]
    if missing:
        print("\nnot concatenating; still missing:")
        for p in missing:
            print("   ", p.name)
        return

    listing = OUT / "concat.txt"
    listing.write_text("".join(f"file '{p}'\n" for p in order))
    final = OUT / f"navier_stokes_{folder}.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "concat",
                    "-safe", "0", "-i", str(listing), "-c", "copy", str(final)],
                   check=True)
    total = duration(final)
    print(f"\n{final}")
    print(f"{int(total//60)}m {total%60:04.1f}s   "
          f"{final.stat().st_size/1e6:.0f} MB")


if __name__ == "__main__":
    main()

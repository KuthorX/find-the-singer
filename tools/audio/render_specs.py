"""Render several audiokit specs in one process (one plugin host, one lock hold).

Run only through tools/audio/render.py, which wraps this in the shared lockf.
"""
import json
import sys

sys.path.insert(0, "/tmp/audiokit")
import render as audiokit  # noqa: E402


def main(paths) -> None:
    for path in paths:
        with open(path) as fh:
            spec = json.load(fh)
        _audio, info = audiokit.render_spec(spec)
        print(f"{path}: {json.dumps(info, default=float)}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])

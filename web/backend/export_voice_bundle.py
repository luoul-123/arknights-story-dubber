"""Build a portable Release asset with the Kal'tsit production voice."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_STORED

DATA = Path(__file__).resolve().parents[1] / ".voice-data"
EXPECTED = {"凯尔希"}
MARKER = "/voice-of-terra/.voice-data/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    store = json.loads((DATA / "characters.json").read_text("utf-8"))
    published = [c for c in store.values() if c.get("published") and c.get("speaker") in EXPECTED]
    if {c["speaker"] for c in published} != EXPECTED:
        raise SystemExit("The published Kal'tsit voice is required.")
    exported = {}
    files = {}
    for character in published:
        c = copy.deepcopy(character)
        ident = c["id"]
        models = c["published"]["models"]
        for key, extension in (("gpt", ".ckpt"), ("sovits", ".pth")):
            source = Path(models[key])
            if not source.is_file():
                raise SystemExit("Missing model: " + str(source))
            relative = f"weights/{ident}-{key}{extension}"
            files[relative] = source
            models[key] = MARKER + relative
        reference = c["published"]["reference"]
        source = Path(reference["path"])
        if not source.is_file():
            raise SystemExit("Missing reference audio: " + str(source))
        relative = f"references/{ident}.wav"
        files[relative] = source
        reference = {key: reference[key] for key in ("id", "text", "duration") if key in reference} | {"path": MARKER + relative}
        c = {key: c[key] for key in ("id", "speaker", "language", "aliases") if key in c}
        c["models"] = models
        c["published"] = {"version": character["published"]["version"], "mode": character["published"].get("mode", "trained"),
                          "models": models, "reference": reference}
        c["clips"] = [reference]
        c["referenceId"] = reference.get("id")
        exported[ident] = c
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", ZIP_STORED, allowZip64=True) as bundle:
        bundle.writestr("characters.json", json.dumps(exported, ensure_ascii=False, indent=2))
        defaults = DATA / "default-voices.json"
        if defaults.is_file():
            bundle.write(defaults, "default-voices.json")
        for relative, source in files.items():
            bundle.write(source, relative)
    if args.output.stat().st_size >= 2 * 1024**3:
        args.output.unlink()
        raise SystemExit("Release asset exceeds GitHub's 2 GiB per-file limit.")
    print(f"{len(exported)} voices, {len(files)} files, {args.output.stat().st_size / 1024**3:.2f} GiB")


if __name__ == "__main__":
    main()

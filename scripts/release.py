"""Release helpers, used by .github/workflows/release.yml.

    python scripts/release.py check v1.2.3      tag matches version in metadata.txt
    python scripts/release.py zip v1.2.3 DIR    build DIR/kof_tools.1.2.3.zip
    python scripts/release.py notes v1.2.3      print the CHANGELOG section
    python scripts/release.py xml v1.2.3        write plugins.xml for the QGIS repository

Everything is read from the git tree at the given tag, not the working copy.
The zip name must start with "kof_tools." because QGIS identifies a plugin
in a repository by the part of file_name before the first dot.
"""

import configparser
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

PLUGIN = "kof_tools"
ROOT = Path(__file__).resolve().parent.parent
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "Kabax04/qgis-kof-tools")


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def metadata(ref: str) -> configparser.SectionProxy:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(git("show", f"{ref}:{PLUGIN}/metadata.txt").decode("utf-8"))
    return parser["general"]


def version_of(tag: str) -> str:
    return tag[1:] if tag.startswith("v") else tag


def check(tag: str) -> None:
    version = metadata(tag)["version"]
    if version_of(tag) != version:
        sys.exit(f"Tag {tag} does not match version={version} in metadata.txt")


def zip_name(version: str) -> str:
    return f"{PLUGIN}.{version}.zip"


def build_zip(tag: str, out_dir: str) -> Path:
    out = Path(out_dir) / zip_name(metadata(tag)["version"])
    out.parent.mkdir(parents=True, exist_ok=True)
    files = git("ls-tree", "-r", "--name-only", tag, PLUGIN).decode("utf-8").split()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name in files:
            z.writestr(name, git("show", f"{tag}:{name}"))
        # plugins.qgis.org requires a LICENSE file inside the plugin folder.
        z.writestr(f"{PLUGIN}/LICENSE", git("show", f"{tag}:LICENSE"))
    return out


def changelog_section(tag: str) -> str:
    """The text under "## [x.y.z]" in CHANGELOG.md, up to the next version."""
    lines = git("show", f"{tag}:CHANGELOG.md").decode("utf-8").splitlines()
    heading = f"## [{metadata(tag)['version']}]"
    section = []
    inside = False
    for line in lines:
        if line.startswith("## ["):
            if inside:
                break
            inside = line.startswith(heading)
            continue
        if inside:
            section.append(line)
    if not inside:
        sys.exit(f"No section {heading} in CHANGELOG.md")
    return "\n".join(section).strip() + "\n"


def plugins_xml(tag: str) -> str:
    meta = metadata(tag)
    version = meta["version"]
    minimum = meta["qgisMinimumVersion"]
    maximum = meta.get("qgisMaximumVersion", f"{minimum.split('.')[0]}.99")
    base = f"https://github.com/{REPOSITORY}"
    raw = f"https://raw.githubusercontent.com/{REPOSITORY}/{tag}/{PLUGIN}"
    created = git("log", "--reverse", "--format=%cI").decode("utf-8").splitlines()[0]
    updated = git("log", "-1", "--format=%cI", tag).decode("utf-8").strip()
    fields = {
        "description": meta["description"],
        "about": meta["about"],
        "version": version,
        "qgis_minimum_version": minimum,
        "qgis_maximum_version": maximum,
        "homepage": meta["homepage"],
        "file_name": zip_name(version),
        "icon": f"{raw}/{meta['icon']}",
        "author_name": meta["author"],
        "download_url": f"{base}/releases/download/{tag}/{zip_name(version)}",
        "uploaded_by": meta["author"],
        "create_date": created,
        "update_date": updated,
        "experimental": meta.get("experimental", "False"),
        "deprecated": meta.get("deprecated", "False"),
        "tracker": meta["tracker"],
        "repository": meta["repository"],
        "tags": meta["tags"],
        "category": meta.get("category", ""),
        "changelog": meta.get("changelog", "").strip(),
    }
    body = "\n".join(f"        <{key}>{escape(value)}</{key}>" for key, value in fields.items())
    return (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<plugins>\n"
        f"    <pyqgis_plugin name={quoteattr(meta['name'])} version={quoteattr(version)}>\n"
        f"{body}\n"
        "    </pyqgis_plugin>\n"
        "</plugins>\n"
    )


def main(argv) -> None:
    command, tag, *rest = argv
    if command == "check":
        check(tag)
    elif command == "zip":
        print(build_zip(tag, rest[0] if rest else "dist"))
    elif command == "notes":
        sys.stdout.write(changelog_section(tag))
    elif command == "xml":
        (ROOT / "plugins.xml").write_text(plugins_xml(tag), encoding="utf-8")
    else:
        sys.exit(f"Unknown command {command}")


if __name__ == "__main__":
    main(sys.argv[1:])

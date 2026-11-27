"""Validate skill metadata and basic Second Brain note/link conventions."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
BRAIN_DIR = ROOT / "brain"
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")


def markdown_files(directory: Path) -> list[Path]:
    """Return Markdown files below a directory, excluding generated folders."""
    return sorted(path for path in directory.rglob("*.md") if ".git" not in path.parts)


def skill_frontmatter(path: Path, errors: list[str]) -> dict[str, str] | None:
    """Read and validate the small YAML frontmatter subset used by project skills."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{path.relative_to(ROOT)}: missing opening frontmatter delimiter")
        return None

    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path.relative_to(ROOT)}: missing closing frontmatter delimiter")
        return None

    values: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if not separator or not key.strip() or not value.strip():
            errors.append(f"{path.relative_to(ROOT)}: malformed frontmatter line {line!r}")
            continue
        key = key.strip()
        if key in values:
            errors.append(f"{path.relative_to(ROOT)}: duplicate frontmatter key {key!r}")
        values[key] = value.strip().strip("\"'")

    required = {"name", "description"}
    missing = required - values.keys()
    if missing:
        errors.append(f"{path.relative_to(ROOT)}: missing fields {', '.join(sorted(missing))}")
    if values.get("name") != path.parent.name:
        errors.append(
            f"{path.relative_to(ROOT)}: skill name must match folder {path.parent.name!r}"
        )
    if len(values.get("description", "")) < 10:
        errors.append(f"{path.relative_to(ROOT)}: description must be at least 10 characters")
    if not re.search(r"^#\s+\S", "\n".join(lines[end + 1 :]), flags=re.MULTILINE):
        errors.append(f"{path.relative_to(ROOT)}: skill body must have a top-level heading")
    return values


def heading_slugs(content: str) -> set[str]:
    """Build the heading anchors used to check wikilink fragments."""
    slugs = set()
    for line in content.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            heading = match.group(1).lower()
            heading = re.sub(r"[^\w\- ]", "", heading)
            slugs.add(re.sub(r"\s+", "-", heading.strip()))
    return slugs


def link_target(raw_target: str) -> tuple[str, str | None]:
    """Split a wikilink target and optional heading fragment."""
    target = raw_target.split("|", 1)[0].strip()
    if "#" in target:
        path, fragment = target.split("#", 1)
        return path.strip(), fragment.strip()
    return target, None


def resolve_link(target: str, markdown_paths: list[Path]) -> Path | None:
    """Resolve a root-relative Obsidian link or an unambiguous note basename."""
    normalized = target.strip().lstrip("/")
    if not normalized or normalized.lower() == "wikilinks":
        return None
    if not normalized.endswith(".md"):
        normalized += ".md"

    exact = ROOT / normalized
    if exact.is_file():
        return exact

    note_name = Path(normalized).stem.casefold()
    matches = [path for path in markdown_paths if path.stem.casefold() == note_name]
    return matches[0] if len(matches) == 1 else None


def validate_brain_notes(errors: list[str]) -> None:
    """Check Brain notes have a title and that their wikilinks resolve."""
    notes = markdown_files(BRAIN_DIR)
    for path in notes:
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)
        # These two empty member files were present in Tharun's original notes.
        # Keep them as placeholders; their owners should write their own notes.
        if relative.as_posix() in {"brain/tharun/Sid.md", "brain/tharun/Viraj.md"}:
            continue
        if not content.strip():
            errors.append(f"{relative}: note is empty")
            continue
        if not re.search(r"^#\s+\S", content, flags=re.MULTILINE):
            errors.append(f"{relative}: missing top-level Markdown title")
        if path.name.startswith("research-"):
            if "**Source:**" not in content and "**Sources:**" not in content:
                errors.append(f"{relative}: research note must include a source")
            if "**Requirements:**" not in content:
                errors.append(f"{relative}: research note must cite requirement IDs")

        for raw_target in WIKILINK.findall(content):
            target, fragment = link_target(raw_target)
            if not target or target.lower() == "wikilinks":
                continue
            resolved = resolve_link(target, notes)
            if resolved is None:
                errors.append(f"{relative}: broken or ambiguous wikilink [[{raw_target}]]")
                continue
            if fragment:
                slugs = heading_slugs(resolved.read_text(encoding="utf-8"))
                requested = re.sub(r"\s+", "-", fragment.strip().lower())
                if not any(
                    slug == requested or slug.startswith(f"{requested}-")
                    for slug in slugs
                ):
                    errors.append(
                        f"{relative}: missing heading #{fragment} in "
                        f"{resolved.relative_to(ROOT)}"
                    )


def validate_skill_brain_citations(skill_paths: list[Path], errors: list[str]) -> None:
    """Require every skill to link at least one resolvable distilled Brain note."""
    brain_notes = markdown_files(BRAIN_DIR)
    for path in skill_paths:
        content = path.read_text(encoding="utf-8")
        citations = []
        for raw_target in WIKILINK.findall(content):
            target, _ = link_target(raw_target)
            if target.startswith("brain/"):
                resolved = resolve_link(target, brain_notes)
                if resolved is not None:
                    citations.append(resolved)
        if not citations:
            errors.append(f"{path.relative_to(ROOT)}: must cite a distilled Brain note")


def main() -> int:
    """Run skill and Brain validation and return a CI-friendly exit status."""
    errors: list[str] = []
    skill_paths = sorted(SKILLS_DIR.rglob("SKILL.md"))
    misplaced_markdown = [
        path for path in markdown_files(SKILLS_DIR) if path.name != "SKILL.md"
    ]
    for path in misplaced_markdown:
        errors.append(f"{path.relative_to(ROOT)}: skill document must be named SKILL.md")
    placeholder_notes = {"brain/tharun/Sid.md", "brain/tharun/Viraj.md"}
    if not skill_paths:
        errors.append("skills/: no SKILL.md files found")

    names: set[str] = set()
    for path in skill_paths:
        values = skill_frontmatter(path, errors)
        if values and values.get("name"):
            name = values["name"]
            if name in names:
                errors.append(f"{path.relative_to(ROOT)}: duplicate skill name {name!r}")
            names.add(name)

    validate_brain_notes(errors)
    research_notes = list((BRAIN_DIR / "sid" / "resources").glob("research-*.md"))
    if len(research_notes) < 10:
        errors.append(
            "brain/sid/resources/: expected at least 10 research notes, "
            f"found {len(research_notes)}"
        )
    validate_skill_brain_citations(skill_paths, errors)

    if errors:
        print("Repository documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    note_count = sum(
        path.relative_to(ROOT).as_posix() not in placeholder_notes
        for path in markdown_files(BRAIN_DIR)
    )
    print(
        f"Validated {len(skill_paths)} skills and {note_count} Brain notes "
        f"({len(placeholder_notes)} empty member placeholders excluded)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

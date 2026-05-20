#!/usr/bin/env python3
"""Quick repository checks for the skills package."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_JSON = ROOT / ".claude-plugin" / "plugin.json"
README = ROOT / "README.md"
SHIPPED_BUCKETS = ("engineering", "productivity", "misc")
UNSHIPPED_BUCKETS = ("personal", "in-progress", "deprecated")


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def skill_dirs(bucket: str) -> list[Path]:
    bucket_dir = ROOT / "skills" / bucket
    if not bucket_dir.exists():
        return []
    return sorted(path.parent for path in bucket_dir.glob("*/SKILL.md"))


def plugin_skill_dirs(errors: list[str]) -> set[str]:
    try:
        data = json.loads(PLUGIN_JSON.read_text())
    except FileNotFoundError:
        fail(errors, f"missing {PLUGIN_JSON.relative_to(ROOT)}")
        return set()
    except json.JSONDecodeError as exc:
        fail(errors, f"invalid JSON in {PLUGIN_JSON.relative_to(ROOT)}: {exc}")
        return set()

    if not isinstance(data.get("name"), str) or not data["name"].strip():
        fail(errors, ".claude-plugin/plugin.json must have a non-empty string name")

    skills = data.get("skills")
    if not isinstance(skills, list):
        fail(errors, ".claude-plugin/plugin.json must have a skills list")
        return set()

    seen: set[str] = set()
    for entry in skills:
        if not isinstance(entry, str):
            fail(errors, f"plugin skill entry must be a string: {entry!r}")
            continue

        normalized = entry.removeprefix("./").rstrip("/")
        skill_dir = ROOT / normalized
        skill_md = skill_dir / "SKILL.md"

        if normalized in seen:
            fail(errors, f"duplicate plugin skill entry: {entry}")
        seen.add(normalized)

        if not skill_md.exists():
            fail(errors, f"plugin skill entry does not point to a skill dir: {entry}")

    return seen


def check_skill_frontmatter(errors: list[str], skill_md: Path) -> None:
    rel = skill_md.relative_to(ROOT)
    text = skill_md.read_text()
    if not text.startswith("---\n"):
        fail(errors, f"{rel} is missing YAML-style frontmatter")
        return

    end = text.find("\n---\n", 4)
    if end == -1:
        fail(errors, f"{rel} has unterminated frontmatter")
        return

    frontmatter = text[4:end]
    name_match = re.search(r"^name:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    description_match = re.search(
        r"^description:\s*(.+?)\s*$", frontmatter, re.MULTILINE
    )

    expected_name = skill_md.parent.name
    if not name_match:
        fail(errors, f"{rel} frontmatter is missing name")
    elif name_match.group(1).strip().strip("\"'") != expected_name:
        fail(
            errors,
            f"{rel} frontmatter name should be {expected_name!r}",
        )

    if not description_match or not description_match.group(1).strip():
        fail(errors, f"{rel} frontmatter is missing description")


def check_readme_mentions(errors: list[str], shipped: list[Path]) -> None:
    try:
        top_readme = README.read_text()
    except FileNotFoundError:
        fail(errors, "missing README.md")
        top_readme = ""

    for skill_dir in shipped:
        rel_skill_md = skill_dir.relative_to(ROOT) / "SKILL.md"
        expected_top_link = f"]({rel_skill_md.as_posix()}"
        expected_top_link_with_dot = f"](./{rel_skill_md.as_posix()}"
        if (
            expected_top_link not in top_readme
            and expected_top_link_with_dot not in top_readme
        ):
            fail(errors, f"README.md missing link to {rel_skill_md}")

    for bucket in SHIPPED_BUCKETS:
        bucket_readme = ROOT / "skills" / bucket / "README.md"
        try:
            bucket_text = bucket_readme.read_text()
        except FileNotFoundError:
            fail(errors, f"missing {bucket_readme.relative_to(ROOT)}")
            continue

        for skill_dir in skill_dirs(bucket):
            expected = f"]({skill_dir.name}/SKILL.md"
            expected_with_dot = f"](./{skill_dir.name}/SKILL.md"
            if expected not in bucket_text and expected_with_dot not in bucket_text:
                fail(
                    errors,
                    f"{bucket_readme.relative_to(ROOT)} missing link to {skill_dir.name}/SKILL.md",
                )


def main() -> int:
    errors: list[str] = []
    plugin_entries = plugin_skill_dirs(errors)

    shipped = [skill for bucket in SHIPPED_BUCKETS for skill in skill_dirs(bucket)]
    shipped_entries = {skill.relative_to(ROOT).as_posix() for skill in shipped}

    for skill_dir in shipped:
        check_skill_frontmatter(errors, skill_dir / "SKILL.md")

    missing_from_plugin = shipped_entries - plugin_entries
    extra_in_plugin = plugin_entries - shipped_entries

    for entry in sorted(missing_from_plugin):
        fail(errors, f"shipped skill missing from plugin.json: {entry}")

    for entry in sorted(extra_in_plugin):
        fail(errors, f"plugin.json includes non-shipped skill: {entry}")

    for bucket in UNSHIPPED_BUCKETS:
        for skill_dir in skill_dirs(bucket):
            entry = skill_dir.relative_to(ROOT).as_posix()
            if entry in plugin_entries:
                fail(errors, f"unshipped skill must not be in plugin.json: {entry}")

    check_readme_mentions(errors, shipped)

    if errors:
        print("quick_validate failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"quick_validate passed: {len(shipped)} shipped skills, "
        f"{len(plugin_entries)} plugin entries"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

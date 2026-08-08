#!/usr/bin/env python3
"""
Check every srcpkgs/*/template for a newer upstream release and, when one is
found and verified, bump `version`, reset `revision` to 1 and refresh
`checksum` in place.

How it decides a package is "supported":
  - `distfiles` must reference GitHub (github.com) or Codeberg (codeberg.org),
    since those are the only hosts this script knows how to query for tags
    and releases.
  - The resolved `distfiles` URL(s) must actually contain the current
    `version` string somewhere, so a newer version can be substituted in.
    Templates pinned to a `${_commit}` hash (no `${version}` in the URL) are
    naturally skipped by this check -- there is no "next" commit to guess.

How it decides a newer version is real (not just "a different tag"):
  1. Candidate versions are collected from the repo's releases and tags.
  2. The highest candidate (best-effort version comparison) is compared to
     the current version.
  3. If it differs, the new distfiles URL(s) are built by literally
     substituting the old version string for the new one inside the
     *resolved* distfiles URL(s) (no guessing at URL structure), then
     actually downloaded.
  4. Only if every URL downloads successfully AND the resulting checksum(s)
     differ from what's on disk does the template get rewritten.

This means a bad guess (e.g. a repo that bakes extra suffixes like "-beta1"
into its download URLs) just fails the download and the package is skipped
-- it never corrupts a template with an unverified checksum.

Unsupported/skippable sources (proprietary CDNs, GitLab, PyPI, GNOME,
Hackage, suckless.org, freedesktop.org, commit-pinned templates, templates
without a `distfiles`/`checksum` at all, ...) are logged and left untouched.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRCPKGS = ROOT / "srcpkgs"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
USER_AGENT = "srcpkgs-d77-template-updater (+https://github.com/d77void/srcpkgs-d77)"

HTTP_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 300
MAX_TAGS = 30

PRERELEASE_MARKERS = ("alpha", "beta", "rc", "pre", "dev", "nightly")

# Bash vars/functions xbps-src ships that a handful of templates rely on for
# their distfiles URL. Defining them here lets the sourcing step below
# resolve those templates the same way xbps-src would.
BASH_PRELUDE = '''
GNOME_SITE="https://download.gnome.org/sources"
PYPI_SITE="https://files.pythonhosted.org/packages/source"
KERNEL_SITE="https://www.kernel.org/pub/linux"
'''

DUMP_VARS = ("pkgname", "version", "revision", "_commit", "distfiles", "checksum", "homepage")


@dataclass
class Result:
    pkgname: str
    old_version: str | None = None
    new_version: str | None = None
    status: str = "skipped"  # updated | skipped | error
    reason: str = ""


@dataclass
class Report:
    updated: list[Result] = field(default_factory=list)
    skipped: list[Result] = field(default_factory=list)
    errors: list[Result] = field(default_factory=list)


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# --------------------------------------------------------------------------
# Template parsing (via bash, since templates are bash scripts)
# --------------------------------------------------------------------------

def dump_template_vars(template: Path) -> dict[str, str]:
    script = BASH_PRELUDE + '''
set -a
source "$1" >/dev/null 2>&1 || true
for var in ''' + " ".join(DUMP_VARS) + '''; do
    val="${!var-}"
    printf '%s\\x1f%s\\x1e' "$var" "$val"
done
'''
    proc = subprocess.run(
        ["bash", "-c", script, "bash", str(template)],
        capture_output=True, text=True, timeout=30,
    )
    fields: dict[str, str] = {}
    for record in proc.stdout.split("\x1e"):
        if not record:
            continue
        k, _, v = record.partition("\x1f")
        fields[k] = v
    return fields


# --------------------------------------------------------------------------
# Source detection
# --------------------------------------------------------------------------

GITHUB_RE = re.compile(r"https?://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/")
CODEBERG_RE = re.compile(r"https?://codeberg\.org/([^/\s]+)/([^/\s]+?)(?:\.git)?/")


def detect_source(distfiles: str) -> tuple[str, str, str] | None:
    m = GITHUB_RE.search(distfiles)
    if m:
        return ("github", m.group(1), m.group(2))
    m = CODEBERG_RE.search(distfiles)
    if m:
        return ("codeberg", m.group(1), m.group(2))
    return None


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------

def http_get_json(url: str, headers: dict[str, str] | None = None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read())


def sha256_of_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
        while chunk := resp.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def github_headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def fetch_candidate_tags(source: str, owner: str, repo: str) -> list[str]:
    tags: list[str] = []
    if source == "github":
        headers = github_headers()
        try:
            data = http_get_json(
                f"https://api.github.com/repos/{owner}/{repo}/tags?per_page={MAX_TAGS}",
                headers,
            )
            tags.extend(t["name"] for t in data)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        try:
            data = http_get_json(
                f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=10",
                headers,
            )
            tags.extend(r["tag_name"] for r in data if not r.get("draft") and not r.get("prerelease"))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    elif source == "codeberg":
        try:
            data = http_get_json(
                f"https://codeberg.org/api/v1/repos/{owner}/{repo}/tags?limit={MAX_TAGS}"
            )
            tags.extend(t["name"] for t in data)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        try:
            data = http_get_json(
                f"https://codeberg.org/api/v1/repos/{owner}/{repo}/releases?limit=10"
            )
            tags.extend(r["tag_name"] for r in data if not r.get("draft") and not r.get("prerelease"))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    return tags


# --------------------------------------------------------------------------
# Version comparison
# --------------------------------------------------------------------------

TAG_PREFIX_RE = re.compile(r"^(?:[A-Za-z][\w.]*?-)?[vV](\d.*)$")
TAG_PLAIN_RE = re.compile(r"^(?:[A-Za-z][\w.]*?-)?(\d.*)$")


def normalize_tag(tag: str) -> str | None:
    tag = tag.strip()
    if not tag:
        return None
    if any(marker in tag.lower() for marker in PRERELEASE_MARKERS):
        return None
    m = TAG_PREFIX_RE.match(tag) or TAG_PLAIN_RE.match(tag)
    if not m:
        return None
    return m.group(1)


def parse_ver(v: str) -> list:
    return [int(x) if x.isdigit() else x for x in re.findall(r"\d+|[A-Za-z]+", v)]


def ver_greater(a: str, b: str) -> bool:
    """True if a > b, falling back to plain string comparison on mismatched shapes."""
    try:
        return parse_ver(a) > parse_ver(b)
    except TypeError:
        return a > b


def best_candidate(current: str, tags: list[str]) -> str | None:
    best: str | None = None
    for tag in tags:
        cand = normalize_tag(tag)
        if cand is None or cand == current:
            continue
        if best is None or ver_greater(cand, best):
            best = cand
    if best is not None and not ver_greater(best, current):
        return None
    return best


# --------------------------------------------------------------------------
# Template rewriting
# --------------------------------------------------------------------------

def format_checksum(hashes: list[str]) -> str:
    if len(hashes) == 1:
        return hashes[0]
    return '"' + "\n ".join(hashes) + '"'


def update_template_text(text: str, new_version: str, hashes: list[str]) -> str:
    text = re.sub(r"(?m)^version=.*$", f"version={new_version}", text, count=1)
    text = re.sub(r"(?m)^revision=.*$", "revision=1", text, count=1)
    checksum_re = re.compile(r'checksum=("(?:[^"\\]|\\.)*"|\S+)', re.DOTALL)
    if not checksum_re.search(text):
        raise ValueError("could not locate checksum= to rewrite")
    text = checksum_re.sub(lambda m: f"checksum={format_checksum(hashes)}", text, count=1)
    return text


# --------------------------------------------------------------------------
# Per-package processing
# --------------------------------------------------------------------------

def process_template(template: Path) -> Result:
    pkgname = template.parent.name
    try:
        fields = dump_template_vars(template)
    except Exception as e:  # noqa: BLE001
        return Result(pkgname, status="error", reason=f"failed to parse template: {e}")

    version = fields.get("version", "")
    distfiles = fields.get("distfiles", "")
    checksum = fields.get("checksum", "")

    if not version or not distfiles or not checksum:
        return Result(pkgname, old_version=version, status="skipped",
                       reason="no distfiles/checksum (local build)")

    source = detect_source(distfiles)
    if source is None:
        return Result(pkgname, old_version=version, status="skipped",
                       reason="unsupported source host (not github.com/codeberg.org)")

    kind, owner, repo = source
    if version not in distfiles:
        return Result(pkgname, old_version=version, status="skipped",
                       reason="version not present in distfiles (likely commit-pinned)")

    try:
        tags = fetch_candidate_tags(kind, owner, repo)
    except Exception as e:  # noqa: BLE001
        return Result(pkgname, old_version=version, status="error",
                       reason=f"failed to query {kind} for {owner}/{repo}: {e}")

    candidate = best_candidate(version, tags)
    if candidate is None:
        return Result(pkgname, old_version=version, status="skipped", reason="already up to date")

    new_distfiles = distfiles.replace(version, candidate)
    urls = [entry.split(">", 1)[0] for entry in new_distfiles.split()]

    try:
        new_hashes = [sha256_of_url(url) for url in urls]
    except Exception as e:  # noqa: BLE001
        return Result(pkgname, old_version=version, new_version=candidate, status="skipped",
                       reason=f"candidate {candidate} found but download verification failed: {e}")

    old_hashes = checksum.split()
    if new_hashes == old_hashes:
        return Result(pkgname, old_version=version, new_version=candidate, status="skipped",
                       reason="candidate verified but checksum unchanged")

    raw_text = template.read_text()
    try:
        new_text = update_template_text(raw_text, candidate, new_hashes)
    except Exception as e:  # noqa: BLE001
        return Result(pkgname, old_version=version, new_version=candidate, status="error",
                       reason=f"failed to rewrite template: {e}")

    template.write_text(new_text)
    return Result(pkgname, old_version=version, new_version=candidate, status="updated")


def main() -> int:
    templates = sorted(SRCPKGS.glob("*/template"))
    report = Report()

    for template in templates:
        pkgname = template.parent.name
        log(f"checking {pkgname} ...")
        result = process_template(template)
        if result.status == "updated":
            log(f"  -> updated {result.old_version} -> {result.new_version}")
            report.updated.append(result)
        elif result.status == "error":
            log(f"  -> error: {result.reason}")
            report.errors.append(result)
        else:
            log(f"  -> skipped: {result.reason}")
            report.skipped.append(result)

    summary_lines = []
    if report.updated:
        summary_lines.append("## Template updates\n")
        summary_lines.append("| Package | Old version | New version |")
        summary_lines.append("|---|---|---|")
        for r in sorted(report.updated, key=lambda r: r.pkgname):
            summary_lines.append(f"| `{r.pkgname}` | {r.old_version} | **{r.new_version}** |")
        summary_lines.append("")
    else:
        summary_lines.append("No template updates found.\n")

    if report.errors:
        summary_lines.append("## Errors while checking for updates\n")
        for r in sorted(report.errors, key=lambda r: r.pkgname):
            summary_lines.append(f"- `{r.pkgname}`: {r.reason}")
        summary_lines.append("")

    summary_lines.append(
        f"<sub>{len(templates)} templates checked, {len(report.updated)} updated, "
        f"{len(report.skipped)} skipped, {len(report.errors)} errored.</sub>"
    )

    summary = "\n".join(summary_lines)
    print(summary)

    summary_path = os.environ.get("UPDATE_SUMMARY_PATH")
    if summary_path:
        Path(summary_path).write_text(summary + "\n")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"has_changes={'true' if report.updated else 'false'}\n")
            f.write(f"updated_count={len(report.updated)}\n")

    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a") as f:
            f.write(summary + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

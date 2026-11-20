#!/usr/bin/env python3
"""Build the merged Surge ad-blocking module from its upstream sources."""

import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


SOURCES = (
    (
        "Block_HTTPDNS",
        "https://raw.githubusercontent.com/Repcz/Tool/X/Surge/Module/Kelee/Block_HTTPDNS.sgmodule",
    ),
    (
        "BlockAdvertisers",
        "https://raw.githubusercontent.com/Repcz/Tool/X/Surge/Module/Kelee/BlockAdvertisers.sgmodule",
    ),
    (
        "Remove_ads_by_keli",
        "https://raw.githubusercontent.com/Repcz/Tool/X/Surge/Module/Kelee/Remove_ads_by_keli.sgmodule",
    ),
)
ADVERTISING_LITE_URL = (
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/"
    "rule/Surge/AdvertisingLite/AdvertisingLite_All_No_Resolve.list"
)
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "adblock.sgmodule"
SECTION_HEADER = re.compile(r"^\[([^\]]+)\]$")
MITM_HOSTNAME = re.compile(r"^hostname\s*=\s*%APPEND%\s*(.*)$")
PREFERRED_SECTIONS = (
    "Rule",
    "URL Rewrite",
    "Header Rewrite",
    "Body Rewrite",
    "Map Local",
    "Script",
    "MITM",
)


class BuildError(Exception):
    """Raised when an upstream source cannot be merged safely."""


def fetch_source(url):
    request = urllib.request.Request(url, headers={"User-Agent": "surge-rule-adblock-builder"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def parse_source(name, url, content):
    date = ""
    sections = {}
    current_section = None

    for original_line in content.splitlines():
        metadata_line = original_line.strip()
        if metadata_line.startswith("#!date=") and not date:
            date = metadata_line.partition("=")[2]
        if original_line.lstrip().startswith("#!"):
            continue

        if not original_line.strip():
            continue

        match = SECTION_HEADER.fullmatch(original_line.strip())
        if match:
            current_section = match.group(1)
            sections.setdefault(current_section, [])
        elif current_section is not None:
            sections[current_section].append(original_line)

    if "Rule" not in sections:
        raise BuildError(f"{name} ({url}) has no [Rule] section")

    return {"name": name, "url": url, "date": date, "sections": sections}


def fetch_sources():
    parsed_sources = []
    for name, url in SOURCES:
        try:
            content = fetch_source(url)
        except (OSError, UnicodeError, urllib.error.URLError) as exc:
            raise BuildError(f"failed to fetch {url}: {exc}") from exc
        parsed_sources.append(parse_source(name, url, content))
    return parsed_sources


def build_module(sources):
    lines = [
        "#!name=去广告合集",
        "#!desc=合并可莉 HTTPDNS拦截器、广告平台拦截器、可莉广告过滤器与 blackmatrix7 AdvertisingLite，每周自动从上游重新生成。需开启 MITM 并信任证书。",
        "#!category=Block",
    ]
    lines.extend(
        f"# source: {source['url']} (upstream date: {source['date']})"
        for source in sources
    )

    section_names = []
    seen_sections = set()
    for section in PREFERRED_SECTIONS:
        if any(section in source["sections"] for source in sources):
            section_names.append(section)
            seen_sections.add(section)
    for source in sources:
        for section in source["sections"]:
            if section not in seen_sections:
                section_names.append(section)
                seen_sections.add(section)

    for section in section_names:
        lines.extend(("", f"[{section}]"))
        if section == "MITM":
            hostnames = []
            seen_hostnames = set()
            for source in sources:
                for line in source["sections"].get(section, []):
                    match = MITM_HOSTNAME.fullmatch(line.strip())
                    if not match:
                        raise BuildError(
                            f"{source['name']} has an unsupported [MITM] line: {line}"
                        )
                    for hostname in match.group(1).split(","):
                        hostname = hostname.strip()
                        if hostname and hostname not in seen_hostnames:
                            hostnames.append(hostname)
                            seen_hostnames.add(hostname)
            lines.append(f"hostname = %APPEND% {', '.join(hostnames)}")
            continue

        emitted_entries = set()
        for source in sources:
            if section not in source["sections"]:
                continue
            lines.append(f"# ---- {source['name']} ----")
            for line in source["sections"][section]:
                is_comment = line.lstrip().startswith("#")
                if not is_comment and line in emitted_entries:
                    continue
                lines.append(line)
                if not is_comment:
                    emitted_entries.add(line)

        if section == "Rule":
            lines.append("# ---- blackmatrix7 AdvertisingLite ----")
            advertising_lite_rule = f"RULE-SET,{ADVERTISING_LITE_URL},REJECT"
            if advertising_lite_rule not in emitted_entries:
                lines.append(advertising_lite_rule)
                emitted_entries.add(advertising_lite_rule)

    return "\n".join(lines).rstrip("\n") + "\n"


def write_atomically(path, content):
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def main():
    try:
        sources = fetch_sources()
        content = build_module(sources)
        write_atomically(OUTPUT_PATH, content)
    except (BuildError, OSError) as exc:
        print(f"build_adblock.py: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

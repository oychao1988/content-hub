#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\n]+)\)(\{[^}]*\})?")


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    evidence: Optional[Dict[str, Any]] = None


def _strip_yaml_scalar(value: str) -> str:
    v = value.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def _parse_front_matter_attrs(attrs: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for line in attrs.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        k = key.strip()
        v = _strip_yaml_scalar(rest)
        result[k] = v
    return result


def parse_front_matter(text: str) -> Tuple[Optional[Dict[str, str]], str, Optional[str]]:
    m = FRONT_MATTER_RE.search(text)
    if not m:
        return None, text, None

    attrs = m.group(1)
    body = text[m.end() :]
    return _parse_front_matter_attrs(attrs), body, m.group(0)


def is_remote_path(p: str) -> bool:
    v = p.strip()
    return v.startswith("http://") or v.startswith("https://")


def resolve_path(p: str, base_dir: str) -> str:
    v = _strip_yaml_scalar(p).strip()
    if os.path.isabs(v):
        return os.path.normpath(v)
    return os.path.normpath(os.path.join(base_dir, v))


def file_exists(path: str) -> bool:
    return os.path.exists(path) and os.path.isfile(path)


def detect_placeholders(body: str) -> List[Finding]:
    findings: List[Finding] = []

    patterns = [
        re.compile(r"\[在此处插入[^\]]*\]"),
        re.compile(r"\[INSERT[^\]]*\]", re.IGNORECASE),
        re.compile(r"\[TODO[^\]]*\]", re.IGNORECASE),
    ]

    for pat in patterns:
        m = pat.search(body)
        if m:
            findings.append(
                Finding(
                    severity="error",
                    code="placeholder_present",
                    message="placeholder remains in body",
                    evidence={"match": m.group(0)},
                )
            )
            break

    ai_meta = re.search(r"\b(作为一个|as an ai|i am an ai|语言模型)\b", body, flags=re.IGNORECASE)
    if ai_meta:
        findings.append(
            Finding(
                severity="warning",
                code="ai_meta_talk_present",
                message="possible AI meta talk remains in body",
                evidence={"match": ai_meta.group(0)},
            )
        )

    return findings


def iter_image_refs(body: str) -> List[Tuple[str, str]]:
    refs: List[Tuple[str, str]] = []
    for m in IMAGE_RE.finditer(body):
        alt = m.group(1)
        href = m.group(2).strip()
        if href:
            refs.append((alt, href))
    return refs


def check_images(
    body: str,
    base_dir: str,
    stage: str,
) -> List[Finding]:
    findings: List[Finding] = []

    refs = iter_image_refs(body)
    for _, href in refs:
        if is_remote_path(href):
            findings.append(
                Finding(
                    severity="error",
                    code="remote_image_url_not_allowed",
                    message="remote image url is not allowed",
                    evidence={"href": href},
                )
            )
            continue

        if stage == "gate3":
            if not href.startswith("./images/"):
                findings.append(
                    Finding(
                        severity="error",
                        code="image_ref_not_relative",
                        message="image ref must be relative ./images/{filename}",
                        evidence={"href": href},
                    )
                )
            else:
                abs_path = resolve_path(href, base_dir)
                if not file_exists(abs_path):
                    findings.append(
                        Finding(
                            severity="error",
                            code="missing_images",
                            message="image file not found",
                            evidence={"href": href, "resolved": abs_path},
                        )
                    )

        elif stage == "gate4":
            if not os.path.isabs(_strip_yaml_scalar(href).strip()):
                findings.append(
                    Finding(
                        severity="error",
                        code="image_path_not_absolute",
                        message="image ref must be an absolute local path in publish-ready file",
                        evidence={"href": href},
                    )
                )
            else:
                abs_path = os.path.normpath(_strip_yaml_scalar(href).strip())
                if not file_exists(abs_path):
                    findings.append(
                        Finding(
                            severity="error",
                            code="missing_images",
                            message="image file not found",
                            evidence={"href": href, "resolved": abs_path},
                        )
                    )

        else:
            raise ValueError(f"unknown stage: {stage}")

    return findings


def check_cover(front_matter: Dict[str, str], base_dir: str, stage: str) -> List[Finding]:
    findings: List[Finding] = []

    title = (front_matter.get("title") or "").strip()
    if not title:
        findings.append(
            Finding(
                severity="error",
                code="front_matter_missing",
                message="front matter missing required field: title",
            )
        )

    cover = (front_matter.get("cover") or "").strip()
    if not cover:
        findings.append(
            Finding(
                severity="error",
                code="cover_missing",
                message="front matter 'cover' missing or empty",
            )
        )
        return findings

    if is_remote_path(cover):
        findings.append(
            Finding(
                severity="error",
                code="remote_image_url_not_allowed",
                message="remote cover url is not allowed",
                evidence={"cover": cover},
            )
        )
        return findings

    if stage == "gate3":
        abs_path = resolve_path(cover, base_dir)
        if not file_exists(abs_path):
            findings.append(
                Finding(
                    severity="error",
                    code="missing_images",
                    message="cover file not found",
                    evidence={"cover": cover, "resolved": abs_path},
                )
            )
    elif stage == "gate4":
        if not os.path.isabs(_strip_yaml_scalar(cover).strip()):
            findings.append(
                Finding(
                    severity="error",
                    code="image_path_not_absolute",
                    message="cover must be an absolute local path in publish-ready file",
                    evidence={"cover": cover},
                )
            )
        else:
            abs_path = os.path.normpath(_strip_yaml_scalar(cover).strip())
            if not file_exists(abs_path):
                findings.append(
                    Finding(
                        severity="error",
                        code="missing_images",
                        message="cover file not found",
                        evidence={"cover": cover, "resolved": abs_path},
                    )
                )
    else:
        raise ValueError(f"unknown stage: {stage}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(prog="contenthub_preflight")
    parser.add_argument("--target", required=True, help="article markdown or publish-ready markdown")
    parser.add_argument("--stage", choices=["gate3", "gate4"], default="gate3")
    parser.add_argument("--output", default=None, help="write JSON report to file (default: stdout)")

    args = parser.parse_args()

    target_path = os.path.abspath(args.target)
    if not os.path.exists(target_path):
        print(f"ERROR: target not found: {target_path}", file=sys.stderr)
        return 2

    base_dir = os.path.dirname(target_path)

    with open(target_path, "r", encoding="utf-8") as f:
        text = f.read()

    front_matter, body, _ = parse_front_matter(text)

    findings: List[Finding] = []

    if front_matter is None:
        findings.append(
            Finding(
                severity="error",
                code="front_matter_missing",
                message="front matter missing",
            )
        )
    else:
        findings.extend(check_cover(front_matter, base_dir, args.stage))

    findings.extend(detect_placeholders(body))
    findings.extend(check_images(body, base_dir, args.stage))

    passed = not any(f.severity == "error" for f in findings)

    report = {
        "schema": "contenthub.preflight.v1",
        "stage": args.stage,
        "target": target_path,
        "passed": passed,
        "findings": [
            {
                "severity": f.severity,
                "code": f.code,
                "message": f.message,
                "evidence": f.evidence or {},
            }
            for f in findings
        ],
    }

    out_json = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        out_path = os.path.abspath(args.output)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(out_json)
            f.write("\n")
    else:
        print(out_json)

    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Deterministic project state for the keeping-skills-current skill."""

from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as datetime_module
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = 1
REVIEW_PROCEDURE_VERSION = 3
DEFAULT_MANIFEST_PATH = ".keeping-skills-current/manifest.json"
LOCATOR_PATH = ".keeping-skills-current/config.json"
REPORT_VERSION = 1
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FINGERPRINT_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
NUMERIC_HOST_LABEL_PATTERN = re.compile(r"^(?:[0-9]+|0x[0-9a-f]+)$", re.IGNORECASE)
UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)
FUNCTIONAL_DIRECTORIES = ("references", "scripts", "evals")
IGNORED_DIRECTORY_NAMES = {
    ".cache",
    ".git",
    "__pycache__",
    "node_modules",
    "outputs",
}
TOP_LEVEL_ORDER = (
    "schemaVersion",
    "scheduler",
    "delivery",
    "correctionStrategy",
    "changeValidation",
    "skills",
)
SKILL_ORDER = (
    "path",
    "schedule",
    "sources",
    "deferredFindings",
    "declinedFindings",
    "state",
)
SOURCE_ORDER = ("url", "retrieval")
RETRIEVAL_ORDER = (
    "strategy",
    "includePaths",
    "excludePaths",
    "maxDepth",
    "maxPages",
)
STATE_ORDER = (
    "lastAttemptedReview",
    "lastAttemptStatus",
    "lastCompletedReview",
    "inputFingerprint",
)
DELIVERY_ORDER = (
    "strategy",
    "reportPath",
    "branchName",
    "autoMergeStrategy",
    "fallbackReportPath",
)
SCHEDULE_ORDER = ("recurrence", "intervalDays")
DECISION_ORDER = ("details", "reason", "decidedAt", "revisitAfter")
DETAILS_ORDER = ("category", "summary", "target", "sources", "proposedAction")
TARGET_ORDER = ("filePath", "currentText", "anchorText")


class ContractError(ValueError):
    """A configuration or structured-result contract violation."""


@dataclasses.dataclass(frozen=True)
class ProjectConfiguration:
    root: Path
    manifest_path: Path
    manifest_relative_path: str
    manifest: dict[str, Any]
    warnings: tuple[str, ...]


def object_schema(properties: Mapping[str, Any], required: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required),
    }


def retrieval_schema() -> dict[str, Any]:
    page = object_schema({"strategy": {"const": "page"}}, ["strategy"])
    crawl = object_schema(
        {
            "strategy": {"const": "crawl"},
            "includePaths": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string", "pattern": r"^/"},
            },
            "excludePaths": {
                "type": "array",
                "uniqueItems": True,
                "items": {"type": "string", "pattern": r"^/"},
            },
            "maxDepth": {"type": "integer", "minimum": 1, "maximum": 5},
            "maxPages": {"type": "integer", "minimum": 1, "maximum": 100},
        },
        ["strategy", "includePaths", "maxDepth", "maxPages"],
    )
    return {"oneOf": [page, crawl]}


def source_schema() -> dict[str, Any]:
    return object_schema(
        {
            "url": {"type": "string", "format": "uri", "pattern": r"^https://"},
            "retrieval": retrieval_schema(),
        },
        ["url", "retrieval"],
    )


def target_schema() -> dict[str, Any]:
    base = {
        "filePath": {"type": "string", "minLength": 1},
        "currentText": {"type": "string", "minLength": 1},
        "anchorText": {"type": "string", "minLength": 1},
    }
    current = object_schema(base, ["filePath", "currentText"])
    current["not"] = {"required": ["anchorText"]}
    anchor = object_schema(base, ["filePath", "anchorText"])
    anchor["not"] = {"required": ["currentText"]}
    return {"oneOf": [current, anchor]}


def finding_details_schema() -> dict[str, Any]:
    return object_schema(
        {
            "category": {
                "enum": ["correction", "improvementSuggestion", "humanDecision"]
            },
            "summary": {"type": "string", "minLength": 1},
            "target": target_schema(),
            "sources": {
                "type": "object",
                "minProperties": 1,
                "propertyNames": {"pattern": ID_PATTERN.pattern},
                "additionalProperties": source_schema(),
            },
            "proposedAction": {"type": "string", "minLength": 1},
        },
        ["category", "summary", "target", "sources", "proposedAction"],
    )


def decision_schema(deferred: bool) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "details": finding_details_schema(),
        "reason": {"type": "string", "minLength": 1},
        "decidedAt": {"type": "string", "format": "date-time"},
    }
    required = ["details", "reason", "decidedAt"]
    if deferred:
        properties["revisitAfter"] = {"type": "string", "format": "date-time"}
        required.append("revisitAfter")
    return object_schema(properties, required)


def state_schema() -> dict[str, Any]:
    return object_schema(
        {
            "lastAttemptedReview": {"type": "string", "format": "date-time"},
            "lastAttemptStatus": {"enum": ["completed", "incomplete"]},
            "lastCompletedReview": {"type": "string", "format": "date-time"},
            "inputFingerprint": {
                "type": "string",
                "pattern": FINGERPRINT_PATTERN.pattern,
            },
        },
        ["lastAttemptedReview", "lastAttemptStatus"],
    )


def schedule_schema() -> dict[str, Any]:
    manual = object_schema({"recurrence": {"const": "manual"}}, ["recurrence"])
    interval = object_schema(
        {
            "recurrence": {"const": "interval"},
            "intervalDays": {"type": "integer", "minimum": 1},
        },
        ["recurrence", "intervalDays"],
    )
    return {"oneOf": [manual, interval]}


def skill_schema() -> dict[str, Any]:
    return object_schema(
        {
            "path": {"type": "string", "minLength": 1},
            "schedule": schedule_schema(),
            "sources": {
                "type": "object",
                "propertyNames": {"pattern": ID_PATTERN.pattern},
                "additionalProperties": source_schema(),
            },
            "deferredFindings": {"type": "array", "items": decision_schema(True)},
            "declinedFindings": {"type": "array", "items": decision_schema(False)},
            "state": state_schema(),
        },
        ["path", "schedule", "sources", "deferredFindings", "declinedFindings"],
    )


def manifest_schema() -> dict[str, Any]:
    local_delivery = object_schema(
        {
            "strategy": {"const": "localReport"},
            "reportPath": {"type": "string", "minLength": 1},
        },
        ["strategy", "reportPath"],
    )
    github_delivery = object_schema(
        {
            "strategy": {"const": "githubPullRequest"},
            "branchName": {"type": "string", "minLength": 1},
            "autoMergeStrategy": {"enum": ["none", "stateOnly"]},
            "fallbackReportPath": {"type": "string", "minLength": 1},
        },
        ["strategy", "branchName", "autoMergeStrategy"],
    )
    schema = object_schema(
        {
            "schemaVersion": {"const": SCHEMA_VERSION},
            "scheduler": {"enum": ["none", "agentPlatform", "githubActions"]},
            "delivery": {"oneOf": [local_delivery, github_delivery]},
            "correctionStrategy": {
                "enum": ["reportOnly", "applyHighConfidenceCorrections"]
            },
            "changeValidation": {"enum": ["enabled", "disabled"]},
            "skills": {
                "type": "object",
                "propertyNames": {"pattern": ID_PATTERN.pattern},
                "additionalProperties": skill_schema(),
            },
        },
        TOP_LEVEL_ORDER,
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://cypherpoet.dev/schemas/keeping-skills-current/manifest.v1.json"
    schema["title"] = "Keeping Skills Current Manifest"
    return schema


def evidence_schema() -> dict[str, Any]:
    return object_schema(
        {
            "sourceId": {"type": "string", "pattern": ID_PATTERN.pattern},
            "sourceRootUrl": {"type": "string", "format": "uri"},
            "evidencePageUrl": {"type": "string", "format": "uri"},
            "summary": {"type": "string", "minLength": 1},
            "excerpt": {"type": "string", "minLength": 1},
        },
        ["sourceId", "sourceRootUrl", "evidencePageUrl", "summary", "excerpt"],
    )


def research_result_schema() -> dict[str, Any]:
    source_outcome = object_schema(
        {
            "sourceId": {"type": "string", "pattern": ID_PATTERN.pattern},
            "rootUrl": {"type": "string", "format": "uri"},
            "status": {"enum": ["retrieved", "missing", "failed"]},
            "successfulPages": {"type": "integer", "minimum": 0},
            "attemptedPages": {"type": "integer", "minimum": 0},
            "limitReached": {"type": "boolean"},
            "failureStage": {"type": "string"},
            "failureReason": {"type": "string"},
        },
        [
            "sourceId",
            "rootUrl",
            "status",
            "successfulPages",
            "attemptedPages",
            "limitReached",
        ],
    )
    finding = object_schema(
        {
            "details": finding_details_schema(),
            "evidence": {"type": "array", "minItems": 1, "items": evidence_schema()},
            "editDisposition": {
                "enum": [
                    "applied",
                    "proposed",
                    "revertedAfterValidationFailure",
                    "notApplicable",
                ]
            },
        },
        ["details", "evidence", "editDisposition"],
    )
    validation = object_schema(
        {
            "status": {"enum": ["passed", "failed", "skipped", "notApplicable"]},
            "checks": {
                "type": "array",
                "items": object_schema(
                    {
                        "name": {"type": "string", "minLength": 1},
                        "status": {"enum": ["passed", "failed", "skipped"]},
                        "note": {"type": "string"},
                    },
                    ["name", "status"],
                ),
            },
        },
        ["status", "checks"],
    )
    schema = object_schema(
        {
            "schemaVersion": {"const": SCHEMA_VERSION},
            "projectIdentity": {"type": "string", "minLength": 1},
            "skillId": {"type": "string", "pattern": ID_PATTERN.pattern},
            "skillPath": {"type": "string", "minLength": 1},
            "inputFingerprint": {
                "type": "string",
                "pattern": FINGERPRINT_PATTERN.pattern,
            },
            "reviewedAt": {"type": "string", "format": "date-time"},
            "status": {"enum": ["completed", "incomplete"]},
            "sourceOutcomes": {"type": "array", "items": source_outcome},
            "findings": {"type": "array", "items": finding},
            "failures": {
                "type": "array",
                "items": object_schema(
                    {
                        "stage": {"type": "string", "minLength": 1},
                        "reason": {"type": "string", "minLength": 1},
                    },
                    ["stage", "reason"],
                ),
            },
            "validation": validation,
        },
        [
            "schemaVersion",
            "projectIdentity",
            "skillId",
            "skillPath",
            "inputFingerprint",
            "reviewedAt",
            "status",
            "sourceOutcomes",
            "findings",
            "failures",
            "validation",
        ],
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://cypherpoet.dev/schemas/keeping-skills-current/research-result.v1.json"
    schema["title"] = "Keeping Skills Current Research Result"
    return schema


def validate_against_model(value: Any, schema: Mapping[str, Any], location: str) -> None:
    if "oneOf" in schema:
        matches = 0
        for alternative in schema["oneOf"]:
            try:
                validate_against_model(value, alternative, location)
            except ContractError:
                continue
            matches += 1
        if matches != 1:
            raise ContractError(f"{location} must match exactly one supported shape")
        return
    if "const" in schema and value != schema["const"]:
        raise ContractError(f"{location} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{location} contains an unsupported value")
    expected_type = schema.get("type")
    type_matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }
    if expected_type is not None and not type_matches.get(expected_type, False):
        raise ContractError(f"{location} must be {expected_type}")
    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise ContractError(f"{location} is missing required field(s): {', '.join(missing)}")
        property_name_schema = schema.get("propertyNames")
        if property_name_schema is not None:
            for key in value:
                validate_against_model(key, property_name_schema, f"{location} key")
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            child_schema = properties.get(key)
            if child_schema is None:
                if additional is False:
                    raise ContractError(f"{location} contains unknown field: {key}")
                if isinstance(additional, dict):
                    child_schema = additional
            if child_schema is not None:
                validate_against_model(child, child_schema, f"{location}.{key}")
        if len(value) < schema.get("minProperties", 0):
            raise ContractError(f"{location} contains too few properties")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            raise ContractError(f"{location} contains too few items")
        if schema.get("uniqueItems"):
            canonical_items = [canonical_json(item) for item in value]
            if len(canonical_items) != len(set(canonical_items)):
                raise ContractError(f"{location} must contain unique items")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, item in enumerate(value):
                validate_against_model(item, item_schema, f"{location}[{index}]")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise ContractError(f"{location} is too short")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(pattern, value) is None:
            raise ContractError(f"{location} does not match its required pattern")
    if isinstance(value, int) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ContractError(f"{location} is below its minimum")
        if "maximum" in schema and value > schema["maximum"]:
            raise ContractError(f"{location} exceeds its maximum")
    if "not" in schema:
        try:
            validate_against_model(value, schema["not"], location)
        except ContractError:
            pass
        else:
            raise ContractError(f"{location} matches a forbidden shape")


def require_object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{location} must be an object")
    return value


def reject_unknown(value: Mapping[str, Any], allowed: Iterable[str], location: str) -> None:
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ContractError(f"{location} contains unknown field(s): {', '.join(unknown)}")


def require_keys(value: Mapping[str, Any], required: Iterable[str], location: str) -> None:
    missing = [key for key in required if key not in value]
    if missing:
        raise ContractError(f"{location} is missing required field(s): {', '.join(missing)}")


def require_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or value == "":
        raise ContractError(f"{location} must be a nonempty string")
    return value


def parse_utc(value: Any, location: str) -> datetime_module.datetime:
    text = require_string(value, location)
    if not UTC_TIMESTAMP_PATTERN.fullmatch(text):
        raise ContractError(f"{location} must be an ISO 8601 UTC instant ending in Z")
    parsed = datetime_module.datetime.fromisoformat(text[:-1] + "+00:00")
    return parsed.astimezone(datetime_module.timezone.utc)


def normalize_relative_path(raw: Any, root: Path, location: str, suffix: str | None = None) -> str:
    value = require_string(raw, location)
    if "\\" in value:
        raise ContractError(f"{location} must use forward slashes")
    pure = PurePosixPath(value)
    if pure.is_absolute() or value in {".", ".."} or any(part in {"", ".", ".."} for part in pure.parts):
        raise ContractError(f"{location} must be a safe repository-relative path")
    normalized = pure.as_posix()
    if suffix is not None and not normalized.endswith(suffix):
        raise ContractError(f"{location} must end with {suffix}")
    root_resolved = root.resolve()
    candidate = (root_resolved / Path(*pure.parts)).resolve(strict=False)
    try:
        candidate.relative_to(root_resolved)
    except ValueError as error:
        raise ContractError(f"{location} resolves outside the project root") from error
    return normalized


def normalize_url_path(raw: Any, location: str) -> str:
    value = require_string(raw, location)
    if "?" in value or "#" in value or not value.startswith("/") or "\\" in value:
        raise ContractError(f"{location} must be a leading-slash URL path without query or fragment")
    parts: list[str] = []
    for part in value.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    normalized = "/" + "/".join(parts)
    return normalized + ("/" if value.endswith("/") and normalized != "/" else "")


def host_is_public(hostname: str) -> bool:
    lowered = hostname.rstrip(".").lower()
    if lowered == "localhost" or lowered.endswith(".localhost") or lowered.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(lowered)
    except ValueError:
        labels = lowered.split(".")
        if labels and all(NUMERIC_HOST_LABEL_PATTERN.fullmatch(label) for label in labels):
            return False
        return "." in lowered
    return address.is_global


def normalize_source_url(raw: Any, location: str, crawl: bool) -> str:
    value = require_string(raw, location)
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ContractError(f"{location} must be an HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise ContractError(f"{location} must not contain credentials")
    if parsed.fragment:
        raise ContractError(f"{location} must not contain a fragment")
    if crawl and parsed.query:
        raise ContractError(f"{location} must not contain a query for crawl retrieval")
    if not host_is_public(parsed.hostname):
        raise ContractError(f"{location} must target a public host")
    path = parsed.path or "/"
    normalized_path = normalize_url_path(path, f"{location} path")
    normalized_hostname = parsed.hostname.lower()
    netloc = f"[{normalized_hostname}]" if ":" in normalized_hostname else normalized_hostname
    if parsed.port is not None:
        netloc += f":{parsed.port}"
    return urlunsplit(("https", netloc, normalized_path, parsed.query, ""))


def path_authorized(path: str, prefixes: Sequence[str]) -> bool:
    candidate = path.rstrip("/") or "/"
    for prefix in prefixes:
        expected = prefix.rstrip("/") or "/"
        if expected == "/" or candidate == expected or candidate.startswith(expected + "/"):
            return True
    return False


def validate_retrieval(value: Any, location: str) -> dict[str, Any]:
    retrieval = require_object(value, location)
    strategy = retrieval.get("strategy")
    if strategy == "page":
        reject_unknown(retrieval, {"strategy"}, location)
        return {"strategy": "page"}
    if strategy != "crawl":
        raise ContractError(f"{location}.strategy must be page or crawl")
    reject_unknown(retrieval, RETRIEVAL_ORDER, location)
    require_keys(retrieval, {"strategy", "includePaths", "maxDepth", "maxPages"}, location)
    includes = retrieval["includePaths"]
    excludes = retrieval.get("excludePaths", [])
    if not isinstance(includes, list) or not includes:
        raise ContractError(f"{location}.includePaths must be a nonempty array")
    if not isinstance(excludes, list):
        raise ContractError(f"{location}.excludePaths must be an array")
    normalized_includes = sorted(
        {normalize_url_path(item, f"{location}.includePaths") for item in includes}
    )
    normalized_excludes = sorted(
        {normalize_url_path(item, f"{location}.excludePaths") for item in excludes}
    )
    max_depth = retrieval["maxDepth"]
    max_pages = retrieval["maxPages"]
    if isinstance(max_depth, bool) or not isinstance(max_depth, int) or not 1 <= max_depth <= 5:
        raise ContractError(f"{location}.maxDepth must be an integer from 1 through 5")
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or not 1 <= max_pages <= 100:
        raise ContractError(f"{location}.maxPages must be an integer from 1 through 100")
    return {
        "strategy": "crawl",
        "includePaths": normalized_includes,
        "excludePaths": normalized_excludes,
        "maxDepth": max_depth,
        "maxPages": max_pages,
    }


def validate_source(value: Any, location: str) -> dict[str, Any]:
    source = require_object(value, location)
    reject_unknown(source, SOURCE_ORDER, location)
    require_keys(source, SOURCE_ORDER, location)
    retrieval = validate_retrieval(source["retrieval"], f"{location}.retrieval")
    url = normalize_source_url(source["url"], f"{location}.url", retrieval["strategy"] == "crawl")
    if retrieval["strategy"] == "crawl":
        starting_path = urlsplit(url).path
        if not path_authorized(starting_path, retrieval["includePaths"]):
            raise ContractError(f"{location}.url path must match an includePaths prefix")
        if path_authorized(starting_path, retrieval["excludePaths"]):
            raise ContractError(f"{location}.url path must not match an excludePaths prefix")
    return {"url": url, "retrieval": retrieval}


def validate_target(value: Any, root: Path, location: str) -> dict[str, Any]:
    target = require_object(value, location)
    reject_unknown(target, {"filePath", "currentText", "anchorText"}, location)
    require_keys(target, {"filePath"}, location)
    has_current = "currentText" in target
    has_anchor = "anchorText" in target
    if has_current == has_anchor:
        raise ContractError(f"{location} must contain exactly one of currentText or anchorText")
    result = {
        "filePath": normalize_relative_path(target["filePath"], root, f"{location}.filePath")
    }
    key = "currentText" if has_current else "anchorText"
    result[key] = require_string(target[key], f"{location}.{key}")
    return result


def validate_details(value: Any, root: Path, location: str) -> dict[str, Any]:
    details = require_object(value, location)
    allowed = {"category", "summary", "target", "sources", "proposedAction"}
    reject_unknown(details, allowed, location)
    require_keys(details, allowed, location)
    category = details["category"]
    if category not in {"correction", "improvementSuggestion", "humanDecision"}:
        raise ContractError(f"{location}.category is invalid")
    sources = validate_sources(details["sources"], root, f"{location}.sources")
    if not sources:
        raise ContractError(f"{location}.sources must contain at least one configured source")
    return {
        "category": category,
        "summary": require_string(details["summary"], f"{location}.summary"),
        "target": validate_target(details["target"], root, f"{location}.target"),
        "sources": sources,
        "proposedAction": require_string(
            details["proposedAction"], f"{location}.proposedAction"
        ),
    }


def validate_decisions(value: Any, root: Path, location: str, deferred: bool) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ContractError(f"{location} must be an array")
    output: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        item_location = f"{location}[{index}]"
        item = require_object(raw, item_location)
        allowed = {"details", "reason", "decidedAt"}
        if deferred:
            allowed.add("revisitAfter")
        reject_unknown(item, allowed, item_location)
        require_keys(item, allowed, item_location)
        parse_utc(item["decidedAt"], f"{item_location}.decidedAt")
        result = {
            "details": validate_details(item["details"], root, f"{item_location}.details"),
            "reason": require_string(item["reason"], f"{item_location}.reason"),
            "decidedAt": item["decidedAt"],
        }
        if deferred:
            parse_utc(item["revisitAfter"], f"{item_location}.revisitAfter")
            result["revisitAfter"] = item["revisitAfter"]
        output.append(result)
    return output


def validate_state(value: Any, location: str) -> dict[str, Any]:
    state = require_object(value, location)
    reject_unknown(state, STATE_ORDER, location)
    attempted = "lastAttemptedReview" in state or "lastAttemptStatus" in state
    completed = "lastCompletedReview" in state or "inputFingerprint" in state
    if attempted:
        require_keys(state, {"lastAttemptedReview", "lastAttemptStatus"}, location)
    else:
        raise ContractError(f"{location} must contain attempted timestamp and status")
    if completed:
        require_keys(state, {"lastCompletedReview", "inputFingerprint"}, location)
    parse_utc(state["lastAttemptedReview"], f"{location}.lastAttemptedReview")
    if state["lastAttemptStatus"] not in {"completed", "incomplete"}:
        raise ContractError(f"{location}.lastAttemptStatus is invalid")
    output = {
        "lastAttemptedReview": state["lastAttemptedReview"],
        "lastAttemptStatus": state["lastAttemptStatus"],
    }
    if completed:
        parse_utc(state["lastCompletedReview"], f"{location}.lastCompletedReview")
        fingerprint = require_string(state["inputFingerprint"], f"{location}.inputFingerprint")
        if not FINGERPRINT_PATTERN.fullmatch(fingerprint):
            raise ContractError(f"{location}.inputFingerprint must be sha256 plus 64 lowercase hex characters")
        output.update(
            {
                "lastCompletedReview": state["lastCompletedReview"],
                "inputFingerprint": fingerprint,
            }
        )
    return output


def validate_schedule(value: Any, sources: Mapping[str, Any], location: str) -> dict[str, Any]:
    schedule = require_object(value, location)
    recurrence = schedule.get("recurrence")
    if recurrence == "manual":
        reject_unknown(schedule, {"recurrence"}, location)
        return {"recurrence": "manual"}
    if recurrence != "interval":
        raise ContractError(f"{location}.recurrence must be manual or interval")
    reject_unknown(schedule, {"recurrence", "intervalDays"}, location)
    require_keys(schedule, {"recurrence", "intervalDays"}, location)
    interval = schedule["intervalDays"]
    if isinstance(interval, bool) or not isinstance(interval, int) or interval < 1:
        raise ContractError(f"{location}.intervalDays must be a positive integer")
    if not sources:
        raise ContractError(f"{location} cannot be interval-based without a source")
    return {"recurrence": "interval", "intervalDays": interval}


def validate_sources(value: Any, root: Path, location: str) -> dict[str, Any]:
    sources = require_object(value, location)
    output: dict[str, Any] = {}
    signatures: set[str] = set()
    for source_id in sorted(sources):
        if not ID_PATTERN.fullmatch(source_id):
            raise ContractError(f"{location} key {source_id!r} must be lowercase kebab-case")
        normalized = validate_source(sources[source_id], f"{location}.{source_id}")
        signature = canonical_json(normalized)
        if signature in signatures:
            raise ContractError(f"{location} contains an exact duplicate source request")
        signatures.add(signature)
        output[source_id] = normalized
    return output


def git_branch_name_is_safe(branch: str) -> bool:
    if branch in {"@", "HEAD"} or branch.startswith("-") or branch.endswith("/"):
        return False
    if "//" in branch or ".." in branch or "@{" in branch:
        return False
    if re.search(r"[\x00-\x20\x7f~^:?*\[\\]", branch):
        return False
    for component in branch.split("/"):
        if not component or component.startswith("."):
            return False
        if component.endswith(".") or component.endswith(".lock"):
            return False
    return True


def check_git_branch_capability(branch: str) -> tuple[bool, bool]:
    try:
        result = subprocess.run(
            ["git", "check-ref-format", "--branch", branch],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, False
    return True, result.returncode == 0


def validate_delivery(value: Any, root: Path) -> dict[str, Any]:
    delivery = require_object(value, "delivery")
    strategy = delivery.get("strategy")
    if strategy == "localReport":
        reject_unknown(delivery, {"strategy", "reportPath"}, "delivery")
        require_keys(delivery, {"strategy", "reportPath"}, "delivery")
        return {
            "strategy": strategy,
            "reportPath": normalize_relative_path(
                delivery["reportPath"], root, "delivery.reportPath", ".md"
            ),
        }
    if strategy != "githubPullRequest":
        raise ContractError("delivery.strategy must be localReport or githubPullRequest")
    allowed = {"strategy", "branchName", "autoMergeStrategy", "fallbackReportPath"}
    reject_unknown(delivery, allowed, "delivery")
    require_keys(delivery, {"strategy", "branchName", "autoMergeStrategy"}, "delivery")
    branch = require_string(delivery["branchName"], "delivery.branchName")
    if not git_branch_name_is_safe(branch):
        raise ContractError("delivery.branchName is not a safe Git branch name")
    auto_merge = delivery["autoMergeStrategy"]
    if auto_merge not in {"none", "stateOnly"}:
        raise ContractError("delivery.autoMergeStrategy must be none or stateOnly")
    result = {
        "strategy": strategy,
        "branchName": branch,
        "autoMergeStrategy": auto_merge,
    }
    if "fallbackReportPath" in delivery:
        result["fallbackReportPath"] = normalize_relative_path(
            delivery["fallbackReportPath"], root, "delivery.fallbackReportPath", ".md"
        )
    return result


def ensure_outside_skills(
    paths: Sequence[str],
    skill_paths: Sequence[str],
    root: Path | None = None,
) -> None:
    for path in paths:
        candidate = PurePosixPath(path)
        for skill_path in skill_paths:
            skill = PurePosixPath(skill_path)
            if candidate == skill or skill in candidate.parents:
                raise ContractError(f"workflow path {path} must remain outside managed skill {skill_path}")
            if root is not None:
                resolved_candidate = (
                    root / Path(*candidate.parts)
                ).resolve(strict=False)
                resolved_skill = (
                    root / Path(*skill.parts)
                ).resolve(strict=False)
                if (
                    resolved_candidate == resolved_skill
                    or resolved_skill in resolved_candidate.parents
                ):
                    raise ContractError(
                        f"workflow path {path} must remain outside managed skill {skill_path}"
                    )


def target_belongs_to_skill(target_path: str, skill_path: str) -> bool:
    target = PurePosixPath(target_path)
    skill = PurePosixPath(skill_path)
    try:
        relative = target.relative_to(skill)
    except ValueError:
        return False
    return relative.parts == ("SKILL.md",) or (
        bool(relative.parts) and relative.parts[0] in FUNCTIONAL_DIRECTORIES
    )


def validate_manifest(raw: Any, root: Path) -> dict[str, Any]:
    manifest = require_object(raw, "manifest")
    reject_unknown(manifest, TOP_LEVEL_ORDER, "manifest")
    require_keys(manifest, TOP_LEVEL_ORDER, "manifest")
    version = manifest["schemaVersion"]
    if version != SCHEMA_VERSION:
        if isinstance(version, int) and version < SCHEMA_VERSION:
            raise ContractError(f"manifest schemaVersion {version} requires interactive migration")
        raise ContractError(f"manifest schemaVersion {version!r} is not supported by this installed skill")
    scheduler = manifest["scheduler"]
    if scheduler not in {"none", "agentPlatform", "githubActions"}:
        raise ContractError("scheduler must be none, agentPlatform, or githubActions")
    correction_strategy = manifest["correctionStrategy"]
    if correction_strategy not in {"reportOnly", "applyHighConfidenceCorrections"}:
        raise ContractError("correctionStrategy is invalid")
    change_validation = manifest["changeValidation"]
    if change_validation not in {"enabled", "disabled"}:
        raise ContractError("changeValidation is invalid")
    delivery = validate_delivery(manifest["delivery"], root)
    if scheduler == "githubActions" and delivery["strategy"] != "githubPullRequest":
        raise ContractError("githubActions requires githubPullRequest delivery")
    skills_raw = require_object(manifest["skills"], "skills")
    skills: dict[str, Any] = {}
    seen_paths: set[str] = set()
    for skill_id in sorted(skills_raw):
        if not ID_PATTERN.fullmatch(skill_id):
            raise ContractError(f"skill ID {skill_id!r} must be lowercase kebab-case")
        location = f"skills.{skill_id}"
        skill = require_object(skills_raw[skill_id], location)
        reject_unknown(skill, SKILL_ORDER, location)
        require_keys(
            skill,
            {"path", "schedule", "sources", "deferredFindings", "declinedFindings"},
            location,
        )
        path = normalize_relative_path(skill["path"], root, f"{location}.path")
        candidate_path = PurePosixPath(path)
        for existing_path_text in seen_paths:
            existing_path = PurePosixPath(existing_path_text)
            if (
                candidate_path == existing_path
                or candidate_path in existing_path.parents
                or existing_path in candidate_path.parents
            ):
                raise ContractError(
                    f"managed skill paths overlap: {existing_path_text} and {path}"
                )
        seen_paths.add(path)
        sources = validate_sources(skill["sources"], root, f"{location}.sources")
        deferred_findings = validate_decisions(
            skill["deferredFindings"], root, f"{location}.deferredFindings", True
        )
        declined_findings = validate_decisions(
            skill["declinedFindings"], root, f"{location}.declinedFindings", False
        )
        for decision in deferred_findings + declined_findings:
            target_path = decision["details"]["target"]["filePath"]
            if not target_belongs_to_skill(target_path, path):
                raise ContractError(
                    f"{location} decision target is outside the managed skill: {target_path}"
                )
        normalized: dict[str, Any] = {
            "path": path,
            "schedule": validate_schedule(skill["schedule"], sources, f"{location}.schedule"),
            "sources": sources,
            "deferredFindings": deferred_findings,
            "declinedFindings": declined_findings,
        }
        if "state" in skill:
            normalized["state"] = validate_state(skill["state"], f"{location}.state")
        skills[skill_id] = normalized
    workflow_paths = [DEFAULT_MANIFEST_PATH, LOCATOR_PATH]
    if delivery["strategy"] == "localReport":
        workflow_paths.append(delivery["reportPath"])
    elif "fallbackReportPath" in delivery:
        workflow_paths.append(delivery["fallbackReportPath"])
    ensure_outside_skills(
        workflow_paths,
        [skill["path"] for skill in skills.values()],
        root,
    )
    normalized_manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "scheduler": scheduler,
        "delivery": delivery,
        "correctionStrategy": correction_strategy,
        "changeValidation": change_validation,
        "skills": skills,
    }
    validate_against_model(normalized_manifest, manifest_schema(), "manifest")
    return normalized_manifest


def resolve_project_root(explicit: str | None) -> Path:
    start = Path(explicit).expanduser() if explicit else Path.cwd()
    start = start.resolve()
    if not start.is_dir():
        raise ContractError(f"project root is not a directory: {start}")
    if explicit is not None:
        return start
    candidate = start
    while True:
        git_marker = candidate / ".git"
        if git_marker.exists():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            return start
        candidate = parent


def resolve_manifest_path(root: Path, explicit: str | None) -> tuple[str, tuple[str, ...]]:
    warnings: list[str] = []
    if explicit is not None:
        return normalize_relative_path(explicit, root, "--manifest", ".json"), tuple(warnings)
    locator = root / LOCATOR_PATH
    if locator.exists():
        if locator.is_symlink() or not locator.is_file():
            raise ContractError(f"{LOCATOR_PATH} must be a regular file")
        try:
            raw = json.loads(locator.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ContractError(f"could not read {LOCATOR_PATH}: {error}") from error
        config = require_object(raw, LOCATOR_PATH)
        reject_unknown(config, {"manifestPath"}, LOCATOR_PATH)
        require_keys(config, {"manifestPath"}, LOCATOR_PATH)
        path = normalize_relative_path(config["manifestPath"], root, "manifestPath", ".json")
        if path == DEFAULT_MANIFEST_PATH:
            warnings.append(f"{LOCATOR_PATH} redundantly points to the default manifest")
        return path, tuple(warnings)
    return DEFAULT_MANIFEST_PATH, tuple(warnings)


def load_configuration(root_argument: str | None, manifest_argument: str | None) -> ProjectConfiguration:
    root = resolve_project_root(root_argument)
    relative_path, warnings = resolve_manifest_path(root, manifest_argument)
    path = root / Path(*PurePosixPath(relative_path).parts)
    if not path.exists():
        raise ContractError(f"Not configured: {relative_path} does not exist")
    if path.is_symlink() or not path.is_file():
        raise ContractError(f"manifest must be a regular file: {relative_path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"could not read {relative_path}: {error}") from error
    manifest = validate_manifest(raw, root)
    ensure_outside_skills(
        [relative_path],
        [skill["path"] for skill in manifest["skills"].values()],
        root,
    )
    if relative_path != DEFAULT_MANIFEST_PATH and (root / DEFAULT_MANIFEST_PATH).exists():
        warnings += (
            f"inactive default manifest exists at {DEFAULT_MANIFEST_PATH}; reconcile it interactively before automated mutation",
        )
    return ProjectConfiguration(root, path, relative_path, manifest, warnings)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def ordered(value: Any, order: Sequence[str] | None = None) -> Any:
    if isinstance(value, list):
        return [ordered(item) for item in value]
    if not isinstance(value, dict):
        return value
    keys = list(value)
    if order is None:
        keys.sort()
    else:
        position = {key: index for index, key in enumerate(order)}
        keys.sort(key=lambda key: (position.get(key, len(position)), key))
    output: dict[str, Any] = {}
    for key in keys:
        child_order: Sequence[str] | None = None
        if key == "skills":
            output[key] = {
                skill_id: ordered(value[key][skill_id], SKILL_ORDER)
                for skill_id in sorted(value[key])
            }
            continue
        if key == "sources":
            output[key] = {
                source_id: ordered(value[key][source_id], SOURCE_ORDER)
                for source_id in sorted(value[key])
            }
            continue
        if key in {"deferredFindings", "declinedFindings"}:
            output[key] = [ordered(item, DECISION_ORDER) for item in value[key]]
            continue
        if key == "retrieval":
            child_order = RETRIEVAL_ORDER
        elif key == "state":
            child_order = STATE_ORDER
        elif key == "delivery":
            child_order = DELIVERY_ORDER
        elif key == "schedule":
            child_order = SCHEDULE_ORDER
        elif key == "details":
            child_order = DETAILS_ORDER
        elif key == "target":
            child_order = TARGET_ORDER
        output[key] = ordered(value[key], child_order)
    return output


def pretty_json(value: Any, order: Sequence[str] | None = None) -> str:
    return json.dumps(ordered(value, order), ensure_ascii=False, indent=2) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def functional_files(root: Path, skill_path: str) -> list[tuple[str, bytes]]:
    skill_root = root / Path(*PurePosixPath(skill_path).parts)
    if skill_root.is_symlink() or not skill_root.is_dir():
        raise ContractError(f"managed skill path is missing or not a regular directory: {skill_path}")
    skill_manifest = skill_root / "SKILL.md"
    if skill_manifest.is_symlink() or not skill_manifest.is_file():
        raise ContractError(f"managed skill must contain one regular root SKILL.md: {skill_path}")
    found: list[Path] = [skill_manifest]
    for directory_name in FUNCTIONAL_DIRECTORIES:
        directory = skill_root / directory_name
        if directory.is_symlink() or not directory.is_dir():
            continue
        for current, directory_names, file_names in os.walk(directory, followlinks=False):
            directory_names[:] = sorted(
                name
                for name in directory_names
                if name not in IGNORED_DIRECTORY_NAMES
                and not name.endswith("-workspace")
                and not (Path(current) / name).is_symlink()
            )
            for file_name in sorted(file_names):
                path = Path(current) / file_name
                if path.is_symlink() or not path.is_file():
                    continue
                try:
                    path.read_text(encoding="utf-8")
                except (UnicodeError, OSError):
                    continue
                found.append(path)
    result: list[tuple[str, bytes]] = []
    for path in sorted(set(found)):
        relative = path.relative_to(root).as_posix()
        result.append((relative, path.read_bytes()))
    return result


def skill_fingerprint(configuration: ProjectConfiguration, skill_id: str) -> tuple[str, list[str]]:
    try:
        skill = configuration.manifest["skills"][skill_id]
    except KeyError as error:
        raise ContractError(f"unknown managed skill: {skill_id}") from error
    files = functional_files(configuration.root, skill["path"])
    payload = {
        "reviewProcedureVersion": REVIEW_PROCEDURE_VERSION,
        "skillId": skill_id,
        "path": skill["path"],
        "files": [
            {
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for path, content in files
        ],
        "sources": skill["sources"],
        "correctionStrategy": configuration.manifest["correctionStrategy"],
        "changeValidation": configuration.manifest["changeValidation"],
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}", [path for path, _ in files]


def due_reason(
    configuration: ProjectConfiguration,
    skill_id: str,
    now: datetime_module.datetime,
    force_failed: bool = False,
) -> tuple[bool, str, str | None]:
    skill = configuration.manifest["skills"][skill_id]
    schedule = skill["schedule"]
    if schedule["recurrence"] == "manual":
        return False, "manual", None
    if not skill["sources"]:
        return False, "draft", None
    fingerprint, _ = skill_fingerprint(configuration, skill_id)
    state = skill.get("state")
    if state and state.get("lastAttemptStatus") == "incomplete" and not force_failed:
        attempted = parse_utc(state["lastAttemptedReview"], "lastAttemptedReview")
        if now < attempted + datetime_module.timedelta(hours=24):
            return False, "incomplete attempt in 24-hour backoff", fingerprint
    if state is None or "lastCompletedReview" not in state:
        return True, "never completed", fingerprint
    if state["inputFingerprint"] != fingerprint:
        return True, "review inputs changed", fingerprint
    if state.get("lastAttemptStatus") == "incomplete" and not force_failed:
        return True, "retry after incomplete attempt", fingerprint
    completed = parse_utc(state["lastCompletedReview"], "lastCompletedReview")
    due_at = completed + datetime_module.timedelta(days=schedule["intervalDays"])
    if now >= due_at:
        return True, f"interval elapsed at {format_utc(due_at)}", fingerprint
    return False, f"next review at {format_utc(due_at)}", fingerprint


def format_utc(value: datetime_module.datetime) -> str:
    return value.astimezone(datetime_module.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def current_utc(raw: str | None) -> datetime_module.datetime:
    if raw is None:
        return datetime_module.datetime.now(datetime_module.timezone.utc)
    return parse_utc(raw, "--now")


def normalized_remote_identity(remote: str) -> str | None:
    remote = remote.strip()
    scp_match = re.fullmatch(r"[^/@:]+@([^:]+):(.+)", remote)
    if scp_match:
        host, path = scp_match.groups()
    else:
        parsed = urlsplit(remote)
        if not parsed.hostname or parsed.scheme not in {"http", "https", "ssh", "git"}:
            return None
        host, path = parsed.hostname, parsed.path
    normalized_path = path.strip("/")
    if normalized_path.endswith(".git"):
        normalized_path = normalized_path[:-4]
    if not normalized_path:
        return None
    return f"{host.lower()}/{normalized_path}"


def project_identity(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return root.name
    if result.returncode == 0:
        identity = normalized_remote_identity(result.stdout)
        if identity:
            return identity
    return root.name


def preflight_output(configuration: ProjectConfiguration, mutation: bool) -> dict[str, Any]:
    warnings = list(configuration.warnings)
    if mutation and any(message.startswith("inactive default") for message in warnings):
        raise ContractError(warnings[-1])
    capabilities: dict[str, Any] = {}
    delivery = configuration.manifest["delivery"]
    if delivery["strategy"] == "githubPullRequest":
        git_available, branch_valid = check_git_branch_capability(
            delivery["branchName"]
        )
        capabilities["gitAvailable"] = git_available
        capabilities["gitBranchValid"] = branch_valid if git_available else None
        if git_available and not branch_valid:
            raise ContractError("delivery.branchName is not a safe Git branch name")
        if mutation and not git_available:
            raise ContractError("githubPullRequest delivery requires Git before mutation")
    skills: dict[str, Any] = {}
    for skill_id, skill in configuration.manifest["skills"].items():
        skill_root = configuration.root / Path(*PurePosixPath(skill["path"]).parts)
        ready = bool(skill["sources"])
        status = "Draft" if not ready else "Configured"
        error: str | None = None
        try:
            functional_files(configuration.root, skill["path"])
        except ContractError as contract_error:
            status = "Failed"
            error = str(contract_error)
        skills[skill_id] = {
            "path": skill["path"],
            "status": status,
            "sourceCount": len(skill["sources"]),
            "error": error,
            "skillRootExists": skill_root.is_dir() and not skill_root.is_symlink(),
        }
    return {
        "projectRoot": str(configuration.root),
        "projectIdentity": project_identity(configuration.root),
        "manifestPath": configuration.manifest_relative_path,
        "warnings": warnings,
        "capabilities": capabilities,
        "manifest": configuration.manifest,
        "skills": skills,
    }


def status_output(configuration: ProjectConfiguration, now: datetime_module.datetime) -> dict[str, Any]:
    preflight = preflight_output(configuration, False)
    skills: dict[str, Any] = {}
    for skill_id, skill in configuration.manifest["skills"].items():
        try:
            due, reason, current_fingerprint = due_reason(configuration, skill_id, now)
            error = None
        except ContractError as contract_error:
            due, reason, current_fingerprint = False, "failed", None
            error = str(contract_error)
        readiness = "Draft" if not skill["sources"] else "Configured"
        skills[skill_id] = {
            "path": skill["path"],
            "readiness": readiness,
            "schedule": skill["schedule"],
            "sourceCount": len(skill["sources"]),
            "due": due,
            "dueReason": reason,
            "currentInputFingerprint": current_fingerprint,
            "state": skill.get("state"),
            "error": error,
        }
    preflight["now"] = format_utc(now)
    preflight["skills"] = skills
    return preflight


def validate_evidence(value: Any, configured_sources: Mapping[str, Any], location: str) -> dict[str, Any]:
    evidence = require_object(value, location)
    allowed = {"sourceId", "sourceRootUrl", "evidencePageUrl", "summary", "excerpt"}
    reject_unknown(evidence, allowed, location)
    require_keys(evidence, allowed, location)
    source_id = require_string(evidence["sourceId"], f"{location}.sourceId")
    if source_id not in configured_sources:
        raise ContractError(f"{location}.sourceId is not configured for the skill")
    source_root = normalize_source_url(evidence["sourceRootUrl"], f"{location}.sourceRootUrl", False)
    if source_root != configured_sources[source_id]["url"]:
        raise ContractError(f"{location}.sourceRootUrl does not match the configured source")
    page_url = normalize_source_url(evidence["evidencePageUrl"], f"{location}.evidencePageUrl", False)
    source = configured_sources[source_id]
    source_parts = urlsplit(source["url"])
    page_parts = urlsplit(page_url)
    if (source_parts.scheme, source_parts.netloc) != (page_parts.scheme, page_parts.netloc):
        raise ContractError(f"{location}.evidencePageUrl leaves the configured origin")
    if source["retrieval"]["strategy"] == "page" and page_url != source["url"]:
        raise ContractError(f"{location}.evidencePageUrl is not the configured page")
    if source["retrieval"]["strategy"] == "crawl":
        retrieval = source["retrieval"]
        if not path_authorized(page_parts.path, retrieval["includePaths"]):
            raise ContractError(f"{location}.evidencePageUrl is outside includePaths")
        if path_authorized(page_parts.path, retrieval["excludePaths"]):
            raise ContractError(f"{location}.evidencePageUrl matches excludePaths")
    excerpt = require_string(evidence["excerpt"], f"{location}.excerpt")
    if len(excerpt.split()) > 25:
        raise ContractError(f"{location}.excerpt exceeds 25 words")
    return {
        "sourceId": source_id,
        "sourceRootUrl": source_root,
        "evidencePageUrl": page_url,
        "summary": require_string(evidence["summary"], f"{location}.summary"),
        "excerpt": excerpt,
    }


def require_target_locator(root: Path, target: Mapping[str, Any], location: str) -> None:
    path = root / Path(*PurePosixPath(target["filePath"]).parts)
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ContractError(f"{location} could not be read from the reviewed file") from error
    locator_key = "currentText" if "currentText" in target else "anchorText"
    if target[locator_key] not in content:
        raise ContractError(
            f"{location}.{locator_key} does not match the unchanged reviewed file"
        )


def validate_research_result(
    value: Any,
    configuration: ProjectConfiguration,
    expected_skill_id: str | None = None,
    require_current_fingerprint: bool = True,
    provisional: bool = False,
) -> dict[str, Any]:
    result = require_object(value, "research result")
    allowed = {
        "schemaVersion",
        "projectIdentity",
        "skillId",
        "skillPath",
        "inputFingerprint",
        "reviewedAt",
        "status",
        "sourceOutcomes",
        "findings",
        "failures",
        "validation",
    }
    reject_unknown(result, allowed, "research result")
    require_keys(result, allowed, "research result")
    if result["schemaVersion"] != SCHEMA_VERSION:
        raise ContractError("research result schemaVersion is unsupported")
    skill_id = require_string(result["skillId"], "research result.skillId")
    if expected_skill_id is not None and skill_id != expected_skill_id:
        raise ContractError("research result skillId does not match the requested skill")
    if skill_id not in configuration.manifest["skills"]:
        raise ContractError(f"research result identifies unknown skill {skill_id}")
    skill = configuration.manifest["skills"][skill_id]
    expected_project_identity = project_identity(configuration.root)
    provided_project_identity = require_string(
        result["projectIdentity"], "research result.projectIdentity"
    )
    if provided_project_identity != expected_project_identity:
        raise ContractError("research result projectIdentity does not match this project")
    skill_path = normalize_relative_path(
        result["skillPath"], configuration.root, "research result.skillPath"
    )
    if skill_path != skill["path"]:
        raise ContractError("research result skillPath does not match configuration")
    input_fingerprint = require_string(
        result["inputFingerprint"], "research result.inputFingerprint"
    )
    if not FINGERPRINT_PATTERN.fullmatch(input_fingerprint):
        raise ContractError("research result.inputFingerprint is invalid")
    if require_current_fingerprint:
        current_fingerprint, _ = skill_fingerprint(configuration, skill_id)
        if input_fingerprint != current_fingerprint:
            raise ContractError(
                "research result.inputFingerprint does not match the current reviewed files and configuration"
            )
    parse_utc(result["reviewedAt"], "research result.reviewedAt")
    status = result["status"]
    if status not in {"completed", "incomplete"}:
        raise ContractError("research result.status is invalid")
    outcomes_raw = result["sourceOutcomes"]
    if not isinstance(outcomes_raw, list):
        raise ContractError("research result.sourceOutcomes must be an array")
    outcomes: list[dict[str, Any]] = []
    outcome_ids: set[str] = set()
    for index, raw in enumerate(outcomes_raw):
        location = f"research result.sourceOutcomes[{index}]"
        outcome = require_object(raw, location)
        allowed_outcome = {
            "sourceId",
            "rootUrl",
            "status",
            "successfulPages",
            "attemptedPages",
            "limitReached",
            "failureStage",
            "failureReason",
        }
        reject_unknown(outcome, allowed_outcome, location)
        require_keys(
            outcome,
            {"sourceId", "rootUrl", "status", "successfulPages", "attemptedPages", "limitReached"},
            location,
        )
        source_id = require_string(outcome["sourceId"], f"{location}.sourceId")
        if source_id not in skill["sources"] or source_id in outcome_ids:
            raise ContractError(f"{location}.sourceId is missing, unknown, or duplicated")
        outcome_ids.add(source_id)
        root_url = normalize_source_url(outcome["rootUrl"], f"{location}.rootUrl", False)
        if root_url != skill["sources"][source_id]["url"]:
            raise ContractError(f"{location}.rootUrl does not match configuration")
        outcome_status = outcome["status"]
        if outcome_status not in {"retrieved", "missing", "failed"}:
            raise ContractError(f"{location}.status is invalid")
        successful = outcome["successfulPages"]
        attempted = outcome["attemptedPages"]
        if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in (successful, attempted)):
            raise ContractError(f"{location} page counts must be nonnegative integers")
        if attempted < 1:
            raise ContractError(f"{location}.attemptedPages must be at least one")
        if successful > attempted:
            raise ContractError(f"{location}.successfulPages cannot exceed attemptedPages")
        if not isinstance(outcome["limitReached"], bool):
            raise ContractError(f"{location}.limitReached must be boolean")
        configured_retrieval = skill["sources"][source_id]["retrieval"]
        attempt_limit = (
            1
            if configured_retrieval["strategy"] == "page"
            else configured_retrieval["maxPages"]
        )
        if attempted > attempt_limit:
            raise ContractError(f"{location}.attemptedPages exceeds the configured boundary")
        if configured_retrieval["strategy"] == "page" and outcome["limitReached"]:
            raise ContractError(f"{location}.limitReached cannot be true for page retrieval")
        has_failure_details = "failureStage" in outcome or "failureReason" in outcome
        if outcome_status == "failed":
            require_keys(outcome, {"failureStage", "failureReason"}, location)
        elif has_failure_details:
            raise ContractError(f"{location} may include failure details only when status is failed")
        if outcome_status == "retrieved" and successful < 1:
            raise ContractError(f"{location}.successfulPages must be positive when retrieved")
        if outcome_status == "missing" and successful != 0:
            raise ContractError(f"{location}.successfulPages must be zero when missing")
        normalized_outcome = {
            "sourceId": source_id,
            "rootUrl": root_url,
            "status": outcome_status,
            "successfulPages": successful,
            "attemptedPages": attempted,
            "limitReached": outcome["limitReached"],
        }
        for field in ("failureStage", "failureReason"):
            if field in outcome:
                normalized_outcome[field] = require_string(outcome[field], f"{location}.{field}")
        outcomes.append(normalized_outcome)
    if outcome_ids != set(skill["sources"]):
        missing = sorted(set(skill["sources"]) - outcome_ids)
        raise ContractError(f"research result is missing source outcomes: {', '.join(missing)}")
    findings_raw = result["findings"]
    if not isinstance(findings_raw, list):
        raise ContractError("research result.findings must be an array")
    findings: list[dict[str, Any]] = []
    functional_file_paths = {path for path, _ in functional_files(configuration.root, skill["path"])}
    for index, raw in enumerate(findings_raw):
        location = f"research result.findings[{index}]"
        finding = require_object(raw, location)
        reject_unknown(finding, {"details", "evidence", "editDisposition"}, location)
        require_keys(finding, {"details", "evidence", "editDisposition"}, location)
        details = validate_details(finding["details"], configuration.root, f"{location}.details")
        if set(details["sources"]) - set(skill["sources"]):
            raise ContractError(f"{location}.details cites sources not configured for the skill")
        for source_id, source in details["sources"].items():
            if source != skill["sources"][source_id]:
                raise ContractError(f"{location}.details source snapshot differs from configuration")
        if details["target"]["filePath"] not in functional_file_paths:
            raise ContractError(f"{location}.details target is outside the skill's functional files")
        if provisional:
            require_target_locator(
                configuration.root,
                details["target"],
                f"{location}.details.target",
            )
        evidence_raw = finding["evidence"]
        if not isinstance(evidence_raw, list) or not evidence_raw:
            raise ContractError(f"{location}.evidence must be a nonempty array")
        evidence = [
            validate_evidence(item, details["sources"], f"{location}.evidence[{evidence_index}]")
            for evidence_index, item in enumerate(evidence_raw)
        ]
        represented_sources = {item["sourceId"] for item in evidence}
        if represented_sources != set(details["sources"]):
            missing_evidence = sorted(set(details["sources"]) - represented_sources)
            raise ContractError(
                f"{location}.evidence does not represent cited source(s): {', '.join(missing_evidence)}"
            )
        disposition = finding["editDisposition"]
        allowed_dispositions = {
            "applied",
            "proposed",
            "revertedAfterValidationFailure",
            "notApplicable",
        }
        if disposition not in allowed_dispositions:
            raise ContractError(f"{location}.editDisposition is invalid")
        if details["category"] == "humanDecision" and disposition in {
            "applied",
            "revertedAfterValidationFailure",
        }:
            raise ContractError(f"{location} applies an edit to a human-decision finding")
        if (
            configuration.manifest["delivery"]["strategy"] == "localReport"
            and configuration.manifest["correctionStrategy"] == "reportOnly"
            and disposition == "applied"
        ):
            raise ContractError(f"{location} applies an edit while correctionStrategy is reportOnly")
        if provisional and details["category"] in {
            "correction",
            "improvementSuggestion",
        } and disposition != "proposed":
            raise ContractError(
                f"{location} must keep a provisional change proposed before mutation"
            )
        findings.append({"details": details, "evidence": evidence, "editDisposition": disposition})
    failures_raw = result["failures"]
    if not isinstance(failures_raw, list):
        raise ContractError("research result.failures must be an array")
    failures: list[dict[str, str]] = []
    for index, raw in enumerate(failures_raw):
        failure = require_object(raw, f"research result.failures[{index}]")
        reject_unknown(failure, {"stage", "reason"}, f"research result.failures[{index}]")
        require_keys(failure, {"stage", "reason"}, f"research result.failures[{index}]")
        failures.append(
            {
                "stage": require_string(failure["stage"], "failure.stage"),
                "reason": require_string(failure["reason"], "failure.reason"),
            }
        )
    validation = require_object(result["validation"], "research result.validation")
    reject_unknown(validation, {"status", "checks"}, "research result.validation")
    require_keys(validation, {"status", "checks"}, "research result.validation")
    validation_status = validation["status"]
    if validation_status not in {"passed", "failed", "skipped", "notApplicable"}:
        raise ContractError("research result.validation.status is invalid")
    if provisional and validation_status != "notApplicable":
        raise ContractError(
            "a provisional research result must use notApplicable validation"
        )
    if not isinstance(validation["checks"], list):
        raise ContractError("research result.validation.checks must be an array")
    normalized_checks: list[dict[str, str]] = []
    for index, raw in enumerate(validation["checks"]):
        check = require_object(raw, f"research result.validation.checks[{index}]")
        reject_unknown(check, {"name", "status", "note"}, "validation check")
        require_keys(check, {"name", "status"}, "validation check")
        if check["status"] not in {"passed", "failed", "skipped"}:
            raise ContractError("validation check.status is invalid")
        normalized_check = {
            "name": require_string(check["name"], "validation check.name"),
            "status": check["status"],
        }
        if "note" in check:
            normalized_check["note"] = require_string(check["note"], "validation check.note")
        normalized_checks.append(normalized_check)
    if validation_status != "failed" and any(
        item["status"] == "failed" for item in normalized_checks
    ):
        raise ContractError(
            "research result.validation.status must be failed when a validation check failed"
        )
    failed_outcome = any(item["status"] == "failed" for item in outcomes)
    if status == "completed" and (failed_outcome or failures or validation_status == "failed"):
        raise ContractError("a completed research result cannot contain a failed retrieval, failure, or failed validation")
    if status == "incomplete" and not (failed_outcome or failures or validation_status == "failed"):
        raise ContractError("an incomplete research result must identify a retrieval, processing, or validation failure")
    provisional_changes = [
        item
        for item in findings
        if item["details"]["category"] in {"correction", "improvementSuggestion"}
    ]
    if provisional and provisional_changes and (
        failed_outcome or failures or status == "incomplete"
    ):
        raise ContractError(
            "provisional changes require every configured source and processing stage to succeed"
        )
    applied_findings = [item for item in findings if item["editDisposition"] == "applied"]
    reverted_findings = [
        item for item in findings if item["editDisposition"] == "revertedAfterValidationFailure"
    ]
    if applied_findings:
        if failed_outcome or failures or status == "incomplete":
            raise ContractError(
                "applied changes require every configured source and processing stage to succeed"
            )
        expected_validation = (
            "passed"
            if configuration.manifest["changeValidation"] == "enabled"
            else "skipped"
        )
        if validation_status != expected_validation:
            raise ContractError(
                f"applied changes require validation status {expected_validation}"
            )
    if reverted_findings and validation_status != "failed":
        raise ContractError("reverted changes require failed validation")
    normalized_result = {
        "schemaVersion": SCHEMA_VERSION,
        "projectIdentity": provided_project_identity,
        "skillId": skill_id,
        "skillPath": skill_path,
        "inputFingerprint": input_fingerprint,
        "reviewedAt": result["reviewedAt"],
        "status": status,
        "sourceOutcomes": outcomes,
        "findings": findings,
        "failures": failures,
        "validation": {"status": validation_status, "checks": normalized_checks},
    }
    validate_against_model(
        normalized_result,
        research_result_schema(),
        "research result",
    )
    return normalized_result


def render_finding(finding: Mapping[str, Any]) -> list[str]:
    details = finding["details"]
    target = details["target"]
    locator = target.get("currentText", target.get("anchorText", ""))
    lines = [
        f"- **{details['summary']}**",
        f"  - Skill: `{finding.get('skillId', '')}`",
        f"  - File: `{target['filePath']}`",
        f"  - Locator: `{locator}`",
        f"  - Proposed action: {details['proposedAction']}",
    ]
    for evidence in finding.get("evidence", []):
        lines.extend(
            [
                f"  - Source `{evidence['sourceId']}`: {evidence['sourceRootUrl']}",
                f"  - Evidence page: {evidence['evidencePageUrl']}",
                f"  - Evidence: “{evidence['excerpt']}” — {evidence['summary']}",
            ]
        )
    disposition = finding.get("editDisposition")
    if disposition and disposition != "notApplicable":
        lines.append(f"  - Disposition: `{disposition}`")
    if finding.get("stale"):
        lines.append(
            "  - Currentness: Based on an earlier configuration or skill revision; a new review is due."
        )
    return lines


def report_state_fingerprint(payload: Mapping[str, Any]) -> str:
    serialized = canonical_json(payload)
    return "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def encoded_report_payload(payload: Mapping[str, Any]) -> str:
    encoded = base64.urlsafe_b64encode(canonical_json(payload).encode("utf-8"))
    return encoded.decode("ascii").rstrip("=")


def decoded_report_payload(encoded: str) -> tuple[dict[str, Any], str]:
    padding = "=" * (-len(encoded) % 4)
    try:
        raw = base64.urlsafe_b64decode(encoded + padding)
        value = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError("existing report contains an unreadable result payload") from error
    payload = require_object(value, "report payload")
    encoded_fingerprint = report_state_fingerprint(payload)
    reject_unknown(payload, {"version", "projectIdentity", "skills"}, "report payload")
    require_keys(payload, {"version", "projectIdentity", "skills"}, "report payload")
    if payload["version"] != REPORT_VERSION:
        raise ContractError("existing report payload version is unsupported")
    require_string(payload["projectIdentity"], "report payload.projectIdentity")
    skills = require_object(payload["skills"], "report payload.skills")
    for skill_id, raw_envelope in skills.items():
        if not ID_PATTERN.fullmatch(skill_id):
            raise ContractError("existing report payload contains an invalid skill ID")
        envelope = require_object(raw_envelope, f"report payload.skills.{skill_id}")
        reject_unknown(
            envelope,
            {"inputFingerprint", "result"},
            f"report payload.skills.{skill_id}",
        )
        require_keys(
            envelope,
            {"inputFingerprint", "result"},
            f"report payload.skills.{skill_id}",
        )
        if not FINGERPRINT_PATTERN.fullmatch(
            require_string(envelope["inputFingerprint"], "report payload inputFingerprint")
        ):
            raise ContractError("existing report payload contains an invalid input fingerprint")
        result = require_object(envelope["result"], "report payload result")
        result_fingerprint = result.get("inputFingerprint")
        if result_fingerprint is None:
            result = {**result, "inputFingerprint": envelope["inputFingerprint"]}
            envelope["result"] = result
        elif result_fingerprint != envelope["inputFingerprint"]:
            raise ContractError(
                "existing report result fingerprint differs from its envelope"
            )
        if result.get("skillId") != skill_id:
            raise ContractError("existing report payload skill identity is inconsistent")
        if result.get("projectIdentity") != payload["projectIdentity"]:
            raise ContractError("existing report payload project identity is inconsistent")
        validate_against_model(
            result,
            research_result_schema(),
            f"report payload.skills.{skill_id}.result",
        )
    return payload, encoded_fingerprint


def existing_report_payload(existing: str, project: str) -> dict[str, Any]:
    if not existing or "keeping-skills-current:" not in existing:
        return {"version": REPORT_VERSION, "projectIdentity": project, "skills": {}}
    regions = list(REPORT_PATTERN.finditer(existing))
    fingerprints = REPORT_FINGERPRINT_PATTERN.findall(existing)
    payloads = REPORT_PAYLOAD_PATTERN.findall(existing)
    if len(regions) != 1 or len(fingerprints) != 1 or len(payloads) != 1:
        raise ContractError("existing report has missing, duplicated, or malformed ownership markers")
    payload, encoded_fingerprint = decoded_report_payload(payloads[0])
    if payload["projectIdentity"] != project:
        raise ContractError("existing report belongs to another project")
    if fingerprints[0] != encoded_fingerprint:
        raise ContractError("existing report payload does not match its ownership fingerprint")
    return payload


def build_report_payload(
    configuration: ProjectConfiguration,
    current_results: Sequence[Mapping[str, Any]],
    existing: str,
) -> dict[str, Any]:
    project = project_identity(configuration.root)
    payload = existing_report_payload(existing, project)
    retained = {
        skill_id: envelope
        for skill_id, envelope in payload["skills"].items()
        if skill_id in configuration.manifest["skills"]
    }
    for result in current_results:
        retained[result["skillId"]] = {
            "inputFingerprint": result["inputFingerprint"],
            "result": result,
        }
    return {
        "version": REPORT_VERSION,
        "projectIdentity": project,
        "skills": {skill_id: retained[skill_id] for skill_id in sorted(retained)},
    }


def decision_key(details: Mapping[str, Any]) -> str:
    return canonical_json(
        {
            "category": details["category"],
            "target": details["target"],
            "sources": details["sources"],
            "proposedAction": details["proposedAction"],
        }
    )


def configured_decisions(
    configuration: ProjectConfiguration,
    now: datetime_module.datetime,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for skill_id, skill in configuration.manifest["skills"].items():
        for key, kind in (("deferredFindings", "deferred"), ("declinedFindings", "declined")):
            for decision in skill[key]:
                suppressing = kind == "declined" or parse_utc(
                    decision["revisitAfter"], "revisitAfter"
                ) > now
                output.append(
                    {
                        "skillId": skill_id,
                        "kind": kind,
                        "suppressing": suppressing,
                        **decision,
                    }
                )
    return output


def render_report(
    configuration: ProjectConfiguration,
    result: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str:
    project = result["projectIdentity"]
    reviewed_at = result.get("reviewedAt", "")
    current_results = report_skill_results(result)
    reviewed_ids = {item["skillId"] for item in current_results}
    reviewed_skills = ", ".join(f"`{skill_id}`" for skill_id in sorted(reviewed_ids))
    draft_ids = {
        skill_id
        for skill_id, skill in configuration.manifest["skills"].items()
        if not skill["sources"]
    }
    skipped_drafts = ", ".join(
        f"`{skill_id}` (no configured sources)" for skill_id in sorted(draft_ids)
    )
    review_state_fingerprint = report_state_fingerprint(payload)
    payload_marker = encoded_report_payload(payload)
    lines = [
        f'<!-- keeping-skills-current:start project="{project}" reportVersion="{REPORT_VERSION}" reviewStateFingerprint="{review_state_fingerprint}" -->',
        "# Keeping Skills Current",
        "",
        f"Configured-source review {'completed' if all(item['status'] == 'completed' for item in current_results) else 'incomplete'}.",
        "",
        f"- Review time: `{reviewed_at}`",
        f"- Reviewed skills: {reviewed_skills}",
    ]
    if skipped_drafts:
        lines.append(f"- Skipped drafts: {skipped_drafts}")
    lines.extend(
        [
            "",
            "| Skill | Status | Sources |",
            "|---|---|---:|",
        ]
    )
    all_findings: list[dict[str, Any]] = []
    all_failures: list[dict[str, Any]] = []
    for skill_id in sorted(set(payload["skills"]) | draft_ids):
        if skill_id in draft_ids:
            lines.append(
                f"| `{skill_id}` | Draft — skipped (no configured sources) | 0 |"
            )
            continue
        envelope = payload["skills"][skill_id]
        item = envelope["result"]
        current_fingerprint, _ = skill_fingerprint(configuration, item["skillId"])
        stale = envelope["inputFingerprint"] != current_fingerprint
        if item["skillId"] in reviewed_ids and stale:
            raise ContractError(
                "review inputs changed before report publication for "
                f"{item['skillId']}"
            )
        if item["skillId"] in reviewed_ids:
            display_status = f"{item['status']} — reviewed this run"
        elif stale:
            display_status = f"{item['status']} — retained; new review due"
        else:
            display_status = f"{item['status']} — retained from {item['reviewedAt']}"
        lines.append(f"| `{item['skillId']}` | {display_status} | {len(item['sourceOutcomes'])} |")
        for source in item["sourceOutcomes"]:
            lines.append(
                f"| ↳ `{source['sourceId']}` | {source['status']} | {source['successfulPages']}/{source['attemptedPages']} pages |"
            )
        for finding in item["findings"]:
            enriched = dict(finding)
            enriched["skillId"] = item["skillId"]
            enriched["stale"] = stale
            all_findings.append(enriched)
        for failure in item["failures"]:
            all_failures.append({"skillId": item["skillId"], **failure})
    now = parse_utc(reviewed_at, "report input.reviewedAt")
    decisions = configured_decisions(configuration, now)
    suppressing_keys = {
        (decision["skillId"], decision_key(decision["details"]))
        for decision in decisions
        if decision["suppressing"]
    }
    active_findings = [
        finding
        for finding in all_findings
        if (finding["skillId"], decision_key(finding["details"])) not in suppressing_keys
    ]
    if not active_findings and not all_failures and not decisions:
        lines.extend(["", "No findings."])
    else:
        categories = [
            ("correction", "## 🛠 Corrections"),
            ("improvementSuggestion", "## 💡 Improvement Suggestions"),
            ("humanDecision", "## 🚩 Human Decisions Needed"),
        ]
        for category, heading in categories:
            lines.extend(["", heading, ""])
            matching = [
                item for item in active_findings if item["details"]["category"] == category
            ]
            if not matching:
                lines.append("No findings.")
            for finding in matching:
                lines.extend(render_finding(finding))
        lines.extend(["", "## ⚠️ Retrieval or Processing Failures", ""])
        if not all_failures:
            lines.append("No findings.")
        for failure in all_failures:
            lines.append(f"- `{failure['skillId']}` — **{failure['stage']}**: {failure['reason']}")
        if decisions:
            lines.extend(["", "## 🗃️ Deferred and Declined Findings", ""])
            for decision in decisions:
                state = "active" if decision["suppressing"] else "inactive — revisit date passed"
                lines.append(
                    f"- `{decision['skillId']}` — **{decision['kind']} ({state})**: "
                    f"{decision['details']['summary']} — {decision['reason']}"
                )
    lines.extend(
        [
            "",
            f"<!-- keeping-skills-current:payload {payload_marker} -->",
            "<!-- keeping-skills-current:end -->",
            "",
        ]
    )
    return "\n".join(lines)


REPORT_PATTERN = re.compile(
    r"<!-- keeping-skills-current:start\b[^>]*-->.*?<!-- keeping-skills-current:end -->",
    re.DOTALL,
)
REPORT_FINGERPRINT_PATTERN = re.compile(
    r'<!-- keeping-skills-current:start\b[^>]*\breviewStateFingerprint="(sha256:[0-9a-f]{64})"[^>]*-->'
)
REPORT_PAYLOAD_PATTERN = re.compile(
    r"<!-- keeping-skills-current:payload ([A-Za-z0-9_-]+) -->"
)


def merge_report(existing: str, owned_region: str) -> str:
    matches = list(REPORT_PATTERN.finditer(existing))
    if not matches:
        if "keeping-skills-current:" in existing:
            raise ContractError("existing report has malformed ownership markers")
        return existing.rstrip() + ("\n\n" if existing.strip() else "") + owned_region
    if len(matches) != 1:
        raise ContractError("existing report must contain exactly one owned region")
    match = matches[0]
    return existing[: match.start()] + owned_region.rstrip() + existing[match.end() :]


def legacy_sources(skill_file: Path) -> dict[str, Any]:
    if not skill_file.is_file():
        return {}
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^## Primary Sources\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
    if not match:
        return {}
    sources: dict[str, Any] = {}
    markdown_links = re.findall(r"\[([^\]]+)\]\((https://[^)\s]+)\)", match.group(1))
    for title, raw_url in markdown_links:
        parsed = urlsplit(raw_url)
        url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))
        base_id = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "source"
        source_id = base_id
        if source_id in sources:
            duplicate_index = 2
            while f"{base_id}-{duplicate_index}" in sources:
                duplicate_index += 1
            source_id = f"{base_id}-{duplicate_index}"
        title_lower = title.lower()
        documentation_root = (
            parsed.path.endswith("/")
            and parsed.hostname not in {"github.com", "registry.npmjs.org"}
            and any(
                token in title_lower
                for token in ("documentation", "docs", "manual", "help", "reference", "hub")
            )
        )
        if documentation_root:
            retrieval = {
                "strategy": "crawl",
                "includePaths": [parsed.path or "/"],
                "excludePaths": [],
                "maxDepth": 2,
                "maxPages": 25,
            }
        else:
            retrieval = {"strategy": "page"}
        sources[source_id] = {"url": url, "retrieval": retrieval}
    return sources


def migrate_legacy(root: Path, legacy_path: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    relative = normalize_relative_path(legacy_path, root, "--legacy-manifest", ".json")
    path = root / relative
    raw = require_object(json.loads(path.read_text(encoding="utf-8")), "legacy manifest")
    tiers = {key: raw.get(key, []) for key in ("weekly", "monthly", "never")}
    for key, value in tiers.items():
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ContractError(f"legacy {key} must be an array of strings")
    skills: dict[str, Any] = {}
    for recurrence, interval in (("weekly", 7), ("monthly", 28)):
        for unit_id in tiers[recurrence]:
            if "/" not in unit_id:
                raise ContractError(f"invalid legacy unit ID: {unit_id}")
            plugin, skill_name = unit_id.split("/", 1)
            skill_path = f"plugins/{plugin}/skills/{skill_name}"
            sources = legacy_sources(root / skill_path / "SKILL.md")
            schedule = (
                {"recurrence": "interval", "intervalDays": interval}
                if sources
                else {"recurrence": "manual"}
            )
            skill_id = skill_name
            if skill_id in skills:
                skill_id = unit_id.replace("/", "-")
            skills[skill_id] = {
                "path": skill_path,
                "schedule": schedule,
                "sources": sources,
                "deferredFindings": [],
                "declinedFindings": [],
            }
    proposal = {
        "schemaVersion": SCHEMA_VERSION,
        "scheduler": "none",
        "delivery": {
            "strategy": "localReport",
            "reportPath": ".keeping-skills-current/report.md",
        },
        "correctionStrategy": "reportOnly",
        "changeValidation": "enabled",
        "skills": skills,
    }
    acknowledgments = raw.get("acknowledged", [])
    if not isinstance(acknowledgments, list):
        raise ContractError("legacy acknowledged must be an array")
    return validate_manifest(proposal, root), acknowledgments


PRIMARY_SOURCES_SECTION_PATTERN = re.compile(
    r"\n+## Primary Sources\s*\n[\s\S]*\Z",
    re.MULTILINE,
)
STANDALONE_VERIFIED_PATTERN = re.compile(
    r"^\*\*Verified:\*\*\s+\d{4}-\d{2}-\d{2}\s*\n+",
    re.MULTILINE,
)


def cleanup_legacy_markers(configuration: ProjectConfiguration, write_changes: bool) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for skill_id, skill in configuration.manifest["skills"].items():
        path = configuration.root / Path(*PurePosixPath(skill["path"]).parts) / "SKILL.md"
        if path.is_symlink() or not path.is_file():
            raise ContractError(f"cannot clean missing managed skill: {skill['path']}")
        original = path.read_text(encoding="utf-8")
        primary_count = len(PRIMARY_SOURCES_SECTION_PATTERN.findall(original))
        verified_count = len(STANDALONE_VERIFIED_PATTERN.findall(original))
        updated = PRIMARY_SOURCES_SECTION_PATTERN.sub("\n", original)
        updated = STANDALONE_VERIFIED_PATTERN.sub("", updated)
        updated = updated.rstrip() + "\n"
        if updated == original:
            continue
        changes.append(
            {
                "skillId": skill_id,
                "path": path.relative_to(configuration.root).as_posix(),
                "primarySourcesSectionsRemoved": primary_count,
                "verifiedMarkersRemoved": verified_count,
            }
        )
        if write_changes:
            atomic_write(path, updated)
    return changes


def write_json_output(value: Any) -> None:
    sys.stdout.write(pretty_json(value))


def load_json_file(path: str, location: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"could not read {location}: {error}") from error


def normalize_report_input(
    raw: Any,
    configuration: ProjectConfiguration,
    current_fingerprint_skill_ids: set[str] | None = None,
    provisional: bool = False,
) -> dict[str, Any]:
    report = require_object(raw, "report input")
    if "skillResults" not in report:
        skill_id = report.get("skillId")
        require_current_fingerprint = (
            current_fingerprint_skill_ids is None
            or (
                isinstance(skill_id, str)
                and skill_id in current_fingerprint_skill_ids
            )
        )
        return validate_research_result(
            report,
            configuration,
            require_current_fingerprint=require_current_fingerprint,
            provisional=provisional,
        )
    allowed = {"projectIdentity", "reviewedAt", "skillResults"}
    reject_unknown(report, allowed, "report input")
    require_keys(report, {"projectIdentity", "reviewedAt", "skillResults"}, "report input")
    project = require_string(report["projectIdentity"], "report input.projectIdentity")
    if project != project_identity(configuration.root):
        raise ContractError("report input projectIdentity does not match this project")
    parse_utc(report["reviewedAt"], "report input.reviewedAt")
    skill_results = report["skillResults"]
    if not isinstance(skill_results, list) or not skill_results:
        raise ContractError("report input.skillResults must be a nonempty array")
    normalized_results = []
    for item in skill_results:
        item_object = require_object(item, "report input skill result")
        skill_id = item_object.get("skillId")
        require_current_fingerprint = (
            current_fingerprint_skill_ids is None
            or (
                isinstance(skill_id, str)
                and skill_id in current_fingerprint_skill_ids
            )
        )
        normalized_results.append(
            validate_research_result(
                item_object,
                configuration,
                require_current_fingerprint=require_current_fingerprint,
                provisional=provisional,
            )
        )
    ids = [item["skillId"] for item in normalized_results]
    if len(ids) != len(set(ids)):
        raise ContractError("report input contains duplicate skill results")
    return {
        "projectIdentity": project,
        "reviewedAt": report["reviewedAt"],
        "skillResults": normalized_results,
    }


def report_skill_results(report_input: Mapping[str, Any]) -> list[dict[str, Any]]:
    if "skillResults" in report_input:
        return list(report_input["skillResults"])
    return [dict(report_input)]


def provisional_result_fingerprint(report_input: Mapping[str, Any]) -> str:
    """Bind final results to the immutable portion of a validated provisional result."""
    normalized_results: list[dict[str, Any]] = []
    for result in report_skill_results(report_input):
        findings = []
        for finding in result["findings"]:
            evidence = sorted(
                finding["evidence"],
                key=canonical_json,
            )
            findings.append(
                {
                    "details": finding["details"],
                    "evidence": evidence,
                }
            )
        normalized_results.append(
            {
                "schemaVersion": result["schemaVersion"],
                "projectIdentity": result["projectIdentity"],
                "skillId": result["skillId"],
                "skillPath": result["skillPath"],
                "reviewedAt": result["reviewedAt"],
                "sourceOutcomes": sorted(
                    result["sourceOutcomes"],
                    key=lambda item: item["sourceId"],
                ),
                "findings": sorted(findings, key=canonical_json),
                "failures": sorted(result["failures"], key=canonical_json),
            }
        )
    payload = {
        "projectIdentity": report_input.get(
            "projectIdentity",
            normalized_results[0]["projectIdentity"],
        ),
        "reviewedAt": report_input.get(
            "reviewedAt",
            normalized_results[0]["reviewedAt"],
        ),
        "skillResults": sorted(normalized_results, key=lambda item: item["skillId"]),
    }
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def requires_provisional_binding(
    configuration: ProjectConfiguration,
) -> bool:
    return (
        configuration.manifest["delivery"]["strategy"] == "githubPullRequest"
        or configuration.manifest["correctionStrategy"]
        == "applyHighConfidenceCorrections"
    )


def configure_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def project_parser(name: str) -> argparse.ArgumentParser:
        command = subparsers.add_parser(name)
        command.add_argument("--project-root")
        command.add_argument("--manifest")
        return command

    preflight = project_parser("preflight")
    preflight.add_argument("--mutation", action="store_true")
    project_parser("canonicalize")
    status = project_parser("status")
    status.add_argument("--now")
    due = project_parser("due-set")
    due.add_argument("--now")
    due.add_argument("--force-failed", action="store_true")
    fingerprint = project_parser("fingerprint")
    fingerprint.add_argument("--skill-id", required=True)
    apply_state = project_parser("apply-state")
    apply_state.add_argument("--input", required=True)
    apply_state.add_argument("--delivered-report", required=True)
    apply_state.add_argument("--skill-id")
    report = project_parser("render-report")
    report.add_argument("--input", required=True)
    report.add_argument("--existing-report")
    report.add_argument("--output")
    report.add_argument("--validate-only", action="store_true")
    report.add_argument("--provisional", action="store_true")
    report.add_argument("--provisional-fingerprint")
    migration = subparsers.add_parser("migrate-legacy")
    migration.add_argument("--project-root")
    migration.add_argument("--legacy-manifest", required=True)
    migration.add_argument("--output")
    migration.add_argument("--write", action="store_true")
    cleanup = project_parser("cleanup-legacy")
    cleanup.add_argument("--write", action="store_true")
    schema = subparsers.add_parser("schema")
    schema.add_argument("--kind", choices=("manifest", "research"), required=True)
    group = schema.add_mutually_exclusive_group()
    group.add_argument("--output")
    group.add_argument("--check")
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    if sys.version_info < (3, 11):
        print("error: keeping-skills-current requires Python 3.11 or newer", file=sys.stderr)
        return 2
    parser = configure_parser()
    args = parser.parse_args(arguments)
    try:
        if args.command == "schema":
            schema_value = manifest_schema() if args.kind == "manifest" else research_result_schema()
            content = pretty_json(schema_value)
            if args.check:
                existing = Path(args.check).read_text(encoding="utf-8")
                if existing != content:
                    raise ContractError(f"generated {args.kind} schema differs from {args.check}")
                write_json_output({"checked": args.check, "kind": args.kind})
            elif args.output:
                atomic_write(Path(args.output), content)
                write_json_output({"written": args.output, "kind": args.kind})
            else:
                sys.stdout.write(content)
            return 0

        if args.command == "migrate-legacy":
            root = resolve_project_root(args.project_root)
            proposal, acknowledgments = migrate_legacy(root, args.legacy_manifest)
            payload = {"manifest": proposal, "legacyAcknowledgments": acknowledgments}
            if args.write:
                output = args.output or DEFAULT_MANIFEST_PATH
                relative = normalize_relative_path(output, root, "--output", ".json")
                atomic_write(root / relative, pretty_json(proposal, TOP_LEVEL_ORDER))
                payload["written"] = relative
            write_json_output(payload)
            return 0

        configuration = load_configuration(args.project_root, args.manifest)
        if args.command == "preflight":
            write_json_output(preflight_output(configuration, args.mutation))
        elif args.command == "canonicalize":
            atomic_write(
                configuration.manifest_path,
                pretty_json(configuration.manifest, TOP_LEVEL_ORDER),
            )
            write_json_output({"written": configuration.manifest_relative_path})
        elif args.command == "cleanup-legacy":
            changes = cleanup_legacy_markers(configuration, args.write)
            write_json_output({"write": args.write, "changes": changes})
        elif args.command == "status":
            write_json_output(status_output(configuration, current_utc(args.now)))
        elif args.command == "due-set":
            now = current_utc(args.now)
            due: list[dict[str, Any]] = []
            skipped: list[dict[str, Any]] = []
            for skill_id in configuration.manifest["skills"]:
                is_due, reason, fingerprint = due_reason(
                    configuration, skill_id, now, args.force_failed
                )
                row = {
                    "skillId": skill_id,
                    "path": configuration.manifest["skills"][skill_id]["path"],
                    "reason": reason,
                    "inputFingerprint": fingerprint,
                }
                (due if is_due else skipped).append(row)
            write_json_output({"now": format_utc(now), "due": due, "skipped": skipped})
        elif args.command == "fingerprint":
            fingerprint, files = skill_fingerprint(configuration, args.skill_id)
            write_json_output(
                {"skillId": args.skill_id, "inputFingerprint": fingerprint, "files": files}
            )
        elif args.command == "apply-state":
            current_fingerprint_skill_ids = (
                {args.skill_id} if args.skill_id is not None else None
            )
            report_input = normalize_report_input(
                load_json_file(args.input, "--input"),
                configuration,
                current_fingerprint_skill_ids,
            )
            results = report_skill_results(report_input)
            delivered = Path(args.delivered_report).read_text(encoding="utf-8")
            selected = [item for item in results if args.skill_id is None or item["skillId"] == args.skill_id]
            if not selected:
                raise ContractError("--skill-id does not identify a result in --input")
            delivered_payload = existing_report_payload(
                delivered,
                project_identity(configuration.root),
            )
            for result in selected:
                envelope = delivered_payload["skills"].get(result["skillId"])
                if envelope is None or canonical_json(envelope["result"]) != canonical_json(result):
                    raise ContractError(
                        "delivered report does not contain the validated current result for "
                        f"{result['skillId']}"
                    )
                current_fingerprint, _ = skill_fingerprint(
                    configuration,
                    result["skillId"],
                )
                if envelope["inputFingerprint"] != current_fingerprint:
                    raise ContractError(
                        "delivered report input fingerprint is stale for "
                        f"{result['skillId']}"
                    )
            updated: dict[str, Any] = {}
            for result in selected:
                skill_id = result["skillId"]
                skill = configuration.manifest["skills"][skill_id]
                attempted = parse_utc(result["reviewedAt"], "research result.reviewedAt")
                state: dict[str, Any] = {
                    "lastAttemptedReview": format_utc(attempted),
                    "lastAttemptStatus": result["status"],
                }
                old_state = skill.get("state", {})
                if result["status"] == "completed":
                    state.update(
                        {
                            "lastCompletedReview": format_utc(attempted),
                            "inputFingerprint": result["inputFingerprint"],
                        }
                    )
                else:
                    for key in ("lastCompletedReview", "inputFingerprint"):
                        if key in old_state:
                            state[key] = old_state[key]
                skill["state"] = validate_state(state, f"skills.{skill_id}.state")
                updated[skill_id] = skill["state"]
            atomic_write(
                configuration.manifest_path,
                pretty_json(configuration.manifest, TOP_LEVEL_ORDER),
            )
            write_json_output({"updated": updated})
        elif args.command == "render-report":
            if args.provisional and not args.validate_only:
                raise ContractError("--provisional requires --validate-only")
            if args.provisional and args.provisional_fingerprint:
                raise ContractError(
                    "--provisional-fingerprint cannot be used with --provisional"
                )
            report_input = normalize_report_input(
                load_json_file(args.input, "--input"),
                configuration,
                provisional=args.provisional,
            )
            binding_fingerprint = provisional_result_fingerprint(report_input)
            if not args.provisional and requires_provisional_binding(configuration):
                if args.provisional_fingerprint is None:
                    raise ContractError(
                        "a final result with edit-capable delivery requires "
                        "--provisional-fingerprint"
                    )
                if not FINGERPRINT_PATTERN.fullmatch(args.provisional_fingerprint):
                    raise ContractError("--provisional-fingerprint is invalid")
                if args.provisional_fingerprint != binding_fingerprint:
                    raise ContractError(
                        "the final result differs from the validated provisional result"
                    )
            existing = ""
            if args.existing_report:
                existing = Path(args.existing_report).read_text(encoding="utf-8")
            payload = build_report_payload(
                configuration,
                report_skill_results(report_input),
                existing,
            )
            owned = render_report(configuration, report_input, payload)
            if args.validate_only:
                response = {"valid": True}
                if args.provisional:
                    response["provisionalFingerprint"] = binding_fingerprint
                write_json_output(response)
                return 0
            rendered = merge_report(existing, owned)
            if args.output:
                atomic_write(Path(args.output), rendered)
                write_json_output({"written": args.output})
            else:
                sys.stdout.write(rendered)
        else:
            parser.error(f"unsupported command: {args.command}")
        return 0
    except (ContractError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

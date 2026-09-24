from __future__ import annotations

import argparse
import csv
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from nutev.audit_guardrails import sha256_file
from nutev.reference_identity import canonical_identity


SCHEMA_VERSION = "nutev.jev-human-comparison.v1"
DOCUMENT_TYPES = {
    "randomized_trial",
    "cohort",
    "cross_sectional",
    "case_control",
    "systematic_review",
    "meta_analysis",
    "guideline",
    "narrative_review",
    "commentary",
    "other",
}
TEMPLATE_FIELDS = [
    "reference_key_sha256",
    "reference_title",
    "nutev_reference_rank",
    "nutev_reference_score",
    "nutev_reference_tier",
    "jev_document_type",
    "jev_document_type_confidence",
    "jev_nutrition_relevance_score",
    "human_document_type",
    "human_nutrition_relevance",
    "reviewer_code",
    "reviewed_at",
    "notes",
]


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _atomic_text(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return sha256_file(path)


def _write_json(path: Path, payload: Any) -> str:
    return _atomic_text(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise RuntimeError(f"Non-object JSONL at {path}:{line_number}")
            rows.append(value)
    return rows


def _reference_key(row: dict[str, Any]) -> str:
    return sha256(canonical_identity(row).encode("utf-8")).hexdigest()


def _number(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _bounded_relevance(value: Any) -> float | None:
    parsed = _number(value)
    if parsed is None or parsed < 0 or parsed > 4:
        return None
    return parsed


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return None
    return numerator / (dx * dy)


def _ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(indexed):
        end = start + 1
        while end < len(indexed) and indexed[end][1] == indexed[start][1]:
            end += 1
        average_rank = (start + 1 + end) / 2
        for position in range(start, end):
            ranks[indexed[position][0]] = average_rank
        start = end
    return ranks


def _spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    return _pearson(_ranks(xs), _ranks(ys))


def _macro_f1(pairs: list[tuple[str, str]]) -> tuple[float | None, dict[str, dict[str, float | int]]]:
    if not pairs:
        return None, {}
    labels = sorted({label for pair in pairs for label in pair})
    by_class: dict[str, dict[str, float | int]] = {}
    f1_values: list[float] = []
    for label in labels:
        tp = sum(1 for truth, pred in pairs if truth == label and pred == label)
        fp = sum(1 for truth, pred in pairs if truth != label and pred == label)
        fn = sum(1 for truth, pred in pairs if truth == label and pred != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        f1_values.append(f1)
        by_class[label] = {
            "support": sum(1 for truth, _ in pairs if truth == label),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }
    return sum(f1_values) / len(f1_values), by_class


def _ece(confidences: list[float], correct: list[int], bins: int = 5) -> float | None:
    if not confidences or len(confidences) != len(correct):
        return None
    total = len(confidences)
    ece = 0.0
    for index in range(bins):
        low = index / bins
        high = (index + 1) / bins
        selected = [
            (confidence, outcome)
            for confidence, outcome in zip(confidences, correct, strict=True)
            if (low <= confidence < high) or (index == bins - 1 and confidence == 1)
        ]
        if not selected:
            continue
        avg_conf = sum(item[0] for item in selected) / len(selected)
        avg_acc = sum(item[1] for item in selected) / len(selected)
        ece += (len(selected) / total) * abs(avg_conf - avg_acc)
    return ece


def _index_ranking(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {_reference_key(row): row for row in rows}


def _index_shadow(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("reference_key_sha256")): row
        for row in rows
        if str(row.get("reference_key_sha256") or "")
    }


def prepare_template(
    ranking_path: Path,
    shadow_path: Path,
    output_path: Path,
    *,
    limit: int | None = None,
) -> dict[str, Any]:
    ranking_sha_before = sha256_file(ranking_path)
    shadow_sha_before = sha256_file(shadow_path)
    ranking = _index_ranking(_read_jsonl(ranking_path))
    shadow_rows = _read_jsonl(shadow_path)
    if limit is not None:
        shadow_rows = shadow_rows[: max(1, limit)]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(f".{output_path.name}.{uuid4().hex}.tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TEMPLATE_FIELDS)
        writer.writeheader()
        for shadow in shadow_rows:
            key = str(shadow.get("reference_key_sha256") or "")
            canonical = ranking.get(key, {})
            writer.writerow({
                "reference_key_sha256": key,
                "reference_title": shadow.get("reference_title") or canonical.get("title") or "",
                "nutev_reference_rank": canonical.get("reference_rank", ""),
                "nutev_reference_score": canonical.get("reference_score", ""),
                "nutev_reference_tier": canonical.get("reference_tier", ""),
                "jev_document_type": shadow.get("document_type", ""),
                "jev_document_type_confidence": shadow.get("document_type_confidence", ""),
                "jev_nutrition_relevance_score": shadow.get("nutrition_relevance_score", ""),
                "human_document_type": "",
                "human_nutrition_relevance": "",
                "reviewer_code": "",
                "reviewed_at": "",
                "notes": "",
            })
    tmp.replace(output_path)

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "status": "HUMAN_LABEL_TEMPLATE_READY",
        "scientific_effect": "none",
        "ranking_effect": "none",
        "records": len(shadow_rows),
        "output": {"path": str(output_path), "sha256": sha256_file(output_path)},
        "inputs": {
            "ranking": {"path": str(ranking_path), "sha256": ranking_sha_before},
            "shadow": {"path": str(shadow_path), "sha256": shadow_sha_before},
        },
        "assertions": {
            "canonical_ranking_not_modified": sha256_file(ranking_path) == ranking_sha_before,
            "semantic_shadow_not_modified": sha256_file(shadow_path) == shadow_sha_before,
            "template_contains_no_scientific_decision": True,
        },
    }


def _read_human_labels(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def analyze(
    ranking_path: Path,
    shadow_path: Path,
    human_labels_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    ranking_sha_before = sha256_file(ranking_path)
    shadow_sha_before = sha256_file(shadow_path)
    human_sha = sha256_file(human_labels_path)

    ranking = _index_ranking(_read_jsonl(ranking_path))
    shadow = _index_shadow(_read_jsonl(shadow_path))
    labels = _read_human_labels(human_labels_path)

    joined: list[dict[str, Any]] = []
    invalid_rows: list[dict[str, Any]] = []
    for index, label in enumerate(labels, start=2):
        key = str(label.get("reference_key_sha256") or "").strip()
        if not key or key not in ranking or key not in shadow:
            invalid_rows.append({"line": index, "reason": "reference_not_joinable", "reference_key_sha256": key})
            continue

        human_type = str(label.get("human_document_type") or "").strip()
        if human_type and human_type not in DOCUMENT_TYPES:
            invalid_rows.append({"line": index, "reason": "invalid_human_document_type", "value": human_type})
            human_type = ""

        human_relevance_raw = str(label.get("human_nutrition_relevance") or "").strip()
        human_relevance = _bounded_relevance(human_relevance_raw) if human_relevance_raw else None
        if human_relevance_raw and human_relevance is None:
            invalid_rows.append({"line": index, "reason": "invalid_human_nutrition_relevance", "value": human_relevance_raw})

        if not human_type and human_relevance is None:
            continue

        joined.append({
            "key": key,
            "human_document_type": human_type or None,
            "human_nutrition_relevance": human_relevance,
            "ranking": ranking[key],
            "shadow": shadow[key],
        })

    type_pairs: list[tuple[str, str]] = []
    confidences: list[float] = []
    correct: list[int] = []
    for row in joined:
        truth = row["human_document_type"]
        pred = str(row["shadow"].get("document_type") or "")
        if truth and pred in DOCUMENT_TYPES:
            type_pairs.append((truth, pred))
            confidence = _number(row["shadow"].get("document_type_confidence"))
            if confidence is not None:
                confidences.append(max(0.0, min(1.0, confidence)))
                correct.append(1 if truth == pred else 0)

    exact_accuracy = (
        sum(1 for truth, pred in type_pairs if truth == pred) / len(type_pairs)
        if type_pairs
        else None
    )
    macro_f1, per_class = _macro_f1(type_pairs)
    brier = (
        sum((confidence - outcome) ** 2 for confidence, outcome in zip(confidences, correct, strict=True))
        / len(confidences)
        if confidences
        else None
    )

    relevance_rows = [
        row
        for row in joined
        if row["human_nutrition_relevance"] is not None
        and _number(row["shadow"].get("nutrition_relevance_score")) is not None
    ]
    human_relevance = [float(row["human_nutrition_relevance"]) for row in relevance_rows]
    jev_relevance = [float(row["shadow"]["nutrition_relevance_score"]) for row in relevance_rows]
    absolute_errors = [abs(human - pred) for human, pred in zip(human_relevance, jev_relevance, strict=True)]

    nutev_score_pairs = [
        (float(row["human_nutrition_relevance"]), float(row["ranking"]["reference_score"]))
        for row in joined
        if row["human_nutrition_relevance"] is not None
        and _number(row["ranking"].get("reference_score")) is not None
    ]
    nutev_rank_pairs = [
        (float(row["human_nutrition_relevance"]), -float(row["ranking"]["reference_rank"]))
        for row in joined
        if row["human_nutrition_relevance"] is not None
        and _number(row["ranking"].get("reference_rank")) is not None
    ]
    jev_nutev_pairs = [
        (float(row["shadow"]["nutrition_relevance_score"]), float(row["ranking"]["reference_score"]))
        for row in joined
        if _number(row["shadow"].get("nutrition_relevance_score")) is not None
        and _number(row["ranking"].get("reference_score")) is not None
    ]

    tier_values: dict[str, list[float]] = {}
    for row in joined:
        human = row["human_nutrition_relevance"]
        if human is None:
            continue
        tier = str(row["ranking"].get("reference_tier") or "unknown")
        tier_values.setdefault(tier, []).append(float(human))

    report = {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "status": "COMPARISON_COMPLETE" if joined else "NEEDS_HUMAN_LABELS",
        "validation_claim": "NOT_ESTABLISHED",
        "scientific_effect": "none",
        "ranking_effect": "none",
        "interpretation_contract": {
            "jev_document_type_is_compared_directly_to_human_label": True,
            "jev_relevance_is_compared_directly_to_human_label": True,
            "nutev_score_is_only_exploratory_priority_association": True,
            "no_eligibility_or_prisma_inference": True,
            "no_quality_certainty_or_recommendation_inference": True,
        },
        "sample": {
            "human_rows": len(labels),
            "joined_rows": len(joined),
            "document_type_labeled": len(type_pairs),
            "nutrition_relevance_labeled": len(relevance_rows),
            "invalid_rows": len(invalid_rows),
        },
        "jev_vs_human": {
            "document_type": {
                "exact_accuracy": _round(exact_accuracy),
                "macro_f1": _round(macro_f1),
                "brier_top_choice": _round(brier),
                "expected_calibration_error_5_bin": _round(_ece(confidences, correct)),
                "per_class": per_class,
            },
            "nutrition_relevance": {
                "mae_0_to_4": _round(_mean(absolute_errors)),
                "within_one_point": _round(
                    sum(1 for error in absolute_errors if error <= 1) / len(absolute_errors)
                    if absolute_errors
                    else None
                ),
                "spearman": _round(_spearman(human_relevance, jev_relevance)),
            },
        },
        "nutev_vs_human_exploratory": {
            "reference_score_spearman_with_human_relevance": _round(
                _spearman(
                    [pair[0] for pair in nutev_score_pairs],
                    [pair[1] for pair in nutev_score_pairs],
                )
            ),
            "priority_rank_spearman_with_human_relevance": _round(
                _spearman(
                    [pair[0] for pair in nutev_rank_pairs],
                    [pair[1] for pair in nutev_rank_pairs],
                )
            ),
            "mean_human_relevance_by_reference_tier": {
                tier: _round(_mean(values))
                for tier, values in sorted(tier_values.items())
            },
        },
        "jev_vs_nutev_exploratory": {
            "jev_relevance_vs_reference_score_spearman": _round(
                _spearman(
                    [pair[0] for pair in jev_nutev_pairs],
                    [pair[1] for pair in jev_nutev_pairs],
                )
            ),
        },
        "invalid_rows": invalid_rows,
        "inputs": {
            "ranking": {"path": str(ranking_path), "sha256": ranking_sha_before},
            "shadow": {"path": str(shadow_path), "sha256": shadow_sha_before},
            "human_labels": {"path": str(human_labels_path), "sha256": human_sha},
        },
        "assertions": {
            "canonical_ranking_not_modified": sha256_file(ranking_path) == ranking_sha_before,
            "semantic_shadow_not_modified": sha256_file(shadow_path) == shadow_sha_before,
            "no_scientific_state_written": True,
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "JEV_COMPARISON_REPORT.json"
    md_path = output_dir / "JEV_COMPARISON_REPORT.md"
    json_sha = _write_json(json_path, report)
    md_sha = _atomic_text(md_path, render_markdown(report))
    report["outputs"] = {
        "json": {"path": str(json_path), "sha256": json_sha},
        "markdown": {"path": str(md_path), "sha256": md_sha},
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    sample = report["sample"]
    doc = report["jev_vs_human"]["document_type"]
    rel = report["jev_vs_human"]["nutrition_relevance"]
    nutev = report["nutev_vs_human_exploratory"]
    lines = [
        "# Jev × Humano × NutEV — relatório de comparação",
        "",
        f"- Status técnico: **{report['status']}**",
        "- Claim de validação científica: **NOT_ESTABLISHED**",
        "- Efeito sobre ranking: **none**",
        "- Efeito sobre estado científico: **none**",
        "",
        "## Amostra",
        "",
        f"- Linhas humanas recebidas: {sample['human_rows']}",
        f"- Linhas juntadas: {sample['joined_rows']}",
        f"- Tipo documental rotulado: {sample['document_type_labeled']}",
        f"- Relevância nutricional rotulada: {sample['nutrition_relevance_labeled']}",
        f"- Linhas inválidas: {sample['invalid_rows']}",
        "",
        "## Jev vs humano",
        "",
        f"- Acurácia de tipo documental: {doc['exact_accuracy']}",
        f"- Macro-F1 de tipo documental: {doc['macro_f1']}",
        f"- Brier da confiança da escolha: {doc['brier_top_choice']}",
        f"- ECE (5 bins): {doc['expected_calibration_error_5_bin']}",
        f"- MAE de relevância nutricional (0–4): {rel['mae_0_to_4']}",
        f"- Dentro de ±1 ponto: {rel['within_one_point']}",
        f"- Spearman Jev vs humano (relevância): {rel['spearman']}",
        "",
        "## NutEV vs humano — associação exploratória",
        "",
        f"- Spearman reference_score vs relevância humana: {nutev['reference_score_spearman_with_human_relevance']}",
        f"- Spearman prioridade de rank vs relevância humana: {nutev['priority_rank_spearman_with_human_relevance']}",
        "",
        "O reference_score do NutEV é prioridade técnica de leitura. As correlações acima não o transformam em",
        "medida de qualidade, elegibilidade, certeza ou recomendação.",
        "",
        "## Guardrails",
        "",
        "- Este relatório não altera reference_score, rank ou tier.",
        "- Não cria inclusão/exclusão nem estado PRISMA.",
        "- Não avalia risco de viés, qualidade metodológica ou certeza.",
        "- Não gera recomendação científica ou clínica.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare human labels and compare Jev semantic shadow with human labels and NutEV priority signals."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    template = sub.add_parser("template", help="Create a human-label CSV template from ranking + Jev shadow.")
    template.add_argument("--ranking", type=Path, required=True)
    template.add_argument("--shadow", type=Path, required=True)
    template.add_argument("--output", type=Path, required=True)
    template.add_argument("--limit", type=int)

    comparison = sub.add_parser("analyze", help="Analyze human labels against Jev and NutEV.")
    comparison.add_argument("--ranking", type=Path, required=True)
    comparison.add_argument("--shadow", type=Path, required=True)
    comparison.add_argument("--human-labels", type=Path, required=True)
    comparison.add_argument("--output-dir", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "template":
        result = prepare_template(args.ranking, args.shadow, args.output, limit=args.limit)
    else:
        result = analyze(args.ranking, args.shadow, args.human_labels, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Unit tests for src/pipeline/quality_check.py

Tests each quality gate check function in isolation using temp metric files.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def write_metrics(tmp_dir: Path, filename: str, data: dict) -> None:
    (tmp_dir / filename).write_text(json.dumps(data))


class TestNERCheck:
    def test_passes_when_above_threshold(self, tmp_path):
        write_metrics(tmp_path, "ner_metrics.json", {"entity_count": 2_000_000})
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_ner
            passed, result = check_ner({"min_entity_count": 1_000_000})
        assert passed is True
        assert result["passed"] is True

    def test_fails_when_below_threshold(self, tmp_path):
        write_metrics(tmp_path, "ner_metrics.json", {"entity_count": 500_000})
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_ner
            passed, result = check_ner({"min_entity_count": 1_000_000})
        assert passed is False

    def test_missing_file_treated_as_zero(self, tmp_path):
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_ner
            passed, result = check_ner({"min_entity_count": 1_000_000})
        assert passed is False
        assert result["value"] == 0


class TestRelationCheck:
    def test_passes_when_above_threshold(self, tmp_path):
        write_metrics(tmp_path, "relation_metrics.json", {"relation_count": 1_000_000})
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_relations
            passed, _ = check_relations({"min_relation_count": 500_000})
        assert passed is True

    def test_fails_when_below_threshold(self, tmp_path):
        write_metrics(tmp_path, "relation_metrics.json", {"relation_count": 100_000})
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_relations
            passed, _ = check_relations({"min_relation_count": 500_000})
        assert passed is False


class TestGraphCheck:
    def test_passes_when_both_above_threshold(self, tmp_path):
        write_metrics(tmp_path, "graph_metrics.json", {
            "entity_nodes": 1_500_000,
            "edge_count": 1_500_000,
        })
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_graph
            passed, _ = check_graph({"min_graph_entity_nodes": 500_000, "min_graph_edge_count": 500_000})
        assert passed is True

    def test_fails_when_nodes_below_threshold(self, tmp_path):
        write_metrics(tmp_path, "graph_metrics.json", {
            "entity_nodes": 100_000,
            "edge_count": 1_500_000,
        })
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_graph
            passed, result = check_graph({"min_graph_entity_nodes": 500_000, "min_graph_edge_count": 500_000})
        assert passed is False


class TestCrossDomainRatio:
    def test_passes_above_ratio(self, tmp_path):
        write_metrics(tmp_path, "graph_metrics.json", {
            "entity_nodes": 1_000_000,
            "edge_count": 1_000_000,
            "cross_domain_edge_count": 800_000,
        })
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_cross_domain_ratio
            passed, result = check_cross_domain_ratio({"min_cross_domain_ratio": 0.50})
        assert passed is True
        assert result["ratio"] == 0.8

    def test_fails_below_ratio(self, tmp_path):
        write_metrics(tmp_path, "graph_metrics.json", {
            "entity_nodes": 1_000_000,
            "edge_count": 1_000_000,
            "cross_domain_edge_count": 100_000,
        })
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_cross_domain_ratio
            passed, _ = check_cross_domain_ratio({"min_cross_domain_ratio": 0.50})
        assert passed is False

    def test_zero_edges_fails_gracefully(self, tmp_path):
        write_metrics(tmp_path, "graph_metrics.json", {
            "entity_nodes": 0,
            "edge_count": 0,
            "cross_domain_edge_count": 0,
        })
        with patch("src.pipeline.quality_check.METRICS_DIR", tmp_path):
            from src.pipeline.quality_check import check_cross_domain_ratio
            passed, result = check_cross_domain_ratio({"min_cross_domain_ratio": 0.50})
        assert passed is False
        assert result["ratio"] == 0.0

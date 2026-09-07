"""Presentation policy + sample catalog (no FAISS / OpenAI required)."""
from __future__ import annotations

import csv
import unittest
from pathlib import Path

from backend import app_settings
from backend.apis.route_query import Clarifying, Constraint, QueryRequest, QueryResponse
from backend.core.retrieval.presentation import (
    apply_constraints,
    decide_presentation,
    distinct_typed_values,
    find_exact_code_match,
    majority_family,
    restrict_to_family,
    usable_column_diff,
)


def _match(
    code: str,
    description: str,
    score: float,
    *,
    family: str = "",
    micron: str = "",
    diameter: str = "",
    sku_key: str = "",
    size: str = "",
    location: str = "",
) -> dict:
    catalog = {
        "code": code,
        "description": description,
        "sku_key": sku_key or code,
    }
    if family:
        catalog["family"] = family
    if micron:
        catalog["micron"] = micron
    if diameter:
        catalog["diameter"] = diameter
    if size:
        catalog["size"] = size
    if location:
        catalog["location"] = location
    return {
        "code": code,
        "description": description,
        "location": location or None,
        "location_state": "present" if location else "empty",
        "score": score,
        "catalog": catalog,
    }


def _filter_grid(score: float = 0.70) -> list:
    rows = []
    n = 0
    for micron in ("5", "10", "25"):
        for diameter in ('1/2"', '1"', '1.5"'):
            n += 1
            rows.append(
                _match(
                    f"10.01.00{100 + n}",
                    f"Υδραυλικό φίλτρο {micron} micron {diameter}",
                    score - n * 0.002,
                    family="filter",
                    micron=micron,
                    diameter=diameter,
                    sku_key=f"FLT-{micron}-{n}",
                    location="A-12-01",
                )
            )
    return rows


class SampleCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(app_settings.SAMPLE_CATALOG_CSV)
        with path.open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_filter_grid_and_bearing_code(self):
        filters = [r for r in self.rows if r.get("family") == "filter"]
        self.assertGreaterEqual(len(filters), 9)
        microns = {r["micron"] for r in filters if r.get("micron")}
        self.assertEqual(microns, {"5", "10", "25"})
        diameters = {r["diameter"] for r in filters if r.get("diameter")}
        self.assertEqual(diameters, {'1/2"', '1"', '1.5"'})
        pairs = {
            (r["micron"], r["diameter"])
            for r in filters
            if r.get("micron") and r.get("diameter")
        }
        for micron in ("5", "10", "25"):
            for diameter in ('1/2"', '1"', '1.5"'):
                self.assertIn((micron, diameter), pairs)
        empty_diam = [r for r in filters if not (r.get("diameter") or "").strip()]
        self.assertGreaterEqual(len(empty_diam), 1)
        self.assertLessEqual(len(empty_diam), 2)

        sku_keys = [r["sku_key"] for r in self.rows]
        self.assertIn("6205-2RS", sku_keys)
        self.assertEqual(len(sku_keys), len(set(sku_keys)))
        bearing = next(r for r in self.rows if r["sku_key"] == "6205-2RS")
        self.assertIn("6205-2RS", bearing["description"])
        self.assertEqual(bearing.get("size"), "6205-2RS")

    def test_location_missing_rate(self):
        missing = sum(1 for r in self.rows if not (r.get("location") or "").strip())
        rate = missing / len(self.rows)
        self.assertGreaterEqual(rate, 0.30)
        self.assertLessEqual(rate, 0.40)
        self.assertGreaterEqual(len(self.rows), 30)
        self.assertLess(len(self.rows), 100)


class PresentationPolicyTests(unittest.TestCase):
    def test_exact_bearing_code_is_single(self):
        matches = [
            _match("10.09.00901", "Ράβδος γείωσης M12", 0.61, family="electrical"),
            _match(
                "10.05.00501",
                "Ρουλεμάν 6205-2RS",
                0.88,
                family="bearing",
                sku_key="6205-2RS",
                size="6205-2RS",
            ),
            _match(
                "10.05.00502",
                "Ρουλεμάν 6308-2RS",
                0.80,
                family="bearing",
                sku_key="6308-2RS",
                size="6308-2RS",
            ),
        ]
        decision = decide_presentation("6205-2RS", matches, top_k=5)
        self.assertEqual(decision["presentation"], "single")
        self.assertEqual(len(decision["matches"]), 1)
        self.assertEqual(decision["matches"][0]["catalog"]["sku_key"], "6205-2RS")
        self.assertIsNone(decision["clarifying"])
        self.assertFalse(decision["empty"])
        self.assertIsNotNone(find_exact_code_match("6205-2RS", matches))

    def test_filter_query_is_clarifying_micron_or_diameter(self):
        matches = _filter_grid()
        self.assertLess(matches[0]["score"] - matches[1]["score"], 0.12)
        decision = decide_presentation("υδραυλικο φιλτρο", matches, top_k=5)
        self.assertEqual(decision["presentation"], "clarifying")
        self.assertIsNotNone(decision["clarifying"])
        self.assertIn(decision["clarifying"]["field"], ("micron", "diameter"))
        options = decision["clarifying"]["options"]
        if decision["clarifying"]["field"] == "micron":
            self.assertEqual(set(options), {"5", "10", "25"})
        else:
            self.assertEqual(set(options), {'1/2"', '1"', '1.5"'})
        self.assertFalse(decision["empty"])
        self.assertGreaterEqual(len(decision["matches"]), 2)

    def test_same_micron_asks_diameter(self):
        matches = [
            _match("A", "φίλτρο 10 1/2", 0.71, family="filter", micron="10", diameter='1/2"'),
            _match("B", "φίλτρο 10 1", 0.705, family="filter", micron="10", diameter='1"'),
            _match("C", "φίλτρο 10 1.5", 0.70, family="filter", micron="10", diameter='1.5"'),
        ]
        clarifying = usable_column_diff(matches)
        self.assertEqual(clarifying["field"], "diameter")
        self.assertEqual(set(clarifying["options"]), {'1/2"', '1"', '1.5"'})

    def test_family_filter_excludes_bearing_from_micron_chips(self):
        matches = _filter_grid() + [
            _match(
                "10.05.00501",
                "Ρουλεμάν 6205-2RS",
                0.69,
                family="bearing",
                sku_key="6205-2RS",
                size="6205-2RS",
            )
        ]
        family = majority_family(matches)
        self.assertEqual(family, "filter")
        pool = restrict_to_family(matches, family)
        values = distinct_typed_values(pool, "micron")
        self.assertEqual(set(values), {"5", "10", "25"})
        decision = decide_presentation("υδραυλικο φιλτρο", matches, top_k=5)
        self.assertEqual(decision["presentation"], "clarifying")
        self.assertNotIn("6205-2RS", decision["clarifying"]["options"])
        self.assertNotIn("bearing", decision["clarifying"]["options"])
        self.assertTrue(all(m["catalog"].get("family") == "filter" for m in decision["matches"]))

    def test_leader_gap_is_single(self):
        matches = [
            _match("10.03.00301", "Ρακόρ 1 inch BSP", 0.82, family="fitting"),
            _match("10.03.00302", "Ρακόρ 3/4 inch BSP", 0.60, family="fitting"),
        ]
        decision = decide_presentation("rakor", matches)
        self.assertEqual(decision["presentation"], "single")
        self.assertEqual(decision["matches"][0]["code"], "10.03.00301")

    def test_no_typed_diff_is_list(self):
        matches = [
            _match("10.09.00901", "Ράβδος γείωσης M12", 0.62, family="electrical"),
            _match("10.09.00902", "Ακροδέκτης καλωδίου 16mm2", 0.60, family="electrical"),
            _match("10.12.01201", "Μπουλόνι M16x80", 0.59, family="fastener"),
        ]
        decision = decide_presentation("zzzz-not-a-code", matches)
        self.assertEqual(decision["presentation"], "list")
        self.assertIsNone(decision["clarifying"])
        self.assertEqual(len(decision["matches"]), 3)

    def test_junk_is_empty(self):
        decision = decide_presentation("zzzznotaproduct999", [])
        self.assertEqual(decision["presentation"], "empty")
        self.assertEqual(decision["matches"], [])
        self.assertTrue(decision["empty"])
        self.assertIsNone(decision["clarifying"])

    def test_constraints_narrow_to_micron_then_diameter(self):
        matches = _filter_grid()
        narrowed = apply_constraints(matches, [{"field": "micron", "value": "10"}])
        self.assertTrue(narrowed)
        self.assertTrue(all(m["catalog"]["micron"] == "10" for m in narrowed))
        self.assertLess(len(narrowed), len(matches))
        decision = decide_presentation("υδραυλικο φιλτρο", narrowed)
        self.assertEqual(decision["presentation"], "clarifying")
        self.assertEqual(decision["clarifying"]["field"], "diameter")
        self.assertEqual(set(decision["clarifying"]["options"]), {'1/2"', '1"', '1.5"'})

        both = apply_constraints(
            matches,
            [{"field": "micron", "value": "10"}, {"field": "diameter", "value": '1"'}],
        )
        self.assertEqual(len(both), 1)
        decision = decide_presentation("υδραυλικο φιλτρο", both)
        self.assertEqual(decision["presentation"], "single")

    def test_empty_diameter_rows_drop_out_of_diameter_constraint(self):
        matches = _filter_grid() + [
            _match(
                "10.01.00110",
                "Υδραυλικό φίλτρο επιστροφής 10 micron",
                0.69,
                family="filter",
                micron="10",
            )
        ]
        narrowed = apply_constraints(matches, [{"field": "diameter", "value": '1/2"'}])
        self.assertTrue(all(_match_has_diameter(m, '1/2"') for m in narrowed))
        self.assertNotIn("10.01.00110", {m["code"] for m in narrowed})


def _match_has_diameter(match: dict, expected: str) -> bool:
    return match["catalog"].get("diameter") == expected


class ContractTests(unittest.TestCase):
    def test_request_accepts_constraints(self):
        body = QueryRequest(
            query="υδραυλικο φιλτρο",
            constraints=[Constraint(field="micron", value="10")],
        )
        dumped = body.model_dump()
        self.assertEqual(dumped["constraints"], [{"field": "micron", "value": "10"}])

    def test_response_requires_presentation_and_clarifying(self):
        body = QueryResponse(
            presentation="clarifying",
            matches=[],
            clarifying=Clarifying(field="micron", label="Micron", options=["5", "10", "25"]),
            empty=False,
        )
        dumped = body.model_dump()
        self.assertEqual(dumped["presentation"], "clarifying")
        self.assertEqual(dumped["clarifying"]["options"], ["5", "10", "25"])
        self.assertFalse(dumped["empty"])


if __name__ == "__main__":
    unittest.main()

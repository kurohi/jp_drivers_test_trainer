"""
TDD tests for scraper modules.

Uses local fixtures — NEVER hits live sites in tests.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
SCRAPERS_DIR = PROJECT_ROOT / "scripts" / "scrapers"

import sys
sys.path.insert(0, str(SCRAPERS_DIR))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def lease_japan_html():
    """Sample HTML mimicking Lease Japan test page structure."""
    return """
    <html>
    <body>
        <div class="content">
            <p>Among those who have only recently obtained a regular driver's license, only drivers who lack confidence in their driving display the novice driver sign; confident drivers are not required to display it.</p>
            <p>Reason: Drivers who have held a license for less than one year must display the novice driver sign, regardless of how confident they feel about their driving.</p>
            <span>True</span>
            <span>False</span>

            <p>When a pedestrian is crossing at or near an intersection without a designated crosswalk, drivers must slow down, stop, or take other necessary precautions to avoid obstructing the pedestrian's crossing.</p>
            <p>Reason: Drivers should remain mindful of pedestrians while operating their vehicles.</p>
            <span>True</span>
            <span>False</span>

            <p>Page 1 of 10</p>

            <p>On national expressways, assuming a dry road surface and new tires, the recommended following distance at 100 km/h is approximately 100 meters.</p>
            <p>Reason: This distance between vehicles is necessary to account for the stopping distance.</p>
            <span>True</span>
            <span>False</span>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def github_tsv_content():
    """Sample TSV content from GitHub repo."""
    return """When your vehicle is in an intersection and you notice an emergency vehicle is approaching from behind, you must stop there immediately.\t\tfalse\tYou must not stop immediately. You must avoid intersection, move to the left and stop.
When passing a railroad crossing where visibility is good or where there is a gateman, you just have to slow down.\t\tfalse\tEven if visibility is good or there is a gateman, you must stop before the railroad crossing.
This side strip indicates parking or stopping is prohibited.\t\ttrue\tCorrect
When you approach a pedestrian crossing and a pedestrian is crossing on it, you slow down and pass the pedestrian crossing while paying attention not to disturb the passage of the pedestrian.\t\tfalse\tWhen a pedestrian is crossing a pedestrian crossing, you must stop before the pedestrian crossing and yield to the pedestrian.
When the surface of the roads changes, the braking distance will also change even in a same speed.\t\ttrue\tCorrect
"""


@pytest.fixture
def sample_raw_questions():
    """Load sample raw questions from fixture."""
    fixture_path = FIXTURES_DIR / "lease_japan_test1.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def github_tsv_questions():
    """Load GitHub TSV fixture questions."""
    fixture_path = FIXTURES_DIR / "github_tsv_questions.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def reddit_questions():
    """Load Reddit fixture questions."""
    fixture_path = FIXTURES_DIR / "reddit_threads.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def npa_questions():
    """Load NPA fixture questions."""
    fixture_path = FIXTURES_DIR / "npa_pdfs.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def menkyo_questions():
    """Load MenkyoHub fixture questions."""
    fixture_path = FIXTURES_DIR / "menkyo_hub.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def br_no_japao_questions():
    """Load BR no Japao fixture questions."""
    fixture_path = FIXTURES_DIR / "br_no_japao.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def dia_adia_questions():
    """Load DIA A DIA fixture questions."""
    fixture_path = FIXTURES_DIR / "dia_adia.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def lo_pal_questions():
    """Load Lo-PAL fixture questions."""
    fixture_path = FIXTURES_DIR / "lo_pal_skill.json"
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Lease Japan scraper tests
# ---------------------------------------------------------------------------

class TestLeaseJapanScraper:
    def test_parse_lease_japan_page(self, lease_japan_html):
        """Test parsing of Lease Japan HTML structure."""
        from lease_japan import _parse_lease_japan_page

        soup = BeautifulSoup(lease_japan_html, "lxml")
        questions = _parse_lease_japan_page(
            soup,
            source_url="https://leasejapan.com/en/license-conversion/written-test-guide/test-1/",
        )

        assert len(questions) >= 2
        q = questions[0]
        assert "novice driver sign" in q["prompt_en"].lower()
        assert q["source_url"] == "https://leasejapan.com/en/license-conversion/written-test-guide/test-1/"
        assert q["license"] == "rewrite-required"
        assert q["attribution"] == "Lease Japan"
        assert "theme_slug" in q

    def test_parse_skips_page_markers(self, lease_japan_html):
        """Test that page markers are not parsed as questions."""
        from lease_japan import _parse_lease_japan_page

        soup = BeautifulSoup(lease_japan_html, "lxml")
        questions = _parse_lease_japan_page(
            soup,
            source_url="https://leasejapan.com/en/license-conversion/written-test-guide/test-1/",
        )

        for q in questions:
            assert "page 1 of 10" not in q["prompt_en"].lower()

    def test_normalize_answer(self):
        """Test answer normalization."""
        from lease_japan import _normalize_answer

        assert _normalize_answer("True") == "true"
        assert _normalize_answer("FALSE") == "false"
        assert _normalize_answer("correct") == "true"

    def test_classify_theme(self):
        """Test theme classification."""
        from lease_japan import _classify_theme

        assert _classify_theme("pedestrian at crosswalk") == "pedestrian-protection"
        assert _classify_theme("following distance braking speed") == "speed-and-following-distance"
        assert _classify_theme("emergency vehicle ambulance approaching") == "emergency-vehicle-priority"

    def test_fixture_questions_have_required_fields(self, sample_raw_questions):
        """Test that fixture questions have all required fields."""
        for q in sample_raw_questions:
            assert "prompt_en" in q
            assert "answer_en" in q
            assert "explanation_en" in q
            assert "theme_slug" in q
            assert "source_url" in q
            assert "license" in q
            assert "attribution" in q
            assert q["prompt_en"]  # non-empty
            assert q["source_url"]  # non-empty
            assert q["license"]  # non-empty
            assert q["attribution"]  # non-empty


# ---------------------------------------------------------------------------
# GitHub TSV scraper tests
# ---------------------------------------------------------------------------

class TestGitHubTSVScraper:
    def test_parse_tsv_format(self, github_tsv_content):
        """Test parsing of TSV format."""
        import csv
        import io

        reader = csv.reader(io.StringIO(github_tsv_content), delimiter="\t")
        rows = list(reader)

        assert len(rows) == 5
        assert "intersection" in rows[0][0].lower()
        assert rows[0][2] == "false"
        assert "avoid intersection" in rows[0][3].lower()

    def test_skips_image_questions(self):
        """Test that image-only questions are skipped."""
        assert "img-x-03044".startswith("img-")

    def test_fixture_questions_have_required_fields(self, github_tsv_questions):
        """Test that fixture questions have all required fields."""
        for q in github_tsv_questions:
            assert q["prompt_en"]
            assert q["answer_en"] in ("true", "false")
            assert q["theme_slug"]
            assert q["source_url"]
            assert q["license"] == "open-source"
            assert q["attribution"]

    def test_classify_theme(self):
        """Test theme classification for GitHub TSV content."""
        from github_tsv import _classify_theme

        assert _classify_theme("pedestrian at crosswalk") == "pedestrian-protection"
        assert _classify_theme("expressway speed limit") == "highway-driving"
        assert _classify_theme("emergency vehicle approaching") == "emergency-vehicle-priority"


# ---------------------------------------------------------------------------
# Reddit scraper tests
# ---------------------------------------------------------------------------

class TestRedditScraper:
    def test_is_driver_test_related(self):
        """Test driver test keyword detection."""
        from reddit_threads import _is_driver_test_related

        assert _is_driver_test_related("How was your driver's license test?") is True
        assert _is_driver_test_related("外免切替 experience") is True
        assert _is_driver_test_related("Best ramen in Tokyo") is False

    def test_classify_theme(self):
        """Test theme classification for Reddit content."""
        from reddit_threads import _classify_theme

        assert _classify_theme("pedestrian at crosswalk rules") == "pedestrian-protection"
        assert _classify_theme("expressway driving tips") == "highway-driving"

    def test_fixture_questions_have_required_fields(self, reddit_questions):
        """Test that fixture questions have all required fields."""
        for q in reddit_questions:
            assert q["prompt_en"]
            assert q["theme_slug"]
            assert q["source_url"]
            assert q["license"] == "community-free"
            assert q["attribution"]


# ---------------------------------------------------------------------------
# NPA PDF scraper tests
# ---------------------------------------------------------------------------

class TestNPAPDFScraper:
    def test_parse_npa_text(self):
        """Test parsing of NPA PDF text."""
        from npa_pdfs import _parse_npa_text

        text = """
National Police Agency
Driver's License Guide

Drivers must stop at red lights. This is a fundamental rule of the road.

Pedestrians have the right of way at crosswalks.

Page 1 of 5
"""
        questions = _parse_npa_text(
            text,
            source_url="https://www.npa.go.jp/english/licence/license_e.pdf",
        )

        assert len(questions) >= 2
        for q in questions:
            assert q["license"] == "public-domain"
            assert "National Police Agency" in q["attribution"]
            assert "page 1 of 5" not in q["prompt_en"].lower()

    def test_fixture_questions_have_required_fields(self, npa_questions):
        """Test that fixture questions have all required fields."""
        for q in npa_questions:
            assert q["prompt_en"]
            assert q["theme_slug"]
            assert q["source_url"]
            assert q["license"] == "public-domain"
            assert "National Police Agency" in q["attribution"]


# ---------------------------------------------------------------------------
# JapanDL scraper tests
# ---------------------------------------------------------------------------

class TestJapanDLScraper:
    def test_classify_theme(self):
        """Test theme classification for JapanDL content."""
        from japandl import _classify_theme

        assert _classify_theme("pedestrian at crosswalk") == "pedestrian-protection"
        assert _classify_theme("expressway speed limit") == "highway-driving"


# ---------------------------------------------------------------------------
# MenkyoHub scraper tests
# ---------------------------------------------------------------------------

class TestMenkyoHubScraper:
    def test_classify_theme(self):
        """Test theme classification for MenkyoHub content."""
        from menkyo_hub import _classify_theme

        assert _classify_theme("blind spot check") == "blind-spots"
        assert _classify_theme("parking rules") == "parking-and-stopping"

    def test_fixture_questions_have_required_fields(self, menkyo_questions):
        """Test that fixture questions have all required fields."""
        for q in menkyo_questions:
            assert q["prompt_en"]
            assert q["theme_slug"]
            assert q["source_url"]
            assert q["license"] == "community-free"
            assert q["attribution"]


# ---------------------------------------------------------------------------
# BR no Japao scraper tests
# ---------------------------------------------------------------------------

class TestBRNoJapaoScraper:
    def test_classify_theme_pt(self):
        """Test PT theme classification."""
        from br_no_japao import _classify_theme_pt

        assert _classify_theme_pt("faixa de pedestre") == "pedestrian-protection"
        assert _classify_theme_pt("ultrapassagem proibida") == "overtaking-and-passing"

    def test_fixture_questions_have_required_fields(self, br_no_japao_questions):
        """Test that fixture questions have all required fields."""
        for q in br_no_japao_questions:
            assert q["prompt_en"]
            assert q["theme_slug"]
            assert q["source_url"]
            assert q["license"] == "rewrite-required"
            assert q["attribution"]


# ---------------------------------------------------------------------------
# DIA A DIA scraper tests
# ---------------------------------------------------------------------------

class TestDiaAdiaScraper:
    def test_classify_theme_pt(self):
        """Test PT theme classification."""
        from dia_adia import _classify_theme_pt

        assert _classify_theme_pt("sinal de trânsito") == "signals"
        assert _classify_theme_pt("velocidade máxima") == "speed-and-following-distance"

    def test_fixture_questions_have_required_fields(self, dia_adia_questions):
        """Test that fixture questions have all required fields."""
        for q in dia_adia_questions:
            assert q["prompt_en"]
            assert q["theme_slug"]
            assert q["source_url"]
            assert q["license"] == "rewrite-required"
            assert q["attribution"]


# ---------------------------------------------------------------------------
# Lo-PAL scraper tests
# ---------------------------------------------------------------------------

class TestLoPalScraper:
    def test_classify_theme(self):
        """Test theme classification for Lo-PAL content."""
        from lo_pal_skill import _classify_theme

        assert _classify_theme("signal timing before turn") == "signals"
        assert _classify_theme("engine oil level check tire pressure") == "vehicle-maintenance"

    def test_fixture_questions_have_required_fields(self, lo_pal_questions):
        """Test that fixture questions have all required fields."""
        for q in lo_pal_questions:
            assert q["prompt_en"]
            assert q["theme_slug"]
            assert q["source_url"]
            assert q["license"] == "rewrite-required"
            assert q["attribution"]

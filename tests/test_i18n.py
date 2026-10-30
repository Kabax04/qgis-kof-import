import re
from pathlib import Path

from kof_tools import i18n
from kof_tools.i18n import tr
from kof_tools.kof_parser import parse_lines

SOURCE = Path(__file__).parent.parent / "kof_tools"
# tr( followed by one or more adjacent string literals.
TR_CALL = re.compile(r'\btr\(\s*((?:"[^"]*"\s*)+)')


def texts_in_source():
    texts = set()
    for path in SOURCE.rglob("*.py"):
        if path.name == "i18n.py":
            continue
        for match in TR_CALL.finditer(path.read_text(encoding="utf-8")):
            texts.add("".join(re.findall(r'"([^"]*)"', match.group(1))))
    return texts


def test_all_texts_have_norwegian_translation():
    texts = texts_in_source()
    assert len(texts) > 30
    missing = sorted(t for t in texts if t not in i18n.NB)
    assert missing == []


def test_no_unused_translations():
    assert sorted(set(i18n.NB) - texts_in_source()) == []


def test_translations_keep_placeholders():
    for english, norwegian in i18n.NB.items():
        source = i18n.EN.get(english, english)
        assert re.findall(r"\{(\w+)", source) == re.findall(r"\{(\w+)", norwegian), english


def test_norwegian():
    i18n.set_language("nb")
    assert tr("Import KOF file") == "Importer KOF-fil"
    result = parse_lines([" 77 noe"])
    assert result.warnings == ["Linje 1: ukjent postkode '77', ignorert"]


def test_nynorsk_uses_norwegian():
    i18n.set_language("nn")
    assert tr("Import KOF file") == "Importer KOF-fil"


def test_english_is_default_text():
    assert tr("Import KOF file") == "Import KOF file"
    assert tr("HELP").startswith("Reads points")

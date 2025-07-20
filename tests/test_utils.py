import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import GitSearch as GS


def test_html_to_raw():
    url = "https://github.com/user/repo/blob/main/file.txt"
    expected = "https://raw.githubusercontent.com/user/repo/main/file.txt"
    assert GS.html_to_raw(url) == expected


def test_build_patterns_case_insensitive():
    dork = "filename:.env DB_PASSWORD 'api key'"
    patterns = GS.build_patterns(dork)
    assert len(patterns) == 2
    assert all(p.flags & re.IGNORECASE for p in patterns)
    assert patterns[0].pattern == re.escape("DB_PASSWORD")
    assert patterns[1].pattern == re.escape("api key")


def test_context_excerpt():
    lines = [f"line{i}\n" for i in range(1,6)]
    excerpt = GS.context_excerpt(lines, 2)
    expected = "".join(lines[0:5]).strip()
    assert excerpt == expected
    assert GS.context_excerpt(lines, 0) == ""

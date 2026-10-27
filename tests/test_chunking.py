import random

import pytest

from caseflow.chunking import chunk_text


@pytest.mark.parametrize("text", ["", " ", "\n\t" * 100])
def test_empty_and_whitespace_only_text(text):
    assert chunk_text(text, chunk_size=10, overlap=2) == []


def test_short_text_is_preserved_with_offsets():
    chunks = chunk_text("  Keep whitespace!\n", chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == "  Keep whitespace!\n"
    assert (chunks[0].position, chunks[0].start, chunks[0].end) == (0, 0, 19)


def test_long_line_is_bounded_and_reconstructable():
    text = "x" * 10001
    chunks = chunk_text(text, chunk_size=800, overlap=120)
    assert all(len(chunk.text) <= 800 for chunk in chunks)
    rebuilt = chunks[0].text + "".join(chunk.text[120:] for chunk in chunks[1:])
    assert rebuilt == text
    assert chunks[-1].end == len(text)


def test_exact_overlap_and_no_redundant_trailing_window():
    text = "abcdefghijklmnop"
    chunks = chunk_text(text, chunk_size=8, overlap=4)
    assert [c.text for c in chunks] == ["abcdefgh", "efghijkl", "ijklmnop"]
    assert [c.position for c in chunks] == [0, 1, 2]
    assert chunks[0].text[-4:] == chunks[1].text[:4]


def test_zero_overlap_and_exact_boundary():
    assert [c.text for c in chunk_text("abcdefgh", 4, 0)] == ["abcd", "efgh"]
    assert len(chunk_text("abcd", 4, 0)) == 1


@pytest.mark.parametrize(
    ("size", "overlap"),
    [(0, 0), (-1, 0), (4, -1), (4, 4), (4, 5), (True, 0), (4, True), (4.5, 0), (4, 0.5)],
)
def test_invalid_window_configuration_fails_even_for_empty_text(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("", size, overlap)


def test_unicode_offsets_and_all_non_whitespace_characters_are_covered():
    rng = random.Random(42)
    for _ in range(50):
        text = "".join(rng.choice("abc  \n\t🧥বাংলা") for _ in range(rng.randrange(1, 300)))
        size = rng.randrange(1, 50)
        overlap = rng.randrange(size)
        chunks = chunk_text(text, size, overlap)
        covered = set()
        for position, chunk in enumerate(chunks):
            assert chunk.position == position
            assert chunk.text == text[chunk.start : chunk.end]
            assert 0 < len(chunk.text) <= size
            covered.update(range(chunk.start, chunk.end))
        assert {i for i, char in enumerate(text) if not char.isspace()} <= covered

import uuid

from src.domain.entities.music import Album, Artist, Franchise, Label, Publisher, Track
from src.domain.value_objects.aliases import (
    MAX_ALIAS_LENGTH,
    MAX_ALIASES_PER_ENTITY,
    normalize_aliases,
)


def test_normalize_aliases_empty_and_falsy() -> None:
    assert normalize_aliases(None) == []
    assert normalize_aliases([]) == []
    assert normalize_aliases(["", "   ", "\n\t"]) == []


def test_normalize_aliases_trims_and_deduplicates_case_insensitively() -> None:
    raw = [" Touhou ", "TOUHOU", "touhou", "  Project  ", "Project"]
    assert normalize_aliases(raw) == ["Touhou", "Project"]


def test_normalize_aliases_filters_non_strings() -> None:
    raw = ["Valid", 123, None, "Another", {"k": "v"}, True]  # type: ignore
    assert normalize_aliases(raw) == ["Valid", "Another"]


def test_normalize_aliases_truncates_long_strings() -> None:
    long_str = "a" * (MAX_ALIAS_LENGTH + 50)
    res = normalize_aliases([long_str])
    assert len(res[0]) == MAX_ALIAS_LENGTH


def test_normalize_aliases_caps_total_count() -> None:
    raw = [f"Alias_{i}" for i in range(MAX_ALIASES_PER_ENTITY + 20)]
    res = normalize_aliases(raw)
    assert len(res) == MAX_ALIASES_PER_ENTITY


def test_entities_post_init_normalizes_aliases() -> None:
    dummy_uuid = uuid.uuid4()
    raw_aliases = [" Alias 1 ", "ALIAS 1", ""]

    artist = Artist(id=dummy_uuid, name_original="Test", aliases=raw_aliases)
    assert artist.aliases == ["Alias 1"]

    franchise = Franchise(id=dummy_uuid, name_original="Test", aliases=raw_aliases)
    assert franchise.aliases == ["Alias 1"]

    label = Label(id=dummy_uuid, name_original="Test", aliases=raw_aliases)
    assert label.aliases == ["Alias 1"]

    publisher = Publisher(id=dummy_uuid, name_original="Test", aliases=raw_aliases)
    assert publisher.aliases == ["Alias 1"]

    track = Track(
        id=dummy_uuid,
        disc_id=dummy_uuid,
        track_number=1,
        title_original="Test",
        aliases=raw_aliases,
        duration_seconds=100,
        audio_codec=None,
        video_codec=None,
        bit_depth=None,
        sample_rate=None,
        bitrate_kbps=None,
        bitrate_mode=None,
    )
    assert track.aliases == ["Alias 1"]

    album = Album(
        id=dummy_uuid,
        title_original="Test",
        aliases=raw_aliases,
    )
    assert album.aliases == ["Alias 1"]

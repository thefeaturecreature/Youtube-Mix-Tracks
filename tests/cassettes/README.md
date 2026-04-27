# Cassettes

VCR cassettes record real HTTP interactions and replay them in tests so they run offline.

## How to record a cassette

1. Set `record_mode="new_episodes"` in `tests/conftest.py`
2. Set your API keys in `.env`
3. Run the specific test: `pytest tests/test_mixesdb.py -k "real_mix"`
4. Commit the new `.yaml` file
5. Revert `record_mode` back to `"none"`

## Required cassettes (to be recorded against real mixes)

See `/Users/random/Documents/Order/Assistant/TODO.md` for which YouTube URLs to use.

| File | Source | Mix |
|---|---|---|
| `yt_description_hit.yaml` | YouTube description | mix with tracklist in description |
| `yt_comment_hit.yaml` | YouTube comment | mix with tracklist in top comment only |
| `mixesdb_hit.yaml` | MixesDB | mix catalogued on MixesDB |
| `1001tl_hit.yaml` | 1001Tracklists | mix on 1001TL but not MixesDB |

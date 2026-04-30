# Functions

## find_a_mix/youtube.py
- `fetch_video_info(youtube, video_id)` — fetch title, channel, and description in one API call; returns `{title, channel, description}`
- `fetch_top_comments(youtube, video_id, max_results)` — fetch top/most-relevant comments, HTML stripped

## find_a_mix/parse.py
- `looks_like_tracklist(text)` — heuristic: returns True if text has tracklist header, 3+ timestamps, or 3+ numbered lines
- `extract_tracklist_block(text)` — returns stripped text if it looks like a tracklist, else None

## find_a_mix/mixesdb.py
- `search(artist, title)` — search MixesDB, return page URL of best result
- `fetch_tracklist(page_url)` — scrape and return track list from a MixesDB page

## find_a_mix/tracklists_1001.py
- `fetch_tracklist(page_url)` — scrape tracks from a 1001Tracklists page; returns list of `{num, title, time}` dicts
- `search_and_fetch(artist, title)` — search 1001Tracklists and fetch the top result's tracklist
- `_wait_past_gate(page, timeout_s)` — polls until the JS forwarding gate clears
- `_fetch_tracklist_page(ctx, url)` — internal: navigate, wait past gate, extract `.tlpItem` elements
- `_search_page(ctx, query)` — internal: fill search box, return first tracklist URL

## find_a_mix/acrcloud.py
- `identify_chunk(audio_bytes, timestamp_sec)` — submit an audio chunk to ACRCloud, return raw result with `_offset_sec` attached

## find_a_mix/infer.py
- `parse_tracks(raw_text)` — call LLM to parse raw tracklist text into `list[dict]` with fields `{num, timestamp, artist, title, label, date, apple_music_id, spotify_id}`

## find_a_mix/output.py
- `_format_track(i, track)` — format a single structured track dict as a markdown line
- `format_markdown(result)` — format a pipeline result dict as a markdown string; all sources render from structured `tracks: list[dict]`
- `_seconds_to_cue_index(ts)` — convert `MM:SS` or `H:MM:SS` timestamp to CUE index format `MM:SS:FF`
- `generate_cue(result, audio_filename, audio_format)` — generate a CUE sheet string from a pipeline result dict; audio_format sets the FILE type line (mp3/opus/aac/flac)

## find_a_mix/download.py
- `download_audio(url, output_dir, audio_format)` — download best audio from URL via yt-dlp, convert to audio_format, return final file path

## find_a_mix/pipeline.py
- `video_id_from_url(url)` — extract YouTube video ID from a URL
- `run(url)` — run the full source cascade (YouTube description → comments → MixesDB → 1001Tracklists); all sources parsed through `parse_tracks()`, returns `{source, video_title, tracks}`

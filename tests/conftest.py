import pytest
import vcr

CASSETTE_DIR = "tests/cassettes"

youtube_vcr = vcr.VCR(
    cassette_library_dir=CASSETTE_DIR,
    record_mode="none",  # change to "new_episodes" to re-record
    match_on=["method", "scheme", "host", "path", "query"],
    filter_query_parameters=["key"],  # strip API key from recordings
)


@pytest.fixture
def fixture_text(request):
    path = request.param
    with open(path) as f:
        return f.read()

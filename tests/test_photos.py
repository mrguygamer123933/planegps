from planegps.photos import PhotoService


class _FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeSession:
    """Records requests and returns canned responses keyed by URL suffix."""

    def __init__(self, responses):
        self._responses = responses
        self.headers = {}
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        for suffix, resp in self._responses.items():
            if url.endswith(suffix):
                return resp
        return _FakeResp(404, {})


_PHOTO_PAYLOAD = {
    "photos": [
        {
            "thumbnail": {"src": "https://t.example/thumb.jpg"},
            "thumbnail_large": {"src": "https://t.example/large.jpg"},
            "link": "https://www.planespotters.net/photo/123",
            "photographer": "Jane Doe",
        }
    ]
}


def _service(responses):
    svc = PhotoService(ttl_s=100)
    svc._session = _FakeSession(responses)
    return svc


def test_lookup_by_hex():
    svc = _service({"/hex/abc123": _FakeResp(200, _PHOTO_PAYLOAD)})
    result = svc.lookup("ABC123", None)
    assert result is not None
    assert result["large"] == "https://t.example/large.jpg"
    assert result["photographer"] == "Jane Doe"
    assert result["source"] == "planespotters.net"


def test_falls_back_to_registration():
    svc = _service(
        {
            "/hex/abc123": _FakeResp(200, {"photos": []}),
            "/reg/G-TEST": _FakeResp(200, _PHOTO_PAYLOAD),
        }
    )
    result = svc.lookup("abc123", "g-test")
    assert result is not None
    assert result["thumbnail"] == "https://t.example/thumb.jpg"


def test_no_photo_returns_none_and_is_cached():
    svc = _service({"/hex/dead00": _FakeResp(200, {"photos": []})})
    assert svc.lookup("dead00", None) is None
    # Second call should hit the cache, not the session again.
    calls_before = len(svc._session.calls)
    assert svc.lookup("dead00", None) is None
    assert len(svc._session.calls) == calls_before


def test_empty_identifiers_returns_none():
    svc = _service({})
    assert svc.lookup(None, None) is None
    assert svc._session.calls == []

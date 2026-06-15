from __future__ import annotations

import pytest

from nutev.download.url_safety import (
    UnsafeURLError,
    assert_public_url,
    is_public_url,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://localhost/admin",
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata
        "http://10.0.0.5/",
        "http://192.168.1.1/",
        "http://172.16.0.1/",
        "http://[::1]/",
        "http://0.0.0.0/",
        "https://8.8.8.8@127.0.0.1/",  # userinfo trick -> host is 127.0.0.1
        "file:///etc/passwd",
        "ftp://example.com/x",
        "gopher://127.0.0.1:70/",
        "//no-scheme",
        "",
    ],
)
def test_blocks_unsafe_urls(url: str) -> None:
    assert is_public_url(url) is False
    with pytest.raises(UnsafeURLError):
        assert_public_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://8.8.8.8/",
        "https://1.1.1.1/resource",
        "https://93.184.216.34/",  # public literal
    ],
)
def test_allows_public_literal_ips(url: str) -> None:
    assert is_public_url(url) is True
    assert assert_public_url(url) == url


def test_ipv4_mapped_ipv6_loopback_blocked() -> None:
    assert is_public_url("http://[::ffff:127.0.0.1]/") is False

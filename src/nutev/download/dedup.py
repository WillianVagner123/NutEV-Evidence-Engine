from __future__ import annotations

import hashlib


class Deduplicator:
    def __init__(self) -> None:
        self.seen_urls: set[str] = set()
        self.seen_hashes: set[str] = set()

    def seen_url(self, url: str) -> bool:
        if url in self.seen_urls:
            return True
        self.seen_urls.add(url)
        return False

    def seen_content(self, content: bytes) -> bool:
        digest = hashlib.sha256(content).hexdigest()
        if digest in self.seen_hashes:
            return True
        self.seen_hashes.add(digest)
        return False

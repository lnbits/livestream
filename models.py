import json
from typing import Optional

from fastapi import Query, Request
from lnurl import Lnurl
from lnurl import encode as lnurl_encode
from lnurl.types import LnurlPayMetadata
from pydantic import BaseModel


class CreateTrack(BaseModel):
    name: str = Query(...)
    download_url: str = Query(None)
    price_msat: int = Query(None, ge=0)
    producer_id: str = Query(None)
    producer_name: str = Query(None)


class Livestream(BaseModel):
    id: str
    wallet: str
    fee_pct: int = 10
    current_track: Optional[str] = None

    def lnurl(self, request: Request) -> Lnurl:
        url = str(request.url_for("livestream.lnurl_livestream", ls_id=self.id))
        return lnurl_encode(url)


class Track(BaseModel):
    id: str
    livestream: str
    producer: str
    name: str
    download_url: Optional[str] = None
    price_msat: int = 0

    @property
    def min_sendable(self) -> int:
        return min(100_000, self.price_msat or 100_000)

    @property
    def max_sendable(self) -> int:
        return max(50_000_000, self.price_msat * 5)

    def lnurl(self, request: Request) -> Lnurl:
        url = str(request.url_for("livestream.lnurl_track", track_id=self.id))
        return lnurl_encode(url)

    async def fullname(self) -> str:
        from .crud import get_producer

        producer = await get_producer(self.producer)
        if producer:
            producer_name = producer.name
        else:
            producer_name = "unknown author"

        return f"'{self.name}', from {producer_name}."

    async def lnurlpay_metadata(self) -> LnurlPayMetadata:
        description = (
            await self.fullname()
        ) + " Like this track? Send some sats in appreciation."

        if self.download_url:
            description += (
                f"Send {round(self.price_msat/1000)} "
                "sats or more and you can download it."
            )

        return LnurlPayMetadata(json.dumps([["text/plain", description]]))


class Producer(BaseModel):
    id: str
    livestream: str
    user: str
    wallet: str
    name: str


class LivestreamOverview(BaseModel):
    lnurl: str
    livestream: Livestream
    tracks: list[Track]
    producers: list[Producer]

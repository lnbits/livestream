from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import require_admin_key, require_invoice_key

from .crud import (
    create_producer,
    create_track,
    delete_track_from_livestream,
    get_or_create_livestream_by_wallet,
    get_producer,
    get_producers,
    get_track,
    get_tracks,
    update_current_track,
    update_livestream_fee,
    update_track,
)
from .models import CreateTrack, LivestreamOverview

livestream_api_router = APIRouter()


@livestream_api_router.get("/api/v1/livestream")
async def api_livestream_from_wallet(
    req: Request, key_info: WalletTypeInfo = Depends(require_invoice_key)
) -> LivestreamOverview:
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    tracks = await get_tracks(ls.id)
    producers = await get_producers(ls.id)
    overview = LivestreamOverview(
        lnurl=str(ls.lnurl(request=req)),
        livestream=ls,
        tracks=tracks,
        producers=producers,
    )
    return overview


@livestream_api_router.put("/api/v1/livestream/track/{track_id}")
async def api_update_track(
    track_id: str, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    track = await get_track(track_id)
    if not track:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Track not found.")
    await update_current_track(ls.id, track.id)


@livestream_api_router.put("/api/v1/livestream/fee/{fee_pct}")
async def api_update_fee(
    fee_pct, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    await update_livestream_fee(ls.id, int(fee_pct))


async def _check_producer(livestream_id, data: CreateTrack):
    if data.producer_id:
        producer = await get_producer(data.producer_id)
        if not producer:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Producer with id: {data.producer_id} not found.",
            )
    else:
        if not data.producer_name:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Producer name required."
            )
        producer = await create_producer(livestream_id, data.producer_name)
    return producer


@livestream_api_router.post("/api/v1/livestream/track")
async def api_add_tracks(
    data: CreateTrack, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    producer = await _check_producer(ls.id, data)
    return await create_track(ls.id, producer.id, data)


@livestream_api_router.put("/api/v1/livestream/track/{track_id}")
async def api_update_tracks(
    track_id: str,
    data: CreateTrack,
    key_info: WalletTypeInfo = Depends(require_admin_key),
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    track = await get_track(track_id)
    if not track:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Track not found.")
    producer = await _check_producer(ls.id, data)

    if data.download_url:
        track.download_url = data.download_url
    if data.price_msat:
        track.price_msat = data.price_msat

    track.name = data.name
    track.producer = producer.id

    return await update_track(track)


@livestream_api_router.delete("/api/v1/livestream/tracks/{track_id}")
async def api_delete_track(
    track_id: str, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    await delete_track_from_livestream(ls.id, track_id)

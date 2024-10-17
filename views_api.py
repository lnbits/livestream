from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import require_admin_key, require_invoice_key
from lnurl.exceptions import InvalidUrl as LnurlInvalidUrl

from .crud import (
    add_producer,
    add_track,
    delete_track_from_livestream,
    get_or_create_livestream_by_wallet,
    get_producers,
    get_tracks,
    update_current_track,
    update_livestream_fee,
    update_track,
)
from .models import CreateTrack

livestream_api_router = APIRouter()


@livestream_api_router.get("/api/v1/livestream")
async def api_livestream_from_wallet(
    req: Request, key_info: WalletTypeInfo = Depends(require_invoice_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    assert ls
    tracks = await get_tracks(ls.id)
    producers = await get_producers(ls.id)

    try:
        return {
            **ls.dict(),
            **{
                "lnurl": ls.lnurl(request=req),
                "tracks": [
                    dict(lnurl=track.lnurl(request=req), **track.dict())
                    for track in tracks
                ],
                "producers": [producer.dict() for producer in producers],
            },
        }
    except LnurlInvalidUrl as exc:
        raise HTTPException(
            status_code=HTTPStatus.UPGRADE_REQUIRED,
            detail=(
                "LNURLs need to be delivered over a publically "
                "accessible `https` domain or Tor."
            ),
        ) from exc


@livestream_api_router.put("/api/v1/livestream/track/{track_id}")
async def api_update_track(
    track_id, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    try:
        tid = int(track_id)
    except ValueError:
        tid = 0

    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    assert ls
    await update_current_track(ls.id, None if tid <= 0 else tid)
    return "", HTTPStatus.NO_CONTENT


@livestream_api_router.put("/api/v1/livestream/fee/{fee_pct}")
async def api_update_fee(
    fee_pct, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    assert ls
    await update_livestream_fee(ls.id, int(fee_pct))
    return "", HTTPStatus.NO_CONTENT


async def check_producer(ls_id, data) -> int:
    if data.producer_id:
        p_id = int(data.producer_id)
    elif data.producer_name:
        p_id = await add_producer(ls_id, data.producer_name)
    else:
        raise TypeError("need either producer_id or producer_name arguments")
    return p_id


@livestream_api_router.post("/api/v1/livestream/tracks")
async def api_add_tracks(
    data: CreateTrack, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    p_id = await check_producer(ls.id, data)
    return await add_track(
        ls.id, data.name, data.download_url, data.price_msat or 0, p_id
    )


@livestream_api_router.put("/api/v1/livestream/tracks/{id}")
async def api_update_tracks(
    data: CreateTrack, tid: int, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    p_id = await check_producer(ls.id, data)
    return await update_track(
        ls.id, tid, data.name, data.download_url, data.price_msat or 0, p_id
    )


@livestream_api_router.delete("/api/v1/livestream/tracks/{track_id}")
async def api_delete_track(
    track_id, key_info: WalletTypeInfo = Depends(require_admin_key)
):
    ls = await get_or_create_livestream_by_wallet(key_info.wallet.id)
    assert ls
    await delete_track_from_livestream(ls.id, track_id)
    return "", HTTPStatus.NO_CONTENT

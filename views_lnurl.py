import math

from fastapi import APIRouter, Query, Request
from lnbits.core.services import create_invoice
from lnurl import (
    CallbackUrl,
    LightningInvoice,
    LnurlErrorResponse,
    LnurlPayActionResponse,
    LnurlPayResponse,
    Max144Str,
    MilliSatoshi,
    UrlAction,
)
from pydantic import parse_obj_as

from .crud import get_livestream, get_livestream_by_track, get_track

livestream_lnurl_router = APIRouter()


@livestream_lnurl_router.get("/lnurl/{ls_id}", name="livestream.lnurl_livestream")
async def lnurl_livestream(
    ls_id: str, request: Request
) -> LnurlPayResponse | LnurlErrorResponse:
    ls = await get_livestream(ls_id)
    if not ls:
        return LnurlErrorResponse(reason="Livestream not found.")

    if not ls.current_track:
        return LnurlErrorResponse(reason="This livestream is offline.")
    track = await get_track(ls.current_track)
    if not track:
        return LnurlErrorResponse(reason="Track not found.")

    url = parse_obj_as(
        CallbackUrl,
        request.url_for("livestream.lnurl_track", track_id=track.id),
    )

    return LnurlPayResponse(
        callback=url,
        minSendable=MilliSatoshi(track.min_sendable),
        maxSendable=MilliSatoshi(track.max_sendable),
        metadata=await track.lnurlpay_metadata(),
        commentAllowed=300,
    )


@livestream_lnurl_router.get("/lnurl/t/{track_id}", name="livestream.lnurl_track")
async def lnurl_track(
    track_id, request: Request
) -> LnurlPayResponse | LnurlErrorResponse:
    track = await get_track(track_id)
    if not track:
        return LnurlErrorResponse(reason="Track not found.")

    url = parse_obj_as(
        CallbackUrl,
        str(request.url_for("livestream.lnurl_track", track_id=track.id)),
    )
    return LnurlPayResponse(
        callback=url,
        minSendable=MilliSatoshi(track.min_sendable),
        maxSendable=MilliSatoshi(track.max_sendable),
        metadata=await track.lnurlpay_metadata(),
        commentAllowed=300,
    )


@livestream_lnurl_router.get("/lnurl/cb/{track_id}", name="livestream.lnurl_callback")
async def lnurl_callback(
    track_id, request: Request, amount: int = Query(...), comment: str = Query("")
) -> LnurlPayActionResponse | LnurlErrorResponse:

    track = await get_track(track_id)
    if not track:
        return LnurlErrorResponse(reason="Track not found.")

    amount_received = int(amount or 0)

    if amount_received < track.min_sendable:
        return LnurlErrorResponse(
            reason=f"""
            Amount {round(amount_received / 1000)} is smaller than
            minimum {math.floor(track.min_sendable)}.
            """
        )
    elif track.max_sendable < amount_received:
        return LnurlErrorResponse(
            reason=f"""
            Amount {round(amount_received / 1000)} is greater than
            maximum {math.floor(track.max_sendable)}.
            """
        )
    if len(comment or "") > 300:
        return LnurlErrorResponse(
            reason=f"""
            Got a comment with {len(comment)} characters,
            but can only accept 300
            """
        )

    ls = await get_livestream_by_track(track_id)
    assert ls

    extra_amount = amount_received - int(amount_received * (100 - ls.fee_pct) / 100)

    payment = await create_invoice(
        wallet_id=ls.wallet,
        amount=int(amount_received / 1000),
        memo=await track.fullname(),
        unhashed_description=(await track.lnurlpay_metadata()).encode(),
        extra={
            "tag": "livestream",
            "track": track.id,
            "comment": comment,
            "amount": int(extra_amount / 1000),
        },
    )

    invoice = parse_obj_as(LightningInvoice, LightningInvoice(payment.bolt11))
    assert track.price_msat
    if amount_received < track.price_msat:
        return LnurlPayActionResponse(pr=invoice)

    url = request.url_for("livestream.track_download", track_id=track.id)
    url_with_query = f"{url}?p={payment.payment_hash}"
    success_action_url = parse_obj_as(CallbackUrl, url_with_query)
    message = parse_obj_as(Max144Str, f"Download {track.name}")
    action = UrlAction(
        description=message,
        url=success_action_url,
    )
    return LnurlPayActionResponse(pr=invoice, successAction=action)

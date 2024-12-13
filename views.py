from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from lnbits.core.crud import get_wallet_payment
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from starlette.datastructures import URL

from .crud import get_livestream_by_track, get_track

livestream_generic_router = APIRouter()


def livestream_renderer():
    return template_renderer(["livestream/templates"])


@livestream_generic_router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: User = Depends(check_user_exists)):
    return livestream_renderer().TemplateResponse(
        "livestream/index.html", {"request": request, "user": user.json()}
    )


@livestream_generic_router.get(
    "/track/{track_id}", name="livestream.track_redirect_download"
)
async def track_redirect_download(track_id, p: str = Query(...)):
    payment_hash = p
    track = await get_track(track_id)
    ls = await get_livestream_by_track(track_id)
    assert ls
    payment = await get_wallet_payment(ls.wallet, payment_hash)

    if not payment:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Couldn't find the payment {payment_hash}.",
        )
    if not track:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Couldn't find the track {track_id}.",
        )

    if payment.pending:
        raise HTTPException(
            status_code=HTTPStatus.PAYMENT_REQUIRED,
            detail=(
                f"Payment {payment_hash} wasn't received yet. "
                "Please try again in a minute."
            ),
        )

    assert track.download_url
    return RedirectResponse(url=URL(track.download_url))

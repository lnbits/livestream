from typing import Optional

from lnbits.core.crud import create_account, create_wallet
from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import CreateTrack, Livestream, Producer, Track

db = Database("ext_livestream")


async def create_livestream(wallet_id: str) -> Livestream:
    livestream = Livestream(
        id=urlsafe_short_hash(),
        wallet=wallet_id,
    )
    await db.insert("livestream.livestreams", livestream)
    return livestream


async def get_livestream(ls_id: str) -> Optional[Livestream]:
    return await db.fetchone(
        "SELECT * FROM livestream.livestreams WHERE id = :id",
        {"id": ls_id},
        Livestream,
    )


async def get_livestream_by_track(track_id: str) -> Optional[Livestream]:
    return await db.fetchone(
        """
        SELECT a.* FROM livestream.tracks as b
        LEFT JOIN livestream.livestreams as a ON a.id = b.livestream
        WHERE b.id = :id
        """,
        {"id": track_id},
        Livestream,
    )


async def get_or_create_livestream_by_wallet(wallet: str) -> Livestream:
    livestream = await db.fetchone(
        "SELECT * FROM livestream.livestreams WHERE wallet = :wallet",
        {"wallet": wallet},
        Livestream,
    )
    if livestream:
        return livestream

    # create on the fly
    ls = await create_livestream(wallet)
    return ls


async def update_current_track(ls_id: str, track_id: Optional[str]):
    await db.execute(
        "UPDATE livestream.livestreams SET current_track = :track_id WHERE id = :id",
        {"track_id": track_id, "id": ls_id},
    )


async def update_livestream_fee(ls_id: str, fee_pct: int):
    await db.execute(
        "UPDATE livestream.livestreams SET fee_pct = :fee_pct WHERE id = :id",
        {"fee_pct": fee_pct, "id": ls_id},
    )


async def create_track(
    livestream: str,
    producer: str,
    data: CreateTrack,
) -> Track:
    track = Track(
        id=urlsafe_short_hash(),
        livestream=livestream,
        producer=producer,
        name=data.name,
        download_url=data.download_url,
        price_msat=data.price_msat,
    )
    await db.insert("livestream.tracks", track)
    return track


async def update_track(track: Track) -> Track:
    await db.update("livestream.tracks", track)
    return track


async def get_track(track_id: str) -> Optional[Track]:
    return await db.fetchone(
        "SELECT * FROM livestream.tracks WHERE id = :id",
        {"id": track_id},
        Track,
    )


async def get_tracks(livestream: str) -> list[Track]:
    return await db.fetchall(
        "SELECT * FROM livestream.tracks WHERE livestream = :livestream",
        {"livestream": livestream},
        Track,
    )


async def delete_track_from_livestream(livestream: str, track_id: str):
    await db.execute(
        """
        DELETE FROM livestream.tracks WHERE livestream = :livestream AND id = :id
        """,
        {"livestream": livestream, "id": track_id},
    )


async def create_producer(livestream_id: str, name: str) -> Producer:
    name = name.strip()
    producer = await db.fetchone(
        """
        SELECT * FROM livestream.producers
        WHERE livestream = :livestream AND lower(name) = :name
        """,
        {"livestream": livestream_id, "name": name.lower()},
        Producer,
    )
    if producer:
        return producer

    user = await create_account()
    wallet = await create_wallet(user_id=user.id, wallet_name="livestream: " + name)

    producer = Producer(
        id=urlsafe_short_hash(),
        livestream=livestream_id,
        user=user.id,
        wallet=wallet.id,
        name=name,
    )
    await db.insert("livestream.producers", producer)
    return producer


async def get_producer(producer_id: str) -> Optional[Producer]:
    return await db.fetchone(
        "SELECT * FROM livestream.producers WHERE id = :id",
        {"id": producer_id},
        Producer,
    )


async def get_producers(livestream: str) -> list[Producer]:
    return await db.fetchall(
        """
        SELECT id, "user", wallet, name
        FROM livestream.producers WHERE livestream = :livestream
        """,
        {"livestream": livestream},
        Producer,
    )

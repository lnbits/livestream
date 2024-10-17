from typing import Optional

from lnbits.core.crud import create_account, create_wallet
from lnbits.db import Database

from .models import Livestream, Producer, Track

db = Database("ext_livestream")


async def create_livestream(wallet_id: str) -> int:
    await db.fetchone(
        """
        INSERT INTO livestream.livestreams (wallet)
        VALUES (:wallet_id)
        """,
        {"wallet_id": wallet_id},
    )
    return 0


async def get_livestream(ls_id: int) -> Optional[Livestream]:
    return await db.fetchone(
        "SELECT * FROM livestream.livestreams WHERE id = :id",
        {"id": ls_id},
        Livestream,
    )


async def get_livestream_by_track(track_id: int) -> Optional[Livestream]:
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
    ls_id = await create_livestream(wallet)
    ls = await get_livestream(ls_id)
    assert ls, "Newly created livestream should exist."
    return ls


async def update_current_track(ls_id: int, track_id: Optional[int]):
    await db.execute(
        "UPDATE livestream.livestreams SET current_track = :track_id WHERE id = :id",
        {"track_id": track_id, "id": ls_id},
    )


async def update_livestream_fee(ls_id: int, fee_pct: int):
    await db.execute(
        "UPDATE livestream.livestreams SET fee_pct = :fee_pct WHERE id = :id",
        {"fee_pct": fee_pct, "id": ls_id},
    )


async def add_track(
    livestream: int,
    name: str,
    download_url: Optional[str],
    price_msat: int,
    producer: Optional[int],
) -> int:
    result = await db.execute(
        """
        INSERT INTO livestream.tracks
        (livestream, name, download_url, price_msat, producer)
        VALUES (:livestream, :name, :download_url, :price_msat, :producer)
        """,
        {
            "livestream": livestream,
            "name": name,
            "download_url": download_url,
            "price_msat": price_msat,
            "producer": producer,
        },
    )
    return result._result_proxy.lastrowid


async def update_track(
    livestream: int,
    track_id: int,
    name: str,
    download_url: Optional[str],
    price_msat: int,
    producer: int,
) -> int:
    result = await db.execute(
        """
        UPDATE livestream.tracks SET
          name = :name,
          download_url = :download_url,
          price_msat = :price_msat,
          producer = :producer
        WHERE livestream = :livestream AND id = :id
        """,
        {
            "livestream": livestream,
            "id": track_id,
            "name": name,
            "download_url": download_url,
            "price_msat": price_msat,
            "producer": producer,
        },
    )
    return result._result_proxy.lastrowid


async def get_track(track_id: int) -> Optional[Track]:
    return await db.fetchone(
        """
        SELECT id, download_url, price_msat, name, producer
        FROM livestream.tracks WHERE id = :id
        """,
        {"id": track_id},
        Track,
    )


async def get_tracks(livestream: int) -> list[Track]:
    return await db.fetchall(
        """
        SELECT id, download_url, price_msat, name, producer
        FROM livestream.tracks WHERE livestream = :livestream
        """,
        {"livestream": livestream},
        Track,
    )


async def delete_track_from_livestream(livestream: int, track_id: int):
    await db.execute(
        """
        DELETE FROM livestream.tracks WHERE livestream = :livestream AND id = :id
        """,
        {"livestream": livestream, "id": track_id},
    )


async def add_producer(livestream_id: int, name: str) -> int:
    name = name.strip()

    livestream = await db.fetchone(
        """
        SELECT id FROM livestream.producers
        WHERE livestream = :livestream AND lower(name) = :name
        """,
        {"livestream": livestream_id, "name": name.lower()},
        Livestream,
    )
    if livestream:
        return livestream.id

    user = await create_account()
    wallet = await create_wallet(user_id=user.id, wallet_name="livestream: " + name)

    await db.execute(
        """
        INSERT INTO livestream.producers (livestream, name, "user", wallet)
        VALUES (:livestream, :name, :user, :wallet)
        """,
        {
            "livestream": livestream_id,
            "name": name,
            "user": user.id,
            "wallet": wallet.id,
        },
    )
    return 1


async def get_producer(producer_id: int) -> Optional[Producer]:
    return await db.fetchone(
        """
        SELECT id, "user", wallet, name
        FROM livestream.producers WHERE id = :id
        """,
        {"id": producer_id},
        Producer,
    )


async def get_producers(livestream: int) -> list[Producer]:
    return await db.fetchall(
        """
        SELECT id, "user", wallet, name
        FROM livestream.producers WHERE livestream = :livestream
        """,
        {"livestream": livestream},
        Producer,
    )

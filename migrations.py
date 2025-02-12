from lnbits.db import Connection


async def m001_initial(db: Connection):
    """
    Initial livestream tables.
    """
    await db.execute(
        """
        CREATE TABLE livestream.livestreams (
            id TEXT PRIMARY KEY,
            wallet TEXT NOT NULL,
            fee_pct INTEGER NOT NULL DEFAULT 10,
            current_track INTEGER
        );
        """
    )

    await db.execute(
        """
        CREATE TABLE livestream.producers (
            id TEXT PRIMARY KEY,
            livestream TEXT NOT NULL,
            "user" TEXT NOT NULL,
            wallet TEXT NOT NULL,
            name TEXT NOT NULL
        );
        """
    )

    await db.execute(
        """
        CREATE TABLE livestream.tracks (
            id TEXT PRIMARY KEY,
            livestream TEXT NOT NULL,
            download_url TEXT,
            price_msat INTEGER NOT NULL DEFAULT 0,
            name TEXT,
            producer TEXT NOT NULL
        );
        """
    )


async def m002_fix_current_track(db: Connection):
    """
    Fix current_track column.
    """
    await db.execute("ALTER TABLE livestream.livestreams DROP COLUMN current_track;")
    await db.execute(
        "ALTER TABLE livestream.livestreams ADD COLUMN current_track TEXT;"
    )

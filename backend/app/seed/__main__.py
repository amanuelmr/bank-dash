"""Seed entrypoint: ``python -m app.seed``."""

import asyncio

from app.seed.data import main

if __name__ == "__main__":
    asyncio.run(main())
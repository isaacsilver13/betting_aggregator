import asyncio
from datetime import datetime, timedelta, timezone

from app.domain.models import MarketType
from app.providers.fixture import FixtureOddsProvider
from app.storage.database import create_schema, create_session_factory
from app.storage.repository import OddsRepository
from sqlalchemy.ext.asyncio import create_async_engine


def test_fixture_comparisons_persist_as_immutable_observations() -> None:
    async def scenario() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        await create_schema(engine)
        repository = OddsRepository(create_session_factory(engine))
        provider = FixtureOddsProvider()
        comparisons = await provider.get_comparisons()
        started_at = datetime.now(timezone.utc)

        await repository.record_comparisons(
            provider=provider.name,
            comparisons=comparisons,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        await repository.record_comparisons(
            provider=provider.name,
            comparisons=comparisons,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        assert await repository.count_refresh_runs("fixture") == 2
        assert await repository.count_observations(comparisons[0].event.id) == 16
        history = await repository.get_history(comparisons[0].event.id, MarketType.MONEYLINE)
        assert len(history) == 6
        assert all(offer.market_type is MarketType.MONEYLINE for offer in history)

        old_comparisons = [
            comparison.model_copy(
                update={
                    "offers": [
                        offer.model_copy(
                            update={"observed_at": started_at - timedelta(days=91)}
                        )
                        for offer in comparison.offers
                    ]
                }
            )
            for comparison in comparisons
        ]
        await repository.record_comparisons(
            provider=provider.name,
            comparisons=old_comparisons,
            started_at=started_at - timedelta(days=91),
            completed_at=started_at - timedelta(days=91),
        )

        removed = await repository.prune_expired(90, datetime.now(timezone.utc))

        assert removed == 8
        assert await repository.count_refresh_runs("fixture") == 2
        assert await repository.count_observations(comparisons[0].event.id) == 16
        await engine.dispose()

    asyncio.run(scenario())
"""Create provider refresh, event, mapping, and offer observation tables."""

import sqlalchemy as sa
from alembic import op

revision = "0001_odds_observations"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_refresh_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("sport", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_type", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("quota_remaining", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=180), nullable=False),
        sa.Column("sport", sa.String(length=20), nullable=False),
        sa.Column("league", sa.String(length=120), nullable=False),
        sa.Column("home_team", sa.String(length=160), nullable=False),
        sa.Column("away_team", sa.String(length=160), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "provider_event_mappings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("provider_event_id", sa.String(length=180), nullable=False),
        sa.Column("event_id", sa.String(length=180), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_provider_event_mappings_provider_raw",
        "provider_event_mappings",
        ["provider", "provider_event_id"],
    )
    op.create_table(
        "offer_observations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(length=180), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("bookmaker", sa.String(length=120), nullable=False),
        sa.Column("market_type", sa.String(length=80), nullable=False),
        sa.Column("selection", sa.String(length=180), nullable=False),
        sa.Column("line", sa.Float(), nullable=True),
        sa.Column("price_american", sa.Integer(), nullable=True),
        sa.Column("price_decimal", sa.Float(), nullable=True),
        sa.Column("player_name", sa.String(length=180), nullable=True),
        sa.Column("provider_offer_id", sa.String(length=240), nullable=True),
        sa.Column("provider_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deep_link", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_offer_observations_event_market_bookmaker_time",
        "offer_observations",
        ["event_id", "market_type", "bookmaker", "observed_at"],
    )
    op.create_index(
        "ix_offer_observations_event_market",
        "offer_observations",
        ["event_id", "market_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_offer_observations_event_market", table_name="offer_observations")
    op.drop_index(
        "ix_offer_observations_event_market_bookmaker_time", table_name="offer_observations"
    )
    op.drop_table("offer_observations")
    op.drop_index(
        "ix_provider_event_mappings_provider_raw", table_name="provider_event_mappings"
    )
    op.drop_table("provider_event_mappings")
    op.drop_table("events")
    op.drop_table("provider_refresh_runs")
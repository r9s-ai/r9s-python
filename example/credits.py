"""
Credits Usage API Examples
Demonstrates how to query management usage records with r9s.credits.usage.
"""

from datetime import date, datetime, timedelta, timezone
import os

from r9s import R9S


def _get_required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise RuntimeError(f"{name} is required for this example")
    return value


def basic_usage_query():
    """Example 1: Query usage in a fixed time range"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Usage Query")
    print("=" * 60)

    with R9S(
        api_key=_get_required_env("R9S_API_KEY"),
        manage_key=_get_required_env("R9S_MANAGE_KEY"),
    ) as r9s:
        res = r9s.credits.usage(
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-08T00:00:00+00:00",
        )

        total_tokens = res.data.total_tokens if res.data else None
        records = res.data.records if res.data and res.data.records else []

        print(f"Total tokens: {total_tokens}")
        print(f"Record count: {len(records)}")
        for record in records[:5]:
            print(
                f"timestamp={record.timestamp}, tokens={record.tokens}, model={record.model}"
            )


def usage_query_with_defaults():
    """Example 2: Use the default time range centered on today"""
    print("\n" + "=" * 60)
    print("Example 2: Default Usage Query")
    print("=" * 60)

    with R9S(
        api_key=_get_required_env("R9S_API_KEY"),
        manage_key=_get_required_env("R9S_MANAGE_KEY"),
    ) as r9s:
        res = r9s.credits.usage()
        print(f"Total tokens: {res.data.total_tokens if res.data else None}")


def daily_usage_query():
    """Example 3: Query usage day by day"""
    print("\n" + "=" * 60)
    print("Example 3: Daily Usage Query")
    print("=" * 60)

    start_day = date(2025, 1, 1)
    days = 3

    with R9S(
        api_key=_get_required_env("R9S_API_KEY"),
        manage_key=_get_required_env("R9S_MANAGE_KEY"),
    ) as r9s:
        for offset in range(days):
            current_day = start_day + timedelta(days=offset)
            next_day = current_day + timedelta(days=1)

            res = r9s.credits.usage(
                start_time=current_day.isoformat(),
                end_time=next_day.isoformat(),
            )

            total_tokens = res.data.total_tokens if res.data else 0
            print(f"{current_day.isoformat()}: total_tokens={total_tokens}")


def usage_query_with_datetime_objects():
    """Example 4: Pass datetime objects directly"""
    print("\n" + "=" * 60)
    print("Example 4: Datetime Object Query")
    print("=" * 60)

    start_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2025, 1, 2, tzinfo=timezone.utc)

    with R9S(
        api_key=_get_required_env("R9S_API_KEY"),
        manage_key=_get_required_env("R9S_MANAGE_KEY"),
    ) as r9s:
        res = r9s.credits.usage(start_time=start_time, end_time=end_time)
        print(f"Total tokens: {res.data.total_tokens if res.data else None}")


if __name__ == "__main__":
    basic_usage_query()
    usage_query_with_defaults()
    daily_usage_query()
    usage_query_with_datetime_objects()

import argparse
import time

import requests

from parcels import get_parcel_ids, search_owner

RETRY_ERRORS = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.HTTPError,
)


def main():
    parser = argparse.ArgumentParser(
        description="Search Croatian cadastral records for a land parcel owner."
    )
    parser.add_argument(
        "--auto-retry", "-r",
        action="store_true",
        help="Automatically retry after being rate-limited instead of exiting.",
    )
    parser.add_argument(
        "--retry-delay", "-d",
        type=float,
        default=2.0,
        metavar="MINUTES",
        help="Minutes to wait before retrying (default: 2).",
    )
    args = parser.parse_args()

    print("Enter bounding box coordinates (lat_min, lon_min, lat_max, lon_max), comma-separated:")
    lat_min, lon_min, lat_max, lon_max = map(float, input().split(","))

    print("\nFetching cadastral parcel IDs...")
    ids = get_parcel_ids(lat_min, lon_min, lat_max, lon_max)
    print(f"Found {len(ids)} parcel(s) in the area.\n")

    print("Enter the name/surname to search for:")
    name = input().strip()

    print(f"\nSearching for '{name}'...")

    while True:
        try:
            results = search_owner(ids, name)
            break
        except RETRY_ERRORS:
            if args.auto_retry:
                mins = args.retry_delay
                print(f"\n  Kicked out by rate limiter. Continuing in {mins:.0f} min...")
                time.sleep(mins * 60)
                print(f"\nResuming search for '{name}'...")
            else:
                print("\n  Kicked out by rate limiter. Re-run the script to continue from where it left off.")
                return

    print(f"\nDone. Found {len(results)} matching possession sheet(s).")
    for r in results:
        print(f"  Parcel {r['parcel_id']} — {r['parcel_address']} — {r['possessors']}")


if __name__ == "__main__":
    main()

import argparse
import sys

from importer.config import load_config
from importer.runner import Runner


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mealie-importer",
        description="Bulk-import Portuguese and Mediterranean recipes into Mealie.",
    )
    parser.add_argument(
        "--cuisine",
        metavar="CUISINE",
        help="Only import this cuisine (e.g. portuguese, mediterranean). Imports all if omitted.",
    )
    parser.add_argument(
        "--source",
        choices=["all", "urls", "static"],
        default="all",
        help="Import source: urls (Mealie scraper), static (local JSON), or all (default).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the run without writing to Mealie.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip recipes that already exist in Mealie (default: true).",
    )
    parser.add_argument(
        "--no-skip-existing",
        dest="skip_existing",
        action="store_false",
        help="Re-import recipes even if they already exist in Mealie.",
    )
    parser.add_argument(
        "--url",
        metavar="URL",
        help="Import a single recipe from this URL via Mealie's scraper.",
    )
    parser.add_argument(
        "--delete-all",
        action="store_true",
        help="Delete ALL recipes from Mealie. Prompts for confirmation unless --yes is given.",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt (use with --delete-all).",
    )

    args = parser.parse_args()

    try:
        config = load_config()
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    runner = Runner(config=config, dry_run=args.dry_run, skip_existing=args.skip_existing)

    if args.delete_all:
        runner.run_delete_all(yes=args.yes)
    elif args.url:
        runner.run_single_url(args.url)
    else:
        runner.run(cuisine=args.cuisine, source=args.source)

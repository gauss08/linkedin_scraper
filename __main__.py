import asyncio
import json
import logging
import sys

from .cli import args_to_config, build_parser, prompt_config
from .display import display_results
from .scraper import LinkedInScraper
from .url_builder import build_url

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)


async def _run_cli(args) -> None:
    config = args_to_config(args)
    url    = build_url(config)
    jobs   = await LinkedInScraper(
        headless=not args.no_headless,
        fetch_descriptions=not args.no_descriptions,
    ).scrape(url, max_results=args.max_results)

    if args.json_only:
        print(json.dumps([j.to_dict() for j in jobs], indent=2, ensure_ascii=False))
    else:
        display_results(jobs, config)


async def _run_interactive() -> None:
    try:
        config, max_results, fetch_desc, headless = prompt_config()
    except ValueError as e:
        print(f"  ❌  {e}")
        return

    url  = build_url(config)
    jobs = await LinkedInScraper(
        headless=headless,
        fetch_descriptions=fetch_desc,
    ).scrape(url, max_results=max_results)

    display_results(jobs, config)


def main() -> None:
    args = build_parser().parse_args()
    if args.keywords:
        asyncio.run(_run_cli(args))
    else:
        asyncio.run(_run_interactive())


if __name__ == "__main__":
    main()
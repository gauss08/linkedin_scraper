import argparse
from .config import SearchConfig

# ─────────────────────────────────────────────
#  Interactive mode
# ─────────────────────────────────────────────

_DATE_OPTIONS = {
    "1h":    "Last 1 hour  (ultra-fresh, fewest results)",
    "6h":    "Last 6 hours",
    "24h":   "Last 24 hours",
    "3d":    "Last 3 days",
    "week":  "Last week",
    "month": "Last month",
    "any":   "Any time (default)",
}
_EXPERIENCE_OPTIONS = {
    "internship": "Internship",
    "entry":      "Entry level",
    "associate":  "Associate",
    "mid":        "Mid-Senior level",
    "director":   "Director",
    "executive":  "Executive",
}
_JOB_TYPE_OPTIONS = {
    "fulltime":   "Full-time",
    "parttime":   "Part-time",
    "contract":   "Contract",
    "temporary":  "Temporary",
    "internship": "Internship",
}
_WORK_TYPE_OPTIONS = {
    "onsite": "On-site",
    "remote": "Remote",
    "hybrid": "Hybrid",
}
_SORT_OPTIONS = {
    "recent":   "Most recent",
    "relevant": "Most relevant",
}

_WIDTH = 70


def prompt_config() -> tuple[SearchConfig, int, bool, bool]:
    """
    Interactively prompt the user for search parameters.
    Returns (SearchConfig, max_results, fetch_descriptions, headless).
    """
    print()
    print("╔" + "═" * (_WIDTH - 2) + "╗")
    print("║" + " ADVANCED LINKEDIN JOB SEARCHER ".center(_WIDTH - 2) + "║")
    print("╚" + "═" * (_WIDTH - 2) + "╝")
    print()

    keywords = input("  🔍  Job title / keywords: ").strip()
    if not keywords:
        raise ValueError("Keywords are required.")
    
    
    location     = input("  📍  Location (city, country, or 'Remote'): ").strip() or "Worldwide"
    secs_or_hours = input("⏱ Custom time window in seconds? (y/n)").lower().startswith('y')

    date_filter = None
    custom_secs = None

    if not secs_or_hours:
        date_filter  = _pick("📅  Date posted:", _DATE_OPTIONS) or "any"
    else:
        custom_secs  = _prompt_int("⏱   Custom time window in seconds? (e.g. 3600 = 1h)") or 1800
    experience   = _pick("🎓  Experience level:", _EXPERIENCE_OPTIONS, multi=True)
    job_type     = _pick("💼  Job type:",         _JOB_TYPE_OPTIONS,    multi=True)
    work_type    = _pick("🏠  Work type:",         _WORK_TYPE_OPTIONS,   multi=True)
    sort_by      = _pick("🔢  Sort by:",           _SORT_OPTIONS)        or "recent"
    easy_apply      = _prompt_bool("⚡  Easy Apply only?")
    actively_hiring = _prompt_bool("🟢  Actively Hiring only?")
    distance        = _prompt_int("📏  Search radius in miles? (e.g. 25, 50) — Enter to skip")
    max_results     = _prompt_int("📊  Max results", default=25) or 25
    fetch_desc      = not _prompt_bool("📝  Skip fetching full descriptions (faster)?", default=False)
    headless        = not _prompt_bool("🖥   Show browser window?", default=False)

    config = SearchConfig(
        keywords=keywords,
        location=location,
        date_filter=date_filter,
        custom_seconds=custom_secs,
        experience=experience,
        job_type=job_type,
        work_type=work_type,
        easy_apply=easy_apply,
        actively_hiring=actively_hiring,
        sort_by=sort_by,
        distance=distance,
    )
    return config, max_results, fetch_desc, headless


# ─────────────────────────────────────────────
#  CLI argument parser
# ─────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Advanced LinkedIn Job Searcher (Playwright)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES
  python3 -m linkedin_scraper -k "Python Developer" -l "London"

  python3 -m linkedin_scraper -k "Data Scientist" -l "Remote" \\
    --date 24h --experience mid director --job-type fulltime \\
    --work-type remote hybrid --easy-apply --sort recent --max 30

  python3 -m linkedin_scraper -k "DevOps Engineer" -l "Berlin" --seconds 7200

DATE OPTIONS     : 1h / 2h / 3h / 6h / 12h / 24h / 3d / week / month / any
EXPERIENCE       : internship / entry / associate / mid / director / executive
JOB TYPE         : fulltime / parttime / contract / temporary / internship
WORK TYPE        : onsite / remote / hybrid
""",
    )
    parser.add_argument("-k", "--keywords",  help="Job title or keywords")
    parser.add_argument("-l", "--location",  default="", help="Location")
    parser.add_argument("--date",            default="any", dest="date_filter", help="Date filter (default: any)")
    parser.add_argument("--seconds",         type=int, dest="custom_seconds", help="Custom time window in seconds")
    parser.add_argument("--experience",      nargs="*", default=[], help="Experience levels (multi)")
    parser.add_argument("--job-type",        nargs="*", default=[], dest="job_type", help="Job types (multi)")
    parser.add_argument("--work-type",       nargs="*", default=[], dest="work_type", help="Work types (multi)")
    parser.add_argument("--easy-apply",      action="store_true", help="Easy Apply only")
    parser.add_argument("--active",          action="store_true", dest="actively_hiring", help="Actively Hiring only")
    parser.add_argument("--sort",            default="recent", choices=["recent", "relevant"], dest="sort_by")
    parser.add_argument("--distance",        type=int, help="Search radius in miles")
    parser.add_argument("--max",             type=int, default=25, dest="max_results")
    parser.add_argument("--no-headless",     action="store_true", help="Show browser window")
    parser.add_argument("--no-descriptions", action="store_true", help="Skip fetching descriptions")
    parser.add_argument("--json-only",       action="store_true", help="Output raw JSON only")
    return parser


def args_to_config(args: argparse.Namespace) -> SearchConfig:
    return SearchConfig(
        keywords=args.keywords,
        location=args.location,
        date_filter=args.date_filter,
        custom_seconds=args.custom_seconds,
        experience=args.experience,
        job_type=args.job_type,
        work_type=args.work_type,
        easy_apply=args.easy_apply,
        actively_hiring=args.actively_hiring,
        sort_by=args.sort_by,
        distance=args.distance,
    )


# ─────────────────────────────────────────────
#  Helper prompts
# ─────────────────────────────────────────────

def _pick(prompt: str, options: dict[str, str], multi: bool = False) -> list[str] | str | None:
    keys = list(options.keys())
    print(f"\n  {prompt}")
    for i, (key, label) in enumerate(options.items(), start=1):
        print(f"    {i:2}. {label:<28} [{key}]")

    suffix = "Numbers separated by commas, or Enter to skip." if multi else "Enter to skip."
    print(f"    {suffix}")
    raw = input("  ➤ ").strip()

    if not raw:
        return [] if multi else None

    chosen = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit() and 1 <= int(part) <= len(keys):
            chosen.append(keys[int(part) - 1])
        elif part in keys:
            chosen.append(part)

    if multi:
        return chosen
    return chosen[0] if chosen else None


def _prompt_bool(label: str, default: bool = False) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    print(f"\n  {label} {hint}: ", end="")
    answer = input().strip().lower()
    if not answer:
        return default
    return answer == "y"


def _prompt_int(label: str, default: int | None = None) -> int | None:
    hint = f" [default: {default}]" if default is not None else " — Enter to skip"
    print(f"\n  {label}{hint}: ", end="")
    raw = input().strip()
    if raw.isdigit():
        return int(raw)
    return default
import json
from datetime import datetime

from .config import JobListing, SearchConfig

_WIDTH = 70


def display_results(jobs: list[JobListing], config: SearchConfig) -> None:
    _print_header(config, len(jobs))

    if not jobs:
        print("  ❌  No results found.")
        _print_footer()
        return

    for i, job in enumerate(jobs, start=1):
        _print_job(i, job)

    _print_footer()
    _save_json(jobs, config)


def _print_header(config: SearchConfig, total: int) -> None:
    print()
    print("=" * _WIDTH)
    print(f"  {'LINKEDIN JOB SEARCH RESULTS':^{_WIDTH - 4}}")
    print("═" * _WIDTH)

    rows = [
        ("Keywords",       config.keywords),
        ("Location",       config.location),
        ("Date filter",    config.date_filter),
        ("Experience",     ", ".join(config.experience) or "all"),
        ("Job type",       ", ".join(config.job_type) or "all"),
        ("Work type",      ", ".join(config.work_type) or "all"),
        ("Easy Apply",     "✓" if config.easy_apply else "—"),
        ("Active hiring",  "✓" if config.actively_hiring else "—"),
        ("Sort by",        config.sort_by),
        ("Distance",       f"{config.distance} mi" if config.distance else "—"),
        ("Results",        str(total)),
    ]
    for label, value in rows:
        print(f"  {label:<17} {value}")
    print("-" * _WIDTH)


def _print_job(index: int, job: JobListing) -> None:
    ea_badge = " ⚡ Easy Apply" if job.easy_apply else ""
    print()
    print(f"  [{index:02d}] {job.title}{ea_badge}")
    print(f"       🏢  {job.company or 'N/A'}")
    print(f"       📍  {job.location or 'N/A'}")
    print(f"       📅  {job.date_posted or 'N/A'}")
    print(f"       👥  {job.num_applicants or 'N/A'}")
    if job.url:
        print(f"       🔗  {job.url}")
    if job.description:
        preview = _description_preview(job.description)
        print(f"       📝  {preview}")


def _description_preview(description: str, max_chars: int = 200) -> str:
    lines = [l.strip() for l in description.splitlines() if l.strip()][:3]
    preview = " • ".join(lines)
    return preview[:max_chars] + "…" if len(preview) > max_chars else preview


def _print_footer() -> None:
    print()
    print("-" * _WIDTH)


def _save_json(jobs: list[JobListing], config: SearchConfig) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"linkedin_jobs_{timestamp}.json"

    output = {
        "meta": {
            **config.__dict__,
            "scraped_at": datetime.now().isoformat(),
            "total": len(jobs),
        },
        "jobs": [j.to_dict() for j in jobs],
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  💾  Saved {len(jobs)} jobs → {filename}")
    print("═" * _WIDTH)
    print()
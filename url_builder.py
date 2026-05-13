from urllib.parse import quote_plus

from .config import (
    DATE_FILTERS, EXPERIENCE_LEVELS, JOB_TYPES,
    WORK_TYPES, SORT_BY, SearchConfig,
)

BASE_URL = "https://www.linkedin.com/jobs/search/?"
 
 
def build_url(config: SearchConfig) -> str:
    """Build a LinkedIn job-search URL from a SearchConfig."""
    params: dict[str, str] = {
        "keywords": config.keywords,
    }
 
    if config.location:
        params["location"] = config.location
 
    # ── Time filter ──────────────────────────────────────────────────────
    if config.custom_seconds:
        params["f_TPR"] = f"r{config.custom_seconds}"
    elif config.date_filter != "any":
        if tpr := DATE_FILTERS.get(config.date_filter):
            params["f_TPR"] = tpr
 
    # ── Multi-select filters ─────────────────────────────────────────────
    _add_multi(params, "f_E",  config.experience, EXPERIENCE_LEVELS)
    _add_multi(params, "f_JT", config.job_type,   JOB_TYPES)
    _add_multi(params, "f_WT", config.work_type,  WORK_TYPES)
 
    # ── Toggle flags ─────────────────────────────────────────────────────
    if config.easy_apply:
        params["f_EA"] = "true"
    if config.actively_hiring:
        params["f_AL"] = "true"
 
    # ── Sort & distance ──────────────────────────────────────────────────
    params["sortBy"] = SORT_BY.get(config.sort_by, "DD")
    if config.distance:
        params["distance"] = str(config.distance)
 
    return BASE_URL + "&".join(
        f"{k}={quote_plus(v)}" for k, v in params.items()
    )
 
 
def _add_multi(params: dict, key: str, selected: list[str], mapping: dict[str, str]) -> None:
    """Encode a multi-select filter as comma-separated codes."""
    codes = [mapping[s] for s in selected if s in mapping]
    if codes:
        params[key] = "%2C".join(codes)

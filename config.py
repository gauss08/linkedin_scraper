from dataclasses import dataclass, field
 
# ─────────────────────────────────────────────
#  Filter value maps  (LinkedIn URL params)
# ─────────────────────────────────────────────
 
DATE_FILTERS: dict[str, str] = {
    "1h":    "r3600",
    "2h":    "r7200",
    "3h":    "r10800",
    "6h":    "r21600",
    "12h":   "r43200",
    "24h":   "r86400",
    "3d":    "r259200",
    "week":  "r604800",
    "month": "r2592000",
    "any":   "",
}
 
EXPERIENCE_LEVELS: dict[str, str] = {
    "internship": "1",
    "entry":      "2",
    "associate":  "3",
    "mid":        "4",
    "director":   "5",
    "executive":  "6",
}
 
JOB_TYPES: dict[str, str] = {
    "fulltime":   "F",
    "parttime":   "P",
    "contract":   "C",
    "temporary":  "T",
    "internship": "I",
}
 
WORK_TYPES: dict[str, str] = {
    "onsite": "1",
    "remote": "2",
    "hybrid": "3",
}
 
SORT_BY: dict[str, str] = {
    "relevant": "R",
    "recent":   "DD",
}
 
# ─────────────────────────────────────────────
#  Typed data structures
# ─────────────────────────────────────────────
 
@dataclass
class SearchConfig:
    keywords: str
    location: str               = "Worldwide"
    date_filter: str            = "any"
    experience: list[str]       = field(default_factory=list)
    job_type: list[str]         = field(default_factory=list)
    work_type: list[str]        = field(default_factory=list)
    easy_apply: bool            = False
    actively_hiring: bool       = False
    sort_by: str                = "recent"
    distance: int | None        = None
    custom_seconds: int | None  = None
 
 
@dataclass
class JobListing:
    title: str            = ""
    company: str          = ""
    location: str         = ""
    date_posted: str      = ""
    date_iso: str         = ""
    easy_apply: bool      = False
    url: str              = ""
    description: str      = ""
    num_applicants: str   = ""
    additional_info: str  = ""
 
    def to_dict(self) -> dict:
        return self.__dict__.copy()
 

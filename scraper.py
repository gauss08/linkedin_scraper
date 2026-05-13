import asyncio
import logging
import re
 
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
 
from .config import JobListing
 
logger = logging.getLogger(__name__)
 
# ─────────────────────────────────────────────
#  Selector constants
# ─────────────────────────────────────────────
 
_MODAL_DISMISS_SELECTORS = [
    "button[aria-label='Dismiss']",
    "button[aria-label='dismiss']",
    ".sign-in-modal__outlet-btn",
    ".contextual-sign-in-modal__modal-dismiss-btn",
    "[data-tracking-control-name*='dismiss']",
    "[data-tracking-control-name*='modal_dismiss']",
    "#artdeco-global-alert-container button",
    ".modal__dismiss",
    "button[data-modal-dismiss]",
    ".artdeco-modal__dismiss",
    "[aria-label='Close']",
    "[aria-label='close']",
]
 
_DESCRIPTION_SELECTORS: list[tuple[str, int]] = [
    (".show-more-less-html__markup",                        80),
    (".jobs-description-content__text",                     80),
    (".jobs-description__content .jobs-box__html-content",  80),
    (".jobs-description__content",                          80),
    (".description__text--rich",                            80),
    (".description__text",                                  80),
    ("[class*='jobs-description']",                        150),
]
 
_EXPAND_SELECTORS = [
    "button.show-more-less-html__button--more",
    "button.show-more-less-html__button",
    "button.jobs-description__footer-button",
    "footer.show-more-less-html button",
]
 
_PANEL_ANCHOR_SELECTORS = [
    ".show-more-less-html",
    ".jobs-description",
    ".description__text",
    ".jobs-description-content__text",
    ".job-details-jobs-unified-top-card__job-insight",
]
 
_APPLICANT_SELECTORS = [
    "figcaption.num-applicants__caption",
    ".num-applicants__caption",
    "[class*='num-applicants']",
    ".jobs-unified-top-card__applicant-count",
    "[class*='applicant-count']",
]
 
_CRITERIA_SELECTORS = [
    "ul.description__job-criteria-list",
    ".job-details-jobs-unified-top-card__job-insight",
    "[class*='job-criteria']",
]
 
_CARD_SELECTORS = [
    "ul.jobs-search__results-list li",
    "[data-entity-urn]",               # fallback
]
 
 
# ─────────────────────────────────────────────
#  Main scraper class
# ─────────────────────────────────────────────
 
class LinkedInScraper:
    def __init__(self, headless: bool = True, fetch_descriptions: bool = True):
        self.headless = headless
        self.fetch_descriptions = fetch_descriptions
 
    async def scrape(self, url: str, max_results: int = 25) -> list[JobListing]:
        jobs: list[JobListing] = []
 
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1200, "height": 800},
                locale="en-US",
            )
            page = await context.new_page()
 
            try:
                logger.info("Opening: %s", url)
                await page.goto(url, wait_until="domcontentloaded", timeout=20_000)
                await page.wait_for_timeout(3_500)
                await self._dismiss_modal(page)
 
                cards = await self._load_cards(page, max_results)
                logger.info("Found %d raw cards, extracting up to %d", len(cards), max_results)
 
                for idx, card in enumerate(cards[:max_results], start=1):
                    job = await self._parse_card(page, card, idx, max_results)
                    if job:
                        jobs.append(job)
 
            except PlaywrightTimeoutError:
                logger.error("Timeout – LinkedIn took too long to respond.")
            except Exception as e:
                logger.error("Unexpected error: %s", e)
            finally:
                await browser.close()
 
        return jobs
 
    # ─────────────────────────────────────────
    #  Card loading
    # ─────────────────────────────────────────
 
    async def _load_cards(self, page, max_results: int):
        """Scroll until we have enough cards or the list stops growing."""
        prev_count = 0
        for _ in range(20):
            await page.keyboard.press("End")
            await page.wait_for_timeout(1_100)
            cards = await page.locator(_CARD_SELECTORS[0]).all()
            if len(cards) >= max_results or len(cards) == prev_count:
                break
            prev_count = len(cards)
 
        cards = await page.locator(_CARD_SELECTORS[0]).all()
        if not cards:
            cards = await page.locator(_CARD_SELECTORS[1]).all()
        return cards
 
    # ─────────────────────────────────────────
    #  Per-card parsing
    # ─────────────────────────────────────────
 
    async def _parse_card(self, page, card, idx: int, total: int) -> JobListing | None:
        try:
            job = JobListing(
                title    = await _get_text(card, ".top-card-layout__title",   "h3.base-search-card__title", ".job-search-card__title", "h3"),
                company  = await _get_text(card, ".topcard__org-name-link",   "h4.base-search-card__subtitle", ".job-search-card__company-name", "h4"),
                location = await _get_text(card, ".topcard__flavor",          ".job-search-card__location", "span.job-search-card__location"),
            )
 
            if not job.title:
                return None
 
            # Date posted
            try:
                time_el = card.locator("time").first
                job.date_posted = (await time_el.inner_text(timeout=500)).strip()
                if dt_attr := await time_el.get_attribute("datetime"):
                    job.date_iso = dt_attr
            except Exception:
                pass
 
            # Easy Apply badge
            try:
                badges = await card.locator(".job-search-card__easy-apply-label, .result-benefits").all_inner_texts()
                job.easy_apply = any("easy apply" in b.lower() for b in badges)
            except Exception:
                pass
 
            # URL
            try:
                if href := await card.locator("a").first.get_attribute("href"):
                    job.url = href.split("?")[0]
            except Exception:
                pass
 
            # Detail panel
            if self.fetch_descriptions:
                logger.info("[%02d/%d] %s — fetching description…", idx, total, job.title[:55])
                try:
                    link = card.locator("a").first
                    await link.scroll_into_view_if_needed()
                    await link.dispatch_event("click")
                    await page.wait_for_timeout(400)
                    await self._dismiss_modal(page)
 
                    detail = await self._read_detail_panel(page)
                    job.description     = detail["description"]
                    job.num_applicants  = detail["num_applicants"]
                    additional_info = detail["additional_info"].split('\n')

                    for i in range(0,len(additional_info),2):
                        job.additional_info[additional_info[i]] = additional_info[i+1]
 
                    # LinkedIn navigates away on the first card click; go back to restore the list.
                    if idx == 1:
                        await page.go_back(wait_until="domcontentloaded", timeout=5_000)
                except Exception as e:
                    logger.debug("Failed to fetch description for card %d: %s", idx, e)
            else:
                logger.info("[%02d/%d] %s", idx, total, job.title[:60])
 
            return job
 
        except Exception as e:
            logger.debug("Failed to parse card %d: %s", idx, e)
            return None
 
    # ─────────────────────────────────────────
    #  Detail panel
    # ─────────────────────────────────────────
 
    async def _read_detail_panel(self, page) -> dict:
        async def _inner():
            result = {"description": "", "num_applicants": "", "additional_info": ""}
 
            # 1. Wait for panel
            panel_found = any(
                [await _wait_for_any(page, _PANEL_ANCHOR_SELECTORS, timeout=4_000)]
            )
            if not panel_found:
                return result
 
            # 2. Expand "Show more"
            await self._expand_description(page)
 
            # 3. Description
            for sel, min_len in _DESCRIPTION_SELECTORS:
                try:
                    els = page.locator(sel)
                    count = await els.count()
                    if not count:
                        continue
                    best = max(
                        [await _safe_inner_text(els.nth(i)) for i in range(min(count, 4))],
                        key=len,
                    )
                    if len(best) >= min_len:
                        result["description"] = best
                        break
                except Exception:
                    continue
 
            # 4. Applicant count
            for sel in _APPLICANT_SELECTORS:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=400):
                        raw = (await el.inner_text(timeout=400)).strip()
                        nums = re.findall(r"[\d,]+", raw)
                        result["num_applicants"] = nums[0].replace(",", "") if nums else raw
                        break
                except Exception:
                    pass
 
            # 5. Job criteria
            for sel in _CRITERIA_SELECTORS:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=400):
                        result["additional_info"] = (await el.inner_text(timeout=500)).strip()
                        break
                except Exception:
                    pass
 
            return result
 
        try:
            return await asyncio.wait_for(_inner(), timeout=10)
        except asyncio.TimeoutError:
            return {"description": "", "num_applicants": "", "additional_info": ""}
 
    async def _expand_description(self, page) -> None:
        for sel in _EXPAND_SELECTORS:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=500):
                    await btn.click()
                    await page.wait_for_timeout(300)
                    return
            except Exception:
                pass
        try:
            btn = page.locator("button", has_text="Show more").first
            if await btn.is_visible(timeout=400):
                await btn.click()
                await page.wait_for_timeout(300)
        except Exception:
            pass
 
    async def _dismiss_modal(self, page) -> None:
        for sel in _MODAL_DISMISS_SELECTORS:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=500):
                    await btn.click()
                    await page.wait_for_timeout(300)
                    return
            except Exception:
                pass
        try:
            await page.keyboard.press("Escape")
        except Exception:
            pass
 
 
# ─────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────
 
async def _get_text(locator, *selectors: str, timeout: int = 500) -> str:
    """Return the first non-empty inner text matched by any selector."""
    for sel in selectors:
        try:
            text = await locator.locator(sel).first.inner_text(timeout=timeout)
            if text.strip():
                return text.strip()
        except Exception:
            pass
    return ""
 
 
async def _safe_inner_text(locator, timeout: int = 600) -> str:
    try:
        return (await locator.inner_text(timeout=timeout)).strip()
    except Exception:
        return ""
 
 
async def _wait_for_any(page, selectors: list[str], timeout: int = 4_000) -> bool:
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=timeout, state="attached")
            return True
        except Exception:
            pass
    return False

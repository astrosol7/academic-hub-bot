"""Download PDF files from a Moodle site into a folder tree that mirrors the LMS.

Usage:
    python tools/download_moodle_pdfs.py https://example.moodle.org

Default download root:
    lms/pdfs/<Course name>/<Section name>/...

Credentials (optional) in .env:
    MOODLE_USERNAME=...
    MOODLE_PASSWORD=...

    python tools/download_moodle_pdfs.py https://example.moodle.org

Options:
    --course-url URL   Crawl only these course pages (repeatable)
    output_dir         Optional second argument: output root (default: <project>/lms/pdfs)
    --quick            Do not follow links beyond the start URL(s)
    --selenium         Use Chrome for JS-heavy pages (requires selenium, webdriver-manager)
    --verbose          Verbose logging
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DEFAULT_OUTPUT_DIR = BASE_DIR / "lms" / "pdfs"

USER_AGENT = "Mozilla/5.0 (compatible; SIT-Academic-Hub-pdf-downloader/1.0)"
PDF_EXTENSIONS = {".pdf"}

INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass
class SimpleHtmlResponse:
    """Minimal stand-in for requests.Response when using Selenium."""

    text: str
    status_code: int = 200
    headers: dict = field(default_factory=lambda: {"Content-Type": "text/html; charset=utf-8"})


@dataclass(frozen=True)
class CrawlTask:
    """URL to fetch and relative folder path under the output root (LMS mirror)."""

    url: str
    path_parts: tuple[str, ...] = ()


def load_json(path: Path, default):
    if not path.is_file():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.warning("Could not read %s: %s", path, e)
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def setup_logging(verbose: bool, log_dir: Path | None = None) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    root = log_dir or DEFAULT_OUTPUT_DIR
    log_path = root / "download_log.txt"
    root.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.is_file():
        return
    with dotenv_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def normalize_url(url: str) -> str:
    if not url:
        return url
    url = url.split("#")[0]
    if url.endswith("/") and url.count("/") > 2:
        return url.rstrip("/")
    return url


def build_default_start_urls(base_url: str) -> list[str]:
    """Start from My courses when given the site root so we discover enrolled courses."""
    b = normalize_url(base_url)
    if "/course/view.php" in b:
        return [b]
    root = b if b.endswith("/") else b + "/"
    my_courses = normalize_url(urljoin(root, "my/courses.php"))
    my_home = normalize_url(urljoin(root, "my/index.php"))
    home = normalize_url(b.rstrip("/"))
    # De-dupe while preserving order
    out: list[str] = []
    for u in (my_courses, my_home, home):
        if u not in out:
            out.append(u)
    return out


def sanitize_path_component(name: str, max_len: int = 120) -> str:
    name = name.strip()
    name = INVALID_FS_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip()
    name = name.strip(". ")
    if not name:
        return "unnamed"
    return name[:max_len]


def is_same_host(url: str, base_netloc: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if not parsed.netloc:
        return True
    return parsed.netloc == base_netloc


def extract_course_view_urls(html: str, page_url: str, base_netloc: str) -> list[str]:
    """Find course/view.php links. Moodle 4 My courses often injects links only in JS/JSON — regex + data-course-id."""
    seen: set[str] = set()
    ordered: list[str] = []

    def add(u: str) -> None:
        u = normalize_url(u)
        if not u or "course/view.php" not in u:
            return
        if "id=" not in u and "course=" not in u:
            return
        if not is_same_host(u, base_netloc):
            return
        if u not in seen:
            seen.add(u)
            ordered.append(u)

    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=True):
        add(urljoin(page_url, a["href"]))
    for el in soup.select("[data-course-id]"):
        cid = el.get("data-course-id") or el.get("data-id")
        if cid and str(cid).isdigit():
            add(urljoin(page_url, f"/course/view.php?id={cid}"))
    for m in re.finditer(
        r"(https?://[^\s\"'<>]+/course/view\.php\?[^\s\"'<>]*id=\d+[^\s\"'<>]*)",
        html,
        re.I,
    ):
        add(m.group(1).rstrip("\",');"))
    for m in re.finditer(
        r'["\']((?:https?:)?//[^"\']*course/view\.php\?[^"\']*id=\d+[^"\']*)["\']',
        html,
        re.I,
    ):
        raw = m.group(1)
        if raw.startswith("//"):
            raw = "https:" + raw
        elif raw.startswith("/"):
            raw = urljoin(page_url, raw)
        elif not raw.startswith("http"):
            raw = urljoin(page_url, raw)
        add(raw)
    return ordered


def is_pdf_link(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path or ""
    if Path(path).suffix.lower() in PDF_EXTENSIONS:
        return True
    q = parsed.query.lower()
    if ".pdf" in q:
        return True
    if "pluginfile.php" in path:
        return True
    return False


def is_pdf_content(session: requests.Session, url: str) -> bool:
    """Moodle often blocks HEAD or returns wrong Content-Type; sniff bytes."""
    try:
        head_resp = session.head(url, timeout=30, allow_redirects=True)
        ct = head_resp.headers.get("Content-Type", "").lower()
        if "application/pdf" in ct:
            return True
    except Exception:
        pass
    try:
        with session.get(url, stream=True, timeout=60, allow_redirects=True) as r:
            if r.status_code >= 400:
                return False
            chunk = next(r.iter_content(chunk_size=8), b"")
            return chunk.startswith(b"%PDF")
    except Exception:
        return False


def get_filename_from_response(response: requests.Response, url: str) -> str:
    content_disposition = response.headers.get("Content-Disposition", "")
    if "filename=" in content_disposition.lower():
        filename = re.split(r"filename\*=|filename=", content_disposition, flags=re.IGNORECASE)[-1]
        filename = filename.strip(" \"'\r\n")
        filename = filename.split(";")[0]
        if filename:
            return filename
    parsed = urlparse(url)
    name = Path(parsed.path).name
    if name:
        return name
    return "downloaded.pdf"


def folder_for_task(output_dir: Path, path_parts: tuple[str, ...]) -> Path:
    p = output_dir
    for part in path_parts:
        p = p / sanitize_path_component(part)
    p.mkdir(parents=True, exist_ok=True)
    return p


def download_pdf(
    session: requests.Session,
    url: str,
    output_dir: Path,
    path_parts: tuple[str, ...],
) -> Path:
    folder = folder_for_task(output_dir, path_parts)
    response = session.get(url, stream=True, timeout=120, allow_redirects=True)
    response.raise_for_status()
    first = next(response.iter_content(chunk_size=16384), b"")
    if not first.startswith(b"%PDF"):
        low = first.lower()
        if low.lstrip().startswith(b"<") or b"<html" in low[:4000]:
            raise ValueError(
                f"Not a PDF (got HTML — check login or URL): {url}"
            )
        raise ValueError(f"Not a PDF (missing %PDF header): {url}")
    filename = get_filename_from_response(response, url)
    if not filename.lower().endswith(".pdf"):
        filename = f"{Path(filename).stem}.pdf"
    dest = folder / Path(filename).name
    counter = 1
    while dest.exists():
        dest = folder / f"{dest.stem}_{counter}{dest.suffix}"
        counter += 1
    logging.info("Downloading %s -> %s", url, dest)
    with dest.open("wb") as f:
        f.write(first)
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    return dest


def extract_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    seen: list[str] = []
    for tag in soup.find_all(["a", "iframe", "embed", "object", "source"]):
        url_attr = tag.get("href") or tag.get("src") or tag.get("data")
        if url_attr:
            seen.append(urljoin(base_url, url_attr))
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(
            p in href
            for p in (
                "/mod/resource/view.php",
                "/mod/folder/view.php",
                "/mod/assign/view.php",
                "/mod/quiz/view.php",
                "/mod/book/view.php",
                "/mod/page/view.php",
            )
        ):
            seen.append(urljoin(base_url, href))
    for m in re.finditer(r"(?P<url>https?://[^\s\"'<>]+\.pdf[^\s\"'<>]*)", html, flags=re.IGNORECASE):
        seen.append(urljoin(base_url, m.group("url")))
    return list(dict.fromkeys(seen))


def parse_course_name(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        t = h1.get_text(strip=True)
        if t:
            return sanitize_path_component(t)
    title = soup.find("title")
    if title:
        t = title.get_text(strip=True)
        t = re.sub(r"\s*[|:]\s*Moodle.*$", "", t, flags=re.I).strip()
        if t:
            return sanitize_path_component(t)
    return "Course"


def section_title_from_li(li) -> str:
    for sel in (".sectionname", "h3.sectionname", "h2.sectionname", "h4.sectionname", ".section-heading"):
        el = li.select_one(sel)
        if el:
            t = el.get_text(strip=True)
            if t:
                return sanitize_path_component(t)
    sid = li.get("id") or ""
    if sid.startswith("section-"):
        return sanitize_path_component(sid.replace("section-", "section_"))
    return "Section"


def _mod_links_in_scope(scope) -> Iterable[tuple[str, str]]:
    """Yield (href, link_text) for activity links."""
    for a in scope.select('a[href*="/mod/"]'):
        href = a.get("href")
        if not href or "/mod/forum/" in href:
            continue
        if "/mod/url/" in href and "redirect" in href:
            continue
        label = a.get_text(strip=True) or "activity"
        yield href, label


def iter_moodle_course_activity_tasks(
    html: str,
    page_url: str,
    course_folder: str,
) -> Iterable[CrawlTask]:
    """Yield crawl tasks for each activity link under a course main page, preserving section folders."""
    soup = BeautifulSoup(html, "html.parser")
    sections = soup.select('li[id^="section-"], li.section')
    if not sections:
        main = soup.select_one("#region-main, [role='main'], #page, #page-content, .course-content")
        if main:
            sections = main.select('li[id^="section-"], li.section, li[id^="section"]')
    if not sections:
        scope = soup.select_one("#region-main, [role='main'], .course-content") or soup
        for href, label in _mod_links_in_scope(scope):
            full = normalize_url(urljoin(page_url, href))
            yield CrawlTask(full, (course_folder, sanitize_path_component(label)))
        return

    for li in sections:
        sec_name = section_title_from_li(li)
        for href, label in _mod_links_in_scope(li):
            full = normalize_url(urljoin(page_url, href))
            act = sanitize_path_component(label)
            yield CrawlTask(full, (course_folder, sec_name, act))


def login_moodle(session: requests.Session, base_url: str, username: str, password: str) -> bool:
    login_url = urljoin(base_url, "/login/index.php")
    resp = session.get(login_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form", id="login") or soup.find("form", action=re.compile(r"login", re.I))
    if not form:
        form = soup.find("form")
    if not form or not form.get("action"):
        logging.error("Could not find login form on Moodle login page.")
        return False
    action = urljoin(login_url, form["action"])
    data = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        data[name] = inp.get("value", "")
    data["username"] = username
    data["password"] = password
    headers = {"User-Agent": USER_AGENT, "Referer": login_url}
    post = session.post(action, data=data, headers=headers, timeout=30)
    if post.status_code not in (200, 302):
        logging.error("Login POST returned status %s", post.status_code)
        return False
    if "login" in post.url and "error" in post.text.lower():
        logging.error("Login failed. Check credentials.")
        return False
    logging.info("Moodle login succeeded.")
    return True


def get_page_with_selenium(url: str, username: str, password: str, site_base: str) -> str | None:
    if not SELENIUM_AVAILABLE:
        raise ImportError("Install selenium and webdriver-manager for --selenium")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    try:
        login_page = urljoin(site_base.rstrip("/") + "/", "login/index.php")
        driver.get(login_page)
        wait = WebDriverWait(driver, 20)
        user_el = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        driver.find_element(By.NAME, "password").clear()
        user_el.clear()
        user_el.send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        for sel in ("input[type='submit']", "button[type='submit']", "#loginbtn", ".btn-primary"):
            try:
                driver.find_element(By.CSS_SELECTOR, sel).click()
                break
            except Exception:
                continue
        wait.until(lambda d: d.current_url and "/login/index.php" not in d.current_url)
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        if "my/courses" in url or "/my/index.php" in url:
            try:
                WebDriverWait(driver, 25).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="course/view.php"]')) > 0
                    or len(d.find_elements(By.CSS_SELECTOR, "[data-course-id]")) > 0
                )
            except Exception:
                logging.debug("Timeout waiting for course cards; continuing with partial DOM.")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        import time

        time.sleep(3)
        return driver.page_source
    finally:
        driver.quit()


def collect_pdf_hrefs_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    for a in soup.find_all("a", href=True):
        h = a["href"]
        if "pluginfile.php" in h or h.lower().endswith(".pdf"):
            out.append(urljoin(base_url, h))
    for tag in soup.find_all(["iframe", "embed", "object"]):
        u = tag.get("src") or tag.get("data")
        if u:
            out.append(urljoin(base_url, u))
    for m in re.finditer(r'["\']([^"\']*pluginfile\.php[^"\']*)["\']', html, re.I):
        out.append(urljoin(base_url, m.group(1)))
    return list(dict.fromkeys(out))


def crawl_and_download(
    base_url: str,
    output_dir: Path,
    session: requests.Session,
    *,
    urls_to_crawl: list[str] | None = None,
    quick: bool = False,
    use_selenium: bool = False,
    username: str = "",
    password: str = "",
    verbose: bool = False,
) -> None:
    base = normalize_url(base_url)
    parsed_base = urlparse(base)
    base_netloc = parsed_base.netloc

    state_dir = output_dir / ".lms_download_state"
    downloaded: set[str] = set(load_json(state_dir / "downloaded_urls.json", []))
    site_structure: dict = load_json(state_dir / "site_structure.json", {})

    visited: set[str] = set()
    if urls_to_crawl:
        start_urls = [normalize_url(u) for u in urls_to_crawl]
    else:
        start_urls = build_default_start_urls(base)
    queue: deque[CrawlTask] = deque(CrawlTask(u, ()) for u in start_urls)

    def fetch(url: str) -> tuple[str, requests.Response | None]:
        if use_selenium and username and password:
            try:
                html = get_page_with_selenium(url, username, password, base)
                if html is None:
                    return url, None
                return url, SimpleHtmlResponse(html)
            except Exception as e:
                logging.warning("Selenium fetch failed for %s: %s", url, e)
        try:
            return url, session.get(url, timeout=60)
        except requests.RequestException as e:
            logging.warning("GET failed %s: %s", url, e)
            return url, None

    while queue:
        task = queue.popleft()
        url = normalize_url(task.url)
        path_parts = task.path_parts
        if not url or url in visited:
            continue
        visited.add(url)
        if verbose:
            print(f"Visit ({len(queue)} queued): {url} -> /{'/'.join(path_parts)}")

        _, resp = fetch(url)
        if resp is None:
            continue
        if resp.status_code >= 400:
            logging.warning("HTTP %s for %s", resp.status_code, url)
            continue

        ct = (resp.headers.get("Content-Type") or "").lower()
        if "application/pdf" in ct or (is_pdf_link(url) and "text/html" not in ct):
            if url in downloaded:
                continue
            try:
                download_pdf(session, url, output_dir, path_parts)
                downloaded.add(url)
                save_json(state_dir / "downloaded_urls.json", list(downloaded))
            except Exception as e:
                logging.error("PDF download failed %s: %s", url, e)
            continue

        text = getattr(resp, "text", None) or (
            resp.content.decode("utf-8", errors="replace") if hasattr(resp, "content") else ""
        )
        soup = BeautifulSoup(text, "html.parser")

        # Course main page: enqueue activities with LMS path (course / section / activity).
        if "/course/view.php" in url:
            course_folder = parse_course_name(soup)
            site_structure[url] = {"type": "course", "name": course_folder}
            if not quick:
                tasks = list(iter_moodle_course_activity_tasks(text, url, course_folder))
                if not tasks:
                    logging.warning(
                        "No activities found on course page (wrong page or theme?). "
                        "Try --course-url with the full course URL, or --selenium if content is JS-only."
                    )
                for t in tasks:
                    folder_for_task(output_dir, t.path_parts)
                for t in tasks:
                    nu = normalize_url(t.url)
                    if nu not in visited:
                        queue.appendleft(CrawlTask(nu, t.path_parts))
                save_json(state_dir / "site_structure.json", site_structure)
            # Also discover PDFs linked directly on course page
            for pu in collect_pdf_hrefs_from_html(text, url):
                if pu in downloaded:
                    continue
                try:
                    if is_pdf_content(session, pu) or is_pdf_link(pu):
                        download_pdf(session, pu, output_dir, (course_folder,))
                        downloaded.add(pu)
                        save_json(state_dir / "downloaded_urls.json", list(downloaded))
                except Exception as e:
                    logging.debug("Skip or fail %s: %s", pu, e)

        # Folder module: extend path with folder title
        if "/mod/folder/view.php" in url:
            h2 = soup.find("h2")
            folder_name = sanitize_path_component(h2.get_text(strip=True) if h2 else "Folder")
            folder_parts = path_parts if path_parts else (folder_name,)
            if path_parts and path_parts[-1] != folder_name:
                folder_parts = (*path_parts, folder_name)
            for a in soup.select('a[href*="pluginfile.php"], a[href$=".pdf"]'):
                href = a.get("href")
                if not href:
                    continue
                fu = normalize_url(urljoin(url, href))
                if fu in downloaded:
                    continue
                try:
                    if is_pdf_content(session, fu) or fu.lower().endswith(".pdf"):
                        download_pdf(session, fu, output_dir, folder_parts)
                        downloaded.add(fu)
                        save_json(state_dir / "downloaded_urls.json", list(downloaded))
                except Exception as e:
                    logging.debug("Folder file %s: %s", fu, e)

        # Resource / embedded PDFs
        if "/mod/resource/view.php" in url:
            for pu in collect_pdf_hrefs_from_html(text, url):
                if pu in downloaded:
                    continue
                try:
                    if is_pdf_content(session, pu) or is_pdf_link(pu):
                        download_pdf(session, pu, output_dir, path_parts)
                        downloaded.add(pu)
                        save_json(state_dir / "downloaded_urls.json", list(downloaded))
                except Exception as e:
                    logging.error("Resource PDF %s: %s", pu, e)

        # My courses / dashboard: discover enrolled courses (often JS-rendered in Moodle 4)
        if ("/my/courses.php" in url or "/my/index.php" in url) and not quick:
            course_urls = extract_course_view_urls(text, url, base_netloc)
            if course_urls:
                logging.info("Found %d course link(s) on %s", len(course_urls), url)
            if (
                not course_urls
                and username
                and password
                and not use_selenium
                and SELENIUM_AVAILABLE
            ):
                logging.warning(
                    "No course links in static HTML — Moodle often loads them with JavaScript. "
                    "Retrying with headless Chrome…"
                )
                try:
                    se_html = get_page_with_selenium(url, username, password, base)
                    if se_html:
                        course_urls = extract_course_view_urls(se_html, url, base_netloc)
                        logging.info("After Selenium: found %d course link(s).", len(course_urls))
                except Exception as e:
                    logging.warning("Selenium discovery failed: %s", e)
            elif not course_urls and not SELENIUM_AVAILABLE:
                logging.warning(
                    "No course links in static HTML. Install selenium and webdriver-manager, "
                    "or pass --course-url with a direct course/view.php?id=… link."
                )
            for cu in course_urls:
                nu = normalize_url(cu)
                if nu not in visited:
                    queue.append(CrawlTask(nu, ()))

        # Generic PDF extraction on any HTML page
        for pu in collect_pdf_hrefs_from_html(text, url):
            if pu in downloaded:
                continue
            try:
                if not is_pdf_content(session, pu):
                    continue
                download_pdf(session, pu, output_dir, path_parts)
                downloaded.add(pu)
                save_json(state_dir / "downloaded_urls.json", list(downloaded))
            except Exception:
                pass

        if quick:
            continue

        for link in extract_links(text, url):
            link = normalize_url(link)
            if not link or link in visited:
                continue
            if is_pdf_link(link) and is_same_host(link, base_netloc):
                if link not in downloaded:
                    try:
                        download_pdf(session, link, output_dir, path_parts)
                        downloaded.add(link)
                        save_json(state_dir / "downloaded_urls.json", list(downloaded))
                    except Exception:
                        pass
                continue
            if not is_same_host(link, base_netloc):
                continue
            if any(
                p in link
                for p in (
                    "/course/view.php",
                    "/mod/resource/view.php",
                    "/mod/folder/view.php",
                    "/mod/assign/view.php",
                    "/mod/quiz/view.php",
                    "/mod/book/view.php",
                    "/mod/page/view.php",
                )
            ):
                if "#" in link:
                    continue
                if link not in visited:
                    queue.append(CrawlTask(link, path_parts))

    logging.info("Finished. Tracked %d unique PDF URLs in state.", len(downloaded))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download PDFs from a Moodle site into lms/pdfs mirror.")
    p.add_argument("base_url", help="Base Moodle URL, e.g. https://lms.example.edu")
    p.add_argument(
        "output_dir",
        nargs="?",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output root (default: {DEFAULT_OUTPUT_DIR})",
    )
    p.add_argument("--username", help="Moodle username (overrides MOODLE_USERNAME in .env)")
    p.add_argument("--password", help="Moodle password (overrides MOODLE_PASSWORD in .env)")
    p.add_argument("--course-url", action="append", help="Only crawl these course URLs (repeatable)")
    p.add_argument("--quick", action="store_true", help="Only process start URL(s), no deep crawl")
    p.add_argument("--selenium", action="store_true", help="Use headless Chrome for fetches (after login)")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose progress on stdout")
    return p.parse_args()


def main() -> int:
    load_dotenv(ENV_FILE)
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(args.verbose, output_dir)

    host = urlparse(args.base_url).netloc.lower()
    if not host or host == "your-lms.example.edu":
        logging.error(
            "Use your real Moodle base URL (not a placeholder), e.g. https://lms.brightergeneration.info"
        )
        return 1

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    username = args.username or os.environ.get("MOODLE_USERNAME", "")
    password = args.password or os.environ.get("MOODLE_PASSWORD", "")
    if username and password:
        if not login_moodle(session, args.base_url, username, password):
            logging.warning("Continuing without authenticated session.")

    if args.selenium and not SELENIUM_AVAILABLE:
        logging.error("Install selenium and webdriver-manager: pip install selenium webdriver-manager")
        return 1

    crawl_and_download(
        args.base_url,
        output_dir,
        session,
        urls_to_crawl=[normalize_url(u) for u in args.course_url] if args.course_url else None,
        quick=args.quick,
        use_selenium=args.selenium,
        username=username,
        password=password,
        verbose=args.verbose,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

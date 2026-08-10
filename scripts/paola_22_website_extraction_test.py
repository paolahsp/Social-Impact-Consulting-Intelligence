import argparse
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse


PAGE_CANDIDATES = [
    ("/", "home"),
    ("/about", "about"),
    ("/our-work", "programs"),
    ("/impact", "impact"),
    ("/financials", "financials"),
    ("/annual-reports", "reports"),
    ("/donate", "fundraising"),
    ("/contact", "contact"),
]


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_website(value):
    value = value.strip()
    if not value.startswith(("http://", "https://")):
        value = f"https://{value}"
    parsed = urlparse(value)
    if not parsed.hostname:
        raise ValueError("website must be an absolute HTTP(S) URL")
    return f"{parsed.scheme}://{parsed.netloc}"


def jina_url(page_url):
    parsed = urlparse(page_url)
    return f"https://r.jina.ai/http://{parsed.netloc}{parsed.path or '/'}"


def fetch(page_url, timeout):
    request = urllib.request.Request(
        jina_url(page_url),
        headers={"Accept": "text/plain", "User-Agent": "SocialImpactConsultingIntelligence/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        text = response.read().decode("utf-8", errors="replace")
    if len(text.strip()) < 80 or re.search(r"Target URL returned error|404 Not Found|Failed to fetch", text, re.I):
        raise ValueError("Jina Reader returned no usable page content")
    title_match = re.search(r"^Title:\s*(.+)$", text, re.M | re.I)
    content = re.sub(r"^(Title|URL Source|Published Time):.*$", "", text, flags=re.M | re.I)
    content = re.sub(r"^Markdown Content:\s*$", "", content, flags=re.M | re.I).strip()
    return (title_match.group(1).strip() if title_match else "", content[:16000])


def select_signals(text, terms, limit=5):
    sentences = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text))
    selected = []
    for sentence in sentences:
        lower = sentence.lower().strip()
        if 40 <= len(sentence) <= 360 and any(term in lower for term in terms):
            selected.append(sentence.strip())
        if len(selected) >= limit:
            break
    return selected


def run(args):
    website = normalize_website(args.website)
    run_context = {
        "run_id": args.run_id,
        "organization": {"name": args.org_name, "website": website, "country": args.country, "mission_area": None},
        "current_challenge": None,
        "uploaded_document_refs": [],
        "status": "created",
        "started_at": now(),
        "errors": [],
    }
    sources = []
    errors = []
    for index, (path, page_type) in enumerate(PAGE_CANDIDATES, start=1):
        page_url = urljoin(f"{website}/", path.lstrip("/"))
        try:
            if args.simulate_failure:
                raise urllib.error.URLError("simulated inaccessible website")
            title, content = fetch(page_url, args.timeout)
            sources.append(
                {
                    "source_id": f"SRC-WEB-{index:03d}",
                    "title": title or f"{args.org_name} — {page_type}",
                    "url": page_url,
                    "source_type": f"official_website_{page_type}",
                    "publisher": args.org_name,
                    "publication_date": None,
                    "retrieved_at": now(),
                    "authority_level": "official",
                    "freshness": "unknown",
                    "is_official": True,
                    "extraction_provider": "jina_reader",
                    "page_type": page_type,
                    "useful_content": content,
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "stage": "EXTRACTION_REQUEST__JINA_READER",
                    "error_type": "request_failure",
                    "page_url": page_url,
                    "message": str(exc),
                }
            )
    all_content = " ".join(source["useful_content"] for source in sources)
    context = {
        "mission_signals": select_signals(all_content, ["mission", "purpose", "our goal", "our vision"]),
        "program_signals": select_signals(all_content, ["program", "how it works", "what we do", "cash transfer", "initiative"]),
        "impact_signals": select_signals(all_content, ["impact", "evidence", "research", "results", "outcomes"]),
        "fundraising_signals": select_signals(all_content, ["donate", "donor", "fundraising", "contribution", "give now"]),
        "stakeholder_entry_points": [
            {"page_type": source["page_type"], "title": source["title"], "url": source["url"]}
            for source in sources
            if source["page_type"] in {"fundraising", "contact", "programs"}
        ],
        "report_links": [
            {"title": source["title"], "url": source["url"], "page_type": source["page_type"]}
            for source in sources
            if source["page_type"] in {"financials", "reports", "impact"}
        ],
    }
    return {
        "run_context": run_context,
        "controlled_state": "success" if sources else "request_failure",
        "extraction_provider": "jina_reader",
        "pages_attempted": len(PAGE_CANDIDATES),
        "sources": sources,
        "website_context": context,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description="Repository harness for Paola workflow 22")
    parser.add_argument("--org-name", required=True)
    parser.add_argument("--website", required=True)
    parser.add_argument("--country", required=True)
    parser.add_argument("--run-id", default="RUN-PAOLA-22-LOCAL")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--simulate-failure", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"controlled_state={payload['controlled_state']}")
    print(f"pages_attempted={payload['pages_attempted']}")
    print(f"sources={len(payload['sources'])}")
    print(f"errors={len(payload['errors'])}")


if __name__ == "__main__":
    main()

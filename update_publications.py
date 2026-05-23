#!/usr/bin/env python3

'''
update_publications.py

Semi-automated publication updater for a Jekyll academic website.

Goals:
- Fetch papers from arXiv
- Compare against existing entries in research.md
- Detect NEW papers only
- NEVER overwrite existing manually curated metadata
- Print suggested {% include article.html ... %} blocks
- Human reviews before copy/paste into website

Usage:
    python update_publications.py

Requirements:
    pip install feedparser requests
'''

import re
import html
import requests
import feedparser

RESEARCH_FILE = "research.md"

OUTPUT_FILE = "generated/new_publications.md"

ARXIV_API_URL = (
    "https://export.arxiv.org/api/query?"
    "search_query=au:Jochym-O%27Connor_Tomas"
    "&start=0&max_results=100"
)

def normalize_arxiv_id(arxiv_id):
    '''
    Remove version suffix from arXiv IDs.
    Example:
        2211.03625v2 -> 2211.03625
    '''
    return re.sub(r'v\d+$', '', arxiv_id)

def load_existing_arxiv_ids(filepath):
    '''
    Parse research.md and extract existing arXiv IDs.
    '''
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    ids = set(
        normalize_arxiv_id(x)
        for x in re.findall(r'arxiv=\"([^\"]+)\"', text)
    )
    return ids


def fetch_arxiv_entries():
    '''
    Fetch papers from arXiv API.
    '''
    url = ARXIV_API_URL

    print(url)
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    feed = feedparser.parse(response.text)

    papers = []

    for entry in feed.entries:
        title = html.unescape(entry.title.replace("\n", " ").strip())

        authors = ", ".join(author.name for author in entry.authors)

        author_names = [author.name for author in entry.authors]

        if "Tomas Jochym-O'Connor" not in author_names:
            continue

        raw_arxiv_id = entry.id.split("/abs/")[-1]
        arxiv_id = normalize_arxiv_id(raw_arxiv_id)

        year = entry.published[:4]

        paper = {
            "title": title,
            "authors": authors,
            "arxiv": arxiv_id,
            "year": year,
        }

        papers.append(paper)

    return papers


def generate_include_block(paper):
    '''
    Generate a suggested Jekyll include block.
    Intentionally omits DOI/journal metadata because
    those often require manual curation.
    '''

    block = """<li>
    {{% include article.html
        title=\"{title}\"
        arxiv=\"{arxiv}\"
        authors=\"{authors}\"
        year=\"{year}\"
    %}}
</li>""".format(
        title=paper["title"],
        arxiv=paper["arxiv"],
        authors=paper["authors"],
        year=paper["year"]
    )

    return block


def main():
    print("\n=== Publication Update Check ===\n")

    existing_ids = load_existing_arxiv_ids(RESEARCH_FILE)

    print(f"Found {len(existing_ids)} existing arXiv entries in {RESEARCH_FILE}")

    papers = fetch_arxiv_entries()

    print("\nFetched papers:\n")

    for p in papers:
        print(p["arxiv"], "-", p["title"])

    new_papers = [
        p for p in papers
        if p["arxiv"] not in existing_ids
    ]

    new_papers.sort(key=lambda p: p["arxiv"], reverse=True)

    if not new_papers:
        print("\nNo new papers found.")
        return

    print(f"\nFound {len(new_papers)} new paper(s):\n")

    for i, paper in enumerate(new_papers, start=1):
        print(f"{i}. {paper['title']}")
        print(f"   arXiv: {paper['arxiv']}")
        print()

    print("\n=== Suggested Entries ===\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for paper in new_papers:
            block = generate_include_block(paper)

            print(block)
            print()

            f.write(block)
            f.write("\n\n")

    print(f"Wrote suggested entries to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

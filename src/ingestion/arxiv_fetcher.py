"""
arXiv fetcher — pulls paper metadata for target domains via the arXiv API.

Output: JSONL files in data/raw/arxiv/{domain}/batch_{n}.jsonl
Each line: one paper record with title, abstract, authors, categories, dates.

Usage:
    python -m src.ingestion.arxiv_fetcher --domain aerospace --max-results 5000
    python -m src.ingestion.arxiv_fetcher --domain medical_devices --max-results 5000
"""

import argparse
import asyncio
import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# arXiv API base
ARXIV_API_URL = "http://export.arxiv.org/api/query"

# Rate limit: arXiv asks for 3 seconds between requests
RATE_LIMIT_SECONDS = 3.0

# Batch size: arXiv max per request is 2000, we use 500 to be safe
BATCH_SIZE = 500

# Domain → arXiv search queries
# Each entry is a list of queries — results are merged and deduplicated
DOMAIN_QUERIES: dict[str, list[str]] = {
    "aerospace": [
        "cat:eess.SY AND (aerospace OR spacecraft OR satellite OR propulsion OR turbine)",
        "cat:physics.flu-dyn AND (aerospace OR aerodynamics OR hypersonic)",
        "cat:cond-mat.mtrl-sci AND (aerospace OR titanium alloy OR carbon fiber OR thermal protection)",
    ],
    "medical_devices": [
        "cat:eess.SP AND (medical device OR implant OR biosensor OR wearable)",
        "cat:physics.med-ph AND (medical device OR imaging OR ultrasound OR MRI)",
        "cat:cs.RO AND (surgical robot OR medical robot OR rehabilitation)",
    ],
    "materials": [
        "cat:cond-mat.mtrl-sci AND (novel material OR alloy OR polymer OR composite OR coating)",
        "cat:cond-mat.supr-con AND (superconductor OR high temperature superconductivity)",
        "cat:physics.app-ph AND (nanomaterial OR 2D material OR graphene OR perovskite)",
    ],
    "energy": [
        "cat:physics.app-ph AND (battery OR solar cell OR fuel cell OR energy storage OR photovoltaic)",
        "cat:cond-mat.mtrl-sci AND (lithium OR electrolyte OR hydrogen storage OR thermoelectric)",
        "cat:eess.SY AND (smart grid OR renewable energy OR wind turbine OR energy harvesting)",
    ],
    "biotechnology": [
        "cat:q-bio.BM AND (CRISPR OR gene editing OR protein engineering OR synthetic biology)",
        "cat:q-bio.GN AND (genomics OR sequencing OR gene expression OR epigenetics)",
        "cat:q-bio.TO AND (tissue engineering OR organoid OR scaffold OR bioreactor)",
    ],
    "robotics": [
        "cat:cs.RO AND (robot OR autonomous OR manipulation OR locomotion OR swarm)",
        "cat:cs.AI AND (reinforcement learning OR robot learning OR sim-to-real)",
        "cat:eess.SY AND (control system OR actuator OR soft robot OR exoskeleton)",
    ],
    "quantum": [
        "cat:quant-ph AND (quantum computing OR qubit OR quantum error correction OR quantum circuit)",
        "cat:quant-ph AND (quantum sensing OR quantum communication OR quantum cryptography)",
        "cat:cond-mat.mes-hall AND (quantum dot OR topological insulator OR spin qubit)",
    ],
    "nanotechnology": [
        "cat:cond-mat.mes-hall AND (nanoparticle OR nanowire OR nanotube OR nanodevice)",
        "cat:physics.app-ph AND (nano OR MEMS OR NEMS OR self-assembly OR nanofabrication)",
        "cat:cond-mat.mtrl-sci AND (nanocomposite OR quantum confinement OR surface functionalization)",
    ],
    "environment": [
        "cat:physics.ao-ph AND (climate change OR carbon capture OR greenhouse gas OR pollution)",
        "cat:physics.app-ph AND (water purification OR desalination OR environmental sensor)",
        "cat:eess.SY AND (carbon neutral OR green hydrogen OR emissions OR sustainability)",
    ],
    "semiconductors": [
        "cat:cond-mat.mes-hall AND (semiconductor OR transistor OR MOSFET OR photonic chip)",
        "cat:physics.app-ph AND (silicon photonics OR GaN OR SiC OR power electronics)",
        "cat:eess.SP AND (chip design OR VLSI OR neuromorphic OR memristor)",
    ],
    "pharma": [
        "cat:q-bio.BM AND (drug discovery OR drug design OR molecular docking OR pharmacology)",
        "cat:q-bio.QM AND (computational drug OR binding affinity OR ADMET OR lead compound)",
        "cat:physics.med-ph AND (drug delivery OR nanoparticle drug OR targeted therapy)",
    ],
    "neuroscience": [
        "cat:q-bio.NC AND (neuroscience OR neural circuit OR brain computer interface OR cognition)",
        "cat:eess.SP AND (EEG OR neural signal OR brain imaging OR neuroprosthetics)",
        "cat:cs.AI AND (neural network OR deep learning OR neuromorphic computing OR brain inspired)",
    ],
}

# arXiv XML namespaces
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

DATA_DIR = Path("data/raw/arxiv")


def parse_entry(entry: ET.Element) -> dict:
    """Parse one <entry> element from arXiv Atom feed into a flat dict."""

    def text(tag: str) -> str:
        el = entry.find(tag, NS)
        return el.text.strip() if el is not None and el.text else ""

    authors = [
        a.findtext("atom:name", namespaces=NS) or ""
        for a in entry.findall("atom:author", NS)
    ]
    categories = [
        c.attrib.get("term", "")
        for c in entry.findall("atom:category", NS)
    ]
    arxiv_id = text("atom:id").split("/abs/")[-1]  # e.g. "2401.12345v1"

    return {
        "arxiv_id": arxiv_id,
        "title": text("atom:title").replace("\n", " "),
        "abstract": text("atom:summary").replace("\n", " "),
        "authors": authors,
        "categories": categories,
        "published": text("atom:published"),
        "updated": text("atom:updated"),
        "doi": text("arxiv:doi"),
        "journal_ref": text("arxiv:journal_ref"),
        "source": "arxiv",
    }


async def fetch_batch(
    session: aiohttp.ClientSession,
    query: str,
    start: int,
    max_results: int,
) -> list[dict]:
    """Fetch one batch from arXiv API. Returns list of parsed paper dicts."""
    params = {
        "search_query": query,
        "start": start,
        "max_results": min(max_results, BATCH_SIZE),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    async with session.get(ARXIV_API_URL, params=params) as resp:
        resp.raise_for_status()
        xml_text = await resp.text()

    root = ET.fromstring(xml_text)
    entries = root.findall("atom:entry", NS)
    return [parse_entry(e) for e in entries]


async def fetch_domain(domain: str, max_results: int) -> None:
    """Fetch all papers for a domain across all its queries, save to JSONL."""
    queries = DOMAIN_QUERIES.get(domain)
    if not queries:
        raise ValueError(f"Unknown domain: {domain}. Choose from {list(DOMAIN_QUERIES)}")

    out_dir = DATA_DIR / domain
    out_dir.mkdir(parents=True, exist_ok=True)

    seen_ids: set[str] = set()
    # Load already-seen IDs from existing batches to enable resuming
    for existing in sorted(out_dir.glob("batch_*.jsonl")):
        with open(existing) as f:
            for line in f:
                record = json.loads(line)
                seen_ids.add(record["arxiv_id"])
    logger.info(f"[{domain}] Resuming — {len(seen_ids)} papers already downloaded")

    batch_num = len(list(out_dir.glob("batch_*.jsonl")))
    total_fetched = 0

    async with aiohttp.ClientSession() as session:
        for query in queries:
            logger.info(f"[{domain}] Query: {query}")
            start = 0
            per_query_count = 0

            while per_query_count < max_results:
                try:
                    papers = await fetch_batch(session, query, start, max_results - per_query_count)
                except aiohttp.ClientError as e:
                    logger.error(f"[{domain}] HTTP error at start={start}: {e}")
                    break

                if not papers:
                    logger.info(f"[{domain}] No more results for this query at start={start}")
                    break

                # Deduplicate
                new_papers = [p for p in papers if p["arxiv_id"] not in seen_ids]
                for p in new_papers:
                    seen_ids.add(p["arxiv_id"])

                if new_papers:
                    batch_path = out_dir / f"batch_{batch_num:04d}.jsonl"
                    with open(batch_path, "w") as f:
                        for paper in new_papers:
                            f.write(json.dumps(paper) + "\n")
                    logger.info(
                        f"[{domain}] Saved {len(new_papers)} papers → {batch_path.name}"
                    )
                    batch_num += 1
                    total_fetched += len(new_papers)

                per_query_count += len(papers)
                start += len(papers)

                if len(papers) < BATCH_SIZE:
                    break  # Reached end of results for this query

                logger.info(f"[{domain}] Rate limiting — sleeping {RATE_LIMIT_SECONDS}s")
                await asyncio.sleep(RATE_LIMIT_SECONDS)

    logger.info(f"[{domain}] Done — {total_fetched} new papers saved to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch arXiv papers by domain")
    parser.add_argument(
        "--domain",
        required=False,
        choices=list(DOMAIN_QUERIES.keys()) + ["all"],
        default="all",
        help="Target domain to fetch, or 'all' to fetch every domain (default: all)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5000,
        help="Max papers to fetch per query (default: 5000)",
    )
    args = parser.parse_args()

    domains = list(DOMAIN_QUERIES.keys()) if args.domain == "all" else [args.domain]
    for domain in domains:
        asyncio.run(fetch_domain(domain, args.max_results))


if __name__ == "__main__":
    main()

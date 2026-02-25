import re
from typing import List, Optional, Tuple

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from app.models import Paper

_LATEX_ACCENTS = {
    '`': '\u0300', "'": '\u0301', '^': '\u0302', '"': '\u0308',
    '~': '\u0303', '=': '\u0304', '.': '\u0307', 'u': '\u0306',
    'v': '\u030C', 'H': '\u030B', 'c': '\u0327', 'd': '\u0323',
    'b': '\u0331', 'k': '\u0328', 'r': '\u030A',
}

_LATEX_COMMANDS = {
    r'\aa': 'å', r'\AA': 'Å', r'\ae': 'æ', r'\AE': 'Æ',
    r'\oe': 'œ', r'\OE': 'Œ', r'\o': 'ø', r'\O': 'Ø',
    r'\ss': 'ß', r'\i': 'ı', r'\j': 'ȷ', r'\l': 'ł', r'\L': 'Ł',
    r'\sim': '~', r'\&': '&', r'\$': '$', r'\%': '%', r'\#': '#',
    r'\textendash': '–', r'\textemdash': '—',
    r'\textbackslash': '\\', r'\textblackslash': '\\',
}


def _decode_latex(text: str) -> str:
    """Convert LaTeX accents and commands to Unicode."""
    if not text:
        return text

    # Replace known commands first
    for cmd, replacement in _LATEX_COMMANDS.items():
        text = text.replace(cmd, replacement)

    # Handle accent commands: \"{a}, \'{e}, \v{s}, etc.
    def replace_accent(m):
        cmd = m.group(1)
        char = m.group(2)
        combining = _LATEX_ACCENTS.get(cmd)
        if combining and len(char) == 1:
            import unicodedata
            return unicodedata.normalize('NFC', char + combining)
        return char

    text = re.sub(r'\\([`\'\\^"~=.uUvHcdbkr])\{([^}]*)\}', replace_accent, text)
    text = re.sub(r'\\([`\'\\^"~=.uUvHcdbkr])\s*([A-Za-z])', replace_accent, text)

    # Remove remaining braces and LaTeX noise
    text = re.sub(r'\\(?:rm|it|bf|text[a-z]+)\b\s*', '', text)
    text = re.sub(r'\\;|\\,|\\!|\\ ', ' ', text)
    text = re.sub(r'\$([^$]*)\$', r'\1', text)
    text = text.replace('{', '').replace('}', '')

    return text.strip()


def parse_bibtex(bibtex_str: str) -> List[dict]:
    parser = BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    bib_db = bibtexparser.loads(bibtex_str, parser=parser)

    entries = []
    for entry in bib_db.entries:
        entries.append({
            "bibtex_key": entry.get("ID", ""),
            "bibtex_type": entry.get("ENTRYTYPE", "article"),
            "title": _decode_latex(entry.get("title", "").strip("{}")),
            "authors": _decode_latex(entry.get("author", "")),
            "year": _safe_int(entry.get("year")),
            "doi": entry.get("doi"),
            "arxiv_id": _extract_arxiv(entry),
            "abstract": _decode_latex(entry.get("abstract", "")),
            "journal": _decode_latex(entry.get("journal", "") or entry.get("booktitle", "")),
            "url": entry.get("url", ""),
        })
    return entries


def _safe_int(val) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _extract_arxiv(entry: dict) -> Optional[str]:
    eprint = entry.get("eprint", "")
    if eprint and entry.get("archiveprefix", "").lower() == "arxiv":
        return eprint
    arxiv = entry.get("arxiv_id") or entry.get("arxivid") or ""
    return arxiv or None


def generate_bibtex(papers: List[Paper]) -> str:
    db = BibDatabase()
    for paper in papers:
        entry = {
            "ENTRYTYPE": paper.bibtex_type or "article",
            "ID": paper.bibtex_key or f"paper{paper.id}",
            "title": paper.title,
            "author": paper.authors or "",
        }
        if paper.year:
            entry["year"] = str(paper.year)
        if paper.doi:
            entry["doi"] = paper.doi
        if paper.journal:
            if paper.bibtex_type in ("inproceedings", "conference"):
                entry["booktitle"] = paper.journal
            else:
                entry["journal"] = paper.journal
        if paper.url:
            entry["url"] = paper.url
        if paper.abstract:
            entry["abstract"] = paper.abstract
        if paper.arxiv_id:
            entry["eprint"] = paper.arxiv_id
            entry["archiveprefix"] = "arXiv"
        db.entries.append(entry)

    writer = BibTexWriter()
    return writer.write(db)


def find_duplicates(entries: List[dict], existing_papers: List[Paper]) -> Tuple[List[dict], List[dict]]:
    existing_dois = {p.doi.lower() for p in existing_papers if p.doi}
    existing_arxiv = {p.arxiv_id.lower() for p in existing_papers if p.arxiv_id}

    new_entries = []
    duplicates = []
    for entry in entries:
        doi = (entry.get("doi") or "").lower()
        arxiv = (entry.get("arxiv_id") or "").lower()
        if (doi and doi in existing_dois) or (arxiv and arxiv in existing_arxiv):
            duplicates.append(entry)
        else:
            new_entries.append(entry)
    return new_entries, duplicates

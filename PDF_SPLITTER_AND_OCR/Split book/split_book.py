#!/usr/bin/env python3
"""
Split a PDF into chapter PDFs or run OCR to make it searchable.

Usage (Windows drag-and-drop):
  - Drag a PDF onto this file to split into chapters (default).

Command-line (more control):
  python split_book.py --mode split <file.pdf>   # split only (default)
  python split_book.py --mode ocr   <file.pdf>   # OCR only, no splitting

Outputs are written to split_book/output/.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence, Tuple

from pypdf import PdfReader, PdfWriter

# Optional OCR dependencies (installed via requirements.txt)
try:
    import pypdfium2  # type: ignore
except Exception:  # pragma: no cover - optional dep
    pypdfium2 = None

try:
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover - optional dep
    pytesseract = None

TOC_PATTERN = re.compile(r"(.{4,}?)(?:\.{2,}|\s{2,})(\d{1,4})$")
BOOK_FOLDER_LIMIT = 40
CHAPTER_FILENAME_LIMIT = 80
MAX_OUTPUT_PATH = 240  # stay safely below Windows MAX_PATH limits
DEFAULT_OCR_DPI = 300
DEFAULT_OCR_LANG = "eng"


@dataclass
class ChapterRange:
    title: str
    start_page: int
    end_page: int


def sanitize_for_filename(text: str) -> str:
    """Remove characters that Windows dislikes while keeping readable spaces."""
    cleaned = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Chapter"


def sanitize_folder_name(text: str) -> str:
    cleaned = sanitize_for_filename(text)
    return cleaned.replace(" ", "_")


def limit_length(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars].rstrip()


def iter_outline_entries(entries: Iterable, reader: PdfReader, level: int = 0) -> Iterator[Tuple[int, str, int]]:
    """Yield (level, title, page_number) tuples from a PDF outline tree."""
    for item in entries:
        if isinstance(item, list):
            yield from iter_outline_entries(item, reader, level + 1)
            continue
        try:
            title = getattr(item, "title", None) or str(item)
            # Handle ByteStringObject and other special types
            if hasattr(title, 'original_bytes'):
                title = title.original_bytes.decode('utf-8', errors='ignore')
            else:
                title = str(title)
        except Exception:
            continue
        try:
            page_number = reader.get_destination_page_number(item) + 1
        except Exception:
            continue
        if title and title.strip():
            yield level, title.strip(), page_number


def detect_from_outline(reader: PdfReader) -> Tuple[List[Tuple[str, int]], str]:
    raw_outline = getattr(reader, "outline", None) or getattr(reader, "outlines", None)
    if not raw_outline:
        return [], ""

    by_level: dict[int, List[Tuple[str, int]]] = {}
    total_pages = len(reader.pages)

    for level, title, page in iter_outline_entries(raw_outline, reader):
        if not title or page < 1 or page > total_pages:
            continue
        bucket = by_level.setdefault(level, [])
        bucket.append((title, page))

    if not by_level:
        return [], ""

    candidates: List[Tuple[float, int, int, List[Tuple[str, int]]]] = []
    for level, entries in by_level.items():
        bucket = dedupe_sort_entries(entries)
        if len(bucket) < 2:
            continue
        chapterish = sum(1 for title, _ in bucket if is_likely_chapter(title))
        ratio = chapterish / len(bucket) if bucket else 0.0
        candidates.append((ratio, len(bucket), -level, bucket))

    if not candidates:
        return [], ""

    candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return candidates[0][3], "PDF bookmarks"


def dedupe_sort_entries(entries: Sequence[Tuple[str, int]]) -> List[Tuple[str, int]]:
    seen_pages: set[int] = set()
    cleaned: List[Tuple[str, int]] = []
    for title, page in sorted(entries, key=lambda entry: (entry[1], entry[0])):
        if page in seen_pages:
            continue
        seen_pages.add(page)
        cleaned.append((title, page))
    return cleaned


def build_page_label_map(reader: PdfReader) -> dict[int, int]:
    labels = getattr(reader, "page_labels", None)
    if not labels:
        return {}
    mapping: dict[int, int] = {}
    for index, raw in enumerate(labels):
        if not raw:
            continue
        try:
            # Handle ByteStringObject and other special types
            raw_str = str(raw)
            if hasattr(raw, 'original_bytes'):
                raw_str = raw.original_bytes.decode('utf-8', errors='ignore')
        except Exception:
            continue
        digits = "".join(ch for ch in raw_str if ch.isdigit())
        if not digits:
            continue
        try:
            number = int(digits)
            mapping.setdefault(number, index + 1)
        except ValueError:
            continue
    return mapping


def scan_table_of_contents(reader: PdfReader, search_pages: int = 60, max_results: int = 200) -> List[dict]:
    limit = min(len(reader.pages), max(1, search_pages))
    matches: List[dict] = []

    for idx in range(limit):
        try:
            text = reader.pages[idx].extract_text() or ""
        except Exception:
            continue
        
        # Handle potential encoding issues
        try:
            if not isinstance(text, str):
                if hasattr(text, 'original_bytes'):
                    text = text.original_bytes.decode('utf-8', errors='ignore')
                else:
                    text = str(text)
        except Exception:
            continue
        
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            if len(line) < 6:
                continue
            try:
                match = TOC_PATTERN.search(line)
            except Exception:
                continue
            if not match:
                continue
            try:
                title = match.group(1).strip(" .�?�\t-")
                if not title:
                    continue
                page_str = match.group(2)
                book_page = int(page_str)
            except (ValueError, AttributeError, TypeError):
                continue
            matches.append(
                {
                    "title": title,
                    "book_page": book_page,
                    "source_pdf_page": idx + 1,
                }
            )
            if len(matches) >= max_results:
                return matches
    return matches


def is_likely_chapter(title: str) -> bool:
    lowered = title.lower()
    if "chapter" in lowered:
        return True
    if re.match(r"^\d+(\.\d+)?\b", lowered):
        return True
    if re.match(r"^[ivxlcdm]+\b", lowered):
        return True
    return False


def detect_from_toc(reader: PdfReader) -> Tuple[List[Tuple[str, int]], str]:
    try:
        label_map = build_page_label_map(reader)
    except Exception:
        # If page labels fail, skip this detection method
        return [], ""
    
    if not label_map:
        return [], ""

    matches = scan_table_of_contents(reader)
    if not matches:
        return [], ""

    converted: List[Tuple[str, int]] = []
    seen_pages: set[int] = set()
    for entry in matches:
        pdf_page = label_map.get(entry["book_page"])
        if not pdf_page or pdf_page in seen_pages:
            continue
        converted.append((entry["title"], pdf_page))
        seen_pages.add(pdf_page)

    if len(converted) < 2:
        return [], ""

    chapter_like = [entry for entry in converted if is_likely_chapter(entry[0])]
    result = chapter_like if len(chapter_like) >= 2 else converted
    return dedupe_sort_entries(result), "table of contents scan"


def compute_chapter_ranges(starts: Sequence[Tuple[str, int]], total_pages: int) -> List[ChapterRange]:
    ordered: List[Tuple[str, int]] = []
    for entry in sorted(starts, key=lambda item: item[1]):
        start = entry[1]
        if 1 <= start <= total_pages:
            ordered.append(entry)

    chapters: List[ChapterRange] = []
    for idx, (title, start_page) in enumerate(ordered):
        if idx + 1 < len(ordered):
            end_page = max(start_page, ordered[idx + 1][1] - 1)
        else:
            end_page = total_pages
        if end_page < start_page:
            continue
        chapters.append(ChapterRange(title=title, start_page=start_page, end_page=end_page))
    return chapters


def detect_chapters(reader: PdfReader) -> Tuple[List[ChapterRange], str]:
    detectors = [detect_from_outline, detect_from_toc]
    total_pages = len(reader.pages)

    candidates: List[Tuple[int, int, List[ChapterRange], str]] = []
    for index, detector in enumerate(detectors):
        starts, source = detector(reader)
        if len(starts) < 2:
            continue
        ranges = compute_chapter_ranges(starts, total_pages)
        if len(ranges) >= 2:
            candidates.append((len(ranges), -index, ranges, source))

    if candidates:
        candidates.sort(reverse=True)
        _, _, best_ranges, source = candidates[0]
        return best_ranges, source
    raise RuntimeError("Unable to detect chapter boundaries automatically.")


def ensure_unique_name(base_name: str, existing: set[str], limit: int | None = None) -> str:
    def clamp(text: str, max_len: int | None) -> str:
        if max_len is None:
            return text
        truncated = limit_length(text, max_len)
        if truncated:
            return truncated
        return text[: max(1, max_len)]

    candidate = clamp(base_name, limit)
    if candidate not in existing:
        existing.add(candidate)
        return candidate

    counter = 2
    while True:
        suffix = f" ({counter})"
        if limit is not None:
            available = max(1, limit - len(suffix))
            trimmed = clamp(base_name, available)
            candidate = f"{trimmed}{suffix}"
        else:
            candidate = f"{base_name}{suffix}"
        if candidate not in existing:
            existing.add(candidate)
            return candidate
        counter += 1


def split_pdf(input_pdf: Path, output_root: Path) -> List[Path]:
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")
    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    try:
        reader = PdfReader(str(input_pdf))
    except Exception as e:
        raise RuntimeError(f"Failed to read PDF: {e}")
    
    try:
        chapters, source = detect_chapters(reader)
    except Exception as e:
        raise RuntimeError(f"Failed to detect chapters: {e}. The PDF might be corrupted or use an unsupported format.")
    
    padding = max(1, len(str(len(chapters))))

    folder_name = sanitize_folder_name(input_pdf.stem) or "book"
    folder_name = limit_length(folder_name, BOOK_FOLDER_LIMIT) or "book"
    book_folder = output_root / folder_name
    book_folder.mkdir(parents=True, exist_ok=True)

    print(f"Detected {len(chapters)} chapters via {source}.")
    print(f"Saving chapters to: {book_folder}")

    produced_files: List[Path] = []
    used_names: set[str] = set()

    base_limit = MAX_OUTPUT_PATH - len(str(book_folder)) - 1 - len(".pdf")
    name_limit = max(12, base_limit)

    for index, chapter in enumerate(chapters, start=1):
        number = str(index).zfill(padding)
        prefix = f"CH {number} "
        available_for_title = max(1, name_limit - len(prefix))
        chapter_cap = max(1, CHAPTER_FILENAME_LIMIT - len(prefix))
        fragment_limit = min(available_for_title, chapter_cap)
        title_fragment = sanitize_for_filename(chapter.title)
        title_fragment = limit_length(title_fragment, fragment_limit) or "Chapter"
        base_name = limit_length(f"{prefix}{title_fragment}".strip(), name_limit)
        safe_name = ensure_unique_name(base_name, used_names, name_limit)
        output_path = book_folder / f"{safe_name}.pdf"

        writer = PdfWriter()
        for page_index in range(chapter.start_page - 1, chapter.end_page):
            writer.add_page(reader.pages[page_index])
        with output_path.open("wb") as fh:
            writer.write(fh)

        produced_files.append(output_path)
        print(f"  - {output_path.name}: pages {chapter.start_page}-{chapter.end_page}")

    return produced_files


def require_ocr_deps() -> None:
    missing: List[str] = []
    if pypdfium2 is None:
        missing.append("pypdfium2")
    if pytesseract is None:
        missing.append("pytesseract")
    if missing:
        raise RuntimeError(
            "OCR mode requires: "
            + ", ".join(missing)
            + ". Install via 'pip install -r requirements.txt'. "
            "You also need the Tesseract OCR engine installed and on your PATH "
            "(Windows installer: https://github.com/UB-Mannheim/tesseract/wiki)."
        )
    try:
        pytesseract.get_tesseract_version()  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Tesseract OCR engine is not installed or not on PATH. "
            "Install it from https://github.com/UB-Mannheim/tesseract/wiki and reopen your terminal."
        ) from exc


def ocr_pdf(input_pdf: Path, output_pdf: Path, dpi: int = DEFAULT_OCR_DPI, lang: str = DEFAULT_OCR_LANG) -> Path:
    require_ocr_deps()
    doc = pypdfium2.PdfDocument(str(input_pdf))  # type: ignore
    scale = max(1.0, dpi / 72.0)

    writer = PdfWriter()
    total_pages = len(doc)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    print(f"Running OCR at {dpi} DPI, language='{lang}' ...")

    for index in range(total_pages):
        page = doc[index]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(image, extension="pdf", lang=lang)  # type: ignore
        temp_reader = PdfReader(io.BytesIO(pdf_bytes))
        for temp_page in temp_reader.pages:
            writer.add_page(temp_page)
        if (index + 1) % 5 == 0 or index + 1 == total_pages:
            print(f"  OCR processed {index + 1}/{total_pages} pages")

    with output_pdf.open("wb") as fh:
        writer.write(fh)

    print(f"OCR output saved to: {output_pdf}")
    return output_pdf


def main(args: Sequence[str]) -> None:
    script_dir = Path(__file__).resolve().parent
    output_root = script_dir / "output"

    parser = argparse.ArgumentParser(
        description="Split a PDF into chapters or run OCR to make it searchable."
    )
    parser.add_argument(
        "pdf",
        nargs="+",
        help="Path(s) to PDF file(s)",
    )
    parser.add_argument(
        "--mode",
        choices=["split", "ocr"],
        default="split",
        help="split = chapter PDFs (default), ocr = searchable PDF without splitting",
    )
    parser.add_argument(
        "--lang",
        default=DEFAULT_OCR_LANG,
        help="Language(s) for Tesseract OCR (e.g., 'eng', 'eng+spa'). Used only in OCR mode.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_OCR_DPI,
        help="Rendering DPI for OCR mode (higher = slower, more accurate).",
    )

    if not args:
        print(
            "Drag a PDF onto this script, or run:\n"
            "  python split_book.py --mode split path/to/book.pdf\n"
            "  python split_book.py --mode ocr   path/to/book.pdf"
        )
        input("Press Enter to exit...")
        return

    parsed = parser.parse_args(list(args))

    try:
        for raw_path in parsed.pdf:
            pdf_path = Path(raw_path).expanduser()
            print(f"\nProcessing: {pdf_path}")
            if parsed.mode == "split":
                split_pdf(pdf_path, output_root)
            else:  # OCR only
                ocr_folder = output_root / "ocr"
                safe_name = sanitize_folder_name(pdf_path.stem)
                output_pdf = ocr_folder / f"{safe_name}_ocr.pdf"
                ocr_pdf(pdf_path, output_pdf, dpi=parsed.dpi, lang=parsed.lang)
        print("\nAll done!")
    except Exception as exc:  # pragma: no cover - drag/drop UX nicety
        print(f"\nError: {exc}")
    finally:
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass


if __name__ == "__main__":
    main(sys.argv[1:])

#!/usr/bin/env python3
"""
Interactive and CLI-friendly PDF splitter + OCR tool.

All outputs are kept in the same directory as this script, allowing simple
drag-and-drop usage on Windows.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from pypdf import PdfReader, PdfWriter

DEFAULT_CHAPTERS = {
    # Example metadata; extend or update to match your textbook(s).
    "CNS": {
        "pages": (4044, 4120),
        "title": "Central Nervous System",
    },
    "Heart": {
        "pages": (4121, 4205),
        "title": "Heart and Lung",
    },
}

CHAPTERS: Dict[str, Dict[str, object]] = {k: v.copy() for k, v in DEFAULT_CHAPTERS.items()}
CHAPTERS_SOURCE = "built-in sample"
CURRENT_CHAPTERS_PATH: Optional[Path] = None
CURRENT_BOOK_KEY = ""

PageRange = Tuple[int, int]


def parse_page_ranges(page_spec: str) -> List[PageRange]:
    """Parse strings like `4044-4120, 4130, 4200-4250` into ranges."""
    if not page_spec:
        raise ValueError("No page ranges provided.")

    cleaned = page_spec.replace(",", " ")
    tokens = [token.strip() for token in cleaned.split() if token.strip()]
    if not tokens:
        raise ValueError("Unable to parse page ranges from the input.")

    ranges: List[PageRange] = []
    for token in tokens:
        if "-" in token:
            start_str, end_str = token.split("-", 1)
            start = int(start_str)
            end = int(end_str)
        else:
            start = end = int(token)
        if start <= 0 or end <= 0:
            raise ValueError("Page numbers must be positive integers.")
        if start > end:
            raise ValueError(f"Invalid range: {token}")
        ranges.append((start, end))
    return ranges


def ensure_ranges_within_document(
    labeled_ranges: Sequence[Tuple[str, PageRange]],
    total_pages: int | None,
) -> None:
    """Make sure every range is valid for this PDF."""
    if total_pages is None:
        return
    for label, (start, end) in labeled_ranges:
        if start < 1 or end > total_pages:
            raise ValueError(
                f"{label} uses pages {start}-{end}, but the PDF only has {total_pages} pages."
            )


def convert_book_pages_to_pdf_ranges(
    ranges: Sequence[PageRange], book_start_page: int | None
) -> List[PageRange]:
    """Shift textbook page numbers to PDF-relative pages."""
    if not book_start_page:
        return [(start, end) for start, end in ranges]
    if book_start_page < 1:
        raise ValueError("Book start page must be >= 1.")
    offset = book_start_page - 1
    converted: List[PageRange] = []
    for start, end in ranges:
        pdf_start = start - offset
        pdf_end = end - offset
        if pdf_start < 1 or pdf_end < 1:
            raise ValueError(
                f"Book pages {start}-{end} map before the beginning of this PDF with the current offset."
            )
        converted.append((pdf_start, pdf_end))
    return converted


def sanitize_book_key(name: str) -> str:
    key = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return key or "book"


def read_chapter_mapping(path: Path) -> Dict[str, Dict[str, object]]:
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError("Chapter file must contain a JSON object at the top level.")
    chapters: Dict[str, Dict[str, object]] = {}
    for label, meta in raw.items():
        if not isinstance(meta, dict):
            raise ValueError(f"Chapter {label} must map to an object.")
        if "pages" not in meta or "title" not in meta:
            raise ValueError(f"Chapter {label} must include 'pages' and 'title'.")
        pages = meta["pages"]
        if (
            not isinstance(pages, (list, tuple))
            or len(pages) != 2
            or not all(isinstance(n, int) for n in pages)
        ):
            raise ValueError(
                f"Chapter {label} pages must be a list '[start, end]' of integers."
            )
        chapters[label] = {
            "pages": (int(pages[0]), int(pages[1])),
            "title": str(meta["title"]),
        }
    return chapters


def write_chapter_mapping(path: Path, mapping: Dict[str, Dict[str, object]]) -> None:
    serializable = {
        label: {"pages": list(meta["pages"]), "title": meta["title"]}
        for label, meta in mapping.items()
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(serializable, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def load_chapters_for_book(input_pdf: Path, script_dir: Path) -> None:
    """Load chapter definitions for the given book, falling back to defaults."""
    global CHAPTERS, CHAPTERS_SOURCE, CURRENT_CHAPTERS_PATH, CURRENT_BOOK_KEY
    CURRENT_BOOK_KEY = sanitize_book_key(input_pdf.stem)
    chapters_dir = script_dir / "chapters"
    candidate_files = [
        chapters_dir / f"{CURRENT_BOOK_KEY}.json",
        script_dir / "chapters.json",
    ]
    for path in candidate_files:
        if path.exists():
            chapters = read_chapter_mapping(path)
            CHAPTERS = chapters
            CHAPTERS_SOURCE = str(path)
            CURRENT_CHAPTERS_PATH = path
            return
    CHAPTERS = {k: v.copy() for k, v in DEFAULT_CHAPTERS.items()}
    CHAPTERS_SOURCE = "built-in sample (update via chapter editor)"
    CURRENT_CHAPTERS_PATH = chapters_dir / f"{CURRENT_BOOK_KEY}.json"


def prompt_positive_int(prompt: str) -> int:
    while True:
        text = input(prompt).strip()
        try:
            value = int(text)
            if value < 1:
                raise ValueError
            return value
        except ValueError:
            print("Please enter a positive integer.")


def prompt_int_with_default(prompt: str, default: int, minimum: int = 1) -> int:
    while True:
        text = input(prompt).strip()
        if not text:
            return default
        try:
            value = int(text)
            if value < minimum:
                raise ValueError
            return value
        except ValueError:
            print(f"Please enter an integer >= {minimum} or press Enter for {default}.")


def scan_table_of_contents(
    input_pdf: Path,
    search_pages: int = 40,
    book_start_page: int | None = None,
    max_results: int = 60,
) -> Tuple[List[int], List[dict]]:
    reader = PdfReader(str(input_pdf))
    total_pages = len(reader.pages)
    limit = min(total_pages, max(search_pages, 1))
    keyword_pages: List[int] = []
    matches: List[dict] = []
    toc_pattern = re.compile(r"(.{4,}?)(?:\.{2,}|\s{2,})(\d{1,4})$")

    for idx in range(limit):
        try:
            text = reader.pages[idx].extract_text() or ""
        except Exception:
            continue
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if any("content" in line.lower() for line in lines):
            keyword_pages.append(idx + 1)
        for line in lines:
            if len(line) < 6:
                continue
            match = toc_pattern.search(line)
            if not match:
                continue
            title = match.group(1).strip(" .•\t-")
            if not title:
                continue
            page_str = match.group(2)
            try:
                book_page = int(page_str)
            except ValueError:
                continue
            estimated_pdf = (
                book_page - book_start_page + 1
                if book_start_page
                else None
            )
            if estimated_pdf is not None and estimated_pdf < 1:
                estimated_pdf = None
            matches.append(
                {
                    "source_pdf_page": idx + 1,
                    "book_page": book_page,
                    "estimated_pdf_page": estimated_pdf,
                    "title": title,
                    "line": line,
                }
            )
            if len(matches) >= max_results:
                return keyword_pages, matches
    return keyword_pages, matches


def display_toc_scan_results(
    keyword_pages: Sequence[int],
    matches: Sequence[dict],
    book_start_page: int | None,
    searched_pages: int,
    total_pages: int | None,
) -> None:
    print(
        f"\nScanned the first {searched_pages} PDF page(s)"
        + (f" (out of {total_pages})" if total_pages else "")
        + " for table-of-contents patterns."
    )
    if keyword_pages:
        print(
            "  Found the word 'content' on PDF pages: "
            + ", ".join(str(p) for p in keyword_pages)
        )
    else:
        print("  Did not find the word 'content' on these pages.")

    if not matches:
        print("No candidate entries were detected. Try increasing the search limit.")
        return

    print("\nPossible Table of Contents entries:")
    header = "BookPg"
    print(f"  {header:<7} | {'PDF≈':<5} | {'Source PDF':<10} | Entry Preview")
    print("  " + "-" * 70)
    for entry in matches:
        book_page = entry["book_page"]
        pdf_est = entry["estimated_pdf_page"]
        src_pdf = entry["source_pdf_page"]
        preview = entry["title"][:70]
        pdf_est_str = str(pdf_est) if pdf_est is not None else "-"
        print(f"  {book_page:<7} | {pdf_est_str:<5} | {src_pdf:<10} | {preview}")
    print(
        "\nUse these hints to populate the chapter editor (option 'edit'). "
        "Each 'BookPg' is taken directly from the detected line."
    )


def edit_chapters_via_prompt() -> bool:
    """Allow the user to edit chapter metadata interactively."""
    if CURRENT_CHAPTERS_PATH is None:
        print("Chapter path is unknown; cannot edit.")
        return False

    global CHAPTERS, CHAPTERS_SOURCE

    print(
        "\nChapter definitions editor\n"
        "--------------------------\n"
        f"Book key: {CURRENT_BOOK_KEY or '(unknown)'}\n"
        f"File: {CURRENT_CHAPTERS_PATH}\n"
        "Enter a label to add/update it, 'delete <label>' to remove, 'list' to view,\n"
        "or press Enter/ type 'done' when finished.\n"
    )

    data: Dict[str, Dict[str, object]] = {
        label: {"pages": meta["pages"], "title": meta["title"]}
        for label, meta in CHAPTERS.items()
    }
    changed = False

    while True:
        command = input("Chapter command: ").strip()
        lower = command.lower()
        if lower in {"", "done", "exit", "quit"}:
            break
        if lower == "list":
            if not data:
                print("No chapters defined yet.")
            else:
                for label, meta in data.items():
                    start, end = meta["pages"]
                    print(f"  {label:<12} {start}-{end} | {meta['title']}")
            continue
        if lower.startswith("delete "):
            label = command.split(maxsplit=1)[1].strip()
            if label in data:
                data.pop(label)
                changed = True
                print(f"Deleted chapter '{label}'.")
            else:
                print(f"No chapter named '{label}'.")
            continue

        label = command
        start = prompt_positive_int("  Start page (book numbering): ")
        end = prompt_positive_int("  End page (book numbering): ")
        if end < start:
            print("  End page must be >= start page.")
            continue
        title = input("  Chapter title: ").strip() or label
        data[label] = {"pages": (start, end), "title": title}
        changed = True
        print(f"  Saved {label}: {start}-{end} | {title}")

    if not changed:
        print("No changes made.")
        return False

    write_chapter_mapping(CURRENT_CHAPTERS_PATH, data)
    updated = read_chapter_mapping(CURRENT_CHAPTERS_PATH)
    CHAPTERS = updated
    CHAPTERS_SOURCE = str(CURRENT_CHAPTERS_PATH)
    print(f"Chapter definitions saved to {CURRENT_CHAPTERS_PATH}.\n")
    return True


def extract_ranges_to_temp_pdf(input_pdf: Path, ranges: Sequence[PageRange]) -> Path:
    """Extract the provided 1-based ranges to a temporary PDF."""
    reader = PdfReader(str(input_pdf))
    writer = PdfWriter()
    total_pages = len(reader.pages)

    for start, end in ranges:
        if end > total_pages:
            raise ValueError(
                f"Range {start}-{end} exceeds total pages ({total_pages})."
            )
        for page_num in range(start - 1, end):
            writer.add_page(reader.pages[page_num])

    with NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        writer.write(tmp_file)
        temp_path = Path(tmp_file.name)
    return temp_path


def dump_text_layer(input_pdf: Path, output_txt: Path, max_pages: int | None = None) -> Tuple[int, int]:
    """Dump the existing PDF text layer to a UTF-8 file for diagnostics."""
    reader = PdfReader(str(input_pdf))
    total_pages = len(reader.pages)
    limit = total_pages if max_pages is None else min(max_pages, total_pages)
    text_pages = 0
    with output_txt.open("w", encoding="utf-8") as fh:
        fh.write(
            f"# Text dump generated from {input_pdf.name}\n"
            f"# Pages included: {limit}/{total_pages}\n\n"
        )
        for index in range(limit):
            page_num = index + 1
            text = reader.pages[index].extract_text() or ""
            if text.strip():
                text_pages += 1
            fh.write(f"--- Page {page_num} ---\n")
            fh.write(text.strip() + "\n\n")
    return limit, text_pages


def run_ocr(input_pdf: Path, output_pdf: Path, timeout_seconds: int = 1800) -> None:
    """Invoke ocrmypdf with the desired settings and a timeout."""
    if shutil.which("ocrmypdf") is None:
        raise FileNotFoundError(
            "ocrmypdf is not installed or not on PATH. Install it (plus Tesseract) before running."
        )
    print(
        f"\nRunning ocrmypdf on {input_pdf.name} -> {output_pdf.name}\n"
        f"Timeout: {timeout_seconds} seconds (~{timeout_seconds//60} minutes)\n"
        "Progress below is reported directly from ocrmypdf.\n"
    )
    cmd = [
        "ocrmypdf",
        "--force-ocr",
        "--deskew",
        "--optimize",
        "1",
        str(input_pdf),
        str(output_pdf),
    ]
    try:
        subprocess.run(cmd, check=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        # Clean up the incomplete output file
        if output_pdf.exists():
            try:
                output_pdf.unlink()
            except Exception:
                pass
        raise RuntimeError(
            f"ocrmypdf timed out after {timeout_seconds} seconds. "
            "The PDF may be corrupted or too large. Try using --inspect-text mode to check the PDF quality."
        ) from None
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "ocrmypdf failed. Review the console output above for details "
            f"(exit code {exc.returncode})."
        ) from exc


def sanitize_filename(name: str) -> str:
    """Remove characters that Windows filesystems reject."""
    name = name.strip().rstrip(".")
    if not name:
        raise ValueError("Filename cannot be empty.")
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    return sanitized or "output"


def ensure_extension(filename: str, extension: str) -> str:
    extension = extension if extension.startswith(".") else f".{extension}"
    return filename if filename.lower().endswith(extension.lower()) else f"{filename}{extension}"


def slugify_title(title: str, limit: int = 25) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "", title)
    return slug[:limit] or "Section"


def get_page_count(input_pdf: Path) -> int:
    reader = PdfReader(str(input_pdf))
    return len(reader.pages)


def confirm_overwrite(path: Path) -> bool:
    if not path.exists():
        return True
    while True:
        choice = input(f"{path.name} already exists. Overwrite? [y/n]: ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("Please answer y or n.")


def show_chapter_menu() -> None:
    print("\nAvailable chapters:")
    print(f"  (Source: {CHAPTERS_SOURCE})")
    if CURRENT_CHAPTERS_PATH:
        print(f"  (Edit file: {CURRENT_CHAPTERS_PATH})")
    for label, meta in CHAPTERS.items():
        pages = meta["pages"]
        print(f"  {label:<10} pages {pages[0]}-{pages[1]}  |  {meta['title']}")
    print()


def build_auto_filename(input_stem: str, config: dict) -> str:
    if config["mode"] == "all":
        return f"{input_stem}_ALL_OCR.pdf"
    if config["mode"] == "chapters":
        labels = config["labels"]
        if len(labels) == 1:
            label = labels[0]
            short_title = slugify_title(CHAPTERS[label]["title"])
            return f"{input_stem}_{label}_{short_title}_OCR.pdf"
        joined = "_".join(labels)
        return f"{input_stem}_{joined}_OCR.pdf"
    if config["mode"] == "pages":
        ranges = config.get("display_ranges", config["ranges"])
        first_start = min(r[0] for r in ranges)
        last_end = max(r[1] for r in ranges)
        return f"{input_stem}_PAGES_{first_start}-{last_end}_OCR.pdf"
    raise ValueError("Unknown configuration for automatic naming.")


def process_document(
    input_pdf: Path,
    output_path: Path,
    config: dict,
) -> None:
    if config["mode"] == "inspect_text":
        max_pages = config.get("max_pages")
        included, text_pages = dump_text_layer(input_pdf, output_path, max_pages)
        print(
            f"Text dump saved ({text_pages}/{included} pages contained text). "
            f"File: {output_path}"
        )
        return

    if config["mode"] == "all":
        run_ocr(input_pdf, output_path)
        return

    ranges: Sequence[PageRange] = config["ranges"]
    temp_pdf = extract_ranges_to_temp_pdf(input_pdf, ranges)
    try:
        run_ocr(temp_pdf, output_path)
    finally:
        try:
            temp_pdf.unlink(missing_ok=True)  # type: ignore[arg-type]
        except TypeError:
            # Python < 3.8 compatibility
            if temp_pdf.exists():
                temp_pdf.unlink()


def prompt_choice(prompt: str, valid_choices: Iterable[str]) -> str:
    valid = {choice.lower(): choice for choice in valid_choices}
    while True:
        answer = input(prompt).strip().lower()
        if answer in valid:
            return valid[answer]
        print(f"Please enter one of: {', '.join(valid_choices)}")


def interactive_mode(input_pdf: Path, script_dir: Path) -> None:
    input_pdf = input_pdf.expanduser()
    print(f"Input PDF: {input_pdf}")
    if not input_pdf.exists():
        print("The input file does not exist.")
        input("Press Enter to exit...")
        return
    if input_pdf.suffix.lower() != ".pdf":
        print("Please provide a PDF file.")
        input("Press Enter to exit...")
        return

    page_count: int | None = None
    try:
        page_count = get_page_count(input_pdf)
        print(f"Detected {page_count} pages.")
    except Exception as exc:
        print(f"Warning: unable to read page count ({exc}). Continuing anyway.")

    if CHAPTERS_SOURCE:
        print(f"Chapter definitions source: {CHAPTERS_SOURCE}")
        if CURRENT_CHAPTERS_PATH and "built-in" in CHAPTERS_SOURCE:
            print(
                "Tip: use the chapter editor (type 'edit' later) to create definitions "
                f"for this book at {CURRENT_CHAPTERS_PATH}."
            )

    book_start_page: int | None = None
    while True:
        resp = input(
            "\nIf PDF page 1 matches a specific textbook page number, enter it now.\n"
            "Otherwise press Enter to use PDF page numbering: "
        ).strip()
        if not resp:
            break
        try:
            value = int(resp)
            if value < 1:
                raise ValueError
        except ValueError:
            print("Please enter a positive integer or press Enter.")
            continue
        book_start_page = value
        print(
            f"Book page {book_start_page} will be treated as PDF page 1 for chapter/range inputs."
        )
        break

    processing_prompt = (
        "\nWhat do you want to process?\n"
        "  1) Whole book\n"
        "  2) One or more predefined chapters\n"
        "  3) Custom page ranges\n"
        "  4) Diagnostic: dump existing PDF text to .txt (no OCR)\n"
        "  5) Scan first PDF pages for possible table-of-contents entries\n\n"
        "Enter 1, 2, 3, 4, or 5: "
    )
    processing_choice = prompt_choice(processing_prompt, {"1", "2", "3", "4", "5"})

    config: dict
    if processing_choice == "1":
        config = {"mode": "all"}
    elif processing_choice == "2":
        while True:
            if CHAPTERS:
                show_chapter_menu()
            else:
                print(
                    "\nNo chapter metadata found for this book yet. "
                    "Type 'edit' to create definitions now."
                )
            raw_labels = input(
                "Enter chapter labels (space-separated) or type 'edit' to modify: "
            ).strip()
            if not raw_labels:
                print("Please enter at least one label or type 'edit'.")
                continue
            lower = raw_labels.lower()
            if lower in {"edit", "e"}:
                if edit_chapters_via_prompt():
                    continue
                print("No changes applied.")
                continue
            if lower in {"cancel", "quit"}:
                print("Aborting at user request.")
                input("Press Enter to exit...")
                return
            if not CHAPTERS:
                print("No chapter metadata available. Please create entries via 'edit'.")
                continue
            selected = raw_labels.split()
            normalized = []
            missing = []
            for label in selected:
                key = next(
                    (chapter for chapter in CHAPTERS if chapter.lower() == label.lower()),
                    None,
                )
                if key:
                    normalized.append(key)
                else:
                    missing.append(label)
            if missing:
                print(f"Unknown labels: {', '.join(missing)}")
                continue
            original_ranges = [CHAPTERS[label]["pages"] for label in normalized]
            try:
                pdf_ranges = convert_book_pages_to_pdf_ranges(
                    original_ranges, book_start_page
                )
            except ValueError as exc:
                print(
                    f"Unable to use those chapters with the provided book start: {exc}"
                )
                continue
            labeled_ranges = []
            for label, book_range, pdf_range in zip(
                normalized, original_ranges, pdf_ranges
            ):
                if book_start_page:
                    label_desc = (
                        f"{label} (book pages {book_range[0]}-{book_range[1]})"
                    )
                else:
                    label_desc = label
                labeled_ranges.append((label_desc, pdf_range))
            try:
                ensure_ranges_within_document(labeled_ranges, page_count)
            except ValueError as exc:
                print(
                    f"{exc}\nUpdate the chapter mapping or adjust the book start page."
                )
                continue
            config = {"mode": "chapters", "labels": normalized, "ranges": pdf_ranges}
            break
    elif processing_choice == "3":
        while True:
            raw_ranges = input(
                "Enter page ranges (example: 4044-4120, 4200-4250, 4300): "
            ).strip()
            try:
                display_ranges = parse_page_ranges(raw_ranges)
            except Exception as exc:
                print(f"Unable to parse ranges: {exc}")
                continue
            try:
                pdf_ranges = convert_book_pages_to_pdf_ranges(
                    display_ranges, book_start_page
                )
            except ValueError as exc:
                print(f"Unable to apply book offset: {exc}")
                continue
            try:
                labels = [
                    (
                        f"Range {orig_start}-{orig_end}"
                        + (
                            f" (book pages {orig_start}-{orig_end})"
                            if book_start_page
                            else ""
                        ),
                        pdf_range,
                    )
                    for (orig_start, orig_end), pdf_range in zip(
                        display_ranges, pdf_ranges
                    )
                ]
                ensure_ranges_within_document(labels, page_count)
            except ValueError as exc:
                print(exc)
                continue
            break
        config = {
            "mode": "pages",
            "ranges": pdf_ranges,
            "display_ranges": display_ranges,
        }
    elif processing_choice == "4":
        max_pages: Optional[int] = None
        while True:
            limit = input(
                "How many pages should be included in the text dump? "
                "(Press Enter for all pages): "
            ).strip()
            if not limit:
                break
            try:
                value = int(limit)
                if value < 1:
                    raise ValueError
                max_pages = value
                break
            except ValueError:
                print("Please enter a positive integer or leave blank.")
        config = {"mode": "inspect_text", "max_pages": max_pages}
    else:
        scan_limit = prompt_int_with_default(
            "Scan how many PDF pages for a table of contents? (Press Enter for 40): ",
            default=40,
        )
        keyword_pages, matches = scan_table_of_contents(
            input_pdf,
            search_pages=scan_limit,
            book_start_page=book_start_page,
        )
        display_toc_scan_results(
            keyword_pages,
            matches,
            book_start_page,
            searched_pages=scan_limit,
            total_pages=page_count,
        )
        input("Press Enter to exit...")
        return

    naming_prompt = (
        "\nOutput naming:\n"
        "  1) Let me type a custom name\n"
        "  2) Use automatic naming based on chapters or selection\n\n"
        "Choose 1 or 2: "
    )
    naming_choice = prompt_choice(naming_prompt, {"1", "2"})

    if naming_choice == "1":
        while True:
            manual = input(
                "Enter output filename (without path, .pdf is optional): "
            ).strip()
            try:
                filename = sanitize_filename(manual)
                desired_ext = ".txt" if config["mode"] == "inspect_text" else ".pdf"
                filename = ensure_extension(filename, desired_ext)
                break
            except ValueError as exc:
                print(exc)
        output_path = script_dir / filename
    else:
        if config["mode"] == "inspect_text":
            auto_name = f"{input_pdf.stem}_TEXT_DUMP.txt"
            filename = sanitize_filename(auto_name)
            filename = ensure_extension(filename, ".txt")
        else:
            auto_name = build_auto_filename(input_pdf.stem, config)
            filename = ensure_extension(sanitize_filename(auto_name), ".pdf")
        output_path = script_dir / filename

    if not confirm_overwrite(output_path):
        print("Aborting at user request.")
        input("Press Enter to exit...")
        return

    try:
        process_document(input_pdf, output_path, config)
    except Exception as exc:
        print(f"Processing failed: {exc}")
    else:
        print(f"\nDone! Saved to: {output_path}")
    finally:
        input("Press Enter to exit...")


def resolve_output_path(output_arg: str, script_dir: Path, extension: str = ".pdf") -> Path:
    filename = ensure_extension(sanitize_filename(Path(output_arg).name), extension)
    return script_dir / filename


def run_cli_mode(args: argparse.Namespace, script_dir: Path) -> None:
    input_pdf = Path(args.input_pdf).expanduser()
    if not input_pdf.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_pdf}")
    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("Input file must be a PDF.")

    extension = ".txt" if args.inspect_text else ".pdf"
    output_path = resolve_output_path(args.output_name, script_dir, extension)
    if output_path.exists():
        raise FileExistsError(f"Output already exists: {output_path}")

    page_count: int | None = None
    try:
        page_count = get_page_count(input_pdf)
    except Exception:
        page_count = None

    book_start_page = args.book_start
    if book_start_page is not None and book_start_page < 1:
        raise ValueError("--book-start must be >= 1.")

    if args.inspect_text:
        max_pages = args.inspect_max_pages
        if max_pages is not None and max_pages < 1:
            raise ValueError("--inspect-max-pages must be >= 1.")
        config = {"mode": "inspect_text", "max_pages": max_pages}
    elif args.all:
        config = {"mode": "all"}
    elif args.chapters:
        labels = []
        for label in args.chapters:
            key = next(
                (chapter for chapter in CHAPTERS if chapter.lower() == label.lower()),
                None,
            )
            if not key:
                raise ValueError(f"Unknown chapter label: {label}")
            labels.append(key)
        original_ranges = [CHAPTERS[label]["pages"] for label in labels]
        pdf_ranges = convert_book_pages_to_pdf_ranges(original_ranges, book_start_page)
        labeled_ranges = []
        for label, book_range, pdf_range in zip(labels, original_ranges, pdf_ranges):
            if book_start_page:
                label_desc = f"{label} (book pages {book_range[0]}-{book_range[1]})"
            else:
                label_desc = label
            labeled_ranges.append((label_desc, pdf_range))
        ensure_ranges_within_document(labeled_ranges, page_count)
        config = {"mode": "chapters", "labels": labels, "ranges": pdf_ranges}
    else:
        display_ranges = parse_page_ranges(args.pages)
        pdf_ranges = convert_book_pages_to_pdf_ranges(display_ranges, book_start_page)
        ensure_ranges_within_document(
            [
                (
                    (
                        f"Range {orig_start}-{orig_end} (book pages {orig_start}-{orig_end})"
                        if book_start_page
                        else f"Range {orig_start}-{orig_end}"
                    ),
                    pdf_range,
                )
                for (orig_start, orig_end), pdf_range in zip(display_ranges, pdf_ranges)
            ],
            page_count,
        )
        config = {"mode": "pages", "ranges": pdf_ranges}

    process_document(input_pdf, output_path, config)
    print(f"Saved to: {output_path}")


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OCR-friendly PDF splitter for textbooks (drag-and-drop aware)."
    )
    parser.add_argument("input_pdf", help="Path to the source PDF.")
    parser.add_argument(
        "output_name",
        help="Desired output filename (will always be created inside this script folder).",
    )
    parser.add_argument(
        "--book-start",
        type=int,
        metavar="PAGE",
        help=(
            "If PDF page 1 corresponds to this textbook page number, supply it so book "
            "page ranges are converted automatically."
        ),
    )
    parser.add_argument(
        "--inspect-max-pages",
        type=int,
        metavar="N",
        help="When using --inspect-text, limit the number of pages written to the txt dump.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Process the entire book.",
    )
    group.add_argument(
        "--chapters",
        nargs="+",
        metavar="LABEL",
        help="One or more predefined chapter labels.",
    )
    group.add_argument(
        "--pages",
        metavar='"RANGES"',
        help='Custom page ranges, e.g. "4044-4120, 4200-4250"',
    )
    group.add_argument(
        "--inspect-text",
        action="store_true",
        help="Diagnostic: dump the existing text layer to a .txt file (no OCR).",
    )
    return parser


def main() -> None:
    script_dir = Path(__file__).resolve().parent

    if len(sys.argv) == 1:
        print(
            "Usage:\n"
            "  Drag and drop a PDF onto this script for interactive mode.\n"
            "  OR use CLI mode, e.g.:\n"
            "    python ocr_textbook.py input.pdf output.pdf --all\n"
            "    python ocr_textbook.py input.pdf chapters.pdf --chapters CNS Heart\n"
            '    python ocr_textbook.py input.pdf selection.pdf --pages "10-20, 35"\n'
        )
        return

    if len(sys.argv) == 2:
        input_pdf = Path(sys.argv[1])
        load_chapters_for_book(input_pdf, script_dir)
        interactive_mode(input_pdf, script_dir)
        return

    parser = build_cli_parser()
    args = parser.parse_args()
    input_pdf = Path(args.input_pdf)
    load_chapters_for_book(input_pdf, script_dir)
    run_cli_mode(args, script_dir)


if __name__ == "__main__":
    main()

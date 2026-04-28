"""Run the raw PPP cleaning pipeline before Stata method prep."""

from pathlib import Path

from sub.PPP_parse_person_names import main as parse_person_names
from sub.PPP_raw_merge_keyword_filter import main as merge_keyword_filter


def find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "Data").is_dir() and (path / "src").is_dir():
            return path
    raise FileNotFoundError("Could not find project root containing Data/ and src/.")


def main() -> None:
    project_root = find_project_root(Path(__file__).resolve())
    print(f"Project root: {project_root}")

    print("\n=== Step 1: raw PPP merge and keyword filter ===")
    merge_keyword_filter(project_root)

    print("\n=== Step 2: PPP person-name parsing ===")
    parse_person_names(project_root)


if __name__ == "__main__":
    main()

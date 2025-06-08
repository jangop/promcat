import click
from pathlib import Path
from typing import Optional, Literal, Iterable
import pathspec
from enum import Enum
from loguru import logger
import dataclasses


class HeaderStyle(str, Enum):
    NEWLINE = "newline"
    SEPARATOR = "separator"
    MARKDOWN = "markdown"
    XML = "xml"


def add_line_numbers(content: str, separator: str = "|") -> str:
    """Add line numbers to content with custom separator."""
    if not content:
        return content

    lines = content.splitlines()
    padding = len(str(len(lines)))

    numbered_lines = [
        f"{str(i + 1).rjust(padding)} {separator} {line}"
        for i, line in enumerate(lines)
    ]

    return "\n".join(numbered_lines)


def format_tree_section(tree: str, style: HeaderStyle) -> str:
    """Format a tree section with the specified style."""
    if style == HeaderStyle.NEWLINE:
        return f"\n\n{tree}"
    elif style == HeaderStyle.SEPARATOR:
        return f"\n=== Directory Tree ===\n{tree}"
    elif style == HeaderStyle.MARKDOWN:
        return f"\n## Directory Tree\n{tree}"
    elif style == HeaderStyle.XML:
        return f"\n<directory_tree>\n{tree}\n</directory_tree>"
    return tree


def format_file_section(
    path: str,
    content: str,
    style: HeaderStyle,
    include_footer: bool = False,
    line_numbers: bool = False,
    number_separator: str = "|",
) -> str:
    """Format a file section with the specified style and options."""
    formatted_content = (
        add_line_numbers(content, number_separator) if line_numbers else content
    )

    if style == HeaderStyle.NEWLINE:
        return f"\n\n{formatted_content}"

    elif style == HeaderStyle.SEPARATOR:
        header = f"\n=== {'start ' if include_footer else ''}{path} ===\n"
        footer = f"\n=== end {path} ===\n" if include_footer else ""
        return f"{header}{formatted_content}{footer}"

    elif style == HeaderStyle.MARKDOWN:
        if path.endswith(".py"):
            header = f"\n# {'start ' if include_footer else ''}{path}\n"
            footer = f"\n# end {path}\n" if include_footer else ""
        else:
            header = f"\n## {'start ' if include_footer else ''}{path}\n"
            footer = f"\n## end {path}\n" if include_footer else ""
        return f"{header}{formatted_content}{footer}"

    elif style == HeaderStyle.XML:
        return f"\n<file>\n<path>{path}</path>\n<content>\n{formatted_content}\n</content>\n</file>"

    return formatted_content  # fallback case


def is_text_file(filepath: Path) -> bool:
    """Heuristically check if a file is likely a text file based on content sampling."""
    try:
        with open(filepath, "rb") as f:
            sample = f.read(1024)
            return not bool(b"\x00" in sample)
    except Exception:
        return False


def get_path_specification(
    root_dir: Path,
    ignore_specification_files: Iterable[Literal[".gitignore", ".promcatignore"]],
    ignore_defaults: bool = True,
) -> pathspec.PathSpec:
    ignore_file_paths = [
        root_dir / ignore_file for ignore_file in ignore_specification_files
    ]
    ignore_file_contents = [
        path.read_text().splitlines() for path in ignore_file_paths if path.exists()
    ]
    ignore_files_lines = [line for lines in ignore_file_contents for line in lines]

    default_ignore_files = [".git", "uv.lock", "package-lock.json"]

    for ignore_file in default_ignore_files:
        if ignore_file not in ignore_files_lines and (root_dir / ignore_file).exists():
            logger.warning(
                f"`{ignore_file}` not in ignore files, but `{ignore_file}` file exists in `{root_dir}`"
            )
        if ignore_defaults:
            logger.info(f"Ignoring `{ignore_file}` file")
            ignore_files_lines.append(ignore_file)

    logger.debug(f"Path specification:\n{ignore_files_lines}")

    return pathspec.PathSpec.from_lines("gitwildmatch", ignore_files_lines)


@dataclasses.dataclass
class FileCollection:
    all_files: list[Path]
    text_files: list[Path]


def collect_files(
    root_dir: Path, path_specification: pathspec.PathSpec
) -> FileCollection:
    """Recursively collect all (text) files in directory."""
    all_files = []
    text_files = []

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue

        if path_specification.match_file(str(path.relative_to(root_dir))):
            continue

        all_files.append(path)

        if not is_text_file(path):
            continue

        text_files.append(path)

    return FileCollection(all_files=all_files, text_files=text_files)


def generate_tree(files: list[Path], root_dir: Path) -> str:
    """Generate a tree representation of the files."""
    tree = {}
    for file in files:
        parts = file.relative_to(root_dir).parts
        current = tree
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current.setdefault(parts[-1], {})

    def build_tree(current: dict, prefix: str = "") -> str:
        lines = []
        entries = sorted(current.keys())
        for i, key in enumerate(entries):
            connector = "└── " if i == len(entries) - 1 else "├── "
            lines.append(f"{prefix}{connector}{key}")
            if isinstance(current[key], dict) and current[key]:
                extension = "    " if i == len(entries) - 1 else "│   "
                lines.append(build_tree(current[key], prefix + extension))
        return "\n".join(lines)

    return build_tree(tree)


@click.command()
@click.argument(
    "directory", type=click.Path(exists=True, path_type=Path), default=Path.cwd()
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (defaults to stdout)",
)
@click.option(
    "--respect-gitignore/--no-respect-gitignore",
    default=True,
    help="Respect .gitignore patterns",
)
@click.option(
    "--respect-promcatignore/--no-respect-promcatignore",
    default=True,
    help="Respect .promcatignore patterns",
)
@click.option(
    "--relative/--absolute",
    default=True,
    help="Use relative or absolute paths in file headers",
)
@click.option(
    "--style",
    type=click.Choice([style.value for style in HeaderStyle]),
    default=HeaderStyle.XML.value,
    help="Header style to use",
)
@click.option(
    "--footer/--no-footer", default=True, help="Include footers for file sections"
)
@click.option(
    "--line-numbers/--no-line-numbers", default=True, help="Add line numbers to output"
)
@click.option(
    "--separator",
    default="|",
    help="Separator between line numbers and content (default: |)",
)
@click.option(
    "--tree/--no-tree",
    default=True,
    help="Include directory tree in the output",
)
def main(
    directory: Path,
    output: Optional[Path],
    respect_gitignore: bool,
    respect_promcatignore: bool,
    relative: bool,
    style: str,
    footer: bool,
    line_numbers: bool,
    separator: str,
    tree: bool,
):
    """Concatenate all text files in a directory, optionally respecting .gitignore and .promcatignore"""
    ignore_files = []
    if respect_gitignore:
        ignore_files.append(".gitignore")
    if respect_promcatignore:
        ignore_files.append(".promcatignore")

    path_specification = get_path_specification(directory, ignore_files)

    file_collection = collect_files(directory, path_specification)

    result = []
    for file_path in file_collection.text_files:
        try:
            path_str = (
                str(file_path.relative_to(directory)) if relative else str(file_path)
            )

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            formatted_section = format_file_section(
                path_str,
                content,
                HeaderStyle(style),
                include_footer=footer,
                line_numbers=line_numbers,
                number_separator=separator,
            )

            result.append(formatted_section)

        except Exception as e:
            click.echo(f"Error reading {file_path}: {e}", err=True)

    if tree:
        tree_representation = generate_tree(file_collection.all_files, directory)
        formatted_tree = format_tree_section(tree_representation, HeaderStyle(style))
        result.append(formatted_tree)

    output_text = "".join(result)

    if output:
        output.write_text(output_text)
        click.echo(f"Output written to {output}")
    else:
        click.echo(output_text)


if __name__ == "__main__":
    main()

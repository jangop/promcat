import click
from pathlib import Path
from typing import Optional, Literal, Iterable
from gitignore_parser import parse_gitignore
from enum import Enum


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


def format_file_section(
    path: str,
    content: str,
    style: HeaderStyle,
    include_footer: bool = False,
    line_numbers: bool = False,
    separator: str = "|",
) -> str:
    """Format a file section with the specified style and options."""
    formatted_content = (
        add_line_numbers(content, separator) if line_numbers else content
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


def get_ignore_matcher(
    root_dir: Path, ignore_file: Literal[".gitignore", ".promcatignore"] = ".gitignore"
) -> Optional[callable]:
    """Create an ignore matcher function if the ignore file exists."""
    ignore_path = root_dir / ignore_file
    if ignore_path.exists():
        return parse_gitignore(ignore_path)
    return None


def collect_text_files(
    root_dir: Path, ignore_matchers: Iterable[callable] = []
) -> list[Path]:
    """Recursively collect all text files in directory."""
    text_files = []

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue

        if any(
            ignore_matcher and ignore_matcher(str(path))
            for ignore_matcher in ignore_matchers
        ):
            continue

        # Hard-reject .git and .venv directories
        relative_path = path.relative_to(root_dir)
        if str(relative_path).startswith((".git", ".venv", "target")):
            continue

        if is_text_file(path):
            text_files.append(path)

    return text_files


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
    type=click.Choice(["newline", "separator", "markdown", "xml"]),
    default="separator",
    help="Header style to use",
)
@click.option(
    "--footer/--no-footer", default=False, help="Include footers for file sections"
)
@click.option(
    "--line-numbers/--no-line-numbers", default=False, help="Add line numbers to output"
)
@click.option(
    "--separator",
    default="|",
    help="Separator between line numbers and content (default: |)",
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
):
    """Concatenate all text files in a directory, optionally respecting .gitignore and .promcatignore"""
    ignore_matchers = []
    if respect_gitignore:
        ignore_matchers.append(get_ignore_matcher(directory, ".gitignore"))
    if respect_promcatignore:
        ignore_matchers.append(get_ignore_matcher(directory, ".promcatignore"))

    text_files = collect_text_files(directory, ignore_matchers)

    result = []
    for file_path in text_files:
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
                separator=separator,
            )

            result.append(formatted_section)

        except Exception as e:
            click.echo(f"Error reading {file_path}: {e}", err=True)

    output_text = "".join(result)

    if output:
        output.write_text(output_text)
        click.echo(f"Output written to {output}")
    else:
        click.echo(output_text)


if __name__ == "__main__":
    main()

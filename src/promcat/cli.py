from pathlib import Path
from typing import Optional

import click

from promcat.core import (
    HeaderStyle,
    collect_files,
    format_file_section,
    format_tree_section,
    generate_tree,
    get_path_specification,
)


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

        except (IOError, UnicodeDecodeError) as e:
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

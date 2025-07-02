import pytest

from promcat.cli import (
    is_text_file,
    collect_files,
    format_file_section,
    HeaderStyle,
    add_line_numbers,
    get_path_specification,
)


@pytest.mark.parametrize(
    "file_content, is_binary, expected_result",
    [
        ("This is a text file.", False, True),
        (b"\x00\x01\x02\x03", True, False),
        ("", False, True),
    ],
)
def test_is_text_file(tmp_path, file_content, is_binary, expected_result):
    file_path = tmp_path / "test_file"
    if is_binary:
        file_path.write_bytes(file_content)
    else:
        file_path.write_text(file_content)
    assert is_text_file(file_path) == expected_result


def test_is_text_file_non_existent(tmp_path):
    non_existent_file = tmp_path / "non_existent.txt"
    assert is_text_file(non_existent_file) is False


def test_collect_text_files(tmp_path):
    # Create test directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1/test1.txt").write_text("test1")
    (tmp_path / "dir1/test2.txt").write_text("test2")

    # Create an empty path specification (no ignore patterns)
    path_spec = get_path_specification(tmp_path, [])

    file_collection = collect_files(tmp_path, path_spec)
    files = [str(f.relative_to(tmp_path)) for f in file_collection.all_files]
    assert len(files) == 2
    assert "dir1/test1.txt" in files
    assert "dir1/test2.txt" in files

    # Test with ignore pattern
    (tmp_path / ".gitignore").write_text(
        "*.txt\n.gitignore"
    )  # Also ignore .gitignore itself
    path_spec = get_path_specification(tmp_path, [".gitignore"])
    file_collection = collect_files(tmp_path, path_spec)
    files = [str(f.relative_to(tmp_path)) for f in file_collection.all_files]
    assert len(files) == 0, (
        f"Found unexpected files: {files}"
    )  # All files should be ignored


@pytest.mark.parametrize(
    "content, separator, expected",
    [
        ("Line 1\nLine 2\nLine 3", "|", "1 | Line 1\n2 | Line 2\n3 | Line 3"),
        ("Single line", "|", "1 | Single line"),
        ("", "|", ""),
        ("Line A\nLine B", ">", "1 > Line A\n2 > Line B"),
        (
            "\n".join([f"Line {i}" for i in range(1, 101)]),
            "|",
            "\n".join([f"{str(i).rjust(3)} | Line {i}" for i in range(1, 101)]),
        ),
    ],
)
def test_add_line_numbers(content, separator, expected):
    assert add_line_numbers(content, separator) == expected


def test_format_file_section():
    content = "test content"
    path = "test.txt"

    # Test with line numbers and custom separator
    section = format_file_section(
        path, content, HeaderStyle.SEPARATOR, line_numbers=True, number_separator=">"
    )
    assert "1 > test content" in section


def test_gitignore_patterns(tmp_path):
    # Create test directory structure
    root = tmp_path
    (root / ".gitignore").write_text("/root-build\nbuild-anywhere")

    # Create test files and directories
    (root / "root-build").mkdir()
    (root / "root-build" / "file.txt").write_text("root build file")

    (root / "src").mkdir()
    (root / "src" / "build-anywhere").mkdir()
    (root / "src" / "build-anywhere" / "file.txt").write_text("nested build file")

    (root / "src" / "root-build").mkdir()
    (root / "src" / "root-build" / "file.txt").write_text("nested root-build file")

    (root / "src" / "code.txt").write_text("regular file")

    # Get path specification
    path_spec = get_path_specification(root, [".gitignore"])

    # Collect files
    file_collection = collect_files(root, path_spec)
    files = [str(f.relative_to(root)) for f in file_collection.all_files]

    # /root-build should only exclude at root level
    assert "root-build/file.txt" not in files, (
        "Root-level pattern should exclude at root"
    )
    assert "src/root-build/file.txt" in files, (
        "Root-level pattern should not exclude in subdirectories"
    )

    # build-anywhere should exclude everywhere
    assert "src/build-anywhere/file.txt" not in files, (
        "Non-root pattern should exclude in subdirectories"
    )

    # Regular files should not be excluded
    assert "src/code.txt" in files, "Regular files should not be excluded"


def test_gitignore_empty_and_comments(tmp_path):
    # Create test directory structure
    root = tmp_path
    (root / ".gitignore").write_text("""
# This is a comment
/root-build

# Empty lines and comments should be ignored

build-anywhere
""")

    # Create test files
    (root / "root-build").mkdir()
    (root / "root-build" / "file.txt").write_text("root build file")

    (root / "src").mkdir()
    (root / "src" / "build-anywhere").mkdir()
    (root / "src" / "build-anywhere" / "file.txt").write_text("nested build file")

    # Get path specification
    path_spec = get_path_specification(root, [".gitignore"])

    # Collect files
    file_collection = collect_files(root, path_spec)
    files = [str(f.relative_to(root)) for f in file_collection.all_files]

    # Verify patterns work with comments and empty lines
    assert "root-build/file.txt" not in files, (
        "Root-level pattern should work with comments"
    )
    assert "src/build-anywhere/file.txt" not in files, (
        "Non-root pattern should work with comments"
    )

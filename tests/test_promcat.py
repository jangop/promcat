from promcat.cli import (
    is_text_file,
    collect_text_files,
    format_file_section,
    HeaderStyle,
    add_line_numbers,
)


def test_is_text_file(tmp_path):
    # Test text file
    text_file = tmp_path / "test.txt"
    text_file.write_text("Hello, world!")
    assert is_text_file(text_file)

    # Test binary file
    binary_file = tmp_path / "test.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03")
    assert not is_text_file(binary_file)


def test_collect_text_files(tmp_path):
    # Create test directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1/test1.txt").write_text("test1")
    (tmp_path / "dir1/test2.txt").write_text("test2")

    files = collect_text_files(tmp_path)
    assert len(files) == 2
    assert all(f.suffix == ".txt" for f in files)


def test_add_line_numbers():
    content = "line1\nline2\nline3"

    # Test default separator
    numbered = add_line_numbers(content)
    assert "1 | line1" in numbered
    assert "3 | line3" in numbered

    # Test custom separator
    numbered = add_line_numbers(content, ">")
    assert "1 > line1" in numbered
    assert "3 > line3" in numbered

    # Test padding
    content = "line1\n" * 100
    numbered = add_line_numbers(content)
    assert "  1 | line1" in numbered
    assert "100 | line1" in numbered


def test_format_file_section():
    content = "test content"
    path = "test.txt"

    # Test with line numbers and custom separator
    section = format_file_section(
        path, content, HeaderStyle.SEPARATOR, line_numbers=True, number_separator=">"
    )
    assert "1 > test content" in section

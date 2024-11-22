# promcat

A command-line tool for concatenating text files in a directory tree, designed for creating context files for LLM prompting.

## Features

- Recursively finds and concatenates all text files in a directory
- Respects `.gitignore` patterns (optional)
- Multiple header styles for file sections
- Line numbering support
- Customizable path display (relative/absolute)
- Various output formatting options

## Installation

Using `uv`:

```bash
uv venv
source .venv/bin/activate  # or Windows equivalent
uv pip install -e .
```

## Usage

Basic usage:
```bash
promcat                     # Process current directory, output to stdout
promcat /path/to/project   # Process specific directory
promcat -o output.txt      # Save to file instead of stdout
```

### Options

```bash
--output, -o              Output file path (defaults to stdout)
--respect-gitignore       Honor .gitignore patterns
--relative/--absolute     Use relative or absolute paths in headers
--style                   Header style (newline|separator|markdown|xml)
--footer                  Include footers for file sections
--line-numbers           Add line numbers to output
--separator              Custom separator for line numbers (default: '|')
```

### Header Styles

1. Newline (`--style newline`):
```
content of file 1

content of file 2
```

2. Separator (`--style separator`):
```
=== file1.txt ===
content of file 1
=== end file1.txt ===
```

3. Markdown (`--style markdown`):
```
## file1.txt
content of file 1
## end file1.txt

# script.py
content of script
# end script.py
```

4. XML (`--style xml`):
```
<file><path>file1.txt</path><content>content of file 1</content></file>
```

### Line Numbers

Add line numbers with custom separator:
```bash
promcat --line-numbers --separator ' > '
```

Output:
```
=== file1.txt ===
  1 > First line
  2 > Second line
```

## Use Cases

1. Creating context files for LLM prompting
2. Combining multiple source files for analysis
3. Creating documentation from source files
4. Code review and auditing
5. Creating backups of text content

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

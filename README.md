# PDF to Markdown Converter

A Python-based tool for converting PDF lecture slides into clean, organized Markdown notes. Perfect for students who want to maintain their notes in Markdown format, especially for use with note-taking apps like Obsidian.

## Features

- **Smart Heading Detection**: Automatically identifies and formats lecture titles and slide headings
- **Code Block Detection**: Recognizes and properly formats code snippets with language-specific syntax highlighting
  - Supports Java, C, Python, and Haskell
  - Automatically detects programming language based on syntax
- **Clean Formatting**:
  - Converts bullet points into proper Markdown lists
  - Joins related sentences for better readability
  - Removes page numbers and other artifacts
  - Maintains proper spacing between sections
- **Content Organization**:
  - Preserves hierarchical structure of slides
  - Distinguishes between main topics and subtopics
  - Groups related content together

## Usage

1. Place your PDF files in the desired directory
2. Run the converter:
```bash
python convert.py "path/to/your/file.pdf"
```
or 
```bash
python convert.py --watch
```
- The second method will run constantly and will convert every pdf file to markdown until process is stopped.

3. Find the converted Markdown file in the same directory with `.md` extension

## Requirements

- Python 3.6+
- PyPDF2 library for PDF processing

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/pdf-to-markdown.git
cd pdf-to-markdown
```

2. Install dependencies:
```bash
pip install PyPDF2
```

## How It Works

The converter uses several sophisticated algorithms to process the PDF:

1. **Text Extraction**: Extracts raw text from PDF while preserving structure
2. **Content Analysis**: 
   - Identifies headings using natural language processing
   - Detects code blocks using syntax patterns
   - Recognizes and preserves list structures
3. **Smart Formatting**:
   - Joins related sentences into coherent paragraphs
   - Formats code with appropriate language tags
   - Maintains clean, consistent spacing

## Future Features

- Table detection and formatting
- Image extraction and linking
- Mathematical equation support
- Batch processing of multiple PDFs
- Watch folder for automatic conversion
- Custom templates and styling
- Direct Obsidian integration
- AI-powered content summarization

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyPDF2 library for PDF processing
- The Obsidian community for inspiration
- All contributors and users of this tool

potential features
Here are potential features we could add to improve the converter:

Content Enhancement:
Code block detection and proper formatting with java or python tags
Table detection and conversion to markdown tables
Image extraction and saving as separate files with proper markdown links
Smart list detection (numbered lists vs bullet points)
Better handling of indentation levels for nested lists
Smart Processing:
Detect and preserve important formatting (bold, italic) from PDFs
Merge related bullet points into coherent paragraphs when appropriate
Remove redundant or repeated content
Handle mathematical equations and formulas (convert to LaTeX or ASCII math)
Smart handling of footnotes and references
Organization Features:
Auto-generate table of contents
Add YAML frontmatter with metadata (date, course, topic)
Add tags based on content analysis
Group related content into sections
Cross-reference similar content across different files
Batch Processing:
Process multiple PDFs at once
Watch folder for new PDFs to auto-convert
Maintain a consistent structure across all converted files
Generate an index file linking all related notes
Customization:
Configuration file for user preferences
Custom templates for different types of content
Adjustable heading detection rules
Custom formatting rules for specific content types
Ignore patterns for unwanted content
Quality of Life:
Progress bar during conversion
Preview mode to see conversion results
Backup original files
Diff view to compare original and converted content
Error logging and reporting
Integration:
Direct integration with Obsidian (via plugin)
Support for Obsidian-specific features (internal links, callouts)
Export to other formats (HTML, DocX)
Version control integration
Intelligence:
AI-powered content summarization
Automatic keyword extraction
Smart section reorganization
Question generation for study purposes
Related content suggestions

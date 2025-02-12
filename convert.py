#!/usr/bin/env python3
# python convert.py --watch
import os
import re
import time
from pathlib import Path
import PyPDF2
from typing import List, Tuple
import argparse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PDFConverter:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.output_path = self._get_output_path()

    def _get_output_path(self) -> str:
        """Convert PDF path to markdown path in the same directory."""
        pdf_path = Path(self.pdf_path)
        return str(pdf_path.with_suffix('.md'))

    def _clean_text(self, text: str) -> str:
        """Clean up text by removing extra whitespace and normalizing characters."""
        if not text:
            return ""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,;:!?)])', r'\1', text)
        # Add space after punctuation if not followed by space
        text = re.sub(r'([.,;:!?)])(?!\s|$)', r'\1 ', text)
        # Remove standalone numbers (likely page numbers)
        text = re.sub(r'^\s*\d+\s*$', '', text)
        return text.strip()

    def _is_heading(self, line: str) -> tuple[bool, bool]:
        """Detect if a line is likely a heading."""
        # Remove numbers and spaces from start
        clean_line = re.sub(r'^\d+\.?\s*', '', line).strip()
        
        # Skip if line is empty or starts with common non-heading indicators
        if not clean_line or clean_line.startswith(('-', '•', '*', '{', '}', '//', '/*', '*/')):
            return False, False
            
        # Skip code-like lines
        if any(code_indicator in clean_line.lower() for code_indicator in 
            ['public class', 'private class', 'protected class', 'void', 'new', 'system.out']):
            return False, False
            
        # Skip lines that look like method calls or variable assignments
        if re.search(r'[=;()\[\]]', clean_line):
            return False, False
            
        # Skip lines that are too long to be headings
        if len(clean_line) > 100:
            return False, False
            
        # Special cases for main headings
        if (re.match(r'^COMP\d{4}$', clean_line) or
            'lecture' in clean_line.lower() or
            'introduction to' in clean_line.lower()):
            return True, True  # (is_heading, is_main_heading)
            
        # Look for characteristics of slide titles/subheadings
        words = clean_line.split()
        return (
            clean_line[0].isupper() and  # Starts with uppercase
            not clean_line.endswith(('.', ',')) and  # Doesn't end with certain punctuation
            not re.search(r'["\']', clean_line) and  # No quotes
            (
                # Common heading words or patterns
                any(word in clean_line.lower() for word in [
                    'overview', 'summary', 'example', 'design',
                    'concepts', 'principles', 'fundamentals', 'types',
                    'using', 'creating', 'working', 'understanding',
                    'comparison', 'differences', 'features', 'basics',
                    'introduction', 'getting started', 'key points',
                    'what is', 'how to', 'why', 'when', 'where',
                    'objects', 'classes', 'methods', 'functions',
                    'variables', 'data', 'memory', 'stack', 'heap'
                ]) or
                # Short phrases that look like titles (2-6 words)
                (1 < len(words) <= 6 and
                 all(len(w) > 1 for w in words) and  # All words are at least 2 chars
                 not any(char in clean_line for char in '.,;()') and
                 not any(w.lower() in ['and', 'or', 'but', 'yet'] for w in words[1:]))  # No conjunctions except at start
            )
        ), False  # (is_heading, is_main_heading)

    def _is_code_line(self, line: str) -> bool:
        """Detect if a line is likely code."""
        # Check for common code indicators
        code_indicators = [
            r'^\s*[{}()\[\];]\s*$',  # Just brackets/semicolons
            r'^\s*public\s+|private\s+|protected\s+',  # Access modifiers
            r'^\s*class\s+\w+',  # Class definitions
            r'^\s*\w+\s*\([^)]*\)\s*[{;]?\s*$',  # Method definitions/calls
            r'^\s*\w+\s*=\s*\w+',  # Variable assignments
            r'^\s*import\s+|package\s+',  # Import/package statements
            r'^\s*//|/\*|\*/',  # Comments
            r'.*\w+\s*\.\s*\w+\s*\([^)]*\)',  # Method calls with dot notation
            r'.*malloc\s*\(|fopen\s*\(|printf\s*\(',  # C function calls
            r'.*->\w+',  # C pointer access
        ]
        return any(re.search(pattern, line) for pattern in code_indicators)

    def _should_join_with_previous(self, current: str, previous: str) -> bool:
        """Determine if the current line should be joined with the previous line."""
        if not previous or not current:
            return False
            
        # Don't join code lines
        if self._is_code_line(current) or self._is_code_line(previous):
            return False
            
        # Don't join if previous line ends with period and current starts with capital
        if previous.endswith('.') and current[0].isupper():
            return False
            
        # Always join if the previous line ends with a connector
        connectors = (':', ',', '-', '–', '—', '(')
        if any(previous.rstrip().endswith(c) for c in connectors):
            return True
            
        # Join if previous line ends with these words
        connecting_words = (' the', ' a', ' an', ' to', ' of', ' in', ' on', ' with', ' by', ' for')
        if any(previous.rstrip().lower().endswith(word) for word in connecting_words):
            return True
            
        # Join if current line starts with lowercase or these characters
        if any(current.lstrip().startswith(c) for c in (')', ']', '}', ',', '.', ':', ';')):
            return True
            
        # Join if current line starts with these words
        continuing_words = ('and ', 'or ', 'but ', 'nor ', 'for ', 'so ', 'yet ', 'which ', 'that ', 'where ', 'when ', 'while ')
        if any(current.lstrip().lower().startswith(word) for word in continuing_words):
            return True
            
        # Join if previous line doesn't end with terminal punctuation and current doesn't start with capital
        if not any(previous.endswith(p) for p in '.!?') and (
            not current[0].isupper() or  # current starts with lowercase
            len(current) == 1 or  # current is a single character
            current.startswith(('etc', 'eg', 'ie'))  # current starts with common abbreviations
        ):
            return True
            
        return False

    def _detect_language(self, code: str) -> str:
        """Detect the programming language of a code block."""
        # Common language indicators
        indicators = {
            'java': [
                r'\bpublic\s+class\b', r'\bprivate\s+class\b',
                r'\bSystem\.out\b', r'\bString\[\]\s+args\b',
                r'\bextends\b', r'\bimplements\b',
                r'\bvoid\b', r'\bnew\b'
            ],
            'c': [
                r'\bprintf\b', r'\bscanf\b', r'\bmalloc\b',
                r'\bfree\b', r'\bNULL\b', r'\bstruct\b',
                r'\bchar\s*\*\b', r'\bint\s+main\b',
                r'\bfopen\b', r'\bfclose\b'
            ],
            'python': [
                r'\bdef\s+\w+\b', r'\bclass\s+\w+\b',
                r'\bself\b', r'\bprint\b', r'\bimport\b',
                r'\bif\s+__name__\s*==\s*[\'"]__main__[\'"]\b'
            ],
            'haskell': [
                r'\bmodule\b', r'\bwhere\b', r'\bdata\b',
                r'\btype\b', r'\bnewtype\b', r'\bderiving\b',
                r'\b::\b', r'\b<-\b', r'\b->\b'
            ]
        }
        
        # Check each language's indicators
        matches = {lang: sum(1 for pattern in patterns if re.search(pattern, code))
                  for lang, patterns in indicators.items()}
        
        # If we have matches, return the language with the most matches
        if any(matches.values()):
            return max(matches.items(), key=lambda x: x[1])[0]
            
        # Default to text if no clear language is detected
        return 'text'

    def _format_code_block(self, code: str) -> str:
        """Format a code block with proper language tags."""
        # Clean up the code
        code = code.strip()
        if not code:
            return ''
            
        # Detect the language
        language = self._detect_language(code)
        
        # Format with markdown code block
        return f'```{language}\n{code}\n```'

    def _is_code_block(self, lines: List[str]) -> bool:
        """Detect if a group of lines is likely a code block."""
        if not lines:
            return False
            
        # Join lines for easier analysis
        text = '\n'.join(lines)
        
        # Code block indicators
        indicators = [
            # Common programming constructs
            r'\b(public|private|protected)\s+(class|void|static)\b',
            r'\b(def|class)\s+\w+\s*[:(]',
            r'\b(module|import|package)\s+\w+',
            r'\b(if|for|while|switch)\s*\(',
            r'\b(return|break|continue)\b',
            # Common syntax patterns
            r'[{};]\s*$',  # Lines ending with {, }, or ;
            r'^\s*[\]}]',  # Lines starting with ] or }
            r'=>|->',      # Arrow syntax
            r'\b\w+\s*\([^)]*\)\s*[{;]?$',  # Function calls/definitions
            # Indentation and brackets
            r'^\s{4,}',    # Significant indentation
            r'\{[^}]*\}',  # Curly brace blocks
            # Comments
            r'^\s*(//|#|/\*|\*)',
            # Variable declarations
            r'\b(var|let|const|int|char|bool|String)\s+\w+\s*=',
        ]
        
        # Check if the text matches code patterns
        code_line_count = sum(1 for line in lines if any(re.search(pattern, line) for pattern in indicators))
        
        # Consider it code if more than 30% of lines match code patterns
        return code_line_count / len(lines) > 0.3 if lines else False

    def _format_content(self, text: str) -> List[str]:
        """Format the content into a clean structure."""
        lines = text.split('\n')
        formatted_lines = []
        current_heading = None
        current_content = []
        current_code_block = []
        in_code_block = False
        
        for line in lines:
            line = self._clean_text(line)
            if not line or line.lower().startswith(('page', 'slide')):
                continue
                
            # Skip standalone numbers (likely page numbers)
            if re.match(r'^\d+$', line.strip()):
                continue

            # Check if it's a heading
            is_heading, is_main_heading = self._is_heading(line)
            if is_heading:
                # First, flush any code block if we have one
                if current_code_block:
                    formatted_lines.append(self._format_code_block('\n'.join(current_code_block)))
                    current_code_block = []
                    in_code_block = False
                
                # Then flush any accumulated content
                if current_content:
                    formatted_lines.append(f"- {' '.join(current_content)}")
                    current_content = []
                
                # Add the heading
                heading = re.sub(r'^\d+\.?\s*', '', line).strip()
                if is_main_heading:
                    formatted_lines.append(f'# {heading}')
                else:
                    formatted_lines.append(f'## {heading}')
                current_heading = heading
            else:
                # Clean up the line
                content = re.sub(r'^[-–—•*]\s*', '', line)
                content = re.sub(r'^[-–—]\s*', '', content)
                content = re.sub(r'^\d+\.\s*', '', content)
                content = content.strip()
                
                if not content:
                    continue

                # Check if we're in or should start a code block
                if in_code_block or (not current_code_block and self._is_code_line(content)):
                    # If we have regular content, flush it first
                    if current_content:
                        formatted_lines.append(f"- {' '.join(current_content)}")
                        current_content = []
                    
                    current_code_block.append(content)
                    in_code_block = True
                    
                    # Check if we should end the code block
                    if len(current_code_block) >= 2 and not self._is_code_block(current_code_block):
                        # Not actually a code block, convert back to regular content
                        current_content.extend(current_code_block)
                        current_code_block = []
                        in_code_block = False
                else:
                    # If we have a code block, flush it first
                    if current_code_block:
                        formatted_lines.append(self._format_code_block('\n'.join(current_code_block)))
                        current_code_block = []
                        in_code_block = False
                    
                    # Handle regular content
                    if current_content and self._should_join_with_previous(content, current_content[-1]):
                        current_content.append(content)
                    else:
                        if current_content:
                            formatted_lines.append(f"- {' '.join(current_content)}")
                        current_content = [content]

        # Don't forget to flush any remaining content
        if current_code_block:
            formatted_lines.append(self._format_code_block('\n'.join(current_code_block)))
        elif current_content:
            formatted_lines.append(f"- {' '.join(current_content)}")

        # Add appropriate spacing around headers and code blocks
        result = []
        for i, line in enumerate(formatted_lines):
            if line.startswith(('#', '```')):
                # Add a blank line before headers and code blocks (except the first one)
                if i > 0:
                    result.append('')
                result.append(line)
                # Add a blank line after headers and code blocks
                if not line.startswith('```') or i == len(formatted_lines) - 1:
                    result.append('')
            else:
                result.append(line)

        return result

    def convert(self):
        """Convert PDF to markdown format."""
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                all_text = []
                
                # Extract text from all pages
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    all_text.append(text)

                # Join all text and format
                complete_text = '\n'.join(all_text)
                formatted_lines = self._format_content(complete_text)

                # Write to markdown file
                with open(self.output_path, 'w', encoding='utf-8') as md_file:
                    md_file.write('\n'.join(formatted_lines))

                print(f"Successfully converted {self.pdf_path} to {self.output_path}")

        except Exception as e:
            print(f"Error converting PDF: {str(e)}")

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith('.pdf'):
            print(f"New PDF detected: {event.src_path}")
            converter = PDFConverter(event.src_path)
            converter.convert()

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith('.pdf'):
            print(f"PDF modified: {event.src_path}")
            converter = PDFConverter(event.src_path)
            converter.convert()

def watch_directories(base_path: str):
    """Watch all course directories for PDF files."""
    observer = Observer()
    event_handler = PDFHandler()
    
    # Watch base directory and all its subdirectories
    for root, dirs, files in os.walk(base_path):
        observer.schedule(event_handler, root, recursive=False)
        print(f"Watching directory: {root}")
        
        # Convert any existing PDFs
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                converter = PDFConverter(pdf_path)
                converter.convert()

    observer.start()
    print(f"\nWatching for PDF files in {base_path} and its subdirectories...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping PDF watcher...")
    
    observer.join()

def main():
    parser = argparse.ArgumentParser(description='Convert PDF to Markdown format')
    parser.add_argument('--watch', action='store_true', help='Watch directories for PDF files')
    parser.add_argument('pdf_path', nargs='?', help='Path to the PDF file (optional if --watch is used)')
    args = parser.parse_args()

    if args.watch:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        watch_directories(base_path)
    elif args.pdf_path:
        converter = PDFConverter(args.pdf_path)
        converter.convert()
    else:
        print("Please either specify a PDF file or use --watch option")

if __name__ == "__main__":
    main()

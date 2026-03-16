import re
from pathlib import Path
from html.parser import HTMLParser
from typing import Optional


class TableHTMLParser(HTMLParser):
    """Parse HTML tables and convert to markdown format with colspan/rowspan support."""
    
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = []
        self.current_cell = ""
        self.in_cell = False
        self.cell_type = None  # 'th' or 'td'
        self.colspan = 1
        self.rowspan = 1
        self.cell_attrs = []  # Store attrs for each cell
    
    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.current_row = []
            self.cell_attrs = []
        elif tag in ("td", "th"):
            self.in_cell = True
            self.cell_type = tag
            self.current_cell = ""
            # Extract colspan and rowspan
            self.colspan = 1
            self.rowspan = 1
            for attr_name, attr_value in attrs:
                if attr_name == "colspan":
                    self.colspan = int(attr_value) if attr_value else 1
                elif attr_name == "rowspan":
                    self.rowspan = int(attr_value) if attr_value else 1
    
    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())
            self.cell_attrs.append({
                'colspan': self.colspan,
                'rowspan': self.rowspan
            })
        elif tag == "tr" and self.current_row:
            self.rows.append({
                'cells': self.current_row,
                'attrs': self.cell_attrs
            })
    
    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


class PDFPreprocessor:
    """
    Class for preprocessing PDF extraction files.
    Converts HTML to Markdown and cleans content.
    """
    
    def __init__(self):
        self.page_break_marker = "~~~PRESERVE_PAGE_BREAK~~~"
    
    def html_table_to_markdown(self, html_table: str) -> str:
        """
        Convert a single HTML table to markdown format.
        Properly handles colspan and rowspan attributes.
        """
        parser = TableHTMLParser()
        try:
            parser.feed(html_table)
        except Exception as e:
            # If parsing fails, return original with minimal cleanup
            return html_table
        
        if not parser.rows:
            return ""
        
        # Build a grid to handle colspan/rowspan
        # First pass: determine grid dimensions
        max_cols = 0
        for row_data in parser.rows:
            cols_count = sum(attr['colspan'] for attr in row_data['attrs'])
            max_cols = max(max_cols, cols_count)
        
        num_rows = len(parser.rows)
        
        # Create empty grid
        grid = [['' for _ in range(max_cols)] for _ in range(num_rows)]
        
        # Track which cells are occupied by rowspan
        occupied = [[False for _ in range(max_cols)] for _ in range(num_rows)]
        
        # Fill the grid
        for row_idx, row_data in enumerate(parser.rows):
            col_idx = 0
            cell_idx = 0
            
            while cell_idx < len(row_data['cells']):
                # Skip occupied cells
                while col_idx < max_cols and occupied[row_idx][col_idx]:
                    col_idx += 1
                
                if col_idx >= max_cols:
                    break
                
                cell_value = row_data['cells'][cell_idx]
                cell_attr = row_data['attrs'][cell_idx]
                colspan = cell_attr['colspan']
                rowspan = cell_attr['rowspan']
                
                # Fill the cell and handle colspan/rowspan
                for r in range(rowspan):
                    for c in range(colspan):
                        if row_idx + r < num_rows and col_idx + c < max_cols:
                            if r == 0 and c == 0:
                                grid[row_idx + r][col_idx + c] = cell_value
                            else:
                                grid[row_idx + r][col_idx + c] = ''  # Empty for spanned cells
                            occupied[row_idx + r][col_idx + c] = True
                
                col_idx += colspan
                cell_idx += 1
        
        # Convert grid to markdown
        md_lines = []
        
        for row_idx, row in enumerate(grid):
            # Escape pipes and newlines in cells
            escaped_cells = []
            for cell in row:
                cell = str(cell).strip()
                cell = cell.replace("|", "\\|")
                cell = cell.replace("\n", " ")
                escaped_cells.append(cell)
            
            md_lines.append("| " + " | ".join(escaped_cells) + " |")
            
            # Add separator after row 1 (assumes first 2 rows are headers)
            if row_idx == 1:
                separator = "| " + " | ".join(["---"] * len(escaped_cells)) + " |"
                md_lines.append(separator)
        
        return "\n".join(md_lines)
    
    def clean_markdown_content(self, markdown_content: str) -> str:
        """
        Clean markdown content (string) by:
        1. Preserve <!-- PAGE BREAK --> tokens with unique marker
        2. Remove all <a id='...'></a> anchors
        3. Remove <::attestation:...::> blocks
        4. Remove <::logo:...::> blocks
        5. Convert HTML tables to markdown
        6. Remove remaining HTML tags
        7. Clean up extra whitespace
        8. Restore <!-- PAGE BREAK --> tokens
        
        Args:
            markdown_content: String content to clean
            
        Returns:
            Cleaned markdown content as string
        """
        text = markdown_content
        
        # STEP 1: Preserve page breaks with unique marker BEFORE any HTML processing
        text = text.replace("<!-- PAGE BREAK -->", self.page_break_marker)
        
        # STEP 2: Remove <a id='...'></a> anchors
        text = re.sub(r"<a id='[^']*'></a>\s*", "", text)
        
        # STEP 3: Remove <::attestation:...::> blocks (multiline)
        text = re.sub(r"<::attestation:.*?::>\s*", "", text, flags=re.DOTALL)
        
        # STEP 4: Remove <::logo:...::> blocks (multiline)
        text = re.sub(r"<::logo:.*?::>\s*", "", text, flags=re.DOTALL)
        
        # STEP 5: Convert HTML tables to markdown
        table_pattern = r"<table[^>]*>.*?</table>"
        
        def replace_table(match):
            html_table = match.group(0)
            md_table = self.html_table_to_markdown(html_table)
            return "\n\n" + md_table + "\n\n" if md_table else ""
        
        text = re.sub(table_pattern, replace_table, text, flags=re.DOTALL | re.IGNORECASE)
        
        # STEP 6: Remove any remaining HTML tags (but keep content)
        text = re.sub(r"<[^>]+>", "", text)
        
        # STEP 7: Clean up multiple consecutive newlines
        text = re.sub(r"\n\n\n+", "\n\n", text)
        
        # STEP 8: Strip leading/trailing whitespace from each line
        lines = text.split("\n")
        lines = [line.rstrip() for line in lines]
        text = "\n".join(lines)
        
        # STEP 9: Restore page breaks
        text = text.replace(self.page_break_marker, "<!-- PAGE BREAK -->")
        
        # STEP 10: Final cleanup
        text = text.strip() + "\n"
        
        return text
    
    def clean_and_convert_extraction(self, input_path: str, output_path: str) -> None:
        """
        Process extraction.md file:
        1. Preserve <!-- PAGE BREAK --> tokens with unique marker
        2. Remove all <a id='...'></a> anchors
        3. Remove <::attestation:...::> blocks
        4. Remove <::logo:...::> blocks
        5. Convert HTML tables to markdown
        6. Remove remaining HTML tags
        7. Clean up extra whitespace
        8. Restore <!-- PAGE BREAK --> tokens
        Save result to output file.
        """
        # Read input file
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        text = input_file.read_text(encoding="utf-8")
        
        # Use clean_markdown_content for processing
        text = self.clean_markdown_content(text)
        
        # Write output file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(text, encoding="utf-8")
        
        print(f"Successfully processed extraction file")
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print(f"Output file size: {len(text)} bytes")
        
        return text
    
    def process_folder(self, input_folder: str, output_folder: str) -> list:
        """
        Process all .extraction.md files in a folder.
        Returns list of processed files.
        """
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        
        processed_files = []
        
        # Find all .extraction.md files
        for file_path in input_path.glob("*.extraction.md"):
            # Tạo tên file output
            output_file = output_path / file_path.name.replace(".extraction.md", "_cleaned.md")
            
            try:
                self.clean_and_convert_extraction(str(file_path), str(output_file))
                processed_files.append({
                    'input': str(file_path),
                    'output': str(output_file)
                })
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        print(f"\nProcessed {len(processed_files)} files")
        return processed_files


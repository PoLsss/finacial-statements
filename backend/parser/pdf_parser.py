import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class PDFParser:
    """
    Class for parsing and chunking PDF with table preservation.
    """
    
    def __init__(self, chunk_size_tokens: int = 1000, overlap_sentences: int = 2):
        self.chunk_size_tokens = chunk_size_tokens
        self.overlap_sentences = overlap_sentences
    
    def extract_tables(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract all markdown tables from text.
        Returns list of (table_text, start_pos, end_pos)
        """
        tables = []
        # Match markdown tables: | ... | on multiple lines
        pattern = r'(\|[^\n]*\|\s*\n(?:\|[-\s|]+\|\s*\n)?(?:\|[^\n]*\|\s*\n)+)'
        
        for match in re.finditer(pattern, text):
            tables.append((match.group(1).strip(), match.start(), match.end()))
        
        return tables

    def split_text_preserve_tables(self, text: str) -> List[Dict]:
        """
        Split text into components, preserving tables as atomic units.
        Returns list of {'type': 'text'|'table', 'content': str, 'table_index': int (for tables)}
        """
        components = []
        tables = self.extract_tables(text)
        
        if not tables:
            # No tables, return whole text
            return [{'type': 'text', 'content': text.strip()}]
        
        last_end = 0
        table_idx = 0
        
        for table_text, start, end in tables:
            # Add text before table
            if start > last_end:
                before_text = text[last_end:start].strip()
                if before_text:
                    components.append({'type': 'text', 'content': before_text})
            
            # Add table (always as atomic unit)
            components.append({
                'type': 'table',
                'content': table_text,
                'table_index': table_idx
            })
            table_idx += 1
            last_end = end
        
        # Add remaining text
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                components.append({'type': 'text', 'content': remaining})
        
        return components

    def count_tokens_estimate(self, text: str) -> int:
        """Estimate token count: ~1 token per 4 characters"""
        return max(1, len(text) // 4)

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _merge_components(self, components: List[Dict]) -> str:
        """Merge components back into text"""
        parts = []
        for comp in components:
            if comp['type'] in ['text', 'table', 'sentence']:
                parts.append(comp['content'])
        return "\n\n".join(parts).strip()




    def semantic_chunk_preserve_tables(
        self,
        pages: List[Tuple[int, str]],
        source: str
    ) -> List[Dict]:
        """
        Semantic chunking while preserving tables as atomic units.
        
        Strategy:
        1. Split each page into text and table components
        2. Tables always stay together (atomic units)
        3. Group text sentences with tables to reach target chunk size
        """
        chunks = []
        
        for page_index, page_text in pages:
            if not page_text or not page_text.strip():
                continue
            
            components = self.split_text_preserve_tables(page_text)
            if not components:
                continue
            
            # Group components into chunks
            current_chunk = []
            current_tokens = 0
            chunk_id = 0
            
            for comp in components:
                comp_tokens = self.count_tokens_estimate(comp['content'])
                
                # Tables are always added (never split)
                if comp['type'] == 'table':
                    # If adding table would exceed limit and current chunk has content,
                    # save current chunk first
                    if current_tokens > 0 and current_tokens + comp_tokens > self.chunk_size_tokens * 1.5:
                        chunk_text = self._merge_components(current_chunk)
                        chunks.append({
                            "text": chunk_text,
                            "metadata": {
                                "page_index": page_index,
                                "source": source,
                                "chunk_id": chunk_id,
                                "tokens": current_tokens,
                                "has_table": any(c['type'] == 'table' for c in current_chunk)
                            }
                        })
                        chunk_id += 1
                        current_chunk = []
                        current_tokens = 0
                    
                    # Add table to chunk
                    current_chunk.append(comp)
                    current_tokens += comp_tokens
                
                # Text components can be split
                else:
                    sentences = self.split_into_sentences(comp['content'])
                    
                    for sent in sentences:
                        sent_tokens = self.count_tokens_estimate(sent)
                        
                        # If adding sentence exceeds limit, save current chunk
                        if current_tokens + sent_tokens > self.chunk_size_tokens and current_chunk:
                            chunk_text = self._merge_components(current_chunk)
                            chunks.append({
                                "text": chunk_text,
                                "metadata": {
                                    "page_index": page_index,
                                    "source": source,
                                    "chunk_id": chunk_id,
                                    "tokens": current_tokens,
                                    "has_table": any(c['type'] == 'table' for c in current_chunk)
                                }
                            })
                            chunk_id += 1
                            current_chunk = []
                            current_tokens = 0
                        
                        # Add sentence
                        current_chunk.append({'type': 'sentence', 'content': sent})
                        current_tokens += sent_tokens
            
            # Save last chunk
            if current_chunk:
                chunk_text = self._merge_components(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "page_index": page_index,
                        "source": source,
                        "chunk_id": chunk_id,
                        "tokens": current_tokens,
                        "has_table": any(c['type'] == 'table' for c in current_chunk)
                    }
                })
        
        return chunks

    def export_chunks_to_jsonl(self, chunks: List[Dict], output_path: str) -> None:
        """Export chunks to JSONL for RAG"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                export_chunk = {
                    "text": chunk["text"],
                    "metadata": chunk["metadata"]
                }
                
                line = json.dumps(export_chunk, ensure_ascii=False)
                f.write(line + "\n")
        
        print(f"✓ Exported {len(chunks)} chunks to: {output_path}")
    
    def parse_content(self, markdown_content: str, source_name: str = "document", output_jsonl_path: Optional[str] = None) -> List[Dict]:
        """
        Parse markdown content (string) and create chunks.
        Returns list of chunks for further use, also saves to JSONL if needed.
        
        Args:
            markdown_content: Markdown string content to parse
            source_name: Name of the source document (for metadata)
            output_jsonl_path: Optional path to save chunks as JSONL
            
        Returns:
            List of chunk dictionaries
        """
        print(f"\nParsing content from: {source_name}")
        print(f"Content size: {len(markdown_content):,} bytes")
        
        # Split by page breaks
        pages_text = markdown_content.split("<!-- PAGE BREAK -->")
        pages = [(idx, page.strip()) for idx, page in enumerate(pages_text) if page.strip()]
        print(f"Pages found: {len(pages)}")
        
        # Count tables
        total_tables = sum(len(self.extract_tables(p[1])) for p in pages)
        print(f"Tables detected: {total_tables}")
        
        # Perform semantic chunking with table preservation
        print(f"\nSemantic chunking ({self.chunk_size_tokens} tokens/chunk)")
        chunks = self.semantic_chunk_preserve_tables(
            pages,
            source=source_name
        )
        print(f"Total chunks created: {len(chunks)}")
        
        # Statistics
        if chunks:
            token_counts = [c["metadata"]["tokens"] for c in chunks]
            chunks_with_tables = sum(1 for c in chunks if c["metadata"]["has_table"])
            print(f"Avg tokens/chunk: {sum(token_counts) / len(token_counts):.1f}")
            print(f"Min/Max tokens: {min(token_counts)}/{max(token_counts)}")
            print(f"Chunks with tables: {chunks_with_tables}")
        
        # Export to JSONL if path provided
        if output_jsonl_path:
            self.export_chunks_to_jsonl(chunks, output_jsonl_path)
        
        return chunks
    
    def parse_file(self, md_file_path: str, output_jsonl_path: Optional[str] = None) -> List[Dict]:
        """
        Parse a markdown file and create chunks.
        Returns list of chunks for further use, also saves to JSONL if needed.
        """
        md_content = Path(md_file_path).read_text(encoding="utf-8")
        
        # Use parse_content for processing
        return self.parse_content(
            markdown_content=md_content,
            source_name=Path(md_file_path).name,
            output_jsonl_path=output_jsonl_path
        )
    
    def parse_folder(self, input_folder: str, output_folder: Optional[str] = None) -> List[Dict]:
        """
        Parse tất cả các file markdown trong folder.
        Returns aggregated chunks from all files.
        """
        input_path = Path(input_folder)
        all_chunks = []
        
        # Find all .md files
        md_files = list(input_path.glob("*.md"))
        
        print(f"\nProcessing {len(md_files)} markdown files from {input_folder}")
        
        for md_file in md_files:
            if output_folder:
                output_jsonl = Path(output_folder) / (md_file.stem + "_chunks.jsonl")
            else:
                output_jsonl = None
            
            chunks = self.parse_file(str(md_file), str(output_jsonl) if output_jsonl else None)
            all_chunks.extend(chunks)
        
        print(f"\nTotal chunks from all files: {len(all_chunks)}")
        return all_chunks


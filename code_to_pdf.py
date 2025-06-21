#!/usr/bin/env python3

"""
Code Folder to PDF Converter with Syntax Highlighting
Converts all code files in a folder to a formatted PDF with table of contents, 
multi-column flow, minimal gutters, column borders, preserved indentation, 
automatic line-wrapping, landscape orientation, and minimal syntax highlighting.
"""

import os
import sys
import re
from pathlib import Path
from collections import defaultdict
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class Config:
    """Configuration loader from environment file"""
    
    def __init__(self, config_file='config.env'):
        self.config = {}
        self.load_config(config_file)
    
    def load_config(self, config_file):
        """Load configuration from .env file"""
        if not Path(config_file).exists():
            raise FileNotFoundError(f"Configuration file {config_file} not found")
        
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    self.config[key.strip()] = value.strip()
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def get_float(self, key, default=0.0):
        """Get configuration value as float"""
        return float(self.get(key, default))
    
    def get_int(self, key, default=0):
        """Get configuration value as integer"""
        return int(self.get(key, default))
    
    def get_list(self, key, separator=',', default=None):
        """Get configuration value as list"""
        value = self.get(key, default)
        return value.split(separator) if value else []
    
    def get_dict(self, key, separator=',', kv_separator=':', default=None):
        """Get configuration value as dictionary"""
        items = self.get_list(key, separator, default)
        result = {}
        for item in items:
            if kv_separator in item:
                k, v = item.split(kv_separator, 1)
                result[k.strip()] = v.strip()
        return result


class PDFDocTemplate(BaseDocTemplate):
    """Custom PDF document template with TOC support"""
    
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)

    def afterFlowable(self, flowable):
        """Register TOC entries for subfolder and code titles"""
        style = getattr(flowable, 'style', None)
        if style and style.name in ('SubfolderTitle', 'CodeTitle'):
            text = flowable.getPlainText()
            level = getattr(flowable, '_tocLevel', 1)
            key = f"toc_{level}_{text}"
            self.canv.bookmarkPage(key)
            self.notify('TOCEntry', (level, text, self.page, key))


class SyntaxHighlighter:
    """Minimal syntax highlighter for common programming languages"""
    
    def __init__(self):
        self.colors = {
            'keyword': colors.blue,
            'string': colors.green,
            'comment': colors.grey,
            'number': colors.red,
            'function': colors.purple,
            'default': colors.black
        }
        
        self.keywords = {
            'python': ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 
                      'import', 'from', 'as', 'return', 'yield', 'lambda', 'with', 'assert', 'break', 
                      'continue', 'pass', 'global', 'nonlocal', 'True', 'False', 'None', 'and', 'or', 
                      'not', 'in', 'is'],
            'javascript': ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while', 'do', 'switch', 
                          'case', 'default', 'try', 'catch', 'finally', 'return', 'break', 'continue', 
                          'class', 'extends', 'import', 'export', 'from', 'as', 'true', 'false', 'null', 
                          'undefined', 'new', 'this', 'typeof', 'instanceof'],
            'java': ['public', 'private', 'protected', 'static', 'final', 'abstract', 'class', 'interface', 
                    'extends', 'implements', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 
                    'try', 'catch', 'finally', 'throw', 'throws', 'return', 'break', 'continue', 'new', 
                    'this', 'super', 'true', 'false', 'null'],
            'cpp': ['int', 'float', 'double', 'char', 'bool', 'void', 'if', 'else', 'for', 'while', 'do', 
                   'switch', 'case', 'default', 'try', 'catch', 'return', 'break', 'continue', 'class', 
                   'struct', 'public', 'private', 'protected', 'virtual', 'static', 'const', 'true', 
                   'false', 'nullptr'],
            'default': ['if', 'else', 'for', 'while', 'function', 'class', 'return', 'true', 'false', 
                       'null', 'undefined', 'public', 'private', 'static', 'const', 'var', 'let']
        }

    def detect_language(self, filename):
        """Detect language based on file extension"""
        ext = Path(filename).suffix.lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp', '.c': 'cpp',
            '.css': 'css',
            '.html': 'html', '.htm': 'html'
        }
        return lang_map.get(ext, 'default')

    def highlight_line(self, line, language):
        """Apply simple syntax highlighting to a single line using safe HTML"""
        if not line.strip():
            return line
        
        # Escape HTML entities first
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        highlighted = line
        
        try:
            # Comments
            if '//' in line or line.strip().startswith('#'):
                if '//' in line:
                    comment_start = line.find('//')
                    before = line[:comment_start]
                    comment = line[comment_start:]
                    highlighted = before + f'<font color="grey">{comment}</font>'
                elif line.strip().startswith('#'):
                    highlighted = f'<font color="grey">{line}</font>'
            
            # String literals
            elif '"' in line or "'" in line:
                if line.count('"') >= 2:
                    parts = line.split('"')
                    result = []
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            result.append(part)
                        else:
                            result.append(f'<font color="green">"{part}"</font>')
                    highlighted = ''.join(result)
                elif line.count("'") >= 2:
                    parts = line.split("'")
                    result = []
                    for i, part in enumerate(parts):
                        if i % 2 == 0:
                            result.append(part)
                        else:
                            result.append(f'<font color="green">\'{part}\'</font>')
                    highlighted = ''.join(result)
            
            # Keywords
            else:
                keywords = self.keywords.get(language, self.keywords['default'])
                words = line.split()
                new_words = []
                for word in words:
                    clean_word = re.sub(r'[^\w]', '', word)
                    if clean_word in keywords:
                        highlighted_word = word.replace(clean_word, f'<font color="blue">{clean_word}</font>')
                        new_words.append(highlighted_word)
                    else:
                        new_words.append(word)
                highlighted = ' '.join(new_words)
        
        except Exception:
            return line
        
        return highlighted


class CodeToPDFConverter:
    """Main converter class for transforming code folders to PDF"""
    
    def __init__(self, config_file='config.env'):
        self.config = Config(config_file)
        self.styles = getSampleStyleSheet()
        self.highlighter = SyntaxHighlighter()
        self._register_fonts()
        self._setup_styles()

    def _register_fonts(self):
        """Register custom fonts"""
        font_regular = self.config.get('FONT_REGULAR_PATH', 'fonts/UbuntuMono-Regular.ttf')
        font_bold = self.config.get('FONT_BOLD_PATH', 'fonts/UbuntuMono-Bold.ttf')
        
        pdfmetrics.registerFont(TTFont('UbuntuMono', font_regular))
        pdfmetrics.registerFont(TTFont('UbuntuMono-Bold', font_bold))

    def _setup_styles(self):
        """Setup paragraph styles"""
        font_size = self.config.get_int('FONT_SIZE', 11)
        title_font_size = self.config.get_int('TITLE_FONT_SIZE', 10)
        
        self.styles.add(ParagraphStyle(
            name='TOCEntry', parent=self.styles['Normal'],
            fontSize=10, leftIndent=20, spaceAfter=3
        ))

        self.styles.add(ParagraphStyle(
            name='SubfolderTitle', parent=self.styles['Normal'],
            fontName='UbuntuMono-Bold', fontSize=title_font_size + 4,
            spaceBefore=12, spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='CodeTitle', parent=self.styles['Normal'],
            fontName='UbuntuMono-Bold',
            fontSize=title_font_size + 2, spaceAfter=2, spaceBefore=8
        ))
        
        self.styles.add(ParagraphStyle(
            name='CodeContent', parent=self.styles['Normal'],
            fontName='UbuntuMono-Bold', fontSize=font_size, 
            leading=font_size + 4, leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='CodeLine', parent=self.styles['Normal'],
            fontName='UbuntuMono', fontSize=font_size, 
            leading=font_size + 2,
            leftIndent=0, spaceAfter=0, spaceBefore=0
        ))

    def _get_page_config(self):
        """Get page configuration from config"""
        page_orientation = self.config.get('PAGE_ORIENTATION', 'landscape')
        page_size = landscape(A4) if page_orientation == 'landscape' else A4
        
        return {
            'page_size': page_size,
            'margin_top': self.config.get_float('MARGIN_TOP', 0.2) * inch,
            'margin_bottom': self.config.get_float('MARGIN_BOTTOM', 0.2) * inch,
            'margin_left': self.config.get_float('MARGIN_LEFT', 0.2) * inch,
            'margin_right': self.config.get_float('MARGIN_RIGHT', 0.2) * inch,
            'columns_per_page': self.config.get_int('COLUMNS_PER_PAGE', 3),
            'gutter': self.config.get_float('GUTTER', 0.02) * inch,
        }

    def _get_supported_extensions(self):
        """Get supported file extensions"""
        return {
            '.py': 'Python', '.js': 'JavaScript', '.html': 'HTML', '.css': 'CSS',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.rb': 'Ruby', '.go': 'Go',
            '.rs': 'Rust', '.sql': 'SQL', '.sh': 'Shell', '.json': 'JSON', 
            '.xml': 'XML', '.md': 'Markdown', '.txt': 'Text'
        }

    def get_code_files(self, folder_path):
        """Get all supported code files from folder"""
        folder = Path(folder_path)
        supported_extensions = set(self._get_supported_extensions().keys())
        return sorted(p for p in folder.rglob('*')
                     if p.is_file() and p.suffix.lower() in supported_extensions)

    def read_file_content(self, file_path):
        """Read file content with encoding fallback"""
        for encoding in ('utf-8', 'latin-1', 'cp1252'):
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        return file_path.read_text(encoding='utf-8', errors='replace')

    def _draw_column_borders(self, canvas, doc):
        """Draw column borders and team name"""
        page_config = self._get_page_config()
        
        left = page_config['margin_left']
        bottom = page_config['margin_bottom']
        top = doc.pagesize[1] - page_config['margin_top']
        usable_w = doc.pagesize[0] - page_config['margin_left'] - page_config['margin_right']
        col_w = (usable_w - (page_config['columns_per_page'] - 1) * page_config['gutter']) / page_config['columns_per_page']

        # Draw column borders
        for i in range(1, page_config['columns_per_page']):
            x = left + i * (col_w + page_config['gutter']) - page_config['gutter'] / 2
            canvas.setStrokeColor(colors.lightgrey)
            canvas.setLineWidth(0.5)
            canvas.line(x, bottom, x, top)

        # Draw team name and page number
        team_name = self.config.get('TEAM_NAME', 'Team Name')
        canvas.setFont("UbuntuMono-Bold", size=10)
        canvas.drawRightString(
            doc.pagesize[0] - 0.1 * inch,
            doc.pagesize[1] - (page_config['margin_top'] / 2) - 0.1 * inch,
            f"{team_name} - {doc.page}"
        )

    def format_code_content(self, content, filename):
        """Format code content with syntax highlighting"""
        language = self.highlighter.detect_language(filename)
        lines = content.split('\n')
        story_elements = []
        
        for line in lines:
            if not line.strip():
                story_elements.append(Paragraph('&nbsp;', self.styles['CodeLine']))
            else:
                highlighted_line = self.highlighter.highlight_line(line, language)
                # Preserve indentation
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indent = '&nbsp;' * leading_spaces
                    highlighted_line = indent + highlighted_line.lstrip()
                
                try:
                    story_elements.append(Paragraph(highlighted_line, self.styles['CodeLine']))
                except:
                    # Fallback to plain text if highlighting fails
                    story_elements.append(Paragraph(
                        line.replace('<', '&lt;').replace('>', '&gt;'), 
                        self.styles['CodeLine']
                    ))
        
        return story_elements

    def build_document(self, folder_path, output_path):
        """Build the PDF document"""
        files = self.get_code_files(folder_path)
        page_config = self._get_page_config()
        
        # Group files by subfolder
        files_by_subfolder = defaultdict(list)
        subfolder_by_file = {}
        for file in files:
            rel = file.parent.relative_to(folder_path)
            key = str(rel) if str(rel) != '.' else ''
            files_by_subfolder[key].append(file)
            subfolder_by_file[file] = key

        used_subfolders = set()

        # Create document
        doc = PDFDocTemplate(
            output_path, pagesize=page_config['page_size'],
            leftMargin=page_config['margin_left'], 
            rightMargin=page_config['margin_right'],
            topMargin=page_config['margin_top'], 
            bottomMargin=page_config['margin_bottom']
        )
        
        # Calculate frame dimensions
        page_w, page_h = doc.pagesize
        usable_w = page_w - page_config['margin_left'] - page_config['margin_right']
        usable_h = page_h - page_config['margin_top'] - page_config['margin_bottom']
        col_w = (usable_w - (page_config['columns_per_page'] - 1) * page_config['gutter']) / page_config['columns_per_page']

        # Create frames
        frames = []
        for i in range(page_config['columns_per_page']):
            x = page_config['margin_left'] + i * (col_w + page_config['gutter'])
            frames.append(Frame(x, page_config['margin_bottom'], col_w, usable_h, id=f'col{i}'))
        
        template = PageTemplate(id='multi', frames=frames, onPage=self._draw_column_borders)
        doc.addPageTemplates([template])

        story = []
        
        # Table of Contents
        toc = TableOfContents()
        toc.levelStyles = [
            self.styles['SubfolderTitle'],
            self.styles['TOCEntry']
        ]

        story.append(Paragraph("Table of Contents", self.styles['Title']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(toc)
        story.append(PageBreak())
        
        # Process files
        for file in files:
            subfolder_name = subfolder_by_file[file]
            
            # Add subfolder title if new subfolder
            if subfolder_name != '' and subfolder_name not in used_subfolders:
                h = Paragraph(subfolder_name, self.styles['SubfolderTitle'])
                h._tocLevel = 0
                story.append(h)
                used_subfolders.add(subfolder_name)

            # Add file title
            p = Paragraph(file.name, self.styles['CodeTitle'])
            p._tocLevel = 1
            story.append(p)

            # Add file content
            content = self.read_file_content(file)
            try:
                formatted_elements = self.format_code_content(content, file.name)
                story.extend(formatted_elements)
            except Exception:
                # Fallback if formatting fails
                from reportlab.platypus import Preformatted
                story.append(Preformatted(content, self.styles['CodeContent']))
        
        doc.multiBuild(story)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: code_to_pdf.py <folder> [output.pdf] [config.env]")
        sys.exit(1)
    
    folder = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else f"{Path(folder).name}.pdf"
    config_file = sys.argv[3] if len(sys.argv) > 3 else 'config.env'
    
    try:
        converter = CodeToPDFConverter(config_file)
        converter.build_document(folder, output)
        print(f"PDF created: {output}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating PDF: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
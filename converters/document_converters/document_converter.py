from docx import Document
from PyPDF2 import PdfReader, PdfWriter
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import StringIO
import markdown
import openpyxl
import xlrd
import xlwt
from odf.opendocument import OpenDocumentText
from odf.text import P
import ebooklib
from ebooklib import epub
import pptx
import json
import csv
import xml.etree.ElementTree as ET
import yaml

class DocumentConverter:
    def __init__(self):
        self.supported_formats = {
            # Text Documents
            'txt': {'type': 'text'},
            'docx': {'type': 'text'},
            'doc': {'type': 'text'},
            'rtf': {'type': 'text'},
            'odt': {'type': 'text'},
            'pdf': {'type': 'text'},
            
            # Markup
            'md': {'type': 'markup'},
            'html': {'type': 'markup'},
            'xml': {'type': 'markup'},
            
            # Spreadsheets
            'xlsx': {'type': 'spreadsheet'},
            'xls': {'type': 'spreadsheet'},
            'csv': {'type': 'spreadsheet'},
            'ods': {'type': 'spreadsheet'},
            
            # Presentations
            'pptx': {'type': 'presentation'},
            'ppt': {'type': 'presentation'},
            'odp': {'type': 'presentation'},
            
            # eBooks
            'epub': {'type': 'ebook'},
            
            # Data formats
            'json': {'type': 'data'},
            'yaml': {'type': 'data'},
            'xml': {'type': 'data'}
        }
    
    def convert(self, input_path, output_path, progress_bar=None):
        try:
            input_format = input_path.split('.')[-1].lower()
            output_format = output_path.split('.')[-1].lower()
            
            if output_format not in self.supported_formats:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            if progress_bar:
                progress_bar.setValue(25)
            
            # Determine conversion type
            input_type = self.supported_formats[input_format]['type']
            output_type = self.supported_formats[output_format]['type']
            
            # Handle different conversion scenarios
            if input_type == 'text':
                self._convert_text_document(input_path, output_path, input_format, output_format)
            elif input_type == 'markup':
                self._convert_markup(input_path, output_path, input_format, output_format)
            elif input_type == 'spreadsheet':
                self._convert_spreadsheet(input_path, output_path, input_format, output_format)
            elif input_type == 'presentation':
                self._convert_presentation(input_path, output_path, input_format, output_format)
            elif input_type == 'ebook':
                self._convert_ebook(input_path, output_path, input_format, output_format)
            elif input_type == 'data':
                self._convert_data_format(input_path, output_path, input_format, output_format)
            
            if progress_bar:
                progress_bar.setValue(100)
                
        except Exception as e:
            raise Exception(f"Document conversion failed: {str(e)}")
    
    def _convert_text_document(self, input_path, output_path, input_format, output_format):
        # Handle text document conversions (DOCX, PDF, TXT, etc.)
        if input_format == 'docx':
            if output_format == 'pdf':
                self._docx_to_pdf(input_path, output_path)
            elif output_format == 'txt':
                self._docx_to_txt(input_path, output_path)
            elif output_format == 'html':
                self._docx_to_html(input_path, output_path)
            elif output_format == 'epub':
                self._docx_to_epub(input_path, output_path)
        elif input_format == 'pdf':
            if output_format == 'docx':
                self._pdf_to_docx(input_path, output_path)
            elif output_format == 'txt':
                self._pdf_to_txt(input_path, output_path)
            elif output_format == 'html':
                self._pdf_to_html(input_path, output_path)
    
    def _convert_markup(self, input_path, output_path, input_format, output_format):
        # Handle markup conversions (MD, HTML, etc.)
        if input_format == 'md':
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if output_format == 'html':
                    html_content = markdown.markdown(content)
                    with open(output_path, 'w', encoding='utf-8') as out:
                        out.write(html_content)
                elif output_format == 'pdf':
                    html_content = markdown.markdown(content)
                    self._html_to_pdf(html_content, output_path)
                elif output_format == 'epub':
                    self._markdown_to_epub(content, output_path)
    
    def _convert_spreadsheet(self, input_path, output_path, input_format, output_format):
        # Handle spreadsheet conversions (XLSX, CSV, etc.)
        if input_format == 'xlsx':
            wb = openpyxl.load_workbook(input_path)
            if output_format == 'csv':
                sheet = wb.active
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    for row in sheet.rows:
                        writer.writerow([cell.value for cell in row])
        elif input_format == 'csv':
            if output_format == 'xlsx':
                wb = openpyxl.Workbook()
                sheet = wb.active
                with open(input_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        sheet.append(row)
                wb.save(output_path)
    
    def _convert_ebook(self, input_path, output_path, input_format, output_format):
        if input_format == 'epub':
            book = epub.read_epub(input_path)
            if output_format == 'html':
                self._epub_to_html(book, output_path)
            elif output_format == 'txt':
                self._epub_to_txt(book, output_path)
    
    def _convert_data_format(self, input_path, output_path, input_format, output_format):
        # Handle data format conversions (JSON, YAML, XML)
        if input_format == 'json':
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if output_format == 'yaml':
                    with open(output_path, 'w', encoding='utf-8') as out:
                        yaml.dump(data, out)
                elif output_format == 'xml':
                    self._dict_to_xml(data, output_path)
    
    def _markdown_to_epub(self, content, output_path):
        book = epub.EpubBook()
        book.set_identifier('id123456')
        book.set_title('Converted from Markdown')
        book.set_language('en')
        
        # Create chapter
        c1 = epub.EpubHtml(title='Content',
                          file_name='content.xhtml',
                          content=markdown.markdown(content))
        
        book.add_item(c1)
        book.spine = [c1]
        epub.write_epub(output_path, book, {})
    
    def _epub_to_html(self, book, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE html><html><body>\n')
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                f.write(item.get_content().decode('utf-8'))
            f.write('</body></html>')
    
    def _epub_to_txt(self, book, output_path):
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                content = item.get_content().decode('utf-8')
                # Remove HTML tags (very basic approach)
                content = content.replace('<br>', '\n')
                content = ''.join(content.split('>')[-1].split('<')[0] for content in content.split('\n'))
                f.write(content + '\n\n')
    
    def _docx_to_epub(self, input_path, output_path):
        doc = Document(input_path)
        book = epub.EpubBook()
        book.set_identifier('id123456')
        book.set_title('Converted from DOCX')
        book.set_language('en')
        
        content = ''
        for para in doc.paragraphs:
            content += f'<p>{para.text}</p>\n'
        
        c1 = epub.EpubHtml(title='Content',
                          file_name='content.xhtml',
                          content=content)
        
        book.add_item(c1)
        book.spine = [c1]
        epub.write_epub(output_path, book, {})

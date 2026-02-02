import os
import re
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from bs4 import BeautifulSoup
import html

class PaperBuilder:
    def __init__(self, media_dir: str):
        self.media_dir = media_dir
        
    def create_paper(self, questions: list, output_path: str):
        doc = Document()
        
        style = doc.styles['Normal']
        style.font.name = 'Microsoft YaHei'
        style.font.size = Pt(10.5) # 5号
        style.paragraph_format.space_after = Pt(0) # Compact
        style.paragraph_format.line_spacing = 1.0 # Single spacing
        
        # Main Title
        # doc.add_heading('错题回顾卷', 0) # User said "No title"? "不要分节符和标题"? 
        # "要四个部分的大标题" (Want 4 part big titles).
        # "去掉回车，不要分节符和标题" -> Maybe "No main title"? Or "No section breaks"?
        # I'll keep Main Title but concise.
        
        # Grouping Logic
        # Order: 常识 -> 言语 -> 数量 -> 判断 -> 资料
        # Map DB types to Sort Order
        type_map = {'常识': 1, '言语': 2, '数量': 3, '判断': 4, '资料': 5}
        
        # Sort: Primary by Type, Secondary by MaterialID (to keep materials together)
        questions.sort(key=lambda q: (type_map.get(q.get('type', ''), 99), q.get('material_id') or 0, q.get('original_num')))
        
        current_type = None
        last_material_id = None
        global_idx = 1
        
        for q in questions:
            q_type = q.get('type')
            if not q_type: q_type = "其他"
            
            # 1. Type Header
            if q_type != current_type:
                # Add spacing before new section (unless first)
                if current_type is not None: doc.add_paragraph("_"*20)
                
                doc.add_heading(q_type, level=1)
                current_type = q_type
                last_material_id = None # Reset material context on type switch
                
            # 2. Material Handling
            mid = q.get('material_id')
            mat_content = q.get('material_content')
            
            if mid and mid != last_material_id:
                if mat_content:
                    doc.add_paragraph("【资料】") # Small label
                    self._add_html_content(doc, mat_content)
                last_material_id = mid
            elif not mid:
                last_material_id = None
            
            # 3. Question Content
            p = doc.add_paragraph()
            p.add_run(f"{global_idx}. ").bold = True
            
            # Stem
            self._add_html_content(doc, q.get('content_html'))
            
            # Options (Now using correct field)
            if q.get('options_html'):
                 self._add_html_content(doc, q.get('options_html'))
            
            # No extra spacing
            # doc.add_paragraph("") 
            
            global_idx += 1
            
        # Answer Key Page
        doc.add_page_break()
        doc.add_heading('参考答案与解析', 1)
        
        for idx, q in enumerate(questions):
            p = doc.add_paragraph()
            p.add_run(f"{idx+1}. ").bold = True
            
            ans = q.get('answer_html')
            if ans:
                self._add_html_content(doc, ans)
            else:
                p.add_run("(暂无解析)")
                
            doc.add_paragraph("-" * 20)

        doc.save(output_path)
        return output_path

    def _add_html_content(self, doc, html_str):
        """
        Naive HTML parser to add content to docx.
        Supports: <p>, <img>, <table>, and plain text.
        """
        if not html_str: return
        
        soup = BeautifulSoup(html_str, 'html.parser')
        
        # Iterate over all elements, handling simpler structure
        # We find top-level block elements.
        # If the HTML is just text or inline, wrap in p.
        
        elements = soup.find_all(['p', 'table', 'div'], recursive=False)
        
        # If no block elements found, maybe it's just text or text with br?
        if not elements and soup.get_text().strip():
             text = soup.get_text().strip()
             doc.add_paragraph(text)
             return

        for element in elements:
            if element.name == 'p':
                text = element.get_text().strip()
                if text:
                    doc.add_paragraph(text)
            elif element.name == 'table':
                # Simple table
                rows = element.find_all('tr')
                if not rows: continue
                
                table = doc.add_table(rows=len(rows), cols=0)
                table.style = 'Table Grid'
                for i, row in enumerate(rows):
                    cells = row.find_all(['td', 'th'])
                    # Ensure table has enough cols
                    while len(table.columns) < len(cells):
                        table.add_column(Inches(1))
                    
                    row_cells = table.rows[i].cells
                    for j, cell in enumerate(cells):
                        if j < len(row_cells):
                            row_cells[j].text = cell.get_text().strip()
            
            elif element.name == 'div' and 'img-container' in element.get('class', []):
                 img = element.find('img')
                 if img:
                     src = img.get('src')
                     fname = src.split('/')[-1]
                     fpath = os.path.join(self.media_dir, fname)
                     
                     if os.path.exists(fpath):
                         try:
                             # Add run to previous paragraph if possible? No, doc.add_picture creates new p normally.
                             doc.add_picture(fpath, width=Inches(4))
                         except:
                             doc.add_paragraph(f"[Image: {fname} Load Failed]")
            
            # Recursive needed? For now we flattened structure in extractor.

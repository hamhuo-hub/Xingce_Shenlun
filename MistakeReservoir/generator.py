import os
import re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from bs4 import BeautifulSoup

class PaperBuilder:
    def __init__(self, media_dir: str):
        self.media_dir = media_dir
        
    def create_paper(self, questions: list, output_path: str):
        doc = Document()
        
        # --- Styles ---
        style = doc.styles['Normal']
        style.font.name = 'Microsoft YaHei'
        style.font.size = Pt(10.5) # 5号
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.line_spacing = 1.0
        
        # --- Logic ---
        # Sort Order
        type_map = {
            '常识': 1, 
            '言语': 2, 
            '数量': 3, 
            '判断': 4, '图形': 4.1, '定义': 4.2, '类比': 4.3, '逻辑': 4.4,
            '资料': 5
        }
        
        questions.sort(key=lambda q: (type_map.get(q.get('type', ''), 99), q.get('material_id') or 0, q.get('original_num')))
        
        current_type = None
        last_material_id = None
        global_idx = 1
        
        section_map = {
            '常识': '第一部分 常识判断',
            '言语': '第二部分 言语理解与表达',
            '数量': '第三部分 数量关系',
            '判断': '第四部分 判断推理',
            '图形': '第四部分 判断推理', # Subtypes grouped under main
            '定义': '第四部分 判断推理',
            '类比': '第四部分 判断推理',
            '逻辑': '第四部分 判断推理',
            '资料': '第五部分 资料分析'
        }
        
        # Track main sections added to avoid repeats
        added_encounters = set()
        
        for q in questions:
            q_type = q.get('type') or "其他"
            clean_type = q_type
            
            # Map subtype to main type for header
            if q_type in ['图形', '定义', '类比', '逻辑']:
                clean_type = '判断'
                
            header_title = section_map.get(clean_type, f"部分 {clean_type}")
            
            # 1. Section Header
            if header_title not in added_encounters:
                if added_encounters: doc.add_paragraph() # Spacing
                h = doc.add_heading(header_title, level=1)
                h.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                added_encounters.add(header_title)
                current_type = clean_type # Logical group
                last_material_id = None
            
            # 2. Material
            mid = q.get('material_id')
            if mid and mid != last_material_id:
                mat_content = q.get('material_content')
                if mat_content:
                    p = doc.add_paragraph()
                    r = p.add_run("根据以下材料，回答下列问题：")
                    r.bold = True
                    self._add_html_content(doc, mat_content)
                    doc.add_paragraph() # Spacing after material
                last_material_id = mid
            elif not mid:
                last_material_id = None

            # 3. Question Logic
            # Stem
            p = doc.add_paragraph()
            p.add_run(f"{global_idx}. ").bold = True
            self._add_html_content_inline(p, q.get('content_html'), doc)
            
            # Options
            if q.get('options_html'):
                 self._add_options(doc, q.get('options_html'))
            
            global_idx += 1
            doc.add_paragraph() # Spacing between questions

        # --- Answer Key ---
        doc.add_page_break()
        h = doc.add_heading('参考答案与解析', level=1)
        h.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        
        for i, q in enumerate(questions):
            p = doc.add_paragraph()
            p.add_run(f"{i+1}. ").bold = True
            
            ans = q.get('answer_html')
            if ans:
                self._add_html_content_inline(p, ans, doc)
            else:
                p.add_run("（暂无解析）")
                
        doc.save(output_path)
        return output_path

    def _add_html_content(self, doc, html_str):
        """Block level adder"""
        if not html_str: return
        soup = BeautifulSoup(html_str, 'html.parser')
        
        # Extract images and text
        # If div.img-container -> Image
        # If p -> text
        
        for elem in soup.find_all(['p', 'div', 'table']):
            if elem.name == 'p':
                if elem.get_text().strip():
                    doc.add_paragraph(elem.get_text().strip())
            elif elem.name == 'div' and 'img-container' in elem.get('class', []):
                self._add_image(doc, elem)
            elif elem.name == 'table':
                # Simplified table
                pass

    def _add_html_content_inline(self, paragraph, html_str, doc):
        """Adds text to existing paragraph, but handles images by creating new paragraphs if needed"""
        if not html_str: return
        soup = BeautifulSoup(html_str, 'html.parser')
        
        # We need to maintain flow.
        # If pure text, append to paragraph.
        # If Image, we might need to break paragraph? 
        # Actually standard docx doesn't handle inline images easily in flow with text runs without complex xml.
        # Strategy: Text -> Run. Image -> New Paragraph (Centered) -> Resume Text (New Paragraph).
        # But `paragraph` arg implies we want to append.
        
        # Simplified: valid for Stem/Answer which are usually Text + Images at end or middle.
        
        txt = soup.get_text().strip()
        if txt:
            paragraph.add_run(txt)
            
        # Check for images in the soup
        imgs = soup.find_all('img')
        if imgs:
            # Add images AFTER the text paragraph
            for img in imgs:
                src = img.get('src')
                self._insert_image_file(doc, src)

    def _add_options(self, doc, html_str):
        """Parses options and puts them on new lines"""
        soup = BeautifulSoup(html_str, 'html.parser')
        text = soup.get_text().strip()
        
        # Regex to find A. B. C. D.
        # They might be in one line or separate p
        # We try to clean them up.
        
        # Assumption: Input is typically "<p>A. xxx</p><p>B. xxx</p>" or "<p>A.x B.x</p>"
        # If p tags exist, use them.
        
        ps = soup.find_all('p')
        if ps:
            for p in ps:
                t = p.get_text().strip()
                if t: doc.add_paragraph(t)
        else:
            # Try to regex split if it's a blob
            # Fallback
            doc.add_paragraph(text)

    def _add_image(self, doc, elem):
        img = elem.find('img')
        if img:
            self._insert_image_file(doc, img.get('src'))
            
    def _insert_image_file(self, doc, src):
        if not src: return
        fname = src.split('/')[-1]
        fpath = os.path.join(self.media_dir, fname)
        if os.path.exists(fpath):
            try:
                doc.add_picture(fpath, width=Inches(3.5)) # Standard width
            except:
                pass

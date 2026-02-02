import os
import re
import uuid
import shutil
from typing import List, Dict, Optional, Tuple
from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

class QuestionExtractor:
    def __init__(self, media_dir: str):
        self.media_dir = media_dir
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
            
        # Regex Patterns
        # Regex Patterns
        self.Q_PATTERN = re.compile(r'^\s*\(?\d+\)?[\.．、\s]')
        self.HEADER_PATTERN = re.compile(
            r'^\s*第[一二三四五六七八九十]+部分|'
            r'^\s*[一二三四五六七八九十]+、|'
            r'^\s*根据.*(材料|回答|短文)'
        )
        self.ANSWER_KEYWORDS = ['【答案】', '【解析】', '【拓展】', '【来源】', '正确答案', '参考答案', '答案:', '答案：', '解析:', '解析：']
        self.OPTION_PATTERN = re.compile(r'^\s*\(?[A-D]\)?[\.．、\s]')
        
        # Current State
        self.current_material_id = None
        self.current_material_content = ""
        self.current_type = "Unknown"

    def iter_block_items(self, parent):
        """Iterate through docx blocks (Paragraphs and Tables)"""
        if isinstance(parent, _Document):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        else:
            raise ValueError("Parent object error")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    def extract_images(self, block) -> List[str]:
        """
        Extract images from a block (Paragraph/Table)
        Save to media_dir and return list of filenames.
        """
        image_paths = []
        
        # Access the underlying xml element
        if isinstance(block, Paragraph):
            elms = [block._element]
        elif isinstance(block, Table):
            elms = []
            for row in block.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        elms.append(p._element)
        
        for elm in elms:
            # Find all drawing elements (blip)
            # This is a simplified approach; getting the actual binary requires accessing the relationship
            pass 
            # Note: python-docx structure for images is complex to trace back from paragraph to part.
            # A more robust way often involves iterating doc.inline_shapes or accessing relationships directly.
            # However, mapping inline_shapes to specific paragraphs is tricky.
            # 
            # Alternative Strategy: 
            # We will use a unique Placeholder in text or just extracting ALL images is not enough, we need context.
            # For this 'MVP', we might need a helper that extracts images from the `doc.part` related to the blipId found in paragraph.
        
        return image_paths

    def _save_image_from_blip(self, doc, blip_rId) -> Optional[str]:
        """
        Internal: Save image binary from blip relationship ID
        """
        try:
            if not blip_rId: return None
            
            # Safe access to related_parts
            if blip_rId not in doc.part.related_parts:
                # Try finding it in the package (document part) relationships
                # This is tricky without delving deep into python-docx internals
                # For now, just return None to avoid crash
                return None
                
            image_part = doc.part.related_parts[blip_rId]
            # Generate filename
            try:
                ext = image_part.content_type.split('/')[-1]
                if ext == 'jpeg': ext = 'jpg'
            except:
                ext = 'png'
            
            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(self.media_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_part.blob)
            
            return filename
        except Exception as e:
            print(f"Error saving image {blip_rId}: {e}")
            return None

    def get_block_images(self, doc, block) -> List[str]:
        """Real implementation of image extraction for a block"""
        images = []
        try:
            if isinstance(block, Paragraph):
                # Search for <a:blip>
                ns = block._element.nsmap
                blips = block._element.findall('.//a:blip', ns)
                for blip in blips:
                    rId = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if rId:
                        fname = self._save_image_from_blip(doc, rId)
                        if fname: images.append(fname)
                        
                # check v:imagedata
                imagedatas = block._element.findall('.//v:imagedata', ns)
                for idata in imagedatas:
                    rId = idata.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                    if rId:
                        fname = self._save_image_from_blip(doc, rId)
                        if fname: images.append(fname)
                        
            elif isinstance(block, Table):
                for row in block.rows:
                    for cell in row.cells:
                        for p in cell.paragraphs:
                            images.extend(self.get_block_images(doc, p))
        except Exception as e:
            print(f"Error getting block images: {e}")
            
        return images

    def block_to_html(self, doc, block) -> Tuple[str, List[str]]:
        """Convert block to simple HTML and extract images"""
        images = self.get_block_images(doc, block)
        html = ""
        
        if isinstance(block, Paragraph):
            text = block.text.strip()
            html = f"<p>{text}</p>" if text else ""
        elif isinstance(block, Table):
            rows = []
            for row in block.rows:
                cells = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    cells.append(f"<td>{cell_text}</td>")
                rows.append(f"<tr>{''.join(cells)}</tr>")
            html = f"<table border='1' cellspacing='0' cellpadding='5'>{''.join(rows)}</table>"
        
        if images:
            for img in images:
                html += f'<div class="img-container"><img src="media/{img}" class="question-img" /></div>'
                
        return html, images

    def process_buffer_as_question(self, doc, buffer: List, q_num: int) -> Dict:
        """
        Convert a buffer of blocks into structured Question data.
        Separates Stem, Options, and Analysis.
        """
        stem_blocks = []
        option_blocks = []
        analysis_blocks = []
        
        # State: 0=Stem, 1=Options, 2=Analysis
        state = 0
        
        
        for block in buffer:
            text = ""
            if isinstance(block, Paragraph):
                text = block.text.strip()
            elif isinstance(block, Table):
                # Extract text from table for keyword checking
                cell_texts = []
                for row in block.rows:
                    for cell in row.cells:
                        cell_texts.append(cell.text.strip())
                text = " ".join(cell_texts)
            
            # Check Switch to Analysis
            is_analysis = False
            for kw in self.ANSWER_KEYWORDS:
                if kw in text:
                    is_analysis = True
                    break
            
            if is_analysis:
                state = 2
            
            # Check Switch to Options (Only if currently in Stem or Options)
            # Typically Options start with A. B. C. D.
            if state < 2:
                if self.OPTION_PATTERN.match(text):
                    print(f"DEBUG: Found Option Start: {text[:10]}")
                    state = 1
            
            if state == 2:
                analysis_blocks.append(block)
            elif state == 1:
                option_blocks.append(block)
            else:
                stem_blocks.append(block)
        
        # Helper to convert list of blocks to HTML
        def blocks_to_html_str(blks):
            htmls = []
            imgs = []
            for b in blks:
                h, i = self.block_to_html(doc, b)
                htmls.append(h)
                imgs.extend(i)
            return "".join(htmls), imgs

        stem_html, stem_imgs = blocks_to_html_str(stem_blocks)
        opt_html, opt_imgs = blocks_to_html_str(option_blocks)
        ana_html, ana_imgs = blocks_to_html_str(analysis_blocks)
        
        return {
            "original_num": q_num,
            "content_html": stem_html,
            "options_html": opt_html,
            "answer_html": ana_html, # Analysis
            "images": stem_imgs + opt_imgs + ana_imgs,
            "type": self.current_type,
            "material_content": self.current_material_content if self.current_material_content else None
        }

    def extract_from_file(self, docx_path: str, target_ids: List[int] = None) -> List[Dict]:
        """
        Main Enty: Parse file and return list of Question Dicts.
        If target_ids is None, return all.
        """
        doc = Document(docx_path)
        blocks = list(self.iter_block_items(doc))
        
        extracted_questions = []
        buffer = []
        current_q_num = 0
        
        # Additional cleaning keywords
        FORCE_DELETE_LINES = ['故', '故。', '故本题选', '故正确答案']
        
        for block in blocks:
            text = ""
            if isinstance(block, Paragraph):
                text = block.text.strip()
            # Table text handling...
            elif isinstance(block, Table):
                 # For headers/patterns, we usually look at paragraphs. 
                 # But if a whole table is somehow a header? Unlikely.
                 pass

            # 1. Check Header (Material / Type Change)
            if self.HEADER_PATTERN.match(text):
                # If we have a pending question in buffer, process it
                if buffer and current_q_num > 0:
                    q = self.process_buffer_as_question(doc, buffer, current_q_num)
                    if target_ids is None or current_q_num in target_ids:
                        extracted_questions.append(q)
                    buffer = []
                
                # Identify Type
                if "常识" in text: self.current_type = "常识"
                elif "言语" in text: self.current_type = "言语"
                elif "数量" in text: self.current_type = "数量"
                elif "判断" in text: self.current_type = "判断"
                elif "资料" in text: self.current_type = "资料"
                
                # Material Handling - RESET Logic
                # Any blocks coming AFTER this header (and before next Q) should be Material.
                # So we reset current_q_num to 0.
                current_q_num = 0
                self.current_material_content = "" 
                
                # If the header itself contains content (like "According to Table 1..."), add it
                if "根据" in text or "材料" in text:
                     h, _ = self.block_to_html(doc, block)
                     self.current_material_content += h
                
                continue

            # 2. Check Question Start
            match = self.Q_PATTERN.match(text)
            is_new_q = False
            found_num = 0
            
            if match:
                try:
                    # Extract digits from text (easier than regex grouping complexities with optional parenthesis)
                    nums = re.findall(r'\d+', text)
                    if nums:
                        found_num = int(nums[0])
                        # Validation logic
                        if current_q_num == 0:
                             is_new_q = True
                        elif (found_num == current_q_num + 1) or (found_num > current_q_num and found_num - current_q_num < 20):
                            is_new_q = True
                except:
                    pass
            
            if is_new_q:
                # Process previous
                if buffer:
                    if current_q_num > 0:
                        q = self.process_buffer_as_question(doc, buffer, current_q_num)
                        if target_ids is None or current_q_num in target_ids:
                            extracted_questions.append(q)
                    else:
                        # Buffer contained Material! (Since q_num was 0)
                        # Append buffer content to current_material_content
                        # But wait, if we are in "Material Accumulation Mode" (q_num=0),
                        # the buffer blocks ARE the material.
                        for b in buffer:
                            h, imgs = self.block_to_html(doc, b)
                            self.current_material_content += h
                
                # Start new
                current_q_num = found_num
                buffer = [block]
                
            else:
                # Add to buffer
                # Check for "故" cleanup here? Or inside process_buffer (better)
                # Just separate Material vs Question Buffer
                if current_q_num > 0:
                    # Check for force delete lines to avoid adding them?
                    # Better to handle in process_buffer for finer control, but global "故" line removal is safe here
                    should_skip = False
                    if isinstance(block, Paragraph) and text in FORCE_DELETE_LINES:
                        should_skip = True
                    
                    if not should_skip:
                        buffer.append(block)
                else:
                    # Accumulating Material
                    # Don't add empty paragraphs to material unless they have images
                    h, imgs = self.block_to_html(doc, block)
                    if text or imgs:
                        self.current_material_content += h

        # Process last
        if buffer and current_q_num > 0:
            q = self.process_buffer_as_question(doc, buffer, current_q_num)
            if target_ids is None or current_q_num in target_ids:
                extracted_questions.append(q)
                
        return extracted_questions

# Usage Example
if __name__ == "__main__":
    extractor = QuestionExtractor(media_dir="media")
    # qs = extractor.extract_from_file("Test.docx", [1, 2])
    # print(qs)

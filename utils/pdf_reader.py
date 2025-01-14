import pdf4llm
import re

def split_markdown_sections(text):
    # Regex to match headers (e.g., #, ##, ###)
    header_pattern = r'^(#{1,6})\s*(.+)$'
    
    # Find all headers and their positions
    matches = list(re.finditer(header_pattern, text, re.MULTILINE))
    
    sections = []
    
    # Iterate over all header matches and split text
    for i, match in enumerate(matches):
        header = match.group(0)  # Full header text: number of # and header name
        level = len(match.group(1))  # Header level (number of #)
        title = match.group(2)  # Header title
        
        # Find the start position of the section (right after the header)
        start_pos = match.end()
        
        # Find the end position (start of the next header or end of the document)
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text)
        
        # Extract section content between this header and the next one
        section_content = text[start_pos:end_pos].strip()
        
        # Store the section as a tuple: (header level, header title, section content)
        sections.append({'level': level, 'title': title, 'content': section_content})
    
    return sections


class PDF4LLMParser(object):
    def __init__(self, write_images=False, page_chunks=False):
        self.write_images = write_images
        self.page_chunks = page_chunks
    
    def pdf2text(self, pdf_path):
        md_text = pdf4llm.to_markdown(pdf_path, write_images=self.write_images, page_chunks=self.page_chunks)

        if self.page_chunks:
            text_array = []
            for md_text_i in md_text:
                text_array.append(md_text_i['text'])
            markdown_text = '\n'.join(text_array)
        else:
            markdown_text = md_text
        return markdown_text
    
    def structured_paper_content(self, markdown_sections: list):
        """
        markdown_sections: list of dictionary, each dictionary consists of
        1. level
        2. title
        3. content

        Title, Author, Abstract, Section_i (i = 1, 2, 3, ...)
        """
        assert len(markdown_sections) > 0
        struct_sections = {}
        start_section = markdown_sections[0]
        title_level = start_section['level']
        
        main_text_idx = -1
        meta_data = []
        for sec_idx, section in enumerate(markdown_sections):
            level_i = section['level']
            title_i = section['title']
            content_i = section['content']
            if level_i == title_level and sec_idx == 0:
                struct_sections['title'] = title_i
                if len(content_i) > 0:
                    meta_data.append(content_i)
            else:
                if 'abstract' in title_i.lower() or 'abstract' in content_i.lower():
                    struct_sections['abstract'] = content_i
                    main_text_idx = sec_idx + 1
                    break
                else:
                    meta_data.append(title_i + content_i)
        struct_sections['author'] = meta_data
        if main_text_idx == -1 and len(markdown_sections) > 0:
            main_text_idx = 0
        assert main_text_idx >= 0
        main_text_list = markdown_sections[main_text_idx:]
        struct_sections['main_text'] = main_text_list
        return struct_sections

    def run(self, pdf_path: str):
        """
        Process a PDF file, extract structured content, and optionally print the results.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            text content
        """
        # Convert PDF to Markdown text
        markdown_text = self.pdf2text(pdf_path=pdf_path)

        # Split the Markdown text into sections
        sections = split_markdown_sections(text=markdown_text)

        # Structure the paper content
        struct_sections = self.structured_paper_content(markdown_sections=sections)
        paper_text = ""
        
        # Iterate over structured sections and format the output
        for section_name, content in struct_sections.items():
            if section_name == 'title':
                paper_text += f"\nTitle: {content}\n\n"
            elif section_name == 'abstract':
                paper_text += f"\nAbstract:\n{content}\n\n"
            elif section_name == 'author':
                paper_text += f"\nAuthor:\n{'\n'.join(content)}\n\n"
            elif section_name == 'main_text':
                for section in content:
                    paper_text += f"\n{section['title']}\n\n{section['content']}\n\n"
        # Return the structured sections as a dictionary

        return paper_text
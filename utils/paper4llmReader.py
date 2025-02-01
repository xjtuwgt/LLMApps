from utils.pdf_reader import split_markdown_sections
import pdf4llm

class PDFPaper4LLMParser(object):
    def __init__(self, write_images=False, page_chunks=False) -> None:
        self.write_images = write_images
        self.page_chunks = page_chunks

    def pdf2text(self, pdf_path: str):
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

    def run(self, pdf_path: str, verbose=True):
        markdown_text = self.pdf2text(pdf_path=pdf_path)
        sections = split_markdown_sections(text=markdown_text)
        struct_sections = self.structured_paper_content(markdown_sections=sections)
        if verbose:
            paper_text = ''
            for k, v in struct_sections.items():
                if k == 'title':
                    paper_text += '\nTitle: ' + v + '\n\n'
                elif k == 'abstract':
                    paper_text += '\nAbstract: \n'  + v + '\n\n'
                elif k == 'author':
                    paper_text += '\nAuthor: \n'  + '\n'.join(v) + '\n\n'
                elif k == 'main_text':
                    for section in v:
                        paper_text += '\n' + section['title'] + '\n\n' + section['content'] + '\n\n'
            print(paper_text)
        return struct_sections
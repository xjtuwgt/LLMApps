"""
paper2slides.py

This script is used to convert a research paper into a set of slides.

"""
slide_datasource = {
    'introduction': ['abstract', 'Introduction'],
    'objective': ['abstract', 'Introduction'],
    'methodoloy': ['abstract', 'Introduction', 'Conclusion', 'Methods'],
    'results': ['abstract', 'Experiments', 'Conclusion'],
    'conclusion': ['abstract', 'Introduction', 'Conclusion'],
}

from utils.paper4llmReader import PDFPaper4LLMParser
from utils.samba_api import call_api, SAMBA_MODEL as MODEL_ALIAS
import json
import time
import string

SLIDE_SEP = '<slide_sep>'

def trim_string(s):
    """
    Trim the string by removing the whitespace and punctuation.
    """
    return s.strip(string.whitespace + string.punctuation)


"""
Scientist paper section name mapping
"""
section_title_key_phrases = {
    'Introduction': ['introduction'],
    'Related Works': ['related work'],
    'Methods': ['method', 'approach'],
    'Experiments': ['experiment'],
    'Conclusion': ['conclusion'],
    'Acknowledgements': ['acknowledgement'],
    'References': ['references', ' references'], #
}

"""
Find the index of the target string in the list.
"""
def find_string_index(string_list, target: str):
    """
    Returns the index of the target string in the list.
    If the target is not found, returns -1.

    Parameters:
    string_list (list): A list of strings
    target (str): The string to find in the list

    Returns:
    int: The index of the target string, or -1 if not found
    """
    try:
        return string_list.index(target)
    except ValueError:
        return -1


"""
Get the section category from the section name.
"""
def get_section_category(section_name: str):
    """
    Scientist paper section name mapping
    """
    for key, phrases in section_title_key_phrases.items():
        for phrase in phrases:
            if phrase in section_name.lower():
                return key
    return 'Other'


class PaperReader(object):
    def __init__(self, page_chunks=False):
        self.paper_reader = PDFPaper4LLMParser(page_chunks=page_chunks)

    def pdf2text(self, paper_pdf_path: str):
        paper_content = self.paper_reader.run(pdf_path=paper_pdf_path, verbose=False)
        return paper_content
    
    def structurize(self, main_text_array: list):
        section_names = [_['title'] for _ in main_text_array]
        section_name_topics = [get_section_category(_) for _ in section_names]
        introduction_idx = find_string_index(section_name_topics, target='Introduction')
        refference_idx = find_string_index(section_name_topics, target='References')
        experiment_idx = find_string_index(section_name_topics, target='Experiments')
        conclusion_idx = find_string_index(section_name_topics, target='Conclusion')
        if refference_idx > 0:
            for idx in range(len(section_name_topics)):
                if idx < refference_idx:
                    if section_name_topics[idx] == 'Other':
                        section_name_topics[idx] = 'Methods'
                elif idx > refference_idx:
                    if not ('appendix' in section_name_topics[idx].lower()):
                        section_name_topics[idx] = 'Appendix: ' + section_name_topics[idx]
                else:
                    continue
            # print(section_name_topics)
            if experiment_idx > 0:
                for idx in range(experiment_idx +1, refference_idx):
                    if section_name_topics[idx] == 'Methods':
                        section_name_topics[idx] = 'Experiments'
        # print(section_name_topics)
        experiment_idx = find_string_index(section_name_topics, target='Experiments')
        method_idx = find_string_index(section_name_topics, target='Methods')
        relatedwork_idx = find_string_index(section_name_topics, target='Related Works')
        ack_idx = find_string_index(section_name_topics, target='Acknowledgements')
        
        paper_structure_dict = {
            'Introduction': [introduction_idx],
            'Related Works': [relatedwork_idx],
            'References': [refference_idx],
            'Conclusion': [conclusion_idx],
            'Acknowledgements': [ack_idx]
        }

        ## Experiments and methodology
        method_idx_array = []
        if method_idx >=0:
            for idx in range(method_idx, len(section_name_topics)):
                if section_name_topics[idx] == 'Methods':
                    method_idx_array.append(idx)
                else:
                    break
        else:
            if introduction_idx >=0 and conclusion_idx >=0:
                for idx in range(introduction_idx+1, conclusion_idx):
                    if section_name_topics[idx] == 'Methods':
                        method_idx_array.append(idx)
                    else:
                        break

        
        exp_idx_array = []
        if experiment_idx >=0:
            for idx in range(experiment_idx, len(section_name_topics)):
                if section_name_topics[idx] == 'Experiments':
                    exp_idx_array.append(idx)
                else:
                    break
        else:
            if introduction_idx >=0 and conclusion_idx >=0:
                for idx in range(introduction_idx+1, conclusion_idx):
                    if section_name_topics[idx] == 'Experiments':
                        exp_idx_array.append(idx)
                    else:
                        break
        
        paper_structure_dict['Experiments'] = exp_idx_array
        paper_structure_dict['Methods'] = method_idx_array
        return section_name_topics, paper_structure_dict

    def run(self, paper_file_name: str):
        paper_content = self.pdf2text(paper_pdf_path=paper_file_name)
        section_name_topics, paper_structure_dict = self.structurize(main_text_array=paper_content['main_text'])
        paper_content['structure'] = paper_structure_dict
        paper_content['section_topic'] = section_name_topics
        return paper_content

### 1. General System Prompt
    
SCHOLAR_PROMPT = """
You are an assistant being skilled at critically reading and analyzing academic papers to extract key insights, trends, and findings.
"""

### 2. Paper Outline Generation from Abstract

ABSTRACT_SUMMARY_PROMPT = """
You are given the **title** and **abstract** of an academic paper. Please first identity the research topic, and then extract the following aspects:
	
    1.	**Background**: Introduces the research context and importance.
	2.	**Research Problem**: Identifies the specific problem or knowledge gap.
	3.	**Objectives**: States the research goals or hypotheses.
	4.	**Methodology**: Summarizes the research design and key methods.
	5.	**Results**: Highlights the most significant findings.
	6.	**Conclusions**: Provides the main takeaways and their relation to the research question.

Reminder: Strictly output in JSON format **only**, using the keys: "Research topic", "Background", "Research problem", "Objectives", "Methodology", "Results" and "Conclusions".
"""

### 3. Evidence extraction from main paper text for "Background"
BACKGROUD_EVIDENCE_PROMPT = """
You are given the **title**, briefly description of **problem backgroud** and **introduction** of a research paper. From the introduction, extract an itemized list of **1 to 5 pieces of evidence** that support the problem background.

    Each piece of evidence must:
        1.	Be directly relevant to the problem background.
        2.	Be clear and concise.
        3.	Be unique, not repeating other evidence.

**Important**: Strictly output the itemized evidences ONLY.
"""


### 4. Evidence extraction from main paper text for "Research Problem"
RESEARCH_PROBLEM_PROMPT = """
You are given the **title**, briefly description of **research problem** and **introduction** of a research paper. Solely from the given introduction, extract the definition of the research problem, focusing on:
    
    1.	**Scope**: Define the problem’s boundaries;
	2.	**Challenges**: Identify key gaps or obstacles the research addresses;
    3.  **Assumptions**: State any assumptions guiding the research;
    4.  **Relevance*: Specify who benefits from solving the problem.

**Note**: Only output the problem definition.
"""


### 5. Evidence extraction from main paper text for "Objectives"

OBJECTIVE_PROMPT = """
You are given the **title**, **objectives** and **introduction** of a research paper. Solely from the given introduction, extract a list of **1 to 5 pieces of evidence** to support these objectives.

    Each piece of evidence must:
        1.	Be directly relevant to the objectives.
        2.	Be clear and concise.
        3.	Be unique, not repeating other evidence.
    
**Note**: Strictly output the itemized evidences ONLY.
"""

### 6. Evidence extraction from main paper text for "Conclusion"

CONCLUSION_PROMT = """
You are given the **title**, birief conclusion, and **full text conclusion** and **introduction** of a research paper. From the given conclusion and introduction, extract the **conclusion**, ensuring it includes:

	1.	**Summary of key findings**: Highlight the main results.
	2.	**Implications**: Explain the significance or impact of these findings.
	3.	**Future directions**: Mention any suggestions for future research or applications.
	4.	**Final takeaway**: Provide the overall takeaway message of the study.

**Note**: Only output the conclusion.”
"""

### 7. Evidence extraction from main paper text for "Experimental results" (iterative)

RESULT_PROMPT_DICT = {
  "system_instruction": """Given the title, the main results of an experimental study, and a paragraph from a research paper, your task is to extract and summarize evidence from the paragraph that supports the 'main results'.

   Follow these steps for each paragraph:
        1.	**Detect Evidence**: Check if the paragraph contains:
            1) Any evidence supporting the main results, or
            2) Experimental study information, including:
                - **Dataset**: Details on datasets, preprocessing, or train/test splits.
                - **Model Description**: Information of baselines, hyperparameters, and training.
                - **Evaluation Metrics**: Relevant metrics like accuracy, F1 score, and their justification.
                - **Comparative Analysis**: Comparisons with baselines, ablation studies, statistical significance.
                - **Runtime & Scalability**: Computational complexity and scalability.
        2.	**Response**: Choose 'YES' or 'NO':
            - If 'YES', extract and summarize the evidence or experimental details in 200 words. Ensure the summary is:
                - Clear and concise
                - Well-formatted for easy reading
                - Focused on key points: dataset, model Description, evaluation metrics, comparative analysis and runtime & scalability.
            - If 'NO', just respond with 'NO EVIDENCE'.
  """,

  "iterative_prompt": """Summarize the experimental details or evidence supporting the 'main results' in 200 words from the following paragraph (with title and content) if experiment-related information is detected. Follow these instructions:

	1.	List 2 to 4 itemized points.
	2.	Each point must specify the type ('Evidence' or 'Experimental Setup') and provide 1-2 sentences of content.

**Note**: Only provide the itemized summary.
  """,

  "final_prompt": """Using the **title**, the **main results** of an experimental study, and a list of experiment summaries from the research paper, follow these steps to summarize the results:

	1.	**Evidence Summary**: prive a numbered, itemized summary of **2-3** key points. Keep each point brief and focused (1-2 sentences).

	2.	**Experimental Summary**: Based all 'Experimental Setup' points and provide a concise summary covering the following aspects:
        1) **Datasets**: List only the names of all datasets used.
        2) **Baselines**: List only the names of all models/algorithms used.
        3) **Metrics**: List only the evaluation metrics used for comparison.
        4) **Results**: Summarize key comparisons and ablation results, focusing on the most important details.

  **Note**: Only output the “Evidence Summary” and “Experimental Summary.”
     """
}

## Methodology extraction

METHOD_PROMPT_DICT = {
    "system_instruction": """Given the **title**, the **method overview**, and a paragraph of a research paper. You task is identify and extract text being relevant to 'method overview' from the given paragraph.

    Follow these steps:
    1. **Method Information Detection**: Check if the paragraph contains:
       1) Any mention of the **method overview** or
       2) Specific method details, such as:
           - **Problem Definition**: The task, input, and expected output.
           - **Model Architecture**: Structure, key components, and learning type.
           - **Algorithm**: Steps of the method.
           - **Training Process**: Training data, optimization method, and loss function.
    2. **Response**: Choose 'YES' or 'NO':
        - If 'YES', summarize the method details in 200 words, ensuring it is:
            - Clear and concise
            - Well-formatted for readability
            - Focused on key points.
        - If 'NO', simply respond with 'NO Information'.
    """,
    "iterative_prompt": """Summarize the method description in 200 words from the following paragraph (with title and content) if method-related information is found. Follow these steps:
        
        1. List **2 to 4** method steps in numbered format..
        2. Ensure each step is related to the **method overview**.
        3. Keep each step clear and concise (1-2 sentences).
    
    **Note**: Only output the itemized method steps.
    """,

    "final_prompt": """Using **title**, **method overview**, and a list of itemized method step summary from a research paper, follow these instructions to summarize the method description::
        
        1. Provide a numbered list of **3-6 method steps** detailing the **method overview**.
        2. Keep each step clear and concise (1-2 sentences).
    
    **Note**: Only output the itemized method steps.
    """
}

SLIDES_REVISION_PROMPT = """You are an expert research assistant. Revise the following research paper slides to improve clarity and readability, while keeping the original structure intact. Different sections are splitted by '{}'. Ensure the following:

	1.	Simplify complex language and make the content concise.
	2.	Maintain the logical flow and structure of the slides.
	3.	Ensure key points and conclusions are easy to follow and well-highlighted.
	4.	Use bullet points where appropriate to enhance clarity.
	5.	Avoid excessive jargon, and ensure the slides are accessible to a broad academic audience.
""".format(SLIDE_SEP)

def make_api_call(model, messages, max_tokens, temperature):
    try:
        response = call_api(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)
        return response
    except Exception as e:
         return f"Failed to generate final answer. Error: {str(e)}", {}

def convert_to_dict(input_string: str):
    # Split the string by the delimiter (e.g., semicolon)
    lines = input_string.strip().split('\n')
    # Initialize an empty dictionary
    result_dict = {}
    # Iterate over each line
    for line in lines:
        # Split each line into key and value by the delimiter (e.g., colon)
        if ':' in line:
            key, value = line.split(':', 1)  # Split only on the first occurrence
            # Strip any whitespace and store in the dictionary
            result_dict[key.strip()] = value.strip()
    return result_dict


class Paper2Slides(object):
    def __init__(self, paper_contents: dict, model: str = 'llama70b_v3', max_tokens = 512, temprature=0.1):
        self.paper_contents = paper_contents
        if not self.valid_paper_checking():
            print('Not a valid paper structure, cannot generate slides')
            exit(1)
        self.model = MODEL_ALIAS[model]
        self.is_rate_limitation = ('405B' in self.model) or ('70B' in self.model)
        self.temprature = temprature
        self.max_failure_attempt_each_step = 3
        if '405B' in self.model:
            self.sleep_time = 8
        else:
            self.sleep_time = 4
        self.max_tokens = max_tokens
        print('{} model is used for slides generation!\nRate limitation = {}'.format(self.model, self.is_rate_limitation))
        self.revise_model = MODEL_ALIAS['llama70b_v3']
    
    def valid_paper_checking(self):
        try:
            assert 'abstract' in self.paper_contents, 'No abstract is detected'
            assert 'title' in self.paper_contents, 'No title is detected'
            paper_structure = self.paper_contents['structure']
            introduction_idx_array = paper_structure['Introduction']
            conclusion_idx_array = paper_structure['Conclusion']
            assert introduction_idx_array[0] >=0, 'No introduction is detected'
            assert conclusion_idx_array[0] >=0, 'No conclusion is detected'
        except AssertionError as e:
            print(f"AssertionError: {e}")
            return False
        return True

    def step(self, messages):
        result = self.run(messages=messages)
        if 'Failed' in result:
            time.sleep(5)
        if self.is_rate_limitation:
            print('sleep {} seconds'.format(self.sleep_time))
            time.sleep(self.sleep_time)
        return result
    
    def run(self, messages):
        for attempt in range(self.max_failure_attempt_each_step):
            try:
                response = make_api_call(messages=messages, model=self.model, max_tokens=self.max_tokens, temperature=self.temprature)
                return response
            except Exception as e:
                if attempt == self.max_failure_attempt_each_step - 1:
                    return "Failed to generate step after {} attempts. $ERROR$: {}".format(self.max_failure_attempt_each_step, str(e))
                else:
                    return "Failed to generate step. $ERROR$: {}".format(str(e))
                time.sleep(2)  # Wait for 1 second before retrying
        return 'Failed to generate reasoning step.'
        
    
    def abstract_summary(self):
        """
        Extract the outline for the slides from abstract
        """
        assert len(self.paper_contents['title']) > 0 and len(self.paper_contents['abstract']) > 512
        prompt = "**title**: {}\n\n**abstract**: {}".format(self.paper_contents['title'], self.paper_contents['abstract'])
        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": ABSTRACT_SUMMARY_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "I will extract the evidences following my instructions."}
        ]
        abstract_summary = self.step(messages=messages)
        try:
            abstract_summary_dict = json.loads(abstract_summary)
        except Exception as e:
            abstract_summary_dict = convert_to_dict(input_string=abstract_summary)
        
        trim_abstract_summary_dict = {}
        for k, v in abstract_summary_dict.items():
            trim_abstract_summary_dict[trim_string(k)] = v
        return trim_abstract_summary_dict

    def support_background(self, background: str, introduction: str):
        """
        Extract support evidences for background from introduction
        """
        prompt = "**title**: {}\n\n**promblem background**: {}\n\n**introduction**: {}".format(self.paper_contents['title'], background, introduction)
        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": BACKGROUD_EVIDENCE_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "I will extract the evidences following my instructions."}
        ]
        evidences = self.step(messages=messages)
        # print('Background evidences = {}'.format(evidences))
        step_num = 1
        return evidences, step_num

    def support_research_problem(self, research_problem: str, introduction: str):
        """
        Extract support evidences for research problem from introduction
        """
        prompt = "**title**: {}\n\n**research problem**: {}\n\n**introduction**: {}".format(self.paper_contents['title'], research_problem, introduction)
        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": RESEARCH_PROBLEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "I will extract the evidences following my instructions."}
        ]
        evidences = self.step(messages=messages)
        step_num = 1
        return evidences, step_num
    
    def support_objectives(self, objectives: str, introduction: str):
        """
        Extract support evidences for objectives from introduction
        """
        prompt = "**title**: {}\n\n**objectives**: {}\n\n**introduction**: {}".format(self.paper_contents['title'], objectives, introduction)
        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": OBJECTIVE_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "I will extract the evidences following my instructions."}
        ]
        evidences = self.step(messages=messages)
        step_num = 1
        return evidences, step_num

    def support_conclusion(self, conclusion: str, introduction: str, conclusion_text: str, step_wise=True):
        """
        Expand conclusion based on full-text conclusion and introducton. 
        If step_wise = True:
            1. Summarize introduction while focusing on conclusion part
            2. Extract conclusion points from introduction summary and full-context conclusion.
        """
        step_num = 0
        prompt = "**title**: {}\n\n**introduction**: {}".format(self.paper_contents['title'], introduction)
        if step_wise:
            messages = [
                {"role": "system", "content": SCHOLAR_PROMPT},
                {"role": "system", "content": "Given a **tititle** and **introduction** of a research paper, summarize and extract conclusion related information in about 200 words."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": "I will extract the conclusion following my instructions."}
            ]
            instruction_conclusion_summary = self.step(messages=messages)
            step_num = step_num + 1
        else:
            instruction_conclusion_summary = introduction

        prompt = "**title**: {}\n\n**brief conclusion**: {}\n\n**conclusion**: \n\n{}**introduction**: {}".format(self.paper_contents['title'], conclusion, conclusion_text, instruction_conclusion_summary)
        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": CONCLUSION_PROMT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "I will extract the conclusions following my instructions."}
        ]
        evidences = self.step(messages=messages)
        step_num = step_num + 1
        return evidences, step_num
    
    def support_experiment_results(self, main_results: str, paragraph_list: list):
        step_num = 0
        prompt = "**title**: {}\n\n**main results**: {}\n\n".format(self.paper_contents['title'], main_results)
        iterative_sys_prompt = RESULT_PROMPT_DICT['iterative_prompt']
        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": RESULT_PROMPT_DICT['system_instruction']},
            {"role": "user", "content": prompt},
            {"role": "system", "content": iterative_sys_prompt},
        ]

        follow_instruction = {"role": "assistant", "content": "I will extract the experimental information following my instructions."}

        paragraph_summary_array = []
        for para_idx in range(len(paragraph_list)):
            para_input_prompt = "Paragraph title: {}\n\nContent: {}\n\n".format(paragraph_list[para_idx]['title'], paragraph_list[para_idx]['content'])
            user_input = {'role': 'user', 'content': para_input_prompt}
            messages.append(user_input)
            messages.append(follow_instruction)
            para_summary = self.step(messages=messages)
            step_num = step_num + 1
            paragraph_summary_array.append(para_summary)
            messages.pop()
            messages.pop()

        ## Experimental result summary

        prompt = "**title**: {}\n\n**main results**: {}\n\n".format(self.paper_contents['title'], main_results)
        summary_prompt = '\n'.join(['**summary** {}:\n\n{}'.format(idx+1, summary) for idx, summary in enumerate(paragraph_summary_array)])
        input_prompt = prompt + summary_prompt

        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": RESULT_PROMPT_DICT['final_prompt']},
            {"role": "user", "content": input_prompt},
            {"role": "assistant", "content": "I will summarize the experimental results following my instructions."},
        ]

        result_summary = self.step(messages=messages)
        step_num = step_num + 1
        return result_summary, step_num

    def experiment_paragraph_extraction(self,):
        intro_idx = self.paper_contents['structure']['Introduction'][0]
        conclusion_idx = self.paper_contents['structure']['Conclusion'][0]
        experiment_idx_array = self.paper_contents['structure']['Experiments']
        if len(experiment_idx_array) == 0:
            experiment_idx_array = [_ for _ in range(intro_idx+1, conclusion_idx)]
        assert len(experiment_idx_array) > 0 and max(experiment_idx_array) < len(self.paper_contents['main_text'])
        experiment_idx_array = [intro_idx] + experiment_idx_array
        paragraphs = [self.paper_contents['main_text'][_] for _ in experiment_idx_array]
        return paragraphs
    
    def support_methodology(self, method_overview: str, paragraph_list: list):
        step_num = 0
        prompt = "**title**: {}\n\n**method overview**: {}\n\n".format(self.paper_contents['title'], method_overview)
        iterative_sys_prompt = METHOD_PROMPT_DICT['iterative_prompt']
        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": METHOD_PROMPT_DICT['system_instruction']},
            {"role": "user", "content": prompt},
            {"role": "system", "content": iterative_sys_prompt},
        ]

        follow_instruction = {"role": "assistant", "content": "I will extract the method information following my instructions."}

        method_summary_array = []
        for para_idx in range(len(paragraph_list)):
            para_input_prompt = "Paragraph title: {}\n\nContent: {}\n\n".format(paragraph_list[para_idx]['title'], paragraph_list[para_idx]['content'])
            user_input = {'role': 'user', 'content': para_input_prompt}
            messages.append(user_input)
            messages.append(follow_instruction)
            method_summary = self.step(messages=messages)
            step_num = step_num + 1
            method_summary_array.append(method_summary)
            messages.pop()
            messages.pop()

        ## Method summary
        prompt = "**title**: {}\n\n**method overview**: {}\n\n".format(self.paper_contents['title'], method_overview)
        method_summary_prompt = '\n'.join(['**method summary** {}:\n\n{}'.format(idx+1, summary) for idx, summary in enumerate(method_summary_array)])
        input_prompt = prompt + method_summary_prompt

        messages = [
            {"role": "system", "content": SCHOLAR_PROMPT},
            {"role": "system", "content": METHOD_PROMPT_DICT['final_prompt']},
            {"role": "user", "content": input_prompt},
            {"role": "assistant", "content": "I will generate a step-by-step method summary following my instructions."},
        ]
        method_summary = self.step(messages=messages)
        step_num = step_num + 1
        return method_summary, step_num
        
    def method_paragraph_extraction(self,):
        intro_idx = self.paper_contents['structure']['Introduction'][0]
        conclusion_idx = self.paper_contents['structure']['Conclusion'][0]
        method_idx_array = self.paper_contents['structure']['Methods']
        if len(method_idx_array) == 0:
            method_idx_array = [_ for _ in range(intro_idx+1, conclusion_idx)]
        assert len(method_idx_array) > 0 and max(method_idx_array) < len(self.paper_contents['main_text'])
        method_idx_array = [intro_idx] + method_idx_array
        paragraphs = [self.paper_contents['main_text'][_] for _ in method_idx_array]
        return paragraphs

    def generate_slides(self, verbose=True, revision=True):
        ## Step 1: Paper content extraction
        intro_idx = self.paper_contents['structure']['Introduction'][0]
        introduction = self.paper_contents['main_text'][intro_idx]['content']
        assert len(introduction) > 512, 'introduction = {}, content = {}'.format(introduction, self.paper_contents['main_text'])
        conclusion_idx = self.paper_contents['structure']['Conclusion'][0]
        conclusion = self.paper_contents['main_text'][conclusion_idx]['content']
        assert len(conclusion) > 128, 'conclusion = {}, content = {}'.format(introduction, self.paper_contents['main_text'])
        method_paragraphs = self.method_paragraph_extraction()
        experiment_paragraphs = self.experiment_paragraph_extraction()

        start_time = time.time()
        ## Step 2: slides structure extraction from abstract
        model_call_number = 0
        print('Slides structure generation')
        slides = {'Title': self.paper_contents['title']}
        outline_dict = self.abstract_summary()
        model_call_number += 1
        slides['Outline'] = outline_dict

        print('Slides generation...')
        background = outline_dict.get('Background', '')
        slides['Background'], b_steps = self.support_background(background=background, introduction=introduction)
        model_call_number += b_steps

        research_problem = outline_dict.get('Research problem', '')
        slides['Research problem'], r_steps = self.support_research_problem(research_problem=research_problem, introduction=introduction)
        model_call_number += r_steps
        
        objectives = outline_dict.get('Objectives', '')
        slides['Objectives'], o_steps = self.support_objectives(objectives=objectives, introduction=introduction)
        model_call_number += o_steps

        brief_conclusion = outline_dict.get('Conclusions', '')
        slides['Conclusions'], c_steps = self.support_conclusion(conclusion=brief_conclusion, introduction=introduction, conclusion_text=conclusion, step_wise=True)
        model_call_number += c_steps

        results = outline_dict.get('Results', '')
        result_summary, res_steps = self.support_experiment_results(main_results=results, paragraph_list=experiment_paragraphs)
        slides['Results'] = result_summary
        model_call_number += res_steps

        methodology = outline_dict.get('Methodology', '')
        method_summary, m_steps = self.support_methodology(method_overview=methodology, paragraph_list=method_paragraphs)
        model_call_number += m_steps
        slides['Methodology'] = method_summary
        runtime = time.time() - start_time
        print('Slide generation takes {:.4f} seconds with {} function calls'.format(runtime, model_call_number))
        if verbose:
            slides_content = self.presentation(slides=slides)
            if revision:
                slides_content = self.slides_revision(slide_content=slides_content)
            print('Generated slides:\n{}'.format(slides_content))
        return slides
    
    def slides_revision(self, slide_content: str):
        messages = [
            {"role": "system", "content": SLIDES_REVISION_PROMPT},
            {"role": "user", "content": slide_content},
            {"role": "assistant", "content": "I will revise the representation slides following my instructions."}
        ]
        print('Slides final revision')
        revised_slides = make_api_call(model=self.revise_model, messages=messages, max_tokens=2048, temperature=self.temprature)
        return revised_slides

    def presentation(self, slides: dict):
        slides_content = ''
        slides_content += '**Title**\n{}\n\n'.format(slides['Title'])
        slides_content += '{}\n'.format(SLIDE_SEP)
        slides_content += '**Outline**\n\n'
        outline_dict = slides['Outline']
        for sect_name, sect_content in outline_dict.items():
            slides_content += '{}\n--\t\t{}\n\n'.format(sect_name, sect_content)
        slides_content += '{}\n'.format(SLIDE_SEP)
        for sect_name in outline_dict.keys():
            if sect_name in slides:
                slides_content += '**{}**\n\n'.format(sect_name)
                slides_content += '{}\n\n'.format(slides[sect_name])
                slides_content += '{}\n'.format(SLIDE_SEP)
        return slides_content
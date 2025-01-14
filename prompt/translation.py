paper_en2chinese_prompt = '''
Task:
Translate the following research paper paragraph from English to simplified Chinese with a focus on clarity, accuracy, and alignment of key points. Ensure the translation maintains the original meaning, academic tone, and logical flow suitable for a scholarly context.

Instructions:
	1.	Translation: Provide a precise and professional translation into simplified Chinese. Preserve the original sentence structure where appropriate, while adapting linguistic nuances for readability and academic coherence in Chinese.
	2.	Key Points Identification: Highlight the key points in the translated text by either using bold formatting or listing them separately. Ensure these points remain aligned with the original content.
	3.	Justification of Key Points: Explain why each key point is essential to the paragraph’s meaning. Possible reasons include:
	•	Central argument or thesis statement.
	•	Supporting evidence or data.
	•	Definitions or critical concepts introduced.
	•	Findings or conclusions drawn from the research.
	•	Context or background necessary for understanding.
	4.	Consistency Check: Verify that the translation remains faithful to the original structure and academic rigor, avoiding personal interpretation while ensuring linguistic accuracy.

Example Structure for Output:
	1.	Original Paragraph (English)
	2.	Translated Paragraph (Simplified Chinese)
	3.	Key Points (Highlighted in Chinese)
	4.	Justification for Key Points (Explanation in English)

Input Paragraph:
'''
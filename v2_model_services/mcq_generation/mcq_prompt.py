def mcq_prompt(text, mcq_count):
    return f"""[INST]Generate {mcq_count} MCQs. Output ONLY this JSON format, nothing else:
[{{"question":"Q1?","options":["A","B","C","D"],"correct_answer":0}}]

Generate {mcq_count} questions from:
{text}[/INST]"""
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:
    import subprocess
    import sys
    # Try to install reportlab if missing
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

def create_sample_pdf(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "The Ecosystem of Artificial Intelligence")

    c.setFont("Helvetica", 12)
    text = [
        "Artificial Intelligence (AI) is a vast field of computer science focused on creating systems capable of performing",
        "tasks that typically require human intelligence. One of the primary subfields is Machine Learning (ML),",
        "which involves the use of algorithms and statistical models to enable computers to improve at tasks through experience.",
        "",
        "Within Machine Learning, Deep Learning (DL) has emerged as a particularly powerful approach. Deep Learning is",
        "based on Artificial Neural Networks (ANNs), which are inspired by the structure and function of the human brain.",
        "These networks consist of layers of interconnected nodes (neurons) that process information.",
        "",
        "Large Language Models (LLMs) are a recent breakthrough in the field of Natural Language Processing (NLP),",
        "a subset of AI dealing with the interaction between computers and human languages. LLMs like GPT or Llama",
        "are trained on massive datasets to understand and generate human-like text.",
        "",
        "The relationship between these concepts is hierarchical: AI encompasses Machine Learning, which encompasses",
        "Deep Learning. Neural Networks are the underlying architecture for Deep Learning, and LLMs are a specific",
        "application within the NLP and Deep Learning domain."
    ]

    y_position = height - 100
    for line in text:
        c.drawString(100, y_position, line)
        y_position -= 20

    c.save()
    print(f"✅ Success! Generated {filename}")

if __name__ == "__main__":
    create_sample_pdf("tests/test_concept_graph_sample.pdf")

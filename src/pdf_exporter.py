from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io

def generate_pdf(topic, summary, full_text):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"<b>AI-Augmented Hypothesis Report</b>", styles["Title"]))
    story.append(Paragraph(f"<b>Topic:</b> {topic}", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Executive Summary</b>", styles["Heading2"]))
    story.append(Paragraph(summary, styles["BodyText"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("<b>Full Investigative Report</b>", styles["Heading2"]))
    story.append(Paragraph(full_text.replace("\n", "<br/>"), styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

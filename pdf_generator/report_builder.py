from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, Image
)
from schemas.output_schema import AnalysisReport
from datetime import datetime
import os

# ── Color palette ──
BLUE_HEADER = colors.HexColor('#2563eb')  # A standard blue
LIGHT_BLUE_BG = colors.HexColor('#dbeafe')
BORDER_COLOR = colors.black
TEXT_COLOR = colors.black

def get_styles():
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(
        name='MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=BLUE_HEADER,
        spaceAfter=20
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.black,
        spaceBefore=20,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='NormalText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=10
    ))
    
    styles.add(ParagraphStyle(
        name='TableText',
        parent=styles['Normal'],
        fontSize=9,
        leading=11
    ))
    
    styles.add(ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=1  # Center
    ))
    
    return styles

def create_table(data, col_widths, style=None):
    t = Table(data, colWidths=col_widths)
    default_style = [
        ('GRID', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 6),
    ]
    if style:
        default_style.extend(style)
    t.setStyle(TableStyle(default_style))
    return t

def header_table_style():
    return [
        ('BACKGROUND', (0,0), (-1,0), BLUE_HEADER),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]

def generate_pdf_report(report: AnalysisReport, output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    styles = get_styles()
    story = []
    
    width = A4[0] - 3*cm
    
    # ── LOGO (Placeholder or Text) ──
    # If a logo exists, we would add it here. For now, text.
    story.append(Paragraph("<b>VAIVAL TECHNOLOGIES</b>", styles['Normal']))
    story.append(Paragraph("Project Requirement Document V1.3", ParagraphStyle('RightAlign', parent=styles['Normal'], alignment=2, textColor=colors.HexColor('#94a3b8'))))
    story.append(Spacer(1, 20))
    
    # ── Project Name & Date ──
    data = [
        [Paragraph("<b>Project Name</b>", styles['TableHeader']), Paragraph(f"<b>{report.project_name}</b>", styles['TableText'])],
        [Paragraph("<b>Date</b>", styles['TableHeader']), Paragraph(report.date, styles['TableText'])]
    ]
    t = create_table(data, [4*cm, width-4*cm], [
        ('BACKGROUND', (0,0), (0,0), BLUE_HEADER), # Project Name Header
        ('BACKGROUND', (0,1), (0,1), BLUE_HEADER), # Date Header
        ('TEXTCOLOR', (0,0), (0,1), colors.white),
    ])
    story.append(t)
    story.append(Spacer(1, 15))
    
    # ── Service Provider & Client ──
    # Header Row
    data = [
        [Paragraph("Service Provider", styles['TableHeader']), Paragraph("Client", styles['TableHeader'])]
    ]
    
    # Content Row
    sp = report.service_provider
    cl = report.client
    
    sp_text = f"""<b>Individual Name:</b> {sp.name}<br/>
<b>Address:</b> {sp.address}<br/>
<b>Contact Number:</b> {sp.contact}<br/>
<b>Email:</b> {sp.email}<br/><br/>
<b>OR</b><br/><br/>
<b>Name Of Company:</b> {sp.company_name}<br/>
<b>Registered Office Address:</b> {sp.company_address}<br/>
<b>Company Registration Number:</b> {sp.company_reg_number}<br/>
<b>Contact Number:</b> {sp.contact}<br/>
<b>Email:</b> {sp.email}"""

    cl_text = f"""<b>Individual Name:</b> {cl.name}<br/>
<b>Address:</b> {cl.address}<br/>
<b>Contact Number:</b> {cl.contact}<br/>
<b>Email:</b> {cl.email}<br/><br/>
<b>OR</b><br/><br/>
<b>Name Of Company:</b> {cl.company_name}<br/>
<b>Registered Office Address:</b> {cl.company_address}<br/>
<b>Company Registration Number:</b> {cl.company_reg_number}<br/>
<b>Contact Number:</b> {cl.contact}<br/>
<b>Email:</b> {cl.email}"""

    data.append([Paragraph(sp_text, styles['TableText']), Paragraph(cl_text, styles['TableText'])])
    
    t = create_table(data, [width/2, width/2], header_table_style())
    story.append(t)
    story.append(PageBreak())
    
    # ── 1. Introduction ──
    story.append(Paragraph("1. Introduction", styles['SectionHeader']))
    story.append(Paragraph(report.introduction, styles['NormalText']))
    story.append(Spacer(1, 10))
    
    # ── 2. Project Overview ──
    story.append(Paragraph("2. Project Overview", styles['SectionHeader']))
    
    # Main Header
    data = [[Paragraph("Project Overview", styles['TableHeader'])]]
    t = create_table(data, [width], header_table_style())
    story.append(t)
    
    # Detailed Rows
    ov = report.project_overview
    
    # Helper to make bullet points
    def make_bullets(items):
        return "<br/>".join([f"• {item}" for item in items])
    
    data = [
        [Paragraph("<b>Project Brief</b>", styles['TableText']), Paragraph(ov.brief, styles['TableText'])],
        [Paragraph("<b>Project Outcome</b>", styles['TableText']), Paragraph(make_bullets(ov.outcomes), styles['TableText'])],
        [Paragraph("<b>Stakeholders involved</b>", styles['TableText']), Paragraph(make_bullets(ov.stakeholders), styles['TableText'])],
        [Paragraph("<b>Project Timelines</b>", styles['TableText']), Paragraph(f"From: {ov.timeline_start}   To: {ov.timeline_end}", styles['TableText'])],
    ]
    t = create_table(data, [4*cm, width-4*cm])
    # Apply bold key formatting manually or relying on Paragraphs
    story.append(t)
    
    # Milestones (Nested Table feel)
    # Header
    data = [[
        Paragraph("<b>Project Milestones</b>", styles['TableText']),
        Paragraph("<b>Milestone 1:</b>", styles['TableText']),
        Paragraph("<b>Project Initiation</b>", styles['TableText']) # Placeholder mostly, layout is tricky
    ]]
    # Resetting the table strategy for Milestones to match the screenshot more closely:
    # Top row: "Project Milestones" | "Milestone X:" | "Name"
    # But wait, the screenshot has "Project Milestones" as a row label, and then columns for the milestone data.
    
    # Let's iterate through milestones and append them to a list to build a single table if possible,
    # OR create separate tables attached to the previous one.
    # The screenshot shows the "Project Milestones" label merging multiple rows on the left.
    # ReportLab supports span.
    
    # Simplified approach: distinct table for milestones.
    
    for i, m in enumerate(ov.milestones, 1):
        # Header Row for Milestone
        data = [
            [Paragraph(f"<b>Milestone {i}:</b>", styles['TableText']), Paragraph(f"<b>{m.name}</b>", styles['TableText'])],
            [Paragraph("Start and Due Date", styles['TableText']), Paragraph(f"{m.start_date} - {m.end_date}", styles['TableText'])],
            [Paragraph("Acceptance Criteria:", styles['TableText']), Paragraph(make_bullets(m.acceptance_criteria), styles['TableText'])]
        ]
        t = create_table(data, [4*cm, width-4*cm], [
            ('BACKGROUND', (0,0), (-1,0), LIGHT_BLUE_BG), # Milestone Header
        ])
        story.append(t)
    
    story.append(Spacer(1, 15))
    
    # ── 3. Project Deliverables ──
    story.append(Paragraph("3. Project Deliverables", styles['SectionHeader']))
    
    d = report.deliverables
    data = [
        [Paragraph("<b>Software Modules</b>", styles['TableHeader']), Paragraph(make_bullets(d.software_modules), styles['TableText'])],
        [Paragraph("<b>Documentation</b>", styles['TableHeader']), Paragraph(make_bullets(d.documentation), styles['TableText'])],
        [Paragraph("<b>Training materials</b>", styles['TableHeader']), Paragraph(make_bullets(d.training_materials), styles['TableText'])],
        [Paragraph("<b>User Manuals</b>", styles['TableHeader']), Paragraph(make_bullets(d.user_manuals), styles['TableText'])],
        [Paragraph("<b>Other[specify]</b>", styles['TableHeader']), Paragraph(make_bullets(d.other), styles['TableText'])],
    ]
    
    t = create_table(data, [4*cm, width-4*cm], [
        ('BACKGROUND', (0,0), (0,-1), BLUE_HEADER),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
    ])
    story.append(t)
    story.append(Spacer(1, 15))
    
    # ── 4. Functional Requirements ──
    story.append(Paragraph("4. Functional Requirements", styles['SectionHeader']))
    
    fr = report.functional_requirements
    data = [
        [Paragraph("<b>User Roles and Permissions</b>", styles['TableHeader']), Paragraph(make_bullets(fr.user_roles_permissions), styles['TableText'])],
        [Paragraph("<b>User Interface Specifications</b>", styles['TableHeader']), Paragraph(make_bullets(fr.ui_ux_specifications), styles['TableText'])],
        [Paragraph("<b>Data Management and Processes Requirements</b>", styles['TableHeader']), Paragraph(make_bullets(fr.data_management), styles['TableText'])],
        [Paragraph("<b>Integration with Other systems or APIs</b>", styles['TableHeader']), Paragraph(make_bullets(fr.integrations), styles['TableText'])],
    ]
    
    t = create_table(data, [6*cm, width-6*cm], [
        ('BACKGROUND', (0,0), (0,-1), BLUE_HEADER),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
    ])
    story.append(t)
    story.append(Spacer(1, 15))
    
    # ── 5. Non-Functional Requirements ──
    story.append(Paragraph("5. Non-Functional Requirements", styles['SectionHeader']))
    
    nfr = report.non_functional_requirements
    data = [
        [Paragraph("<b>Performance requirements</b>", styles['TableHeader']), Paragraph(make_bullets(nfr.performance), styles['TableText'])],
        [Paragraph("<b>Reliability requirements</b>", styles['TableHeader']), Paragraph(make_bullets(nfr.reliability), styles['TableText'])],
        [Paragraph("<b>Usability requirements</b>", styles['TableHeader']), Paragraph(make_bullets(nfr.usability), styles['TableText'])],
        [Paragraph("<b>Compatibility requirements</b>", styles['TableHeader']), Paragraph(make_bullets(nfr.compatibility), styles['TableText'])],
        [Paragraph("<b>Regulatory compliance requirements</b>", styles['TableHeader']), Paragraph(make_bullets(nfr.compliance), styles['TableText'])],
        [Paragraph("<b>Scalability</b>", styles['TableHeader']), Paragraph(make_bullets(nfr.scalability), styles['TableText'])],
        [Paragraph("<b>Maintainability</b>", styles['TableHeader']), Paragraph(make_bullets(nfr.maintainability), styles['TableText'])],
    ]
    
    t = create_table(data, [6*cm, width-6*cm], [
        ('BACKGROUND', (0,0), (0,-1), BLUE_HEADER),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
    ])
    story.append(t)
    story.append(Spacer(1, 15))
    
    # ── 6. Specific Technical Requirements ──
    story.append(Paragraph("6. Specific Technical Requirements", styles['SectionHeader']))
    
    tr = report.technical_requirements
    data = [
        [Paragraph("<b>Programming Language and Frameworks</b>", styles['TableHeader']), Paragraph(make_bullets(tr.languages_frameworks), styles['TableText'])],
        [Paragraph("<b>Database Requirements</b>", styles['TableHeader']), Paragraph(make_bullets(tr.database), styles['TableText'])],
        [Paragraph("<b>Hosting Environments</b>", styles['TableHeader']), Paragraph(make_bullets(tr.hosting), styles['TableText'])],
        [Paragraph("<b>Security Requirements</b>", styles['TableHeader']), Paragraph(make_bullets(tr.security), styles['TableText'])],
        [Paragraph("<b>Performance and Scalability Considerations</b>", styles['TableHeader']), Paragraph(make_bullets(tr.perf_scalability), styles['TableText'])],
    ]
    
    t = create_table(data, [6*cm, width-6*cm], [
        ('BACKGROUND', (0,0), (0,-1), BLUE_HEADER),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
    ])
    story.append(t)
    story.append(Spacer(1, 20))

    # ── 7. User Stories ──
    if report.user_stories:
        story.append(Paragraph("7. User Stories", styles['SectionHeader']))

        # Table header
        header = [
            Paragraph("<b>ID</b>", styles['TableHeader']),
            Paragraph("<b>User Story</b>", styles['TableHeader']),
            Paragraph("<b>Acceptance Criteria</b>", styles['TableHeader']),
        ]
        us_data = [header]

        for us in report.user_stories:
            story_text = (
                f"<b>As a</b> {us.role}, <b>I want to</b> {us.action}, "
                f"<b>so that</b> {us.benefit}."
            )
            criteria_text = make_bullets(us.acceptance_criteria)
            us_data.append([
                Paragraph(us.id, styles['TableText']),
                Paragraph(story_text, styles['TableText']),
                Paragraph(criteria_text, styles['TableText']),
            ])

        us_col_widths = [1.5*cm, (width - 1.5*cm) * 0.5, (width - 1.5*cm) * 0.5]
        us_table = create_table(us_data, us_col_widths, [
            ('BACKGROUND', (0, 0), (-1, 0), BLUE_HEADER),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ])
        story.append(us_table)
        story.append(Spacer(1, 20))

    # ── Signatories ──
    # Header
    data = [[Paragraph("Service Provider", styles['TableHeader']), Paragraph("Client", styles['TableHeader'])]]
    t = create_table(data, [width/2, width/2], header_table_style())
    story.append(t)
    
    # Sign blocks
    # Screenshot shows Title, Company Name, Signature, Date for both.
    
    sp_sign = f"""<b>Title:</b><br/><br/>
<b>Company Name:</b> {sp.company_name}<br/><br/><br/><br/>
<b>Signature:</b> __________________________<br/><br/>
<b>Date:</b> _______________________________"""

    cl_sign = f"""<b>Title:</b><br/><br/>
<b>Company Name:</b> {cl.company_name}<br/><br/><br/><br/>
<b>Signature:</b> __________________________<br/><br/>
<b>Date:</b> _______________________________"""
    
    data = [[Paragraph(sp_sign, styles['TableText']), Paragraph(cl_sign, styles['TableText'])]]
    t = create_table(data, [width/2, width/2])
    story.append(t)
    
    doc.build(story)
    print(f"✅ PDF report saved: {output_path}")

"""
Generate Security Assessment Report PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.colors import HexColor
from datetime import datetime

def create_security_report():
    """Generate the security assessment report PDF."""
    
    filename = f"Security_Assessment_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter,
                           rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1*inch, bottomMargin=0.75*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=HexColor('#2C3E50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#34495E'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=HexColor('#2C3E50'),
        spaceAfter=8,
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=HexColor('#2C3E50'),
        leftIndent=20,
        spaceAfter=6,
        leading=14
    )
    
    # Title
    elements.append(Paragraph("Security Assessment Report", title_style))
    elements.append(Paragraph("WebAutomationTool", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Date
    date_text = f"<b>Date:</b> November 22, 2025"
    elements.append(Paragraph(date_text, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    elements.append(Paragraph("Executive Summary", heading1_style))
    summary_text = """
    Comprehensive security review of WebAutomationTool completed. The application demonstrates 
    strong security posture with industry best practices implemented across encryption, authentication, 
    SSL/TLS handling, and input validation. Overall security score: <b>92/100</b>.
    """
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Security Score Table
    score_data = [
        ['Security Area', 'Score', 'Status'],
        ['Encryption', '10/10', '✅ Excellent'],
        ['Authentication', '9/10', '✅ Excellent'],
        ['SSL/TLS', '10/10', '✅ Excellent'],
        ['Input Validation', '10/10', '✅ Excellent'],
        ['Command Injection', '7/10', '⚠️ Medium'],
        ['File Handling', '9/10', '✅ Good'],
        ['Logging', '10/10', '✅ Excellent'],
        ['API Security', '9/10', '✅ Good'],
    ]
    
    score_table = Table(score_data, colWidths=[3*inch, 1*inch, 1.5*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#ECF0F1')]),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Page Break
    elements.append(PageBreak())
    
    # EXCELLENT FINDINGS
    elements.append(Paragraph("✅ EXCELLENT - No Action Required", heading1_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # 1. Credential Storage
    elements.append(Paragraph("1. Credential Storage & Encryption", heading2_style))
    cred_items = [
        "<b>Windows DPAPI:</b> API credentials encrypted with OS-level security",
        "<b>AES-256 Fernet:</b> Database fields encrypted (passwords, SSH credentials)",
        "<b>Bcrypt (12 rounds):</b> Password hashing with automatic salting",
        "<b>Secure key storage:</b> Encryption keys protected with file permissions (chmod 600)",
        "<b>Status:</b> Industry best practices implemented"
    ]
    for item in cred_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 2. Authentication
    elements.append(Paragraph("2. Authentication & Session Management", heading2_style))
    auth_items = [
        "<b>Session timeout:</b> 30-minute inactivity timeout with 5-minute warning",
        "<b>No hardcoded credentials:</b> Test credentials removed from login_dialog.py ✅",
        "<b>Password requirements:</b> Strong hashing prevents rainbow table attacks",
        "<b>Audit logging:</b> All authentication events tracked",
        "<b>Status:</b> Excellent implementation"
    ]
    for item in auth_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 3. SSL/TLS
    elements.append(Paragraph("3. SSL/TLS Certificate Handling", heading2_style))
    ssl_items = [
        "<b>Three security modes:</b> Full verification / Certificate pinning / Bypass (with warnings)",
        "<b>Visual warnings:</b> Red alerts when SSL verification disabled",
        "<b>Certificate manager:</b> Fingerprint tracking and change detection",
        "<b>Default secure:</b> verify=True by default, bypass requires explicit opt-in",
        "<b>Status:</b> Outstanding security controls"
    ]
    for item in ssl_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 4. Input Validation
    elements.append(Paragraph("4. Input Validation", heading2_style))
    validation_items = [
        "<b>Comprehensive module:</b> 11 validators created (input_validator.py) ✅",
        "<b>Database integration:</b> Validation enforced on all add/update operations ✅",
        "<b>XSS prevention:</b> Script tag and event handler detection",
        "<b>Type safety:</b> Regex patterns for AP IDs, IPs, emails, URLs, ports, MAC addresses",
        "<b>Status:</b> Newly implemented, excellent coverage"
    ]
    for item in validation_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 5. Logging
    elements.append(Paragraph("5. Logging & Information Disclosure", heading2_style))
    logging_items = [
        "<b>DEBUG messages removed:</b> No longer exposing URLs/usernames in console ✅",
        "<b>Error sanitizer:</b> ErrorSanitizer class prevents sensitive data leaks",
        "<b>Activity log filtering:</b> Info messages now unchecked by default ✅",
        "<b>Status:</b> Good information disclosure controls"
    ]
    for item in logging_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    
    # Page Break
    elements.append(PageBreak())
    
    # MEDIUM PRIORITY
    elements.append(Paragraph("⚠️ MEDIUM PRIORITY - Recommended Improvements", heading1_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # 6. Command Injection
    elements.append(Paragraph("6. Command Injection Risk (SSH/Batch Operations)", heading2_style))
    cmd_items = [
        "<b>Current state:</b> SSH commands executed via Paramiko without validation",
        "<b>Risk:</b> Users can execute any command on remote APs",
        "<b>Mitigation:</b> Warning message displayed, but no command whitelist",
        "<b>Recommendation:</b> Add dangerous pattern detection for commands like: rm -rf, dd if=, mkfs, shutdown, reboot, iptables flush. Require confirmation dialog for destructive operations.",
        "<b>Priority:</b> MEDIUM (mitigated by authentication and audit logging)"
    ]
    for item in cmd_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 7. Path Traversal
    elements.append(Paragraph("7. Path Traversal Protection", heading2_style))
    path_items = [
        "<b>Current state:</b> Uses os.path.join() for file paths (adequate)",
        "<b>Locations reviewed:</b> Screenshot saving, log file downloads, certificate cache",
        "<b>Status:</b> Generally safe, but could add explicit path validation",
        "<b>Recommendation:</b> Create safe_path_join() helper that validates paths stay within base directory",
        "<b>Priority:</b> LOW (current implementation is adequate)"
    ]
    for item in path_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # LOW PRIORITY
    elements.append(Paragraph("❌ LOW PRIORITY - Future Enhancements", heading1_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # 8. Rate Limiting
    elements.append(Paragraph("8. API Rate Limiting", heading2_style))
    rate_items = [
        "<b>Current state:</b> No rate limiting on authentication attempts",
        "<b>Risk:</b> Brute force attacks theoretically possible",
        "<b>Mitigation:</b> Bcrypt (12 rounds) makes brute force extremely slow; audit logging tracks all failed attempts; session timeout limits attack window",
        "<b>Recommendation:</b> Add login attempt tracking with temporary lockout (5 failed attempts = 15 minute lockout)",
        "<b>Priority:</b> LOW (bcrypt provides strong defense)"
    ]
    for item in rate_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # 9. Subprocess
    elements.append(Paragraph("9. Subprocess Command Execution", heading2_style))
    subprocess_items = [
        "<b>Locations:</b> batch_ping.py (ping commands), build scripts (PyInstaller)",
        "<b>Current state:</b> Limited to specific commands (ping, pyinstaller)",
        "<b>Status:</b> Safe - no user input passed to subprocess",
        "<b>Priority:</b> No action required"
    ]
    for item in subprocess_items:
        elements.append(Paragraph(f"• {item}", bullet_style))
    
    # Page Break
    elements.append(PageBreak())
    
    # Conclusion
    elements.append(Paragraph("Conclusion", heading1_style))
    conclusion_text = """
    WebAutomationTool demonstrates a <b>strong security posture</b> with industry best practices 
    implemented across all critical areas. The encryption implementation using Windows DPAPI and 
    AES-256 is excellent. Authentication with bcrypt hashing and session management provides robust 
    protection against unauthorized access. SSL/TLS handling includes multiple security modes with 
    clear visual warnings. The newly implemented input validation system provides comprehensive 
    protection against injection attacks.
    <br/><br/>
    The remaining issues identified are primarily about defense-in-depth and represent low to medium 
    risk. The SSH command injection risk is mitigated by authentication requirements and audit logging, 
    though adding command validation would provide an additional security layer. The lack of rate 
    limiting on authentication attempts is well-mitigated by bcrypt's computational cost.
    <br/><br/>
    <b>Overall Assessment:</b> The application is production-ready from a security perspective, with 
    a score of 92/100. The recommended improvements would bring the score to 98/100 and should be 
    considered for future releases.
    """
    elements.append(Paragraph(conclusion_text, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Recommendations Summary
    elements.append(Paragraph("Priority Recommendations", heading1_style))
    
    rec_data = [
        ['Priority', 'Item', 'Effort'],
        ['MEDIUM', 'Implement SSH command validation with dangerous pattern detection', 'Medium'],
        ['LOW', 'Add safe_path_join() helper for explicit path validation', 'Low'],
        ['LOW', 'Implement login rate limiting (5 attempts = 15 min lockout)', 'Low'],
    ]
    
    rec_table = Table(rec_data, colWidths=[1*inch, 3.5*inch, 1*inch])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E74C3C')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#BDC3C7')),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#ECF0F1')]),
    ]))
    elements.append(rec_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer note
    footer_text = """
    <i>This security assessment was conducted on November 22, 2025. The application code should be 
    re-assessed after major feature additions or when handling new types of sensitive data.</i>
    """
    elements.append(Paragraph(footer_text, body_style))
    
    # Build PDF
    doc.build(elements)
    print(f"✅ Security report generated: {filename}")
    return filename

if __name__ == "__main__":
    create_security_report()

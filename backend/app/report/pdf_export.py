"""PDF report generation using Jinja2 templates."""
import logging
import os

from jinja2 import Environment, FileSystemLoader

from app.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def generate_pdf(report_data: dict, session_id: str) -> str | None:
    """Generate a PDF report from report data. Returns file path."""
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning("weasyprint not available, skipping PDF generation")
        return _generate_html_only(report_data, session_id)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")
    html_content = template.render(**report_data)

    output_dir = settings.capture_dir
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"report_{session_id}.pdf")

    try:
        HTML(string=html_content).write_pdf(pdf_path)
        logger.info(f"PDF report saved: {pdf_path}")
        return pdf_path
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        return _generate_html_only(report_data, session_id)


def _generate_html_only(report_data: dict, session_id: str) -> str | None:
    """Fallback: save HTML report when PDF generation is not available."""
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")
    html_content = template.render(**report_data)

    output_dir = settings.capture_dir
    os.makedirs(output_dir, exist_ok=True)
    html_path = os.path.join(output_dir, f"report_{session_id}.html")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path

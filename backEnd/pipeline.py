from dotenv import load_dotenv
# Load environment
load_dotenv()
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, HRFlowable
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from tzlocal import get_localzone
from reportlab.lib import colors
from datetime import datetime
from typing import Optional, List
import argparse
import requests
import json
import os
import re



# Global case metadata initialization
case_metadata = {
    "case_name": "Sample Case",
    "citation": "Sample Citation",
    "date": "Unknown Date",
    "url": "N/A",
    "judges": "Unknown",
    "procedural_history": "...",
    "attorneys": "...",
    "disposition": "..."
}

def build_cover_page(brief: dict, styles: dict, logo_path: str):
    elems = []
    # Centered logo
    img = ImageReader(logo_path)
    orig_w, orig_h = img.getSize()
    cover_h = 2 * inch
    cover_w = orig_w * (cover_h / orig_h)
    logo = Image(logo_path, width=cover_w, height=cover_h)
    logo.hAlign = "CENTER"
    elems.append(Spacer(1, 1.35 * inch))
    elems.append(logo)
    elems.append(Spacer(1, 0.5 * inch))

    # Case Title
    case_name = brief.get("Case Name", "Unknown Case")
    date_filed = brief.get("Date Filed", "Unknown Date")
    year = date_filed.split("-")[0] if "-" in date_filed else date_filed
    title = f"{case_name} ({year})"
    elems.append(Paragraph(title, styles["TitleText"]))
    elems.append(Spacer(1, 0.2 * inch))
    elems.append(Paragraph("– CASE BRIEF –", styles["CoverMetaHeading"]))
    elems.append(Spacer(1, 0.5 * inch))

    # Docket & Date
    elems.append(Paragraph(f"Citation: {brief.get('Citation', '—')}", styles["CoverMeta"]))       
    elems.append(Paragraph(f"Docket No.: {brief.get('Docket Number', '—')}", styles["CoverMeta"]))  
    elems.append(Paragraph(f"Date Filed: {brief.get('Date Filed', 'Unknown Date')}", styles["CoverMeta"]))

    # Final rule line
    elems.append(Spacer(1, 0.5 * inch))
    elems.append(HRFlowable(
        width="85%",
        thickness=4,
        lineCap="round",
        color=colors.HexColor("#800020"),
        spaceBefore=12, spaceAfter=24
    ))

    # Push main brief to page 2
    elems.append(PageBreak())
    return elems

def _draw_header(canvas, doc):
    canvas.saveState()
    page_w, page_h = doc.pagesize

    # load your logo…
    logo_path = os.path.join(os.path.dirname(__file__), 'logo_transparent.png')
    img = ImageReader(logo_path)
    orig_w, orig_h = img.getSize()

    # scale logo to 0.9" tall
    h = 0.85 * inch
    w = orig_w * (h / orig_h)

    # fixed 0.25" margin
    margin = 0.25 * inch

    # bottom-left of logo at (margin, page_h – margin – logo_height)
    x = margin
    y = page_h - margin - h

    canvas.drawImage(logo_path, x, y, width=w, height=h, mask='auto')
    canvas.restoreState()

def make_unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    while os.path.exists(new_path):
        new_path = f"{base} ({counter}){ext}"
        counter += 1
    return new_path

# ----------- Mixtral Integration -----------
def generate_case_sections_with_mixtral(
    text: str,
    mode: str = "professional",
    case_name: str = "",
    citation: str = "",
    temperature: float = 0.3,
    max_tokens: int = 1500,
    stop: Optional[List[str]] = None,
    _retry: bool = False
) -> dict:
    if mode == "student":
        detail_instructions = (
            "Use clear, accessible legal language and explain each section in 4–6 sentences. "
            "Include examples or analogies where helpful to aid comprehension."
        )
    else:
        detail_instructions = (
            "Use formal, detailed legal writing. Provide 3–5 sentences per section using precise legal terminology, "
            "with references to relevant facts, doctrines, or precedent when appropriate."
        )

    prompt = f"""
You are LexEmetica Clerk, a legal writing assistant.

The following is the full text of the U.S. Supreme Court opinion in **{case_name}, {citation}**, a real and specific legal case.

Analyze *only* this opinion and extract the following six sections using professional legal language. Refer to the actual events, rulings, and reasoning in this case only:

- Disposition
- Rule of Law
- Facts
- Issue
- Holding and Reasoning
- Dissent

Each section should be explained in detail (minimum 3–5 sentences). Respond in JSON format like:

{{
    "Disposition": "...",
    "Rule of Law": "...",
    "Facts": "...",
    "Issue": "...",
    "Holding & Reasoning": "...",
    "Dissent": "..."
}}

🛡️ Before returning your final answer, carefully verify the accuracy of each section based strictly on the court opinion provided above. Do not rely on general legal knowledge or assumptions.

Perform the following quality checks before submitting your response:

- ✅ Cross-check all extracted facts and holdings directly against the provided opinion text.
- ✅ Ensure all references to constitutional amendments, legal doctrines, and precedents are explicitly supported by the source text.
- ✅ Do not fabricate names, case titles, or outcomes — only use entities explicitly mentioned.
- ✅ If dissenting justices are mentioned, confirm they are correctly identified and not misattributed to the majority.
- ✅ Do not include content that generalizes beyond this specific case (e.g., unrelated doctrines or other case law).
- ✅ Do not include interpretations or reasoning not present in the opinion.
- ✅ Use only the facts and language presented in the court's own wording wherever possible.
- ✅ If uncertain about the accuracy of a statement, omit it entirely.
- ✅ If any section fails verification, **rewrite only that section** to eliminate the issue.

📚 After each section, include a parenthetical indicating the page number from the opinion text, such as (Page 440), to help the reader locate the source.

All content must remain strictly specific to **{case_name}**, {citation}.

Court Opinion:
{text}
"""

    try:
        print("⏳ Generating case brief using Mixtral... (this may take a while)")
        payload = {
            "model": "mixtral",
            "prompt": prompt,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop is not None:
            payload["stop"] = stop

        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload
        )
        print("DEBUG RAW RESPONSE:")
        print(response.text)

        result_str = response.json().get("response", "")
        match = re.search(r"\{.*\}", result_str, re.DOTALL)

        if match:
            brief_data = json.loads(match.group(0))

            combined_text = " ".join(brief_data.values()).lower()
            case_name_keyword = case_name.lower().split()[0]

            if case_name_keyword not in combined_text:
                if not _retry:
                    print("⚠️ Hallucination detected on first try. Retrying with stricter prompt...")
                    return generate_case_sections_with_mixtral(
                        text,
                        mode,
                        case_name,
                        citation,
                        temperature,
                        max_tokens,
                        stop,
                        _retry=True
                    )
                else:
                    print("❌ Second attempt also failed: hallucination still detected.")
                    return {k: "[ERROR: hallucination]" for k in ["Disposition", "Rule of Law", "Facts", "Issue", "Holding & Reasoning", "Dissent"]}

            return brief_data

        else:
            raise ValueError("No JSON object found in model response.")

    except Exception as e:
        print(f"Error generating brief: {e}")
        return {k: "[ERROR]" for k in ["Disposition", "Rule of Law", "Facts", "Issue", "Holding & Reasoning", "Dissent"]}

# ----------- Input Handling -----------
def handle_input(case_number: Optional[str] = None, pdf_path: Optional[str] = None, raw_text: Optional[str] = None) -> str:
    global case_metadata
    if case_number:
        result = fetch_case_by_citation(case_number, os.getenv("CL_API_KEY"))
        if "error" in result:
            raise ValueError(result["error"])
        case_metadata = result
        return result["full_text"]
    elif pdf_path:
        abs_pdf = os.path.abspath(pdf_path)
        case_metadata["url"] = f"file://{abs_pdf}"
        return parse_pdf_to_text(pdf_path)
    elif raw_text:
        return raw_text
    else:
        raise ValueError("No input provided")

# ----------- CourtListener API Fetch -----------
def fetch_case_by_citation(citation: str, api_key: str) -> dict:
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "LexEmetica Clerk/1.0 (Theodor Owchariw; for academic use)"
    }
    try:
        response = requests.post(
            "https://www.courtlistener.com/api/rest/v4/citation-lookup/",
            headers=headers,
            json={"text": citation}
        )
        response.raise_for_status()
        results = response.json()
        cluster = results[0]["clusters"][0]
        opinion_data = requests.get(cluster["sub_opinions"][0], headers=headers).json()
        rel_path = cluster.get("absolute_url", "")
        full_url = f"https://www.courtlistener.com{rel_path}"

        return {
            "case_name": cluster.get("case_name", "Unknown Case"),
            "citation": citation,
            "date": cluster.get("date_filed", "Unknown Date"),
            "url": full_url, 
            "judges": cluster.get("judges", "Unknown"),
            "procedural_history": cluster.get("procedural_history", "..."),
            "attorneys": cluster.get("attorneys", "..."),
            "disposition": cluster.get("disposition", "..."),
            "full_text": opinion_data.get("plain_text", "No full text available."),
            "court":       cluster.get("court_id", "Unknown Court"),    
            "docket_number": cluster.get("docketNumber", "—"),  
            "opinion_author": opinion_data.get("author", "Unknown"),    
        }
    except Exception as e:
        return {"error": f"Error fetching case: {str(e)}"}

# ----------- PDF Fallback -----------
def parse_pdf_to_text(pdf_path: str) -> str:
    return "[PDF Parsing Placeholder]"

def preprocess(text: str) -> str:
    # Normalize stray punctuation and merge line breaks first    
    text = text.replace(".,", ",")                              
    text = re.sub(r"\s*\n\s*", " ", text)                      

    # Existing cleanup
    text = re.sub(r"\*(\d{1,4})", r"[Page \1]", text)
    text = re.sub(r'\n(?=\S)', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ----------- Segment Brief -----------
def segment_case_sections(
    text: str,
    metadata: dict,
    mode: str,
    temperature: float,
    max_tokens: int,
    stop: Optional[List[str]]
) -> dict:
    summary = generate_case_sections_with_mixtral(
        text,
        mode=mode,
        case_name=metadata.get("case_name", ""),
        citation=metadata.get("citation", ""),
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop
    )
    return {
        "Court":        metadata.get("court", "Unknown Court"),   
        "Docket Number": metadata.get("docket_number", "—"),       
        "Judges": metadata.get("judges", "Unknown"),
        "Opinion Author": metadata.get("opinion_author", "Unknown"),
        "Procedural History": metadata.get("procedural_history", "..."),
        "Attorneys": metadata.get("attorneys", "..."),
        "Disposition": summary.get("Disposition", metadata.get("disposition", "...")),
        "Rule of Law": summary.get("Rule of Law", "..."),
        "Facts": summary.get("Facts", "..."),
        "Issue": summary.get("Issue", "..."),
        "Holding & Reasoning": summary.get("Holding & Reasoning", "..."),
        "Dissent": summary.get("Dissent", "...")
    }

# ----------- Export Brief -----------
def export_brief(brief: dict, fmt: str, out: str):
    # Add timestamp and disclosure for JSON and TXT exports
    if fmt in ("json", "txt"):
        local_timezone = get_localzone()
        timestamp = datetime.now(local_timezone).strftime("%B %d, %Y at %I:%M %p (%Z)")
        generation_note = f"Generated using LexEmetica Clerk on {timestamp}"
        disclosure_text = (
            "This brief was generated with the assistance of an AI system trained to summarize legal opinions based on the provided court text. "
            "While efforts have been made to ensure accuracy, this document may contain errors, omissions, or hallucinated content.\n\n"
            "Users must not rely solely on this brief for legal decision-making, academic work, or court preparation. "
            "Always cross-check information against the original court opinion and consult with a licensed attorney if applicable.\n\n"
            "Use of this tool is at your own risk. No liability is assumed by the developer or contributors for any inaccuracies."
        )

    # JSON output
    if fmt == "json":
        output_data = brief.copy()
        output_data["Generation Info"] = generation_note
        output_data["Disclosure"] = disclosure_text
        with open(out, 'w') as f:
            json.dump(output_data, f, indent=2)

    # Plain-text output
    elif fmt == "txt":
        with open(out, 'w') as f:
            for k, v in brief.items():
                f.write(f"{k}:\n{v}\n\n")
            f.write("Generation Info:\n")
            f.write(f"{generation_note}\n\n")
            f.write("Disclosure:\n")
            f.write(f"{disclosure_text}\n")

    # PDF output
    elif fmt == "pdf":
        # Create the document
        doc = SimpleDocTemplate(
            out,
            pagesize=LETTER,
            leftMargin=1 * inch,
            rightMargin=1 * inch,
            topMargin=1 * inch,
            bottomMargin=1 * inch,
            title="LexEmetica Case Brief"
        )

        # Load and configure styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="LegalBodyText",
            parent=styles["Normal"],
            fontName="Times-Roman",
            fontSize=11,
            leading=14,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            name="CoverMeta",
            parent=styles["Normal"],
            fontName="Times-Roman",
            fontSize=14,
            leading=18,
            alignment=1            
        ))
        styles.add(ParagraphStyle(
            name="CoverMetaHeading",
            parent=styles["Heading3"],
            fontName="Times-Bold",
            fontSize=20,
            spaceAfter=6,
            textColor=colors.HexColor("#800020"),
            alignment=1
        ))
        styles.add(ParagraphStyle(
            name="BriefHeading",
            parent=styles["Heading3"],
            fontName="Times-Bold",
            fontSize=13,
            spaceAfter=6,
            textColor="navy"
        ))
        styles.add(ParagraphStyle(
            name="TitleText",
            parent=styles["Normal"],
            fontName="Times-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#800020"),
            spaceAfter=10,
            alignment=1
        ))
        styles.add(ParagraphStyle(
            name="DisclosureText",
            parent=styles["Normal"],
            fontName="Times-Italic",
            fontSize=9,
            leading=12,
            textColor=colors.grey,
            spaceBefore=12,
            spaceAfter=12
        ))

        elements = []
        # 1) Cover Page
        logo_path = os.path.join(os.path.dirname(__file__), 'logo_transparent.png')
        elements.extend(build_cover_page(
            brief=brief,
            styles=styles,
            logo_path=logo_path
        ))
        

        # --- Generate and Add Title ---
        case_title = brief.get("Case Name", "Unknown Case")
        case_year = brief.get("Date Filed", "Unknown Date").split("-")[0]
        title_text = f"{case_title} ({case_year}) – Case Brief"
        elements.append(Paragraph(title_text, styles["TitleText"]))

        # Horizontal rule under title
        elements.append(HRFlowable(
            width="85%",
            thickness=2,
            lineCap='round',
            color=colors.HexColor("#800020"),
            spaceBefore=4,
            spaceAfter=20
        ))

        # --- Main Brief Content ---
        for section, content in brief.items():
            elements.append(Paragraph(f"<b>{section}:</b>", styles["BriefHeading"]))
            elements.append(Paragraph(content.replace('\n', '<br/>'), styles["LegalBodyText"]))

        # --- Footer with Timestamp & Disclosure ---
        timestamp = datetime.now(get_localzone()).strftime("%B %d, %Y at %I:%M %p (%Z)")
        disclosure_full = (
            f"Generated using LexEmetica Clerk on {timestamp}<br/><br/>"
            "<b>Disclosure:</b><br/>"
            "This brief was generated with the assistance of an AI system trained to summarize legal opinions based on the provided court text. "
            "While efforts have been made to ensure accuracy, this document may contain errors, omissions, or hallucinated content.<br/><br/>"
            "Users must not rely solely on this brief for legal decision-making, academic work, or court preparation. "
            "Always cross-check information against the original court opinion and consult with a licensed attorney if applicable.<br/><br/>"
            "Use of this tool is at your own risk. No liability is assumed by the developer or contributors for any inaccuracies."
            "<br/><br/>© 2025 LexEmetica Clerk. All rights reserved.<br/>"
            "Unauthorized copying, reproduction, or distribution of this material, in whole or in part, without the prior written consent of LexEmetica Clerk is strictly prohibited."
        )
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph(disclosure_full, styles["DisclosureText"]))

        doc.build(
          elements,
          onFirstPage=lambda c, d: None,  # no header on cover
          onLaterPages=_draw_header      # header starting with page 2
        )

# ----------- CLI -----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=str, help="Case citation number")
    parser.add_argument("--pdf", type=str, help="Path to PDF")
    parser.add_argument("--text", type=str, help="Raw case text")
    parser.add_argument("--mode", type=str, choices=["student", "professional"], default="student")
    parser.add_argument("--format", type=str, choices=["json", "txt", "pdf"], default="json")
    parser.add_argument("--output", type=str, default="brief_output.json")
    parser.add_argument("--temperature", type=float, default=0.3, help="Sampling temperature for generation (0.0–1.0)")
    parser.add_argument("--max-tokens", type=int, default=1500, help="Maximum number of tokens to generate")
    parser.add_argument("--stop-sequences", nargs="*", default=None, help="One or more stop sequences (e.g. --stop-sequences '###' '')")
    args = parser.parse_args()

    full_text = handle_input(args.case, args.pdf, args.text)
    cleaned_text = preprocess(full_text)
    brief_sections = segment_case_sections(
        cleaned_text,
        case_metadata,
        args.mode,
        args.temperature,
        args.max_tokens,
        args.stop_sequences
    )

    final_brief = {
        # 1) Identifiers
        "Case Name":      case_metadata["case_name"],
        "Citation":       case_metadata["citation"],
        "Date Filed":     case_metadata["date"],          
        "Docket Number":  brief_sections["Docket Number"],

        # 2) Context / Metadata
        "Court":              brief_sections["Court"],
        "Source URL":         case_metadata["url"],
        "Judges":             brief_sections["Judges"],
        "Procedural History": brief_sections["Procedural History"],
        "Attorneys":          brief_sections["Attorneys"],

        # 3) Substantive Sections
        "Facts":                brief_sections["Facts"],
        "Issue":                brief_sections["Issue"],
        "Rule of Law":          brief_sections["Rule of Law"],
        "Holding & Reasoning":  brief_sections["Holding & Reasoning"],
        "Disposition":          brief_sections["Disposition"],
        "Dissent":              brief_sections["Dissent"],
    }


    if args.format == "pdf" and args.output == "brief_output.json":
        args.output = f"{final_brief['Case Name'].replace(' ', '_').replace('/', '_')}.pdf"

    if any("[ERROR" in v for v in final_brief.values()):
        print("❌ Brief generation failed due to hallucination. Nothing was saved.")
    else:
        if args.format == "pdf":
            args.output = make_unique_path(args.output)

        export_brief(final_brief, args.format, args.output)
        print(f"✅ Brief saved to {args.output}")
        print(args.output)
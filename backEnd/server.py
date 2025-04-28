# --- server.py (FastAPI Backend) ---

import subprocess
import shlex
import os

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import FileResponse

app = FastAPI(
    title="LexEmetica-Clerk Server",
    description="Proxy to pipeline.py for PDF case briefs",
    version="1.0"
)

@app.post("/api/brief/by-citation")
async def brief_by_citation(
    citation: str = Form(...),
    mode:     str = Form("professional"),
    fmt:      str = Form("pdf")
):
    # Validate inputs
    if not citation.strip():
        raise HTTPException(400, "Citation cannot be empty")
    if fmt.lower() != "pdf":
        raise HTTPException(400, "This endpoint only supports PDF")

    # Build the safe shell command
    cmd = (
        f"python3 pipeline.py "
        f"--case {shlex.quote(citation)} "
        f"--mode {shlex.quote(mode)} "
        f"--format pdf"
    )

    try:
        # Run the pipeline and capture stdout/stderr
        proc = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        # Return the pipeline's stderr on failure
        raise HTTPException(500, f"Pipeline error:\n{e.stderr}")

    # The last line of stdout should be the generated filename
    lines = proc.stdout.strip().splitlines()
    if not lines:
        raise HTTPException(500, "Pipeline did not report an output file")
    output_file = lines[-1]

    # Confirm it exists
    if not os.path.isfile(output_file):
        raise HTTPException(500, f"Pipeline reported file '{output_file}' but it was not found")

    # Derive case name for better download filename
    case_name = os.path.splitext(os.path.basename(output_file))[0]
    clean_case_name = case_name.replace('_', ' ').replace('.', '').strip()

    response = FileResponse(
        output_file,
        filename=os.path.basename(output_file),
        media_type='application/pdf'
    )
    response.headers["X-Case-Name"] = clean_case_name
    return response
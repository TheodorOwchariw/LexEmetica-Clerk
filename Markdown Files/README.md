# LexEmetica Clerk

**A command-line and web API tool to generate case briefs from U.S. Supreme Court opinions.**

## Tech Stack

- Python 3.10+
- FastAPI
- Uvicorn
- ReportLab
- tzlocal
- CourtListener API integration
- Frontend: React + Tailwind + Vite (proxy to API)
- [Node.js v18+](https://nodejs.org/) (install via nvm, Homebrew, apt, etc.)

## Quickstart

1. **Clone the repo**

   ```bash
   git clone https://github.com/TheodorOwchariw/LexEmetica-Clerk.git
   cd LexEmetica-Clerk
   ```

2. **(Optional) Build the sandbox container**\
   To fully replicate the environment, you can build a Singularity sandbox container using provided 'Singularity_LexEmetica-Clerk.def':

   ```bash
   sudo singularity build LexEmetica-Clerk_sandbox.sif Singularity_LexEmetica-Clerk.def
   ```

   Then enter the sandbox:

   ```bash
   singularity shell --nv --writable LexEmetica-Clerk_sandbox.sif
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

 4. **Create and populate your `.env` file** (see `ENVIRONMENT.md`)

    ```bash
    # Open a new .env in nano:
    nano .env

    # Then inside the editor, add your API key:
    CL_API_KEY=your_courtlistener_token_here

    # Save (Ctrl+O, Enter) and exit (Ctrl+X)
    ```

5. **Start all required servers**

   - **Model Server** (Ollama or Mixtral) on port `11434`:
     ```bash
     ollama serve
     # or
     mixtral serve
     ```
   - **FastAPI Back End** on port `8000`:
     ```bash
     uvicorn server:app --reload --host 0.0.0.0 --port 8000
     ```
   - **Vite Front End** (optional, for UI) on port `5173`:
     ```bash
     cd frontEnd
     npm install
     npm run dev -- --host 0.0.0.0 --port 5173
     ```

6. **Use the Web UI**

Open your browser to:

```
http://localhost:5173
```

7. **Use the CLI**

   ```bash
   python pipeline.py --case "384 U.S. 436" --mode professional --format pdf
   ```

8. **Use the API**

   ```bash
   curl -X POST http://localhost:8000/api/brief/by-citation \
     -F "citation=384 U.S. 436" -F "mode=professional" -F "fmt=pdf" \
     -o Miranda_v._Arizona.pdf
   ```

---
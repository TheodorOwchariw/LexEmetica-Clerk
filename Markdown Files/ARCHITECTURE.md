# Architecture Overview

```
+------------+      HTTP       +------------+      Shell      +-------------+
| Frontend   | ----------------> | FastAPI   | --------------> | pipeline.py |
| (React/Vite)|                  | server.py |   subprocess    | CLI logic   |
+------------+                   +-----------+                  +-------------+
                                    |
                                    | File download (PDF)
                                    v
                                 Browser/User
```

- **pipeline.py**: Core CLI to fetch, parse, segment, and export briefs.
- **server.py**: Thin FastAPI layer wrapping the CLI, streaming back PDFs.
- **Frontend**: React + Tailwind + Vite proxy to `/api` endpoints for JSON and PDF.

Case briefs are named by sanitized case names (e.g. `Miranda_v._Arizona.pdf`) and stored in the working directory.
# HPC Development Guide for LexEmetica-Clerk

Follow these steps to set up and run the full stack (model server, back end, front end) on an HPC cluster.

---

## 1. Enter Your Container or Sandbox

If you’re using a containerized environment, shell into it:

```bash

singularity shell --nv --writable LexEmetica-Clerk_sandbox.sif
```

---

## 2. Start the Model Server

Inside the container, launch your LLM server (e.g. Ollama or Mixtral):

```bash
# Ollama example
ollama serve

# Or Mixtral example
mixtral serve
```

By default this listens on port `11434`.

---

## 3. Start the FastAPI Back End

SSH through your login node to a compute node:

```bash
ssh -J <login-user>@<login-host> <compute-user>@<compute-node>
```

Then, on the compute node:

```bash
cd /path/to/LexEmetica-Clerk/backEnd
pip install -r requirements.txt
uvicorn server:app   --host 0.0.0.0   --port 8000   --reload
```

- FastAPI will serve on port `8000`.

---

## 4. Start the Vite Front End

In another shell (inside the same container, if needed), SSH in again, then:

```bash
cd /path/to/LexEmetica-Clerk/frontEnd
npm install      # if not already done
npm run dev --   --host 0.0.0.0   --port 5173
```

- Vite will serve the UI on port `5173`.

---

## 5. Set Up Local SSH Port Forwarding

On your **local machine**, forward the remote ports so you can access them in your browser:

```bash
ssh -N   -J <login-user>@<login-host>   -L 5173:localhost:5173   -L 8000:localhost:8000   -L 11434:localhost:11434   <compute-user>@<compute-node>
```

- `<login-user>@<login-host>`: your cluster’s login/bastion host.  
- `<compute-user>@<compute-node>`: the node running the services.  
- Ports forwarded:  
  - **5173** → Vite front end  
  - **8000** → FastAPI back end  
  - **11434** → Model server  

---

## 6. Verify Services

On your local machine, confirm each service is reachable:

```bash
curl http://localhost:11434/health      # Model server health (if supported)
curl http://localhost:8000/             # FastAPI root or health endpoint
```

All should respond without error.

---

## 7. Use the Web UI

Open your browser to:

```
http://localhost:5173
```

You can now generate JSON briefs or download PDFs by citation through the Vite UI, which proxies through your forwarded ports to the HPC services.

---

### Tips

- Replace paths (`/path/to/...`), usernames, and hostnames with your actual cluster details.  
- Ensure your container has all dependencies installed (`uvicorn`, `fastapi`, `ollama`/`mixtral`, etc.).  
- If you change ports, update the forwarding (`-L`) flags and the front end’s proxy configuration accordingly.  
- For persistent setups, consider using `screen` or `tmux` on the compute node to keep servers running after you disconnect.

// index.js 
import express from "express"; 
import { createProxyMiddleware } from "http-proxy-middleware"; 
 
const app = express(); 
 
// Proxy all /api requests to your Python server 
app.use( 
    "/api", 
    createProxyMiddleware({
    target: "http://localhost:8000",
    changeOrigin: true,
  })
);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Node proxy listening on http://0.0.0.0:${PORT}`));
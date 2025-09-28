// --- Amara Script Metadata ---
// Repo: amara-core
// Role: Express app entry point (helmet, CORS, routes, SSE test)
// Owner: core
// Secrets: none
// Notes: Guarded by pre-commit validate-script-headers

// Amara Core — Minimal Express ESM API
import express from "express";
import cors from "cors";
import helmet from "helmet";
import routes from "./routes/api.js";

const app = express();
app.use(helmet({ contentSecurityPolicy: false }));
app.use(express.json());

const CORS_ORIGINS = process.env.CORS_ORIGINS?.split(",")
  .map((s) => s.trim())
  .filter(Boolean) || ["*"];
app.use(cors({ origin: CORS_ORIGINS, credentials: false }));

// Simple token gate (upgrade to OIDC later)
app.use((req, res, next) => {
  const required = process.env.AGENT_TOKEN;
  if (!required) return next();
  const got = req.get("X-Agent-Token");
  if (got !== required) return res.status(401).send("unauthorized");
  next();
});

// Health
app.get("/api/healthz", (_req, res) => res.type("text/plain").send("ok"));

// Test SSE endpoint
app.get("/api/stream/test", (req, res) => {
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  let i = 0;
  const id = setInterval(() => {
    res.write(`data: {"tick": ${++i}}\n\n`);
    if (i >= 3) {
      clearInterval(id);
      res.end();
    }
  }, 1000);
  req.on("close", () => clearInterval(id));
});

// App routes
app.use("/api", routes);

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`[amara-core] API listening on ${port}`));

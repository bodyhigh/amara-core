// --- Amara Script Metadata ---
// Repo: amara-core
// Role: Express routes for Amara Core API
// Owner: core
// Secrets: none
// Notes: Guarded by pre-commit validate-script-headers

// Amara Core — Routes
import { Router } from "express";
const r = Router();

// Example placeholder route
r.get("/brief/view", (_req, res) => {
  res.json({ status: "ok", msg: "brief view placeholder" });
});

// LiteLLM passthrough will be handled by NGINX to /api/llm/*
export default r;

"use strict";

const http = require("http");
const mainGraph = require("../traditional_medical_agent/neo4j_main/knowledge_graph_query");
const caseGraph = require("../traditional_medical_agent/neo4j_case/neo4j_agent_api");

const PORT = Number.parseInt(process.env.KG_SERVICE_PORT || "3000", 10);
const MAX_CONCURRENCY = Math.max(1, Number.parseInt(process.env.KG_NODE_MAX_CONCURRENCY || "4", 10));
const MAX_BODY_BYTES = Math.max(1024, Number.parseInt(process.env.KG_NODE_MAX_BODY_BYTES || "65536", 10));
let activeRequests = 0;

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(payload));
}

function readJson(request) {
  return new Promise((resolve, reject) => {
    let bytes = 0;
    let tooLarge = false;
    const chunks = [];
    request.on("data", (chunk) => {
      if (tooLarge) return;
      bytes += chunk.length;
      if (bytes > MAX_BODY_BYTES) {
        tooLarge = true;
        reject(new Error("body_too_large"));
        request.resume();
        return;
      }
      chunks.push(chunk);
    });
    request.on("end", () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"));
      } catch {
        reject(new Error("invalid_json"));
      }
    });
    request.on("error", reject);
  });
}

async function withCapacity(response, work) {
  if (activeRequests >= MAX_CONCURRENCY) {
    sendJson(response, 503, { ok: false, error: "kg_busy" });
    return;
  }
  activeRequests += 1;
  try {
    await work();
  } finally {
    activeRequests -= 1;
  }
}

async function handleQuery(request, response, graph, isCaseGraph) {
  let body;
  try {
    body = await readJson(request);
  } catch (error) {
    sendJson(response, error.message === "body_too_large" ? 413 : 400, { ok: false, error: "invalid_request" });
    return;
  }

  const action = typeof body.action === "string" ? body.action : "";
  const params = body.params && typeof body.params === "object" && !Array.isArray(body.params) ? body.params : {};
  const allowWrite = process.env.KG_ALLOW_CASE_WRITE === "true";
  if (!action || (isCaseGraph && action === "addCase" && !allowWrite)) {
    sendJson(response, 400, { ok: false, error: "invalid_action" });
    return;
  }

  await withCapacity(response, async () => {
    try {
      const result = await graph.runAgentQuery(action, params);
      if (!result || result.ok !== true) {
        // 图谱模块会将底层异常转换为 { ok: false, error }；记录摘要供运维定位，
        // 不向调用方泄露数据库连接或查询细节。
        console.error("kg_query_rejected", {
          source: isCaseGraph ? "case" : "main",
          action,
          error: typeof result?.error === "string" ? result.error.slice(0, 300) : "unknown",
        });
        sendJson(response, 502, { ok: false, error: "query_failed" });
        return;
      }
      sendJson(response, 200, result);
    } catch (error) {
      console.error("kg_query_failed", { source: isCaseGraph ? "case" : "main", action, error: error.name });
      sendJson(response, 502, { ok: false, error: "query_failed" });
    }
  });
}

const server = http.createServer(async (request, response) => {
  if (request.method === "GET" && request.url === "/health") {
    try {
      const [mainHealth, caseHealth] = await Promise.all([mainGraph.healthCheck(), caseGraph.healthCheck()]);
      if (mainHealth.ok && caseHealth.ok) {
        sendJson(response, 200, { status: "healthy" });
      } else {
        sendJson(response, 503, { status: "unhealthy" });
      }
    } catch (error) {
      console.error("kg_health_failed", { error: error.name });
      sendJson(response, 503, { status: "unhealthy" });
    }
    return;
  }
  if (request.method === "POST" && request.url === "/main/query") {
    await handleQuery(request, response, mainGraph, false);
    return;
  }
  if (request.method === "POST" && request.url === "/case/query") {
    await handleQuery(request, response, caseGraph, true);
    return;
  }
  sendJson(response, 404, { ok: false, error: "not_found" });
});

async function shutdown(signal) {
  console.info("kg_service_shutdown", { signal });
  server.close(async () => {
    await Promise.allSettled([mainGraph.close(), caseGraph.close()]);
    process.exit(0);
  });
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
server.listen(PORT, "0.0.0.0", () => console.info("kg_service_listening", { port: PORT, maxConcurrency: MAX_CONCURRENCY }));

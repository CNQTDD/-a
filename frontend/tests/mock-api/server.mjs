import http from "node:http";

const sessions = new Map();
const port = Number(process.env.MOCK_API_PORT ?? 5184);

function sendJson(response, status, body) {
  response.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Last-Event-ID",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  });
  response.end(JSON.stringify(body));
}

function parseBody(request) {
  return new Promise((resolve, reject) => {
    let raw = "";
    request.on("data", (chunk) => {
      raw += chunk;
    });
    request.on("end", () => {
      if (!raw) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(raw));
      } catch (error) {
        reject(error);
      }
    });
    request.on("error", reject);
  });
}

function writeSseEvent(response, payload) {
  response.write(`id: ${payload.id}\n`);
  response.write(`event: ${payload.type}\n`);
  response.write(`data: ${JSON.stringify(payload)}\n\n`);
}

const server = http.createServer(async (request, response) => {
  if (request.method === "OPTIONS") {
    response.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "Content-Type, Last-Event-ID",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    });
    response.end();
    return;
  }

  const url = new URL(request.url ?? "/", `http://${request.headers.host}`);

  if (request.method === "POST" && url.pathname === "/api/v1/complaints/sessions") {
    const body = await parseBody(request);
    const sessionId = body.id ?? `session-${sessions.size + 1}`;
    sessions.set(sessionId, {
      id: sessionId,
      complaintText: body.complaintText ?? "",
      feedbackAction: null,
      feedbackReason: "",
    });
    sendJson(response, 200, { session_id: sessionId });
    return;
  }

  const messageMatch = url.pathname.match(/^\/api\/v1\/complaints\/([^/]+)\/messages$/);
  if (request.method === "POST" && messageMatch) {
    const sessionId = messageMatch[1];
    const body = await parseBody(request);
    const session = sessions.get(sessionId) ?? { id: sessionId };
    session.complaintText = body.complaint_text ?? "";
    sessions.set(sessionId, session);
    sendJson(response, 200, { run_id: `${sessionId}-run-1` });
    return;
  }

  const eventsMatch = url.pathname.match(/^\/api\/v1\/complaints\/([^/]+)\/events$/);
  if (request.method === "GET" && eventsMatch) {
    const sessionId = eventsMatch[1];
    response.writeHead(200, {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "Access-Control-Allow-Origin": "*",
    });

    const events = [
      {
        id: `${sessionId}-1`,
        sessionId,
        sequence: 1,
        type: "workflow_started",
        stage: "intent",
      },
      {
        id: `${sessionId}-2`,
        sessionId,
        sequence: 2,
        type: "intent_completed",
        intent: "billing",
        emotion: "angry",
        entities: ["package", "bill"],
      },
      {
        id: `${sessionId}-3`,
        sessionId,
        sequence: 3,
        type: "retrieval_completed",
        evidence: [
          {
            id: "evidence-1",
            sourceType: "business_rule",
            title: "Evidence Item 1",
            contentSnapshot: "套餐账单规则说明",
            score: 0.98,
            articleNumber: "1",
          },
        ],
      },
      {
        id: `${sessionId}-4`,
        sessionId,
        sequence: 4,
        type: "generation_delta",
        delta: "已核对账单并调整套餐费用。",
      },
      {
        id: `${sessionId}-5`,
        sessionId,
        sequence: 5,
        type: "validation_completed",
        validation: {
          status: "passed",
          details: "引用有效",
        },
      },
      {
        id: `${sessionId}-6`,
        sessionId,
        sequence: 6,
        type: "workflow_completed",
      },
    ];

    let index = 0;
    const interval = setInterval(() => {
      const next = events[index++];
      if (!next) {
        clearInterval(interval);
        response.end();
        return;
      }
      writeSseEvent(response, next);
    }, 100);

    request.on("close", () => {
      clearInterval(interval);
    });
    return;
  }

  const sessionMatch = url.pathname.match(/^\/api\/v1\/complaints\/([^/]+)$/);
  if (request.method === "GET" && sessionMatch) {
    const sessionId = sessionMatch[1];
    const session =
      sessions.get(sessionId) ?? {
        id: sessionId,
        complaintText: "",
        feedbackAction: null,
        feedbackReason: "",
      };
    sendJson(response, 200, {
      id: sessionId,
      complaintText: session.complaintText,
      status: session.feedbackAction ? "resolved" : "running",
      stage: session.feedbackAction ? "resolved" : "generation",
      intent: "billing",
      emotion: "angry",
      entities: ["package", "bill"],
      evidence: [
        {
          id: "evidence-1",
          sourceType: "business_rule",
          title: "Evidence Item 1",
          contentSnapshot: "套餐账单规则说明",
          score: 0.98,
          articleNumber: "1",
        },
      ],
      streamedSolution: "已核对账单并调整套餐费用。",
      finalSolution: "已核对账单并调整套餐费用。",
      validation: {
        status: "passed",
        details: "引用有效",
      },
      feedbackAction: session.feedbackAction,
      feedbackReason: session.feedbackReason,
      archived: session.feedbackAction === "accept",
    });
    return;
  }

  const feedbackMatch = url.pathname.match(/^\/api\/v1\/complaints\/([^/]+)\/feedback$/);
  if (request.method === "POST" && feedbackMatch) {
    const sessionId = feedbackMatch[1];
    const body = await parseBody(request);
    const session = sessions.get(sessionId) ?? { id: sessionId };
    session.feedbackAction = body.action ?? "accept";
    session.feedbackReason = body.reason ?? "";
    sessions.set(sessionId, session);
    sendJson(response, 200, { ok: true, session_id: sessionId });
    return;
  }

  sendJson(response, 404, { message: "not found" });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Mock API listening on http://127.0.0.1:${port}`);
});

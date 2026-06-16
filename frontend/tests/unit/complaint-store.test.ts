import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useComplaintStore } from "../../src/stores/complaint";

describe("complaint store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("creates a session and reduces workflow events", () => {
    const store = useComplaintStore();

    const session = store.createSession({
      id: "session-1",
      complaintText: "I was overcharged for my package",
    });

    expect(session.status).toBe("draft");
    expect(store.activeSessionId).toBe("session-1");

    store.applyEvent({
      id: "event-1",
      sessionId: "session-1",
      sequence: 1,
      type: "workflow_started",
      stage: "intent",
    });
    store.applyEvent({
      id: "event-2",
      sessionId: "session-1",
      sequence: 2,
      type: "generation_delta",
      delta: "Hello",
    });
    store.applyEvent({
      id: "event-3",
      sessionId: "session-1",
      sequence: 3,
      type: "validation_completed",
      validation: {
        status: "passed",
        details: "ok",
      },
    });

    const stored = store.sessions["session-1"];
    expect(stored.stage).toBe("validation");
    expect(stored.streamedSolution).toBe("Hello");
    expect(stored.validation?.status).toBe("passed");
  });

  it("ignores duplicate and out-of-order events", () => {
    const store = useComplaintStore();
    store.createSession({
      id: "session-2",
      complaintText: "The router is broken",
    });

    store.applyEvent({
      id: "event-1",
      sessionId: "session-2",
      sequence: 2,
      type: "generation_delta",
      delta: "first",
    });
    store.applyEvent({
      id: "event-1",
      sessionId: "session-2",
      sequence: 2,
      type: "generation_delta",
      delta: "duplicate",
    });
    store.applyEvent({
      id: "event-0",
      sessionId: "session-2",
      sequence: 1,
      type: "workflow_started",
      stage: "retrieval",
    });

    const stored = store.sessions["session-2"];
    expect(stored.streamedSolution).toBe("first");
    expect(stored.stage).toBe("generation");
    expect(store.appliedEventIds).toEqual(["event-1"]);
  });
});

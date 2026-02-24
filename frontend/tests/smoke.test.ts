/**
 * US-1.01: Smoke test for frontend test runner.
 */
import { describe, it, expect } from "vitest";

describe("Frontend smoke test", () => {
  it("runs successfully", () => {
    expect(1 + 1).toBe(2);
  });
});

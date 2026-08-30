// SPDX-License-Identifier: MIT
/**
 * evorule.client 快照包（bundle）API 单元测试（本地 stub server 版）
 *
 * 不依赖 evorule-server：node:http 起本地 stub，覆盖成功路径与 400
 * 显式错误路径（断言服务端 error 字段透传，不静默）。
 * 运行：npx tsx tests/test_bundles.ts
 */

import * as http from "node:http";
import { EvoruleClient, EvoruleError } from "../src/index.js";

// ======================================================================
// 极简断言器
// ======================================================================

let passed = 0;
let failed = 0;

function assert(cond: boolean, name: string, detail?: string): void {
  if (cond) {
    passed += 1;
    console.log(`  PASS ${name}`);
  } else {
    failed += 1;
    console.error(`  FAIL ${name}${detail ? ` — ${detail}` : ""}`);
  }
}

async function assertThrows(
  fn: () => Promise<unknown>,
  name: string,
  expectContains?: string,
): Promise<void> {
  try {
    await fn();
    assert(false, name, "未按预期抛出 EvoruleError");
  } catch (e) {
    const isTarget = e instanceof EvoruleError;
    const contains =
      expectContains === undefined || String((e as Error).message).includes(expectContains);
    assert(isTarget && contains, name, `message=${String((e as Error).message)}`);
  }
}

// ======================================================================
// 最小合法 bundle fixture（set 元指令，满足 6 元指令枚举）
// ======================================================================

function sampleBundle(): Record<string, unknown> {
  return {
    bundle_schema_version: "1.0",
    bundle_id: "bundle-demo-v1",
    dataset: { id: "ds-demo", name: "demo" },
    entries: [
      {
        entry_id: "rule-001-abc",
        rule_id: "rule.001",
        source_version: "v1",
        rule_body: {
          kind: "rule",
          id: "rule.001",
          transform: [{ type: "set", target: "x", value: 1 }],
        },
      },
    ],
  };
}

// ======================================================================
// stub server
// ======================================================================

interface RecordedRequest {
  path: string;
  body: { bundle?: Record<string, unknown> } | null;
}

function startStubServer(): Promise<{ server: http.Server; port: number; requests: RecordedRequest[] }> {
  const requests: RecordedRequest[] = [];
  const server = http.createServer((req, res) => {
    let raw = "";
    req.on("data", (chunk: Buffer) => {
      raw += chunk.toString();
    });
    req.on("end", () => {
      requests.push({ path: req.url ?? "", body: raw ? JSON.parse(raw) : null });
      const respond = (status: number, payload: unknown): void => {
        res.writeHead(status, { "Content-Type": "application/json" });
        res.end(JSON.stringify(payload));
      };

      if (req.url === "/api/bundles/import") {
        respond(201, {
          imported: true,
          bundle_id: "bundle-demo-v1",
          dataset_id: "ds-demo",
          activated_version: "v1",
          entry_count: 1,
          missing_services: [],
        });
      } else if (req.url === "/api/bundles/import/dry-run") {
        respond(200, {
          valid: true,
          bundle_id: "bundle-demo-v1",
          dataset_id: "ds-demo",
          source_version: "v1",
          selection_mode: "Pinned",
          resolved_version: "v1",
          entry_count: 1,
          verdict: "Accept",
          missing_services: [],
        });
      } else if (req.url === "/api/bundles/active") {
        respond(200, {
          bundles: [
            {
              bundle_id: "bundle-demo-v1",
              dataset_id: "ds-demo",
              source_version: "v1",
              selection_mode: "pinned",
              content_hash: "blake3:abc",
              entry_count: 1,
            },
          ],
          count: 1,
        });
      } else if (req.url?.startsWith("/api/bundles/imports")) {
        respond(200, { imports: [], count: 0 });
      } else if (req.url === "/api/bundles/reject") {
        respond(400, { error: "entry rule.001: unknown service svc.x", imported: false });
      } else if (req.url === "/api/bundles/reject/dry-run") {
        respond(400, { error: "content_hash mismatch", valid: false });
      } else {
        respond(404, { error: "not found" });
      }
    });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const addr = server.address() as { port: number };
      resolve({ server, port: addr.port, requests });
    });
  });
}

// ======================================================================
// 用例
// ======================================================================

async function main(): Promise<void> {
  const { server, port, requests } = await startStubServer();
  const client = new EvoruleClient(`http://127.0.0.1:${port}`);

  try {
    // --- importBundle ---
    console.log("importBundle:");
    const imp = await client.importBundle(sampleBundle());
    assert(imp.imported === true, "imported=true");
    assert(imp.bundle_id === "bundle-demo-v1", "bundle_id");
    assert(imp.entry_count === 1, "entry_count");
    const importReq = requests.find((r) => r.path === "/api/bundles/import");
    assert(
      JSON.stringify(importReq?.body) === JSON.stringify({ bundle: sampleBundle() }),
      "请求体为 {\"bundle\": <object>} 包裹形态",
    );

    // --- dryRunImport ---
    console.log("dryRunImport:");
    const dry = await client.dryRunImport(sampleBundle());
    assert(dry.valid === true, "valid=true");
    assert(dry.verdict === "Accept", "verdict");
    assert(dry.selection_mode === "Pinned", "selection_mode");

    // --- listActiveBundles ---
    console.log("listActiveBundles:");
    const active = await client.listActiveBundles();
    assert(active.count === 1, "count=1");
    assert(active.bundles[0].dataset_id === "ds-demo", "dataset_id");
    assert(active.bundles[0].content_hash === "blake3:abc", "content_hash");

    // --- listBundleImports ---
    console.log("listBundleImports:");
    const imports = await client.listBundleImports(50);
    assert(imports.count === 0, "count=0");
    assert(
      requests.some((r) => r.path === "/api/bundles/imports?limit=50"),
      "limit 查询参数透传",
    );

    // --- 400 错误透传（不静默）：独立 stub 端口固定返回 400 ---
    console.log("400 错误透传:");
    const rejectServer = http.createServer((req, res) => {
      let raw = "";
      req.on("data", (c: Buffer) => (raw += c.toString()));
      req.on("end", () => {
        const isDryRun = (req.url ?? "").endsWith("/dry-run");
        res.writeHead(400, { "Content-Type": "application/json" });
        res.end(
          JSON.stringify(
            isDryRun
              ? { error: "content_hash mismatch", valid: false }
              : { error: "entry rule.001: unknown service svc.x", imported: false },
          ),
        );
      });
    });
    await new Promise<void>((resolve) => rejectServer.listen(0, "127.0.0.1", resolve));
    const rejectPort = (rejectServer.address() as { port: number }).port;
    const rejectClient = new EvoruleClient(`http://127.0.0.1:${rejectPort}`);
    await assertThrows(
      () => rejectClient.importBundle(sampleBundle()),
      "import 400 → 服务端 error 透传",
      "unknown service svc.x",
    );
    await assertThrows(
      () => rejectClient.dryRunImport(sampleBundle()),
      "dry-run 400 → 服务端 error 透传",
      "content_hash mismatch",
    );
    rejectServer.close();

    console.log(`\n结果: ${passed} passed, ${failed} failed`);
    if (failed > 0) {
      process.exitCode = 1;
    }
  } finally {
    await client.close();
    server.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});

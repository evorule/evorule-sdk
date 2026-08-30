// SPDX-License-Identifier: AGPL-3.0-or-later
package com.evorule;

import com.evorule.exceptions.EvoruleException;
import com.evorule.models.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 快照包（DatasetBundle）API 单元测试
 *
 * 校验口径零复刻：六项校验链由服务端执行（evorule-bundle SSOT），
 * 本测试用 JDK 内置 HttpServer 模拟服务端，验证 URL/方法/请求体包裹
 * 与响应字段映射、400 error 透传（不静默）。
 */
public class BundleApiTest {
    private HttpServer server;
    private EvoruleClient client;
    private ObjectMapper mapper;

    private final AtomicReference<String> lastPath = new AtomicReference<>("");
    private final AtomicReference<String> lastMethod = new AtomicReference<>("");
    private final AtomicReference<String> lastBody = new AtomicReference<>("");

    @BeforeEach
    void setup() throws IOException {
        mapper = new ObjectMapper();
        server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/", this::dispatch);
        server.start();
        client = new EvoruleClient("http://localhost:" + server.getAddress().getPort());
    }

    @AfterEach
    void teardown() {
        server.stop(0);
    }

    /** 记录请求并按注册的响应回放 */
    private void dispatch(HttpExchange exchange) throws IOException {
        lastPath.set(exchange.getRequestURI().getPath()
                + (exchange.getRequestURI().getQuery() != null
                        ? "?" + exchange.getRequestURI().getQuery() : ""));
        lastMethod.set(exchange.getRequestMethod());
        lastBody.set(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
        byte[] body = currentResponse.get();
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(currentStatus.get(), body.length);
        exchange.getResponseBody().write(body);
        exchange.close();
    }

    private final AtomicReference<Integer> currentStatus = new AtomicReference<>(200);
    private final AtomicReference<byte[]> currentResponse = new AtomicReference<>(new byte[0]);

    private void respond(int status, String json) {
        currentStatus.set(status);
        currentResponse.set(json.getBytes(StandardCharsets.UTF_8));
    }

    @Test
    void importBundleSuccess() throws Exception {
        respond(201, """
                {"imported": true, "bundle_id": "b-123", "dataset_id": "ds-1",
                 "activated_version": "1.2.0", "entry_count": 7, "missing_services": []}""");

        ObjectNode bundle = mapper.createObjectNode();
        bundle.put("bundle_id", "b-123");
        ImportBundleResponse resp = client.importBundle(bundle);

        assertEquals("/api/bundles/import", lastPath.get());
        assertEquals("POST", lastMethod.get());
        // 请求体必须是 {"bundle": {...}} 包裹
        JsonNode body = mapper.readTree(lastBody.get());
        assertTrue(body.has("bundle"), "expected body wrapped as {bundle: {...}}");
        assertEquals("b-123", body.get("bundle").get("bundle_id").asText());

        assertTrue(resp.isImported());
        assertEquals("b-123", resp.getBundleId());
        assertEquals("ds-1", resp.getDatasetId());
        assertEquals("1.2.0", resp.getActivatedVersion());
        assertEquals(7, resp.getEntryCount());
        assertTrue(resp.getMissingServices().isEmpty());
    }

    @Test
    void importBundle400ErrorTransparent() {
        respond(400, """
                {"error": "bundle hash mismatch: expected abc, got def", "imported": false}""");

        EvoruleException ex = assertThrows(EvoruleException.class,
                () -> client.importBundle(mapper.createObjectNode()));
        // 服务端 error 字段必须透传，不静默
        assertTrue(ex.getMessage().contains("bundle hash mismatch: expected abc, got def"),
                "expected server error to be transparent, got: " + ex.getMessage());
    }

    @Test
    void dryRunImportSuccess() throws Exception {
        respond(200, """
                {"valid": true, "bundle_id": "b-123", "dataset_id": "ds-1",
                 "source_version": "1.2.0", "selection_mode": "pinned",
                 "resolved_version": "1.2.0", "entry_count": 7, "verdict": "pass",
                 "missing_services": ["http:weather"]}""");

        DryRunImportResponse resp = client.dryRunImport(mapper.createObjectNode());

        assertEquals("/api/bundles/import/dry-run", lastPath.get());
        assertEquals("POST", lastMethod.get());
        assertTrue(resp.isValid());
        assertEquals("b-123", resp.getBundleId());
        assertEquals("pinned", resp.getSelectionMode());
        assertEquals("1.2.0", resp.getResolvedVersion());
        assertEquals("pass", resp.getVerdict());
        assertEquals(1, resp.getMissingServices().size());
        assertEquals("http:weather", resp.getMissingServices().get(0));
    }

    @Test
    void dryRunImport400ErrorTransparent() {
        respond(400, """
                {"error": "entry 3: schema validation failed", "valid": false}""");

        EvoruleException ex = assertThrows(EvoruleException.class,
                () -> client.dryRunImport(mapper.createObjectNode()));
        assertTrue(ex.getMessage().contains("entry 3: schema validation failed"),
                "expected server error to be transparent, got: " + ex.getMessage());
    }

    @Test
    void listActiveBundlesSuccess() throws Exception {
        respond(200, """
                {"bundles": [{"bundle_id": "b-123", "dataset_id": "ds-1",
                    "source_version": "1.2.0", "selection_mode": "pinned",
                    "resolved_version": "1.2.0", "content_hash": "deadbeef",
                    "entry_count": 7}], "count": 1}""");

        ActiveBundlesResponse resp = client.listActiveBundles();

        assertEquals("/api/bundles/active", lastPath.get());
        assertEquals(1, resp.getCount());
        assertEquals(1, resp.getBundles().size());
        ActiveBundleInfo b = resp.getBundles().get(0);
        assertEquals("b-123", b.getBundleId());
        assertEquals("ds-1", b.getDatasetId());
        assertEquals("deadbeef", b.getContentHash());
        assertEquals(7, b.getEntryCount());
    }

    @Test
    void listBundleImportsWithLimit() throws Exception {
        respond(200, """
                {"imports": [{"id": 1, "bundle_id": "b-123", "dataset_id": "ds-1",
                    "source_version": "1.2.0", "selection_mode": "auto_by_effective_date",
                    "resolved_version": "1.2.0", "content_hash": "deadbeef",
                    "entry_count": 7, "imported_at": "2026-08-30T10:00:00Z",
                    "imported_by": "admin"}], "count": 1}""");

        BundleImportsResponse resp = client.listBundleImports(50);

        assertEquals("/api/bundles/imports?limit=50", lastPath.get());
        assertEquals(1, resp.getCount());
        assertEquals(1, resp.getImports().size());
        BundleImportRecord rec = resp.getImports().get(0);
        assertEquals(1, rec.getId());
        assertEquals("b-123", rec.getBundleId());
        assertEquals(7, rec.getEntryCount());
        assertEquals("admin", rec.getImportedBy());
        assertEquals("auto_by_effective_date", rec.getSelectionMode());
    }

    @Test
    void listBundleImportsWithoutLimitUsesServerDefault() throws Exception {
        respond(200, "{\"imports\": [], \"count\": 0}");

        BundleImportsResponse resp = client.listBundleImports(null);

        assertEquals("/api/bundles/imports", lastPath.get(), "expected no limit param");
        assertEquals(0, resp.getCount());
        assertTrue(resp.getImports().isEmpty());
    }
}

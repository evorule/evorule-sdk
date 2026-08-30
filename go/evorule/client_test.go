// SPDX-License-Identifier: Apache-2.0
package evorule

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

// newTestClient 创建连接到 httptest server 的 Client
func newTestClient(t *testing.T, srv *httptest.Server, token string) *Client {
	t.Helper()
	c := NewClientWithAuth(srv.URL, token)
	return c
}

// === 认证头注入测试 ===

func TestAuthHeader(t *testing.T) {
	var gotAuth string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAuth = r.Header.Get("Authorization")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 1, "message": "ok"}`))
	}))
	defer srv.Close()

	t.Run("with token", func(t *testing.T) {
		c := newTestClient(t, srv, "secret-token")
		_, err := c.CreateSession()
		if err != nil {
			t.Fatalf("CreateSession failed: %v", err)
		}
		if gotAuth != "Bearer secret-token" {
			t.Errorf("expected 'Bearer secret-token', got %q", gotAuth)
		}
	})

	t.Run("without token", func(t *testing.T) {
		c := NewClient(srv.URL)
		_, err := c.CreateSession()
		if err != nil {
			t.Fatalf("CreateSession failed: %v", err)
		}
		if gotAuth != "" {
			t.Errorf("expected empty Authorization, got %q", gotAuth)
		}
	})
}

// === CreateSession 测试 ===

func TestCreateSession(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Errorf("expected POST, got %s", r.Method)
		}
		if r.URL.Path != "/api/sessions" {
			t.Errorf("expected /api/sessions, got %s", r.URL.Path)
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 42, "message": "Session created"}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	id, err := c.CreateSession()
	if err != nil {
		t.Fatalf("CreateSession failed: %v", err)
	}
	if id != 42 {
		t.Errorf("expected session_id=42, got %d", id)
	}
}

// === ListSessions 测试 ===

func TestListSessions(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"sessions": [1, 2, 3]}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	ids, err := c.ListSessions()
	if err != nil {
		t.Fatalf("ListSessions failed: %v", err)
	}
	if len(ids) != 3 || ids[0] != 1 || ids[1] != 2 || ids[2] != 3 {
		t.Errorf("expected [1,2,3], got %v", ids)
	}
}

// === SubmitCommand 测试 ===

func TestSubmitCommand(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/sessions/7/command" {
			t.Errorf("expected /api/sessions/7/command, got %s", r.URL.Path)
		}
		body, _ := io.ReadAll(r.Body)
		var payload map[string]interface{}
		if err := json.Unmarshal(body, &payload); err != nil {
			t.Fatalf("failed to parse body: %v", err)
		}
		if payload["instruction"] == nil {
			t.Error("expected instruction field in body")
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	err := c.SubmitCommand(7, map[string]interface{}{"type": "test"})
	if err != nil {
		t.Fatalf("SubmitCommand failed: %v", err)
	}
}

// === GetState 测试（验证 StateResponse 新字段） ===

func TestGetState(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/sessions/1/state" {
			t.Errorf("expected /api/sessions/1/state, got %s", r.URL.Path)
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"payload": {"x": 1},
			"queue": [{"type": "cmd"}],
			"version": 5,
			"reactor": {"phase": "Idle"}
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	state, err := c.GetState(1)
	if err != nil {
		t.Fatalf("GetState failed: %v", err)
	}
	if state.Version != 5 {
		t.Errorf("expected version=5, got %d", state.Version)
	}
	if len(state.Queue) != 1 {
		t.Errorf("expected queue len=1, got %d", len(state.Queue))
	}
	if state.Payload == nil {
		t.Error("expected non-nil payload")
	}
}

// === Rewind 测试（验证 URL 和字段名） ===

func TestRewind(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/sessions/3/rewind" {
			t.Errorf("expected /api/sessions/3/rewind, got %s", r.URL.Path)
		}
		if r.URL.Query().Get("version") != "2" {
			t.Errorf("expected version=2, got %s", r.URL.Query().Get("version"))
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"session_id": 3,
			"target_version": 2,
			"actual_version": 2,
			"payload": {"x": 0},
			"queue": []
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	resp, err := c.Rewind(3, 2)
	if err != nil {
		t.Fatalf("Rewind failed: %v", err)
	}
	if resp.ActualVersion != 2 {
		t.Errorf("expected actual_version=2, got %d", resp.ActualVersion)
	}
	if resp.TargetVersion != 2 {
		t.Errorf("expected target_version=2, got %d", resp.TargetVersion)
	}
}

// === Diff 测试（验证 URL 和字段名） ===

func TestDiff(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/sessions/1/diff" {
			t.Errorf("expected /api/sessions/1/diff, got %s", r.URL.Path)
		}
		if r.URL.Query().Get("a") != "1" || r.URL.Query().Get("b") != "3" {
			t.Errorf("expected a=1&b=3, got %s", r.URL.RawQuery)
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"session_id": 1,
			"from_version": 1,
			"to_version": 3,
			"added": [{"key": "y", "value": 2}],
			"removed": [],
			"changed": [],
			"unchanged": [{"key": "x", "value": 1}],
			"summary": {"total_changes": 1}
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	resp, err := c.Diff(1, 1, 3)
	if err != nil {
		t.Fatalf("Diff failed: %v", err)
	}
	if resp.FromVersion != 1 {
		t.Errorf("expected from_version=1, got %d", resp.FromVersion)
	}
	if resp.ToVersion != 3 {
		t.Errorf("expected to_version=3, got %d", resp.ToVersion)
	}
	if len(resp.Added) != 1 {
		t.Errorf("expected added len=1, got %d", len(resp.Added))
	}
	if len(resp.Unchanged) != 1 {
		t.Errorf("expected unchanged len=1, got %d", len(resp.Unchanged))
	}
}

// === GetSharedFacts 测试（验证 URL 编码） ===

func TestGetSharedFacts(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/shared/facts" {
			t.Errorf("expected /api/shared/facts, got %s", r.URL.Path)
		}
		prefix := r.URL.Query().Get("prefix")
		if prefix != "a/b c" {
			t.Errorf("expected prefix='a/b c' (URL-decoded), got %q", prefix)
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`[]`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	_, err := c.GetSharedFacts("a/b c")
	if err != nil {
		t.Fatalf("GetSharedFacts failed: %v", err)
	}
}

// === ForkSession 测试（验证 version 可选） ===

func TestForkSession(t *testing.T) {
	var lastPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		lastPath = r.URL.Path + "?" + r.URL.RawQuery
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 10, "parent_session_id": 1, "forked_from_version": 3, "message": "ok"}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")

	t.Run("with version", func(t *testing.T) {
		_, err := c.ForkSession(1, 3)
		if err != nil {
			t.Fatalf("ForkSession failed: %v", err)
		}
		if !strings.Contains(lastPath, "/api/sessions/fork/1?version=3") {
			t.Errorf("expected fork path with version, got %s", lastPath)
		}
	})

	t.Run("without version (from variant)", func(t *testing.T) {
		_, err := c.ForkSession(1, 0)
		if err != nil {
			t.Fatalf("ForkSession failed: %v", err)
		}
		if !strings.Contains(lastPath, "/api/sessions/from/1") {
			t.Errorf("expected from path, got %s", lastPath)
		}
	})
}

// === GetReplay 测试（验证返回数组） ===

func TestGetReplay(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/sessions/1/replay" {
			t.Errorf("expected /api/sessions/1/replay, got %s", r.URL.Path)
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`[
			{"id": 1, "type": "Command", "version": 1},
			{"id": 2, "type": "StateTransition", "version": 2}
		]`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	replay, err := c.GetReplay(1)
	if err != nil {
		t.Fatalf("GetReplay failed: %v", err)
	}
	if len(replay) != 2 {
		t.Fatalf("expected 2 facts, got %d", len(replay))
	}
	if replay[0].ID != 1 || replay[0].Type != "Command" {
		t.Errorf("fact[0] mismatch: id=%d type=%s", replay[0].ID, replay[0].Type)
	}
}

// === SSE Events 测试 ===

func TestEvents(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/sessions/1/events" {
			t.Errorf("expected /api/sessions/1/events, got %s", r.URL.Path)
		}
		if r.Header.Get("Accept") != "text/event-stream" {
			t.Errorf("expected Accept: text/event-stream, got %s", r.Header.Get("Accept"))
		}
		w.Header().Set("Content-Type", "text/event-stream")
		w.WriteHeader(http.StatusOK)
		// 发送 3 个事件然后关闭
		fmt.Fprintf(w, "data: {\"type\":\"Command\",\"id\":1}\n\n")
		w.(http.Flusher).Flush()
		fmt.Fprintf(w, "event: transition\ndata: {\"type\":\"StateTransition\",\"id\":2}\n\n")
		w.(http.Flusher).Flush()
		fmt.Fprintf(w, "data: {\"type\":\"Stable\",\"id\":3}\n\n")
		w.(http.Flusher).Flush()
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	ch, err := c.Events(ctx, 1)
	if err != nil {
		t.Fatalf("Events failed: %v", err)
	}

	var events []SseEvent
	for ev := range ch {
		events = append(events, ev)
		if len(events) == 3 {
			cancel()
			break
		}
	}

	if len(events) != 3 {
		t.Fatalf("expected 3 events, got %d", len(events))
	}

	// 验证第二个事件有 event 类型
	if events[1].Event != "transition" {
		t.Errorf("expected event[1].Event='transition', got %q", events[1].Event)
	}

	// 验证事件数据
	var data map[string]interface{}
	if err := json.Unmarshal(events[0].Data, &data); err != nil {
		t.Fatalf("failed to parse event[0] data: %v", err)
	}
	if data["type"] != "Command" {
		t.Errorf("expected type=Command, got %v", data["type"])
	}
}

// === 错误处理测试 ===

func TestErrorHandling(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusNotFound)
		_, _ = w.Write([]byte(`{"error": "session not found"}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	_, err := c.GetState(999)
	if err == nil {
		t.Fatal("expected error for 404, got nil")
	}
	if !strings.Contains(err.Error(), "404") {
		t.Errorf("expected error to contain '404', got %v", err)
	}
}

// === CloseSession 测试 ===

func TestCloseSession(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodDelete {
			t.Errorf("expected DELETE, got %s", r.Method)
		}
		if r.URL.Path != "/api/sessions/5" {
			t.Errorf("expected /api/sessions/5, got %s", r.URL.Path)
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	if err := c.CloseSession(5); err != nil {
		t.Fatalf("CloseSession failed: %v", err)
	}
}

// === S4 端点测试 ===

func TestFinished(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 1, "finished": true}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	finished, err := c.Finished(1)
	if err != nil {
		t.Fatalf("Finished failed: %v", err)
	}
	if !finished {
		t.Error("expected finished=true")
	}
}

func TestCausalDepth(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 1, "causal_depth": 42}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	depth, err := c.CausalDepth(1)
	if err != nil {
		t.Fatalf("CausalDepth failed: %v", err)
	}
	if depth != 42 {
		t.Errorf("expected causal_depth=42, got %d", depth)
	}
}

func TestInvariants(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 1, "structural_invariant_violations": 0}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	violations, err := c.Invariants(1)
	if err != nil {
		t.Fatalf("Invariants failed: %v", err)
	}
	if violations != 0 {
		t.Errorf("expected violations=0, got %d", violations)
	}
}

func TestPendingIoCount(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 1, "pending_io_count": 3}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	count, err := c.PendingIoCount(1)
	if err != nil {
		t.Fatalf("PendingIoCount failed: %v", err)
	}
	if count != 3 {
		t.Errorf("expected pending_io_count=3, got %d", count)
	}
}

func TestStep(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"session_id": 1, "current_step": 7}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	step, err := c.Step(1)
	if err != nil {
		t.Fatalf("Step failed: %v", err)
	}
	if step != 7 {
		t.Errorf("expected current_step=7, got %d", step)
	}
}

func TestSnapshot(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"session_id": 1,
			"finished": false,
			"phase": "Idle",
			"version": 5,
			"steps": 10,
			"pending_io_count": 2,
			"structural_invariant_violations": 0
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	snap, err := c.Snapshot(1)
	if err != nil {
		t.Fatalf("Snapshot failed: %v", err)
	}
	if snap.Finished {
		t.Error("expected finished=false")
	}
	if snap.Phase != "Idle" {
		t.Errorf("expected phase=Idle, got %s", snap.Phase)
	}
	if snap.Version != 5 {
		t.Errorf("expected version=5, got %d", snap.Version)
	}
	if snap.Steps != 10 {
		t.Errorf("expected steps=10, got %d", snap.Steps)
	}
}

// === 快照包（DatasetBundle）API 测试 ===

func TestImportBundle(t *testing.T) {
	var gotPath string
	var gotMethod string
	var gotBody map[string]interface{}
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotMethod = r.Method
		body, _ := io.ReadAll(r.Body)
		if err := json.Unmarshal(body, &gotBody); err != nil {
			t.Errorf("failed to parse body: %v", err)
		}
		w.WriteHeader(http.StatusCreated)
		_, _ = w.Write([]byte(`{
			"imported": true,
			"bundle_id": "b-123",
			"dataset_id": "ds-1",
			"activated_version": "1.2.0",
			"entry_count": 7,
			"missing_services": []
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	bundle := map[string]interface{}{"bundle_id": "b-123"}
	resp, err := c.ImportBundle(bundle)
	if err != nil {
		t.Fatalf("ImportBundle failed: %v", err)
	}
	if gotPath != "/api/bundles/import" {
		t.Errorf("expected /api/bundles/import, got %s", gotPath)
	}
	if gotMethod != http.MethodPost {
		t.Errorf("expected POST, got %s", gotMethod)
	}
	// 请求体必须是 {"bundle": {...}} 包裹
	inner, ok := gotBody["bundle"].(map[string]interface{})
	if !ok {
		t.Fatalf("expected body wrapped as {bundle: {...}}, got %v", gotBody)
	}
	if inner["bundle_id"] != "b-123" {
		t.Errorf("expected inner bundle_id=b-123, got %v", inner["bundle_id"])
	}
	if !resp.Imported {
		t.Error("expected imported=true")
	}
	if resp.BundleID != "b-123" || resp.DatasetID != "ds-1" || resp.ActivatedVersion != "1.2.0" {
		t.Errorf("response fields mismatch: %+v", resp)
	}
	if resp.EntryCount != 7 {
		t.Errorf("expected entry_count=7, got %d", resp.EntryCount)
	}
	if len(resp.MissingServices) != 0 {
		t.Errorf("expected empty missing_services, got %v", resp.MissingServices)
	}
}

func TestImportBundle400ErrorTransparent(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"error": "bundle hash mismatch: expected abc, got def", "imported": false}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	_, err := c.ImportBundle(map[string]interface{}{})
	if err == nil {
		t.Fatal("expected error for 400, got nil")
	}
	// 服务端 error 字段必须透传，不静默
	if !strings.Contains(err.Error(), "bundle hash mismatch: expected abc, got def") {
		t.Errorf("expected server error to be transparent, got %v", err)
	}
}

func TestDryRunImport(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"valid": true,
			"bundle_id": "b-123",
			"dataset_id": "ds-1",
			"source_version": "1.2.0",
			"selection_mode": "pinned",
			"resolved_version": "1.2.0",
			"entry_count": 7,
			"verdict": "pass",
			"missing_services": ["http:weather"]
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	resp, err := c.DryRunImport(map[string]interface{}{"bundle_id": "b-123"})
	if err != nil {
		t.Fatalf("DryRunImport failed: %v", err)
	}
	if gotPath != "/api/bundles/import/dry-run" {
		t.Errorf("expected /api/bundles/import/dry-run, got %s", gotPath)
	}
	if !resp.Valid {
		t.Error("expected valid=true")
	}
	if resp.SelectionMode != "pinned" {
		t.Errorf("expected selection_mode=pinned, got %s", resp.SelectionMode)
	}
	if resp.ResolvedVersion == nil || *resp.ResolvedVersion != "1.2.0" {
		t.Errorf("expected resolved_version=1.2.0, got %v", resp.ResolvedVersion)
	}
	if resp.Verdict != "pass" {
		t.Errorf("expected verdict=pass, got %s", resp.Verdict)
	}
	if len(resp.MissingServices) != 1 || resp.MissingServices[0] != "http:weather" {
		t.Errorf("expected missing_services=[http:weather], got %v", resp.MissingServices)
	}
}

func TestDryRunImport400ErrorTransparent(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"error": "entry 3: schema validation failed", "valid": false}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	_, err := c.DryRunImport(map[string]interface{}{})
	if err == nil {
		t.Fatal("expected error for 400, got nil")
	}
	if !strings.Contains(err.Error(), "entry 3: schema validation failed") {
		t.Errorf("expected server error to be transparent, got %v", err)
	}
}

func TestListActiveBundles(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"bundles": [{
				"bundle_id": "b-123",
				"dataset_id": "ds-1",
				"source_version": "1.2.0",
				"selection_mode": "pinned",
				"resolved_version": "1.2.0",
				"content_hash": "deadbeef",
				"entry_count": 7
			}],
			"count": 1
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")
	resp, err := c.ListActiveBundles()
	if err != nil {
		t.Fatalf("ListActiveBundles failed: %v", err)
	}
	if gotPath != "/api/bundles/active" {
		t.Errorf("expected /api/bundles/active, got %s", gotPath)
	}
	if resp.Count != 1 || len(resp.Bundles) != 1 {
		t.Fatalf("expected 1 bundle, got count=%d len=%d", resp.Count, len(resp.Bundles))
	}
	b := resp.Bundles[0]
	if b.BundleID != "b-123" || b.DatasetID != "ds-1" || b.ContentHash != "deadbeef" {
		t.Errorf("bundle fields mismatch: %+v", b)
	}
}

func TestListBundleImports(t *testing.T) {
	var gotPath string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		if q := r.URL.RawQuery; q != "" {
			gotPath += "?" + q
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{
			"imports": [{
				"id": 1,
				"bundle_id": "b-123",
				"dataset_id": "ds-1",
				"source_version": "1.2.0",
				"selection_mode": "auto_by_effective_date",
				"resolved_version": "1.2.0",
				"content_hash": "deadbeef",
				"entry_count": 7,
				"imported_at": "2026-08-30T10:00:00Z",
				"imported_by": "admin"
			}],
			"count": 1
		}`))
	}))
	defer srv.Close()

	c := newTestClient(t, srv, "")

	t.Run("with limit", func(t *testing.T) {
		resp, err := c.ListBundleImports(50)
		if err != nil {
			t.Fatalf("ListBundleImports failed: %v", err)
		}
		if gotPath != "/api/bundles/imports?limit=50" {
			t.Errorf("expected /api/bundles/imports?limit=50, got %s", gotPath)
		}
		if resp.Count != 1 || len(resp.Imports) != 1 {
			t.Fatalf("expected 1 import, got count=%d len=%d", resp.Count, len(resp.Imports))
		}
		rec := resp.Imports[0]
		if rec.ID != 1 || rec.BundleID != "b-123" || rec.EntryCount != 7 {
			t.Errorf("import record fields mismatch: %+v", rec)
		}
		if rec.ImportedBy != "admin" {
			t.Errorf("expected imported_by=admin, got %s", rec.ImportedBy)
		}
	})

	t.Run("without limit (server default)", func(t *testing.T) {
		if _, err := c.ListBundleImports(0); err != nil {
			t.Fatalf("ListBundleImports(0) failed: %v", err)
		}
		if gotPath != "/api/bundles/imports" {
			t.Errorf("expected no limit param, got %s", gotPath)
		}
	})
}

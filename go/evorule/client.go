// SPDX-License-Identifier: AGPL-3.0-or-later
package evorule

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type Client struct {
	baseURL    string
	authToken  string
	httpClient *http.Client
}

type Fact struct {
	ID         uint64          `json:"id"`
	Type       string          `json:"type"`
	Cause      uint64          `json:"cause,omitempty"`
	Instruction *json.RawMessage `json:"instruction,omitempty"`
	NewPayload *json.RawMessage `json:"new_payload,omitempty"`
	NewQueue   []json.RawMessage `json:"new_queue,omitempty"`
	IoType     string          `json:"io_type,omitempty"`
	Params     *json.RawMessage `json:"params,omitempty"`
	RequestID  uint64          `json:"request_id,omitempty"`
	Result     *json.RawMessage `json:"result,omitempty"`
	Error      *string         `json:"error,omitempty"`
	FinalSnapshot *json.RawMessage `json:"final_snapshot,omitempty"`
	Message    string          `json:"message,omitempty"`
}

type SharedFact struct {
	FactID          uint64          `json:"fact_id"`
	Path            string          `json:"path"`
	Value           *json.RawMessage `json:"value"`
	SourceSessionID uint64          `json:"source_session_id"`
	Version         uint64          `json:"version"`
}

// StateResponse 对应 GET /api/sessions/{id}/state 的响应
//
// server 返回 {payload, queue, version, reactor: {phase, causal_depth, ...}}
type StateResponse struct {
	Payload *json.RawMessage   `json:"payload"`
	Queue   []json.RawMessage  `json:"queue"`
	Version uint64             `json:"version"`
	Reactor *json.RawMessage   `json:"reactor,omitempty"`
}

// ReplayResponse 对应 GET /api/sessions/{id}/replay 的响应
//
// server 直接返回 Fact 数组（非对象包裹），每项为 fact + version 字段
type ReplayResponse = []Fact

// RewindResponse 对应 GET /api/sessions/{id}/rewind?version=X 的响应
//
// server 返回 {session_id, target_version, payload, queue, actual_version}
// actual_version 是实际回滚到的版本（可能因版本间隙与 target_version 不同）
type RewindResponse struct {
	SessionID     uint64            `json:"session_id"`
	TargetVersion uint64            `json:"target_version"`
	ActualVersion uint64            `json:"actual_version"`
	Payload       *json.RawMessage  `json:"payload"`
	Queue         []json.RawMessage `json:"queue"`
}

type DiffEntry struct {
	Key   string          `json:"key"`
	Value *json.RawMessage `json:"value"`
}

type DiffChangedEntry struct {
	Key      string          `json:"key"`
	OldValue *json.RawMessage `json:"old_value"`
	NewValue *json.RawMessage `json:"new_value"`
}

// DiffResponse 对应 GET /api/sessions/{id}/diff?a=X&b=Y 的响应
//
// server 返回 {session_id, from_version, to_version, added, removed, changed, unchanged, summary}
type DiffResponse struct {
	SessionID   uint64             `json:"session_id"`
	FromVersion uint64             `json:"from_version"`
	ToVersion   uint64             `json:"to_version"`
	Added       []DiffEntry        `json:"added"`
	Removed     []DiffEntry        `json:"removed"`
	Changed     []DiffChangedEntry `json:"changed"`
	Unchanged   []DiffEntry        `json:"unchanged"`
	Summary     *json.RawMessage   `json:"summary,omitempty"`
}

// P3 新增类型

type ApiResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	FactID  *uint64 `json:"fact_id"`
}

type ForkSessionResponse struct {
	SessionID         uint64 `json:"session_id"`
	ParentSessionID   uint64 `json:"parent_session_id"`
	ForkedFromVersion uint64 `json:"forked_from_version"`
	Message           string `json:"message"`
}

type HistoryEntry struct {
	Version uint64 `json:"version"`
	Type    string `json:"type"`
}

type SessionFactEntry struct {
	FactID  uint64          `json:"fact_id"`
	Version uint64          `json:"version"`
	Path    string          `json:"path"`
	Value   *json.RawMessage `json:"value"`
}

// NewClient 创建不带认证的 Client（仅适用于 loopback 开发环境）
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// NewClientWithAuth 创建带 Bearer token 认证的 Client
//
// evorule-server 在非 loopback 地址上必须配置认证 token（B3 fail-closed），
// 此时必须使用此构造函数。token 为空字符串时等价于 NewClient（不发送 Authorization 头）。
func NewClientWithAuth(baseURL, token string) *Client {
	c := NewClient(baseURL)
	c.authToken = token
	return c
}

// do 发送 HTTP 请求，自动注入 Authorization 头
func (c *Client) do(req *http.Request) (*http.Response, error) {
	if c.authToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.authToken)
	}
	return c.httpClient.Do(req)
}

// doGet 发送 GET 请求（带认证）
func (c *Client) doGet(urlStr string) (*http.Response, error) {
	req, err := http.NewRequest(http.MethodGet, urlStr, nil)
	if err != nil {
		return nil, err
	}
	return c.do(req)
}

// doPost 发送 POST 请求（带认证 + Content-Type: application/json）
func (c *Client) doPost(urlStr string, body []byte) (*http.Response, error) {
	var bodyReader io.Reader
	if body != nil {
		bodyReader = bytes.NewBuffer(body)
	}
	req, err := http.NewRequest(http.MethodPost, urlStr, bodyReader)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	return c.do(req)
}

// doDelete 发送 DELETE 请求（带认证）
func (c *Client) doDelete(urlStr string) (*http.Response, error) {
	req, err := http.NewRequest(http.MethodDelete, urlStr, nil)
	if err != nil {
		return nil, err
	}
	return c.do(req)
}

// CreateSession 创建新会话（POST /api/sessions）
//
// server 返回 {"session_id": int, "message": "Session created"}
func (c *Client) CreateSession() (uint64, error) {
	resp, err := c.doPost(c.baseURL+"/api/sessions", nil)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("failed to create session: %s", resp.Status)
	}
	var result struct {
		SessionID uint64 `json:"session_id"`
		Message   string `json:"message"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}
	return result.SessionID, nil
}

func (c *Client) ListSessions() ([]uint64, error) {
	resp, err := c.doGet(c.baseURL + "/api/sessions")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list sessions: %s", resp.Status)
	}
	var result struct {
		Sessions []uint64 `json:"sessions"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Sessions, nil
}

func (c *Client) CloseSession(id uint64) error {
	resp, err := c.doDelete(fmt.Sprintf("%s/api/sessions/%d", c.baseURL, id))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to close session: %s", resp.Status)
	}
	return nil
}

func (c *Client) SubmitCommand(id uint64, instruction interface{}) error {
	wrapped := map[string]interface{}{"instruction": instruction}
	data, err := json.Marshal(wrapped)
	if err != nil {
		return err
	}
	resp, err := c.doPost(
		fmt.Sprintf("%s/api/sessions/%d/command", c.baseURL, id),
		data,
	)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to submit command: %s", resp.Status)
	}
	return nil
}

func (c *Client) GetState(id uint64) (*StateResponse, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/state", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get state: %s", resp.Status)
	}
	var state StateResponse
	if err := json.NewDecoder(resp.Body).Decode(&state); err != nil {
		return nil, err
	}
	return &state, nil
}

func (c *Client) GetReplay(id uint64) (ReplayResponse, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/replay", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get replay: %s", resp.Status)
	}
	var replay ReplayResponse
	if err := json.NewDecoder(resp.Body).Decode(&replay); err != nil {
		return nil, err
	}
	return replay, nil
}

func (c *Client) Rewind(id, version uint64) (*RewindResponse, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/rewind?version=%d", c.baseURL, id, version))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to rewind: %s", resp.Status)
	}
	var rewind RewindResponse
	if err := json.NewDecoder(resp.Body).Decode(&rewind); err != nil {
		return nil, err
	}
	return &rewind, nil
}

func (c *Client) Diff(id, from, to uint64) (*DiffResponse, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/diff?a=%d&b=%d", c.baseURL, id, from, to))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to diff: %s", resp.Status)
	}
	var diff DiffResponse
	if err := json.NewDecoder(resp.Body).Decode(&diff); err != nil {
		return nil, err
	}
	return &diff, nil
}

func (c *Client) GetSharedFacts(prefix string) ([]SharedFact, error) {
	u := c.baseURL + "/api/shared/facts"
	if prefix != "" {
		u += "?prefix=" + url.QueryEscape(prefix)
	}
	resp, err := c.doGet(u)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get shared facts: %s", resp.Status)
	}
	var facts []SharedFact
	if err := json.NewDecoder(resp.Body).Decode(&facts); err != nil {
		return nil, err
	}
	return facts, nil
}

func (c *Client) RecordUsedAtStartup(id uint64, factIDs []uint64) error {
	data, err := json.Marshal(map[string][]uint64{"fact_ids": factIDs})
	if err != nil {
		return err
	}
	resp, err := c.doPost(
		fmt.Sprintf("%s/api/sessions/%d/used_at_startup", c.baseURL, id),
		data,
	)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to record used_at_startup: %s", resp.Status)
	}
	return nil
}

func (c *Client) Interrupt(id uint64) error {
	resp, err := c.doPost(
		fmt.Sprintf("%s/api/sessions/%d/interrupt", c.baseURL, id),
		nil,
	)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to interrupt session: %s", resp.Status)
	}
	return nil
}

func (c *Client) SubmitIoResponse(id, requestID uint64, result interface{}, errMsg *string) error {
	data, err := json.Marshal(map[string]interface{}{
		"request_id": requestID,
		"result":     result,
		"error":      errMsg,
	})
	if err != nil {
		return err
	}
	resp, err := c.doPost(
		fmt.Sprintf("%s/api/sessions/%d/io_response", c.baseURL, id),
		data,
	)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to submit io response: %s", resp.Status)
	}
	return nil
}

func (c *Client) DebugPhase(id uint64) (string, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/debug/phase", c.baseURL, id))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("failed to get phase: %s", resp.Status)
	}
	var result struct {
		Phase string `json:"phase"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	return result.Phase, nil
}

func (c *Client) DebugQueue(id uint64) ([]json.RawMessage, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/debug/queue", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get queue: %s", resp.Status)
	}
	var result struct {
		Queue []json.RawMessage `json:"queue"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Queue, nil
}

func (c *Client) DebugPendingIo(id uint64) ([]struct {
	FactID    uint64 `json:"fact_id"`
	IoType    string `json:"io_type"`
	DurationMs int64 `json:"duration_ms"`
}, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/debug/pending_io", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get pending io: %s", resp.Status)
	}
	var result struct {
		PendingIo []struct {
			FactID    uint64 `json:"fact_id"`
			IoType    string `json:"io_type"`
			DurationMs int64 `json:"duration_ms"`
		} `json:"pending_io"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.PendingIo, nil
}

// ===== P3 端点补齐 =====

// Liveness 探针：GET /api/health/liveness
func (c *Client) Liveness() (*ApiResponse, error) {
	resp, err := c.doGet(c.baseURL + "/api/health/liveness")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("liveness probe failed: %s", resp.Status)
	}
	var apiResp ApiResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, err
	}
	return &apiResp, nil
}

// Readiness 探针：GET /api/health/readiness
// 未就绪时返回 503 错误
func (c *Client) Readiness() (*ApiResponse, error) {
	resp, err := c.doGet(c.baseURL + "/api/health/readiness")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("readiness probe failed: %s", resp.Status)
	}
	var apiResp ApiResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, err
	}
	return &apiResp, nil
}

// ForkSession 从父会话分叉新会话
//
// - version > 0: POST /api/sessions/fork/{parent_id}?version=X（指定版本分叉）
// - version == 0: POST /api/sessions/from/{parent_id}（从最新版本分叉）
func (c *Client) ForkSession(parentID, version uint64) (*ForkSessionResponse, error) {
	var urlStr string
	if version > 0 {
		urlStr = fmt.Sprintf("%s/api/sessions/fork/%d?version=%d", c.baseURL, parentID, version)
	} else {
		urlStr = fmt.Sprintf("%s/api/sessions/from/%d", c.baseURL, parentID)
	}
	resp, err := c.doPost(urlStr, nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to fork session: %s", resp.Status)
	}
	var forkResp ForkSessionResponse
	if err := json.NewDecoder(resp.Body).Decode(&forkResp); err != nil {
		return nil, err
	}
	return &forkResp, nil
}

// SharedFactSource 查询共享 Fact 的来源信息
// GET /api/shared/facts/{fact_id}/source
func (c *Client) SharedFactSource(factID uint64) (*SharedFact, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/shared/facts/%d/source", c.baseURL, factID))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get shared fact source: %s", resp.Status)
	}
	var fact SharedFact
	if err := json.NewDecoder(resp.Body).Decode(&fact); err != nil {
		return nil, err
	}
	return &fact, nil
}

// SharedFactUsedBy 查询使用了指定共享 Fact 的会话列表
// GET /api/shared/facts/{fact_id}/used_by
func (c *Client) SharedFactUsedBy(factID uint64) ([]uint64, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/shared/facts/%d/used_by", c.baseURL, factID))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get shared fact used_by: %s", resp.Status)
	}
	var result struct {
		FactID   uint64   `json:"fact_id"`
		Sessions []uint64 `json:"sessions"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Sessions, nil
}

// SessionAudit 查询会话审计报告
// GET /api/sessions/{id}/audit
func (c *Client) SessionAudit(id uint64) (json.RawMessage, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/audit", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get audit: %s", resp.Status)
	}
	var raw json.RawMessage
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return nil, err
	}
	return raw, nil
}

// SessionAuditVerify 校验会话审计链完整性
// GET /api/sessions/{id}/audit/verify
func (c *Client) SessionAuditVerify(id uint64) (bool, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/audit/verify", c.baseURL, id))
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return false, fmt.Errorf("failed to verify audit: %s", resp.Status)
	}
	var result struct {
		Valid     bool   `json:"valid"`
		SessionID uint64 `json:"session_id"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false, err
	}
	return result.Valid, nil
}

// SessionHistory 查询会话历史
// GET /api/sessions/{id}/history
func (c *Client) SessionHistory(id uint64) ([]HistoryEntry, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/history", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get history: %s", resp.Status)
	}
	var entries []HistoryEntry
	if err := json.NewDecoder(resp.Body).Decode(&entries); err != nil {
		return nil, err
	}
	return entries, nil
}

// SessionFactsByPrefix 按路径前缀查询会话内 Facts
// GET /api/sessions/{id}/facts?prefix=xxx
func (c *Client) SessionFactsByPrefix(id uint64, prefix string) ([]SessionFactEntry, error) {
	u := fmt.Sprintf("%s/api/sessions/%d/facts", c.baseURL, id)
	if prefix != "" {
		u += "?prefix=" + url.QueryEscape(prefix)
	}
	resp, err := c.doGet(u)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get session facts: %s", resp.Status)
	}
	var entries []SessionFactEntry
	if err := json.NewDecoder(resp.Body).Decode(&entries); err != nil {
		return nil, err
	}
	return entries, nil
}

// GetUsedAtStartup 查询会话启动时引用的共享 Fact ID 列表
// GET /api/sessions/{id}/used_at_startup
func (c *Client) GetUsedAtStartup(id uint64) ([]uint64, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/used_at_startup", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get used_at_startup: %s", resp.Status)
	}
	var result struct {
		SessionID uint64   `json:"session_id"`
		FactIDs   []uint64 `json:"fact_ids"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.FactIDs, nil
}

// SessionJoin 加入集群协作
// POST /api/sessions/{id}/join
// direction: "atob" / "btoa" / "" (双向)
//
// ⚠️ DEPRECATED: evorule-server 已移除 cluster 端点（多 reactor 协作原语属应用层功能）。
// 调用此方法将返回 404。保留代码供未来 cluster 模块重新启用时使用。
func (c *Client) SessionJoin(id, targetID uint64, direction string) (*ApiResponse, error) {
	body := map[string]interface{}{"target_id": targetID}
	if direction != "" {
		body["direction"] = direction
	}
	data, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	resp, err := c.doPost(
		fmt.Sprintf("%s/api/sessions/%d/join", c.baseURL, id),
		data,
	)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to join session: %s", resp.Status)
	}
	var apiResp ApiResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, err
	}
	return &apiResp, nil
}

// SessionLeave 离开所有集群协作
// POST /api/sessions/{id}/leave
//
// ⚠️ DEPRECATED: evorule-server 已移除 cluster 端点。调用此方法将返回 404。
func (c *Client) SessionLeave(id uint64) (*ApiResponse, error) {
	resp, err := c.doPost(
		fmt.Sprintf("%s/api/sessions/%d/leave", c.baseURL, id),
		nil,
	)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to leave session: %s", resp.Status)
	}
	var apiResp ApiResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return nil, err
	}
	return &apiResp, nil
}

// SessionClusterStatus 查询会话集群成员
// GET /api/sessions/{id}/cluster
//
// ⚠️ DEPRECATED: evorule-server 已移除 cluster 端点。调用此方法将返回 404。
func (c *Client) SessionClusterStatus(id uint64) ([]uint64, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/cluster", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get cluster status: %s", resp.Status)
	}
	var result struct {
		SessionID      uint64   `json:"session_id"`
		ClusterMembers []uint64 `json:"cluster_members"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.ClusterMembers, nil
}

// ===== SSE 事件流 =====

// SseEvent 表示一个 SSE 事件
//
// server 推送的事件格式为 data: {JSON}\n\n
// Event 字段对应 SSE 的 event: 行（如有），Data 为 data: 行的原始 JSON
type SseEvent struct {
	Event string
	Data  json.RawMessage
}

// Events 订阅会话的 SSE 事件流（GET /api/sessions/{id}/events）
//
// 返回一个只读 channel，持续产出 SseEvent。流在以下情况关闭：
//   - ctx 被取消（调用方主动退出）
//   - server 关闭连接（会话结束）
//   - 读取发生错误
//
// 调用方应通过 for ev := range ch 迭代事件，并在适当时机取消 ctx。
//
// 使用示例：
//
//	ctx, cancel := context.WithCancel(context.Background())
//	defer cancel()
//	ch, err := client.Events(ctx, sessionID)
//	if err != nil { ... }
//	for ev := range ch {
//	    fmt.Println(string(ev.Data))
//	    if bytes.Contains(ev.Data, []byte(`"Stable"`)) {
//	        cancel()
//	    }
//	}
func (c *Client) Events(ctx context.Context, id uint64) (<-chan SseEvent, error) {
	req, err := http.NewRequestWithContext(
		ctx,
		http.MethodGet,
		fmt.Sprintf("%s/api/sessions/%d/events", c.baseURL, id),
		nil,
	)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "text/event-stream")
	if c.authToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.authToken)
	}

	// SSE 是长连接，不能受 httpClient.Timeout（30s）限制。
	// 复用原 Transport（连接池配置），但不设 Timeout，由 ctx 控制取消。
	sseClient := &http.Client{
		Transport: c.httpClient.Transport,
	}
	resp, err := sseClient.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		resp.Body.Close()
		return nil, fmt.Errorf("failed to open SSE stream: %s", resp.Status)
	}

	ch := make(chan SseEvent)
	go func() {
		defer resp.Body.Close()
		defer close(ch)

		scanner := bufio.NewScanner(resp.Body)
		// SSE 事件可能较大，增大 buffer
		scanner.Buffer(make([]byte, 0, 64*1024), 1024*1024)

		var eventType string
		for scanner.Scan() {
			line := scanner.Text()
			if line == "" {
				// 空行表示事件边界，重置 event 类型
				eventType = ""
				continue
			}
			if strings.HasPrefix(line, "event:") {
				eventType = strings.TrimSpace(line[len("event:"):])
			} else if strings.HasPrefix(line, "data: ") {
				data := line[len("data: "):]
				select {
				case ch <- SseEvent{Event: eventType, Data: json.RawMessage(data)}:
				case <-ctx.Done():
					return
				}
			} else if strings.HasPrefix(line, "data:") {
				data := strings.TrimSpace(line[len("data:"):])
				select {
				case ch <- SseEvent{Event: eventType, Data: json.RawMessage(data)}:
				case <-ctx.Done():
					return
				}
			}
		}
	}()
	return ch, nil
}

// ===== S4 端点补齐：会话运行时状态查询 =====

// SnapshotResponse 对应 GET /api/sessions/{id}/snapshot 的响应
type SnapshotResponse struct {
	SessionID                    uint64 `json:"session_id"`
	Finished                     bool   `json:"finished"`
	Phase                        string `json:"phase"`
	Version                      uint64 `json:"version"`
	Steps                        uint64 `json:"steps"`
	PendingIoCount               uint64 `json:"pending_io_count"`
	StructuralInvariantViolations uint64 `json:"structural_invariant_violations"`
}

// Finished 查询会话是否已完成（GET /api/sessions/{id}/finished）
func (c *Client) Finished(id uint64) (bool, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/finished", c.baseURL, id))
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return false, fmt.Errorf("failed to check finished: %s", resp.Status)
	}
	var result struct {
		Finished bool `json:"finished"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return false, err
	}
	return result.Finished, nil
}

// CausalDepth 查询因果链深度（GET /api/sessions/{id}/causal_depth）
func (c *Client) CausalDepth(id uint64) (uint64, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/causal_depth", c.baseURL, id))
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("failed to get causal_depth: %s", resp.Status)
	}
	var result struct {
		CausalDepth uint64 `json:"causal_depth"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}
	return result.CausalDepth, nil
}

// Invariants 查询结构不变式违规计数（GET /api/sessions/{id}/invariants）
func (c *Client) Invariants(id uint64) (uint64, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/invariants", c.baseURL, id))
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("failed to get invariants: %s", resp.Status)
	}
	var result struct {
		Violations uint64 `json:"structural_invariant_violations"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}
	return result.Violations, nil
}

// PendingIoCount 查询待处理 I/O 数量（GET /api/sessions/{id}/pending_io_count）
func (c *Client) PendingIoCount(id uint64) (uint64, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/pending_io_count", c.baseURL, id))
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("failed to get pending_io_count: %s", resp.Status)
	}
	var result struct {
		Count uint64 `json:"pending_io_count"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}
	return result.Count, nil
}

// Step 查询当前执行步数（GET /api/sessions/{id}/step）
func (c *Client) Step(id uint64) (uint64, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/step", c.baseURL, id))
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("failed to get step: %s", resp.Status)
	}
	var result struct {
		CurrentStep uint64 `json:"current_step"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return 0, err
	}
	return result.CurrentStep, nil
}

// Snapshot 查询完整状态快照（GET /api/sessions/{id}/snapshot）
func (c *Client) Snapshot(id uint64) (*SnapshotResponse, error) {
	resp, err := c.doGet(fmt.Sprintf("%s/api/sessions/%d/snapshot", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get snapshot: %s", resp.Status)
	}
	var snap SnapshotResponse
	if err := json.NewDecoder(resp.Body).Decode(&snap); err != nil {
		return nil, err
	}
	return &snap, nil
}
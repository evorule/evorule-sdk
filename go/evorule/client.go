package evorule

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type Client struct {
	baseURL    string
	httpClient *http.Client
}

type Session struct {
	ID         uint64 `json:"session_id"`
	Phase      string `json:"phase"`
	Version    uint64 `json:"version"`
	MaxRounds  uint64 `json:"max_rounds"`
	CreatedAt  string `json:"created_at"`
	ExpiresAt  string `json:"expires_at"`
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

type StateResponse struct {
	Payload *json.RawMessage `json:"payload"`
}

type ReplayResponse struct {
	Facts []Fact `json:"facts"`
}

type RewindResponse struct {
	Version uint64          `json:"version"`
	Payload *json.RawMessage `json:"payload"`
	Queue   []json.RawMessage `json:"queue"`
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

type DiffResponse struct {
	VersionA uint64             `json:"version_a"`
	VersionB uint64             `json:"version_b"`
	Added    []DiffEntry        `json:"added"`
	Removed  []DiffEntry        `json:"removed"`
	Changed  []DiffChangedEntry `json:"changed"`
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

func NewClient(baseURL string) *Client {
	return &Client {
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *Client) CreateSession() (*Session, error) {
	resp, err := c.httpClient.Post(c.baseURL+"/api/sessions", "application/json", nil)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to create session: %s", resp.Status)
	}
	var session Session
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return nil, err
	}
	return &session, nil
}

func (c *Client) GetSession(id uint64) (*Session, error) {
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d", c.baseURL, id))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to get session: %s", resp.Status)
	}
	var session Session
	if err := json.NewDecoder(resp.Body).Decode(&session); err != nil {
		return nil, err
	}
	return &session, nil
}

func (c *Client) ListSessions() ([]Session, error) {
	resp, err := c.httpClient.Get(c.baseURL + "/api/sessions")
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("failed to list sessions: %s", resp.Status)
	}
	var result struct {
		Sessions []Session `json:"sessions"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	return result.Sessions, nil
}

func (c *Client) CloseSession(id uint64) error {
	req, err := http.NewRequest(http.MethodDelete, fmt.Sprintf("%s/api/sessions/%d", c.baseURL, id), nil)
	if err != nil {
		return err
	}
	resp, err := c.httpClient.Do(req)
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
	resp, err := c.httpClient.Post(
		fmt.Sprintf("%s/api/sessions/%d/command", c.baseURL, id),
		"application/json",
		bytes.NewBuffer(data),
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/state", c.baseURL, id))
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

func (c *Client) GetReplay(id uint64) (*ReplayResponse, error) {
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/replay", c.baseURL, id))
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
	return &replay, nil
}

func (c *Client) Rewind(id, version uint64) (*RewindResponse, error) {
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/rewind/%d", c.baseURL, id, version))
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/diff?a=%d&b=%d", c.baseURL, id, from, to))
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
	url := c.baseURL + "/api/shared/facts"
	if prefix != "" {
		url += "?prefix=" + prefix
	}
	resp, err := c.httpClient.Get(url)
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
	resp, err := c.httpClient.Post(
		fmt.Sprintf("%s/api/sessions/%d/used_at_startup", c.baseURL, id),
		"application/json",
		bytes.NewBuffer(data),
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
	req, err := http.NewRequest(http.MethodPost, fmt.Sprintf("%s/api/sessions/%d/interrupt", c.baseURL, id), nil)
	if err != nil {
		return err
	}
	resp, err := c.httpClient.Do(req)
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
	resp, err := c.httpClient.Post(
		fmt.Sprintf("%s/api/sessions/%d/io_response", c.baseURL, id),
		"application/json",
		bytes.NewBuffer(data),
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/debug/phase", c.baseURL, id))
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/debug/queue", c.baseURL, id))
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/debug/pending_io", c.baseURL, id))
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
	resp, err := c.httpClient.Get(c.baseURL + "/api/health/liveness")
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
	resp, err := c.httpClient.Get(c.baseURL + "/api/health/readiness")
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

// ForkSession 从父会话的指定版本分叉新会话
// POST /api/sessions/fork/{parent_id}?version=X
func (c *Client) ForkSession(parentID, version uint64) (*ForkSessionResponse, error) {
	resp, err := c.httpClient.Post(
		fmt.Sprintf("%s/api/sessions/fork/%d?version=%d", c.baseURL, parentID, version),
		"application/json",
		nil,
	)
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/shared/facts/%d/source", c.baseURL, factID))
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/shared/facts/%d/used_by", c.baseURL, factID))
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/audit", c.baseURL, id))
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/audit/verify", c.baseURL, id))
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/history", c.baseURL, id))
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
	url := fmt.Sprintf("%s/api/sessions/%d/facts", c.baseURL, id)
	if prefix != "" {
		url += "?prefix=" + prefix
	}
	resp, err := c.httpClient.Get(url)
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
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/used_at_startup", c.baseURL, id))
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
func (c *Client) SessionJoin(id, targetID uint64, direction string) (*ApiResponse, error) {
	body := map[string]interface{}{"target_id": targetID}
	if direction != "" {
		body["direction"] = direction
	}
	data, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}
	resp, err := c.httpClient.Post(
		fmt.Sprintf("%s/api/sessions/%d/join", c.baseURL, id),
		"application/json",
		bytes.NewBuffer(data),
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
func (c *Client) SessionLeave(id uint64) (*ApiResponse, error) {
	resp, err := c.httpClient.Post(
		fmt.Sprintf("%s/api/sessions/%d/leave", c.baseURL, id),
		"application/json",
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
func (c *Client) SessionClusterStatus(id uint64) ([]uint64, error) {
	resp, err := c.httpClient.Get(fmt.Sprintf("%s/api/sessions/%d/cluster", c.baseURL, id))
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
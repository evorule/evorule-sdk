// SPDX-License-Identifier: AGPL-3.0-or-later
/**
 * evorule SDK 类型定义
 */

/** 通用 JSON 值类型 */
export type Json =
  | null
  | boolean
  | number
  | string
  | Json[]
  | { [key: string]: Json };

/** 指令 JSON（业务规则指令） */
export interface Instruction {
  type: string;
  params?: Record<string, Json>;
  [key: string]: Json | undefined;
}

/** API 响应 */
export interface ApiResponse {
  success: boolean;
  message: string;
  fact_id: number | null;
}

/** 会话状态快照（GET /api/sessions/{id}/state）
 *
 * server 返回 {payload, queue, version, reactor: {phase, causal_depth, ...}}
 */
export interface SessionState {
  payload: Record<string, Json>;
  queue: Json[];
  version: number;
  reactor?: ReactorInfo;
}

/** 反应器运行时信息（SessionState.reactor 子对象） */
export interface ReactorInfo {
  phase: string | null;
  causal_depth: number | null;
  structural_invariant_violations: number;
  pending_io_count: number | null;
  current_step: number | null;
  [key: string]: Json | undefined;
}

/** 创建会话响应 */
export interface CreateSessionResponse {
  session_id: number;
  message: string;
}

/** 列出会话响应 */
export interface ListSessionsResponse {
  sessions: number[];
}

/** Replay 响应（GET /api/sessions/{id}/replay）
 *
 * server 直接返回 Fact 数组（非对象包裹），每项为 fact + version 字段
 */
export type ReplayResponse = EventData[];

/** Rewind 响应（GET /api/sessions/{id}/rewind?version=X）
 *
 * server 返回 {session_id, target_version, payload, queue, actual_version}
 * actual_version 是实际回滚到的版本（可能因版本间隙与 target_version 不同）
 */
export interface RewindResponse {
  session_id: number;
  target_version: number;
  actual_version: number;
  payload: Record<string, Json>;
  queue: Json[];
}

/** Diff 响应中 added/removed 项 */
export interface DiffEntry {
  key: string;
  value: Json;
}

/** Diff 响应中 changed 项 */
export interface DiffChangedEntry {
  key: string;
  old_value: Json;
  new_value: Json;
}

/** Diff 响应（GET /api/sessions/{id}/diff?a=X&b=Y）
 *
 * server 返回 {session_id, from_version, to_version, added, removed, changed, unchanged, summary}
 */
export interface DiffResponse {
  session_id: number;
  from_version: number;
  to_version: number;
  added: DiffEntry[];
  removed: DiffEntry[];
  changed: DiffChangedEntry[];
  unchanged: DiffEntry[];
  summary?: Json;
}

/** 共享 Fact */
export interface SharedFact {
  fact_id: number;
  path: string;
  value: Json;
  source_session_id: number;
  version: number;
}

/** 挂起的 I/O 请求信息 */
export interface PendingIoInfo {
  fact_id: number;
  io_type: string;
  duration_ms: number;
}

/** debug/phase 响应 */
export interface DebugPhaseResponse {
  phase: string;
}

/** debug/queue 响应 */
export interface DebugQueueResponse {
  queue: Json[];
}

/** debug/pending_io 响应 */
export interface DebugPendingIoResponse {
  pending_io: PendingIoInfo[];
}

/** Fork 会话响应 */
export interface ForkSessionResponse {
  session_id: number;
  parent_session_id: number;
  forked_from_version: number;
  message: string;
}

/** audit/verify 响应 */
export interface AuditVerifyResponse {
  verified: boolean;
  session_id: number;
}

/** history 单项 */
export interface HistoryEntry {
  version: number;
  type: string;
}

/** 会话内 Fact 单项（按前缀查询） */
export interface SessionFactEntry {
  fact_id: number;
  version: number;
  path: string;
  value: Json;
}

/** GET used_at_startup 响应 */
export interface UsedAtStartupResponse {
  session_id: number;
  fact_ids: number[];
}

// ===== S4 端点补齐：会话运行时状态查询 =====

/** GET /api/sessions/{id}/finished 响应 */
export interface FinishedResponse {
  session_id: number;
  finished: boolean;
}

/** GET /api/sessions/{id}/causal_depth 响应 */
export interface CausalDepthResponse {
  session_id: number;
  causal_depth: number;
}

/** GET /api/sessions/{id}/invariants 响应 */
export interface InvariantsResponse {
  session_id: number;
  structural_invariant_violations: number;
}

/** GET /api/sessions/{id}/pending_io_count 响应 */
export interface PendingIoCountResponse {
  session_id: number;
  pending_io_count: number;
}

/** GET /api/sessions/{id}/step 响应 */
export interface StepResponse {
  session_id: number;
  current_step: number;
}

/** GET /api/sessions/{id}/snapshot 响应 */
export interface SnapshotResponse {
  session_id: number;
  finished: boolean;
  phase: string;
  version: number;
  steps: number;
  pending_io_count: number;
  structural_invariant_violations: number;
}

/** shared_fact_source 响应 */
export interface SharedFactSourceResponse {
  fact_id: number;
  path: string;
  value: Json;
  source_session_id: number;
  version: number;
}

/** shared_fact_used_by 响应 */
export interface SharedFactUsedByResponse {
  fact_id: number;
  sessions: number[];
}

/** cluster_status 响应 */
export interface ClusterStatusResponse {
  session_id: number;
  cluster_members: number[];
}

/** 集群同步方向 */
export type SyncDirection = "atob" | "btoa" | "bidirectional";

/** 事件类型枚举 */
export type EventType =
  | "Command"
  | "StateTransition"
  | "IoRequest"
  | "IoResponse"
  | "Stable"
  | "PayloadUpdate"
  | "Error";

/** SSE 事件原始 JSON */
export interface EventData {
  type: EventType;
  id: number;
  cause?: number;
  instruction?: Json;
  new_payload?: Record<string, Json>;
  new_queue?: Json[];
  final_snapshot?: Record<string, Json>;
  io_type?: string;
  params?: Record<string, Json>;
  request_id?: number;
  result?: Json;
  error?: string;
  path?: string;
  value?: Json;
  message?: string;
  [key: string]: Json | undefined;
}

/** 客户端配置 */
export interface ClientOptions {
  /** Bearer 认证 token */
  token?: string;
  /** 请求超时（毫秒），默认 30000 */
  timeout?: number;
}

// ===== 快照包（DatasetBundle）API =====
// 校验口径零复刻：六项校验链由服务端执行（evorule-bundle SSOT），
// SDK 侧类型仅描述 HTTP 响应形状，不做本地校验。

/** 导入快照包请求体（`{"bundle": DatasetBundle}` 包裹形态） */
export interface ImportBundleRequest {
  bundle: Record<string, unknown>;
}

/** POST /api/bundles/import 成功响应（导入即激活） */
export interface ImportBundleResponse {
  imported: boolean;
  bundle_id: string;
  dataset_id: string;
  activated_version: string;
  entry_count: number;
  missing_services: string[];
}

/** POST /api/bundles/import/dry-run 成功响应（只校验，不落盘不重载） */
export interface DryRunImportResponse {
  valid: boolean;
  bundle_id: string;
  dataset_id: string;
  source_version: string;
  /** `auto_by_effective_date` | `pinned` */
  selection_mode: string;
  resolved_version?: string | null;
  entry_count: number;
  verdict: string;
  missing_services: string[];
}

/** 当前激活快照（来自 bundle_manifest.json 的精简视图） */
export interface ActiveBundleInfo {
  bundle_id: string;
  dataset_id: string;
  source_version: string;
  selection_mode: string;
  resolved_version?: string;
  effective_from?: string;
  content_hash: string;
  entry_count: number;
}

/** GET /api/bundles/active 响应 */
export interface ActiveBundlesResponse {
  bundles: ActiveBundleInfo[];
  count: number;
}

/** 单条导入溯源记录（管理元数据，墙钟旁路，不参与审计验证链） */
export interface BundleImportRecord {
  id: number;
  bundle_id: string;
  dataset_id: string;
  source_version: string;
  selection_mode: string;
  resolved_version?: string | null;
  content_hash: string;
  entry_count: number;
  imported_at: string;
  imported_by: string;
}

/** GET /api/bundles/imports 响应 */
export interface BundleImportsResponse {
  imports: BundleImportRecord[];
  count: number;
}

// ===== 异常类 =====

/** evorule SDK 基础异常 */
export class EvoruleError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EvoruleError";
  }
}

/** 认证失败（HTTP 401） */
export class AuthenticationError extends EvoruleError {
  constructor(message: string) {
    super(message);
    this.name = "AuthenticationError";
  }
}

/** 会话不存在（HTTP 404） */
export class SessionNotFoundError extends EvoruleError {
  constructor(message: string) {
    super(message);
    this.name = "SessionNotFoundError";
  }
}

/** 会话已在客户端关闭 */
export class SessionClosedError extends EvoruleError {
  constructor(message: string) {
    super(message);
    this.name = "SessionClosedError";
  }
}

/** 命令提交失败 */
export class CommandError extends EvoruleError {
  constructor(message: string) {
    super(message);
    this.name = "CommandError";
  }
}

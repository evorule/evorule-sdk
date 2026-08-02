#!/usr/bin/env python3
# =============================================================================
# check_doc_safety.py — EvoRule SDK 文档安全与引用完整性检查器
#
# 覆盖规则：
#   R-门控1 : git staged 文件不得包含「wendang/」路径（禁止仓内私有文档 commit）
#   R3-引用合规零容忍：L1 公开文档禁止出现私有集合路径/文件名字面量
#   R-交叉引用完整性：L1 文档中指向同层 L1 的链接必须真实存在
#   R-索引存在性：DOCS_INDEX.md 列出的 L1 路径必须存在（单向存在性检查）
#   R-L1不提L2/L3：L1 公开文档禁止链接到 wendang/ 子目录
#   R-兄弟仓零谈论：L1 公开文档禁止谈论兄弟仓内部（依赖声明除外）
#   R-agent身份零泄露：L1 公开文档禁止泄露 AI agent 身份表述（产品概念除外）
#
# 用法：
#   python scripts/check_doc_safety.py                 # 默认 = --strict（全项 + 有违规 exit 1）
#   python scripts/check_doc_safety.py --warn          # 仅输出违规，exit 总是 0
#   python scripts/check_doc_safety.py --skip-git      # 跳过 R-门控1（本地非 git 环境）
#   python scripts/check_doc_safety.py --json          # JSON 输出（CI 消费）
#
# 退出码（--strict 模式）：
#   0 = 全部通过, 1 = 违规, 2 = 环境错误（不是 git repo / 文件不可读等）
# =============================================================================

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 规则模式
# ---------------------------------------------------------------------------

# R-门控1：wendang/ 路径（staged 文件不能带此前缀）
DOCS_PATH_PATTERN = re.compile(r'(^|[\\/])wendang($|[\\/])')

# R3：私有集合泄露
PRIVATE_LEAK_PATTERNS = [
    re.compile(r'_PRIVATE_zh_docs'),
    re.compile(r'0[1-9]\d_[\u4e00-\u9fa5A-Za-z]'),
]

# ---------------------------------------------------------------------------
# R-兄弟仓零谈论：L1 公开文档禁止谈论兄弟仓内部结构/状态/路径/运行方式/发布情况
# 基调：各仓独立发布,只管自己仓真实情况。最多说明依赖哪个仓哪个版本,其他不多说一句。
# ---------------------------------------------------------------------------
SIBLING_REPO_PATTERNS = [
    re.compile(r'evorule-application'),
    re.compile(r'evo-agent'),
    re.compile(r'主仓'),
    re.compile(r'核心仓'),
]
# 依赖声明白名单
DEPENDENCY_DECLARATION_HINTS = re.compile(
    r'(依赖|depends|depend|requires|需要|基于|powered by|'
    r'SDK|客户端|client|独立仓|独立发布|'
    r'提供|exposes|暴露|封装|wrapper|'
    r'配套|运行期依赖|HTTP API|通信|通信|'
    r'见.*仓|请使用.*仓|详见|归属)'
)
# 明确的"谈论内部"特征
SIBLING_INTERNAL_DISCUSSION_HINTS = re.compile(
    r'(仓内|独立仓的|仓的|目录|路径|src/|main\.rs|'
    r'默认监听|监听\s*\d+|运行方式|cargo run|'
    r'已迁|迁至|迁移到|拆分|拆出|外迁|'
    r'CI|workflow|发布情况|已发布|未发布|'
    r'bin|二进制|crate\b|内部结构|内部决策|'
    r'双许可|核心三 crate|reactor 协作原语)'
)

# ---------------------------------------------------------------------------
# R-agent身份零泄露：L1 公开文档禁止泄露 AI agent 身份表述
# ---------------------------------------------------------------------------
AGENT_IDENTITY_PATTERNS = [
    re.compile(r'给\s*AI\s*agent\s*的\s*规则'),
    re.compile(r'给\s*agent\s*的\s*规则'),
    re.compile(r'给\s*AI\s*agent'),
    re.compile(r'给\s*LLM'),
    re.compile(r'LLM\s*/\s*agent\s*程序化'),
    re.compile(r'LLM/agent'),
    re.compile(r'程序化消费'),
    re.compile(r'供\s*LLM\s*消费'),
    re.compile(r'供\s*agent\s*消费'),
    re.compile(r'AI\s*agent\s*开发'),
    re.compile(r'agent\s*程序化'),
    re.compile(r'LLM\s*读'),
    re.compile(r'LLM\s*程序化'),
    re.compile(r'agent\s*读'),
    re.compile(r'想跑\s*LLM\s*Agent'),
    re.compile(r'LLM\s*客户端'),
    re.compile(r'LLM\s*Agent\s*编排'),
]
# agent 产品概念白名单
AGENT_PRODUCT_HINTS = re.compile(
    r'(agent\s*编排|agent\s*应用|agent\s*框架|agent\s*能力|'
    r'构建\s*agent|agent\s*demo|agent\s*示例|'
    r'research\s*agent|reactive\s*agent|'
    r'agent\s*层|agent\s*系统|多\s*agent)'
)

# R3 例外：规则声明文件
RULE_DECLARATION_FILES = {
    'DOCS_INDEX.md',
}
RULE_DECLARATION_LINE_HINTS = re.compile(
    r'(零容忍|禁止出现|不得引用|本地私有|私有集合|绝对不 commit|绝对不在|引用合规|文档索引强制)'
)

# R-L1不提L2/L3
L2L3_REF_PATTERN = re.compile(r'wendang[\\/](shenji|design|implement|benchmarks|archive)')
L2L3_EXEMPT_HINTS = re.compile(
    r'(永不发布|\.gitignore 保护|不发布|仓内私有)'
)

# L1 层目录定义：
# 根目录 *.md + docs/** + 各语言子目录根级 *.md（README.md, CHANGELOG.md）
L1_ROOTS = [
    REPO_ROOT,                 # 根目录 md
    REPO_ROOT / 'docs',        # docs/**
    REPO_ROOT / 'python',      # python/README.md, python/CHANGELOG.md
    REPO_ROOT / 'typescript',  # typescript/README.md, typescript/CHANGELOG.md
    REPO_ROOT / 'go',          # go/README.md
    REPO_ROOT / 'java',        # java/README.md, java/CHANGELOG.md
]
L1_EXCLUDE_DIRS = {
    '.git', 'target', 'node_modules', '.build', '.trae', '.gitee-ci', '.github',
    'wendang', '__pycache__', '.pytest_cache', '.mypy_cache', '.gradle',
    'build', 'dist', '.idea', '.vscode',
    # 各语言子目录中的源码/测试目录（只扫描根级 .md）
    'src', 'tests', 'examples', 'evorule', 'gradle',
}

# R-交叉引用
MD_LINK_RE = re.compile(r'\[[^\]]*\]\(([^)]+)\)')


def run(cmd: List[str], cwd: Path) -> Tuple[str, str, int]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))
    except FileNotFoundError:
        return '', 'git not found', 127
    return r.stdout, r.stderr, r.returncode


# ---------------------------------------------------------------------------
# R-门控1
# ---------------------------------------------------------------------------

def check_gate_staged(cwd: Path, check_history: bool) -> Tuple[bool, List[str], List[str]]:
    staged_violations: List[str] = []
    history_violations: List[str] = []

    out, _, rc = run(['git', 'diff', '-z', '--cached', '--name-only', '--diff-filter=ACMRT'], cwd)
    if rc != 0:
        return False, [], []
    staged_files = [f for f in out.split('\0') if f]
    staged_violations = [f for f in staged_files if DOCS_PATH_PATTERN.search(f)]

    ok = not staged_violations and not history_violations
    return ok, staged_violations, history_violations


# ---------------------------------------------------------------------------
# 辅助：列出 L1 公开文档路径
# ---------------------------------------------------------------------------

def list_l1_docs(root: Path) -> List[Path]:
    files: List[Path] = []
    for base in L1_ROOTS:
        if not base.exists():
            continue
        if base == root or base == root / 'docs':
            # 根目录和 docs/：递归扫描所有 .md（排除 L1_EXCLUDE_DIRS）
            for p in base.rglob('*.md'):
                if any(excl in p.parts for excl in L1_EXCLUDE_DIRS):
                    continue
                if base == root and p.parent != root:
                    continue  # 根目录只看直下
                files.append(p.resolve())
        else:
            # 各语言子目录：只扫描根级 .md（README.md, CHANGELOG.md）
            for p in base.glob('*.md'):
                if any(excl in p.parts for excl in L1_EXCLUDE_DIRS):
                    continue
                files.append(p.resolve())
    return sorted(set(files))


# ---------------------------------------------------------------------------
# R3：L1 私有集合泄露检查
# ---------------------------------------------------------------------------

def check_private_leak(docs: List[Path], root: Path) -> List[Tuple[Path, int, str, str]]:
    violations: List[Tuple[Path, int, str, str]] = []
    for doc in docs:
        rel_name = doc.name
        try:
            lines = doc.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines, 1):
            if rel_name in RULE_DECLARATION_FILES and RULE_DECLARATION_LINE_HINTS.search(line):
                continue
            for pat in PRIVATE_LEAK_PATTERNS:
                m = pat.search(line)
                if m:
                    violations.append((doc, i, pat.pattern, line.strip()))
                    break
    return violations


# ---------------------------------------------------------------------------
# R-L1不提L2/L3
# ---------------------------------------------------------------------------

def check_l1_mentions_l2l3(docs: List[Path], root: Path) -> List[Tuple[Path, int, str]]:
    violations: List[Tuple[Path, int, str]] = []
    for doc in docs:
        rel_name = doc.name
        try:
            lines = doc.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines, 1):
            if rel_name in RULE_DECLARATION_FILES and L2L3_EXEMPT_HINTS.search(line):
                continue
            if L2L3_REF_PATTERN.search(line):
                violations.append((doc, i, line.strip()))
    return violations


# ---------------------------------------------------------------------------
# R-兄弟仓零谈论
# ---------------------------------------------------------------------------

def check_sibling_mention(docs: List[Path], root: Path) -> List[Tuple[Path, int, str, str]]:
    violations: List[Tuple[Path, int, str, str]] = []
    for doc in docs:
        try:
            lines = doc.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        if '[已废弃]' in '\n'.join(lines[:50]):
            continue
        for i, line in enumerate(lines, 1):
            for pat in SIBLING_REPO_PATTERNS:
                m = pat.search(line)
                if not m:
                    continue
                repo_name = m.group(0)
                if SIBLING_INTERNAL_DISCUSSION_HINTS.search(line):
                    violations.append((doc, i, repo_name, line.strip()))
                    break
                if DEPENDENCY_DECLARATION_HINTS.search(line):
                    continue
                violations.append((doc, i, repo_name, line.strip()))
                break
    return violations


# ---------------------------------------------------------------------------
# R-agent身份零泄露
# ---------------------------------------------------------------------------

def check_agent_identity_leak(docs: List[Path], root: Path) -> List[Tuple[Path, int, str, str]]:
    violations: List[Tuple[Path, int, str, str]] = []
    for doc in docs:
        try:
            lines = doc.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        if '[已废弃]' in '\n'.join(lines[:50]):
            continue
        for i, line in enumerate(lines, 1):
            for pat in AGENT_IDENTITY_PATTERNS:
                m = pat.search(line)
                if not m:
                    continue
                if AGENT_PRODUCT_HINTS.search(line):
                    continue
                violations.append((doc, i, pat.pattern, line.strip()))
                break
    return violations


# ---------------------------------------------------------------------------
# R-交叉引用完整性
# ---------------------------------------------------------------------------

PLACEHOLDER_LINK_MARKERS = re.compile(
    r'(申请表单|^NOTICE$|vX\.Y\.Z|v\*|\*_AUDIT_v\*)'
)

KNOWN_DELETED_DOCS: set = set()


def resolve_md_link(link: str, source_doc: Path, root: Path) -> Path | None:
    if not link or link.startswith('#') or link.startswith('http://') or link.startswith('https://') \
            or link.startswith('mailto:'):
        return None
    raw = link.split(' ', 1)[0]
    raw = raw.split('#', 1)[0]
    if not raw:
        return None
    if raw.startswith('/'):
        target = (root / raw.lstrip('/')).resolve()
    else:
        target = (source_doc.parent / raw).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target


def check_cross_refs(docs: List[Path], root: Path) -> List[Tuple[Path, int, str, Path]]:
    violations: List[Tuple[Path, int, str, Path]] = []
    for doc in docs:
        try:
            lines = doc.read_text(encoding='utf-8').splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for i, line in enumerate(lines, 1):
            for m in MD_LINK_RE.finditer(line):
                raw = m.group(1).split(' ', 1)[0].split('#', 1)[0]
                if PLACEHOLDER_LINK_MARKERS.search(raw):
                    continue
                if raw.split('/')[-1] in KNOWN_DELETED_DOCS:
                    continue
                # 非 .md / .py / .ts / .go / .java / .json / .toml / .kts 链接跳过
                if not raw.endswith(('.md', '.py', '.ts', '.go', '.java', '.json', '.toml', '.kts', '.html')):
                    continue
                target = resolve_md_link(m.group(1), doc, root)
                if target is None:
                    continue
                if not target.exists():
                    violations.append((doc, i, m.group(1), target))
    return violations


# ---------------------------------------------------------------------------
# R-索引存在性
# ---------------------------------------------------------------------------

DOCS_INDEX_NAME = 'DOCS_INDEX.md'


def check_docs_index_exist(docs: List[Path], root: Path) -> List[Tuple[Path, int, str, Path]]:
    violations: List[Tuple[Path, int, str, Path]] = []
    idx = root / DOCS_INDEX_NAME
    if not idx.exists():
        return violations
    try:
        lines = idx.read_text(encoding='utf-8').splitlines()
    except (OSError, UnicodeDecodeError):
        return violations

    for i, line in enumerate(lines, 1):
        for m in re.finditer(r'\(([^\s)]+\.md(?:#[^)]*)?)\)', line):
            raw = m.group(1).split('#', 1)[0]
            if PLACEHOLDER_LINK_MARKERS.search(raw) or '*' in raw:
                continue
            if raw.split('/')[-1] in KNOWN_DELETED_DOCS:
                continue
            target = resolve_md_link(m.group(1), idx, root)
            if target is None:
                continue
            try:
                rel = target.relative_to(root)
            except ValueError:
                continue
            # L1 = 直下 md 或 docs/** 下 md 或 各语言子目录根级 md
            in_l1 = (len(rel.parts) == 1 and str(rel).endswith('.md')) or \
                    (len(rel.parts) >= 2 and rel.parts[0] == 'docs') or \
                    (len(rel.parts) == 2 and rel.parts[0] in ('python', 'typescript', 'go', 'java') and str(rel).endswith('.md'))
            if in_l1 and not target.exists():
                violations.append((idx, i, raw, target))

    return violations


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def collect_all(root: Path, skip_git: bool) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        'gate_staged': {'ok': True, 'staged_violations': [], 'history_violations': []},
        'private_leak_l1': [],
        'l1_mentions_l2l3': [],
        'sibling_mention_l1': [],
        'agent_identity_leak_l1': [],
        'cross_ref_l1': [],
        'docs_index_exist': [],
    }

    if not skip_git:
        ok, staged, hist = check_gate_staged(root, check_history=False)
        result['gate_staged'] = {
            'ok': ok, 'staged_violations': staged, 'history_violations': hist,
        }

    docs = list_l1_docs(root)
    result['_l1_docs_count'] = len(docs)

    for (p, ln, pat, snip) in check_private_leak(docs, root):
        result['private_leak_l1'].append({
            'file': str(p.relative_to(root)),
            'line': ln, 'pattern': pat, 'snippet': snip,
        })
    for (p, ln, snip) in check_l1_mentions_l2l3(docs, root):
        result['l1_mentions_l2l3'].append({
            'file': str(p.relative_to(root)),
            'line': ln, 'snippet': snip,
        })
    for (p, ln, repo, snip) in check_sibling_mention(docs, root):
        result['sibling_mention_l1'].append({
            'file': str(p.relative_to(root)),
            'line': ln, 'repo': repo, 'snippet': snip,
        })
    for (p, ln, pat, snip) in check_agent_identity_leak(docs, root):
        result['agent_identity_leak_l1'].append({
            'file': str(p.relative_to(root)),
            'line': ln, 'pattern': pat, 'snippet': snip,
        })
    for (p, ln, raw, tgt) in check_cross_refs(docs, root):
        result['cross_ref_l1'].append({
            'file': str(p.relative_to(root)), 'line': ln,
            'link': raw, 'missing': str(tgt.relative_to(root)),
        })
    for (p, ln, raw, tgt) in check_docs_index_exist(docs, root):
        result['docs_index_exist'].append({
            'file': str(p.relative_to(root)), 'line': ln,
            'entry': raw, 'missing': str(tgt.relative_to(root)),
        })

    return result


def any_violation(r: Dict[str, Any]) -> bool:
    gs = r.get('gate_staged', {})
    if not gs.get('ok', True):
        return True
    for k in ('private_leak_l1', 'l1_mentions_l2l3', 'sibling_mention_l1',
              'agent_identity_leak_l1', 'cross_ref_l1', 'docs_index_exist'):
        if r.get(k):
            return True
    return False


def print_human(r: Dict[str, Any]):
    def hr(title: str):
        print(f'\n--- {title} ---')

    gs = r['gate_staged']
    if not gs['staged_violations'] and not gs['history_violations']:
        print('✓ [R-门控1] staged 无 wendang/ 路径')
    else:
        print('✗ [R-门控1] 检测到 commit wendang/ 路径', file=sys.stderr)
        for v in gs['staged_violations']:
            print(f'   staged: {v}', file=sys.stderr)

    hr('R3 引用合规（L1 私有路径泄露）')
    if not r['private_leak_l1']:
        print('✓ 未检测到 L1 公开文档出现私有集合路径/编号前缀')
    else:
        for v in r['private_leak_l1']:
            print(f"   ✗ {v['file']}:{v['line']}  pattern={v['pattern']}  {v['snippet']}", file=sys.stderr)

    hr('L1 不提 L2/L3')
    if not r['l1_mentions_l2l3']:
        print('✓ L1 公开文档未出现 wendang/design|implement|benchmarks|archive/ 字面量')
    else:
        for v in r['l1_mentions_l2l3']:
            print(f"   ✗ {v['file']}:{v['line']}  {v['snippet']}", file=sys.stderr)

    hr('R-兄弟仓零谈论')
    if not r['sibling_mention_l1']:
        print('✓ L1 公开文档未谈论兄弟仓内部(依赖声明除外)')
    else:
        for v in r['sibling_mention_l1']:
            print(f"   ✗ {v['file']}:{v['line']}  repo={v['repo']}  {v['snippet']}", file=sys.stderr)

    hr('R-agent身份零泄露')
    if not r['agent_identity_leak_l1']:
        print('✓ L1 公开文档未泄露 AI agent 身份(agent 产品概念除外)')
    else:
        for v in r['agent_identity_leak_l1']:
            print(f"   ✗ {v['file']}:{v['line']}  pattern={v['pattern']}  {v['snippet']}", file=sys.stderr)

    hr('L1 交叉引用完整性')
    if not r['cross_ref_l1']:
        print('✓ L1 文档内所有链接指向的仓内文件均存在')
    else:
        for v in r['cross_ref_l1']:
            print(f"   ✗ {v['file']}:{v['line']}  link=[{v['link']}]  missing=/{v['missing']}", file=sys.stderr)

    hr('DOCS_INDEX 索引存在性')
    if not r['docs_index_exist']:
        print('✓ DOCS_INDEX.md 中列出的 L1 路径均存在')
    else:
        for v in r['docs_index_exist']:
            print(f"   ✗ {v['file']}:{v['line']}  entry=[{v['entry']}]  missing=/{v['missing']}", file=sys.stderr)


def main():
    default_root = str(Path(__file__).resolve().parent.parent)
    p = argparse.ArgumentParser(description='EvoRule SDK 文档安全 + 引用完整性检查')
    p.add_argument('--warn', action='store_true', help='只警告不报错（exit 恒 0）')
    p.add_argument('--skip-git', action='store_true', help='跳过 git staged/history 检查（非 git 环境）')
    p.add_argument('--json', action='store_true', help='JSON 输出')
    p.add_argument('--cwd', default=default_root, help='repo 根目录（默认自动定位 scripts/..）')
    args = p.parse_args()

    cwd = Path(args.cwd).resolve()

    r = collect_all(cwd, skip_git=args.skip_git)

    if args.json:
        r['summary'] = {
            'l1_docs_count': r.pop('_l1_docs_count', 0),
            'any_violation': any_violation(r),
        }
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print_human(r)

    if args.warn:
        sys.exit(0)
    sys.exit(1 if any_violation(r) else 0)


if __name__ == '__main__':
    main()

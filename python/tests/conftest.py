"""pytest 共享 fixture（CI 与本地 pytest 入口）

tests/test_e2e.py 与 tests/test_e2e_self_contained.py 的 14 个场景为 E2E
集成测试：前者需要运行中的 evorule-server，后者需要本地 .build 服务端二进制。
两者均自带脚本入口（不经 pytest 执行）：

    python tests/test_e2e_self_contained.py   # 自启动 evorule-server，全场景自包含
    python tests/test_e2e.py                  # 连接已启动的 evorule-server

pytest 收集到这些场景时统一跳过，CI 只执行单元测试。
"""

import pytest


@pytest.fixture
def tr():
    pytest.skip(
        "E2E 场景不经 pytest 执行："
        "本地运行 python tests/test_e2e_self_contained.py（自包含）"
        "或 python tests/test_e2e.py（需已启动 evorule-server）"
    )

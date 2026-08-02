// SPDX-License-Identifier: AGPL-3.0-or-later
package main

import (
	"encoding/json"
	"fmt"
	"gitee.com/evo-rule-lab/evorule-sdk/go/evorule"
)

func main() {
	// 无认证（仅 loopback 开发环境）
	// client := evorule.NewClient("http://localhost:18080")

	// 带 Bearer token 认证（evorule-server 非 loopback 部署时必须）
	client := evorule.NewClientWithAuth("http://localhost:18080", "secret123")

	fmt.Println("1. 创建会话...")
	sessionID, err := client.CreateSession()
	if err != nil {
		fmt.Printf("创建会话失败: %v\n", err)
		return
	}
	fmt.Printf("会话创建成功: ID=%d\n", sessionID)

	fmt.Println("\n2. 提交命令...")
	instruction := map[string]interface{}{
		"type": "increment",
		"params": map[string]interface{}{
			"attr":  "x",
			"delta": 1,
		},
	}
	if err := client.SubmitCommand(sessionID, instruction); err != nil {
		fmt.Printf("提交命令失败: %v\n", err)
		return
	}
	fmt.Println("命令提交成功")

	fmt.Println("\n3. 查询状态...")
	state, err := client.GetState(sessionID)
	if err != nil {
		fmt.Printf("查询状态失败: %v\n", err)
		return
	}
	if state.Payload != nil {
		var payload map[string]interface{}
		if err := json.Unmarshal(*state.Payload, &payload); err == nil {
			fmt.Printf("状态: %v (version=%d)\n", payload, state.Version)
		}
	}

	fmt.Println("\n4. 获取执行历史...")
	replay, err := client.GetReplay(sessionID)
	if err != nil {
		fmt.Printf("获取历史失败: %v\n", err)
		return
	}
	fmt.Printf("历史记录数: %d\n", len(replay))
	for _, fact := range replay {
		fmt.Printf("  - %s (F%d)\n", fact.Type, fact.ID)
	}

	fmt.Println("\n5. 关闭会话...")
	if err := client.CloseSession(sessionID); err != nil {
		fmt.Printf("关闭会话失败: %v\n", err)
		return
	}
	fmt.Println("会话关闭成功")
}
package main

import (
	"encoding/json"
	"fmt"
	"github.com/evorule/go-sdk/evorule"
)

func main() {
	client := evorule.NewClient("http://localhost:18080")

	fmt.Println("1. 创建会话...")
	session, err := client.CreateSession()
	if err != nil {
		fmt.Printf("创建会话失败: %v\n", err)
		return
	}
	fmt.Printf("会话创建成功: ID=%d, Phase=%s\n", session.ID, session.Phase)

	fmt.Println("\n2. 提交命令...")
	instruction := map[string]interface{}{
		"type": "increment",
		"params": map[string]interface{}{
			"attr":  "x",
			"delta": 1,
		},
	}
	if err := client.SubmitCommand(session.ID, instruction); err != nil {
		fmt.Printf("提交命令失败: %v\n", err)
		return
	}
	fmt.Println("命令提交成功")

	fmt.Println("\n3. 查询状态...")
	state, err := client.GetState(session.ID)
	if err != nil {
		fmt.Printf("查询状态失败: %v\n", err)
		return
	}
	if state.Payload != nil {
		var payload map[string]interface{}
		if err := json.Unmarshal(*state.Payload, &payload); err == nil {
			fmt.Printf("状态: %v\n", payload)
		}
	}

	fmt.Println("\n4. 获取执行历史...")
	replay, err := client.GetReplay(session.ID)
	if err != nil {
		fmt.Printf("获取历史失败: %v\n", err)
		return
	}
	fmt.Printf("历史记录数: %d\n", len(replay.Facts))
	for _, fact := range replay.Facts {
		fmt.Printf("  - %s (F%d)\n", fact.Type, fact.ID)
	}

	fmt.Println("\n5. 关闭会话...")
	if err := client.CloseSession(session.ID); err != nil {
		fmt.Printf("关闭会话失败: %v\n", err)
		return
	}
	fmt.Println("会话关闭成功")
}
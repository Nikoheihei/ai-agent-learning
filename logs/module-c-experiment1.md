# 模块 C 实验 1：AI 输出 → Sepolia 链上执行

> 日期：2026-05-19  
> 实验类型：AI 生成命令 → 人工复核 → 链上执行 → Etherscan 验证  
> 网络：Sepolia 测试网（chainId=11155111）

---

## 一、AI 生成阶段

**AI 生成的 `cast send` 命令**：

```bash
cast send \
  --account test-wallet \
  --rpc-url $SEPOLIA_RPC \
  --gas-limit 21000 \
  0x0a8f8647bb07dc926aa1320d40b56ee976011b8a \
  --value 0
```

**AI 说明**：
- `to` 地址为钱包本人（自转，无资产风险）
- `value = 0`（不转移 ETH，只消耗 gas）
- `gas-limit = 21000`（标准 ETH 转账）

---

## 二、人工复核阶段

| 检查项 | 结果 | 说明 |
|---|---|---|
| `to` 地址是否正确？ | ✅ | 0x0a8F...1b8A，本人钱包 |
| `value` 是否为 0？ | ✅ | 无 ETH 转移风险 |
| `rpc-url` 是否指向 Sepolia？ | ✅ | $SEPOLIA_RPC = sepolia publicnode |
| 钱包是否为测试钱包？ | ✅ | keystore 独立，非主钱包 |
| gas 消耗预估 | ~0.0003 ETH | 余额 0.05 ETH，可承受 |

**复核结论**：✅ **通过，执行**

---

## 三、执行阶段

**执行命令**（终端输出）：

```
blockHash           0x6926b6...56b9c4  (block hash)
blockNumber         10879932
gasUsed             21000
status              1 (success)
transactionHash     0x64271846dd281b4a1a731a2e45e526d3ade2003b3b4b83b476d1890ea44c9d69
from                0x0a8f8647bB07Dc926aa1320D40b56EE976011B8A
to                  0x0a8f8647bB07Dc926aa1320D40b56EE976011B8A
type                2
```

---

## 四、Etherscan 验证

**验证链接**：
https://sepolia.etherscan.io/tx/0x64271846dd281b4a1a731a2e45e526d3ade2003b3b4b83b476d1890ea44c9d69

**验证结果**：

| 字段 | 值 | 状态 |
|---|---|---|
| Status | Success | ✅ |
| Block | 10879932 | ✅ |
| From | 0x0a8F...1b8A | ✅ |
| To | 0x0a8F...1b8A | ✅ |
| Value | 0 ETH | ✅ |
| Transaction Fee | ~0.00029 ETH | ✅ |

---

## 五、流程图（本次实验完整链路）

```
AI 生成 cast send 命令
        ↓
人工复核（检查 to/value/gas/rpc）
        ↓  ✅ 通过
输入 keystore 密码（钱包确认）
        ↓
cast send 广播交易到 Sepolia
        ↓
获取 transactionHash: 0x6427...9d69
        ↓
Etherscan 查询（Status=Success）
        ↓
记录到 logs/module-c-experiment1.md ✅
```

---

## 六、实验总结

### 成功点
1. ✅ AI 生成命令准确无误
2. ✅ 人工复核有效拦截风险（value=0 确认无资产转移）
3. ✅ keystore 加密存储私钥，未泄露明文
4. ✅ 链上执行成功，Etherscan 可验证

### 风险点（主网需特别注意）
1. ⚠️ `to` 地址必须人工二次确认（有误会丢资产）
2. ⚠️ `value` 单位换算需谨慎（1 ETH = 10^18 wei）
3. ⚠️ `gas-price` 需根据网络拥堵动态调整
4. ⚠️ 私钥/keystore 密码不能截图/外传

### 下一步
- [ ] 实验 2：AI 解释合约 ABI（USDC Sepolia）
- [ ] 实验 3：AI 生成合约调用命令（调用真实合约函数）
- [ ] 编写 `.env.example` 模板（规范环境变量管理）

---

> 实验完成时间：2026-05-19  
> 执行者：NikoHeiHeiHei  
> 工具：Foundry (cast) + Sepolia 测试网

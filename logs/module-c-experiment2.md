# 模块 C 实验 2：智能合约部署 & 读写

> 日期：2026-05-19  
> 实验类型：Foundry 合约部署 + cast 读写验证  
> 网络：Sepolia 测试网（chainId=11155111）

---

## 一、合约说明

**合约名**：`Counter.sol`  
**功能**：最简单的计数器，支持 `get/inc/dec/reset`

```solidity
contract Counter {
    uint256 private count;

    function get() external view returns (uint256);  // 读，免费
    function inc() external;                          // 写，+1
    function dec() external;                          // 写，-1（0时revert）
    function reset() external;                        // 写，归零
}
```

源码：`demos/contracts/src/Counter.sol`

---

## 二、部署阶段

**部署命令**：

```bash
cd demos/contracts
forge create \
  --rpc-url https://ethereum-sepolia.publicnode.com \
  --account test-wallet \
  --broadcast \
  src/Counter.sol:Counter
```

**部署结果**：

| 字段 | 值 |
|---|---|
| Deployer | `0x0a8F...1b8A` |
| **合约地址** | `0xb812b83Db8e676Dc7f50d96947f39d79166F891b` |
| Tx Hash | `0xae65...4f02` |
| Block | `10880170`（约） |

**Etherscan 验证链接**：  
👉 https://sepolia.etherscan.io/address/0xb812b83Db8e676Dc7f50d96947f39d79166F891b

---

## 三、读写验证阶段

### 3.1 读取初始值（call）

```bash
cast call \
  --rpc-url https://ethereum-sepolia.publicnode.com \
  0xb812b83Db8e676Dc7f50d96947f39d79166F891b \
  "get()"
```

**输出**：`0x0000...0000` → **0** ✅

---

### 3.2 写入（inc）

```bash
cast send \
  --account test-wallet \
  --rpc-url https://ethereum-sepolia.publicnode.com \
  0xb812b83Db8e676Dc7f50d96947f39d79166F891b \
  "inc()"
```

**输出**：

```
status              1 (success)
transactionHash     0x7474...0c8
gasUsed             45108
logs                [Incremented event 触发]
```

---

### 3.3 读取 inc 后的值（call）

```bash
cast call \
  --rpc-url https://ethereum-sepolia.publicnode.com \
  0xb812b83Db8e676Dc7f50d96947f39d79166F891b \
  "get()"
```

**输出**：`0x0000...0001` → **1** ✅

---

## 四、完整流程图

```
编写 Counter.sol
        ↓
forge build（编译）
        ↓
forge create → Sepolia 部署
        ↓
获得合约地址：0xb812...F891b
        ↓
cast call "get()"  →  返回 0  ✅
        ↓
cast send "inc()"  →  tx 成功  ✅
        ↓
cast call "get()"  →  返回 1  ✅
        ↓
Etherscan 验证：https://sepolia.etherscan.io/address/0xb812...F891b
        ↓
记录到 logs/module-c-experiment2.md  ✅
```

---

## 五、实验总结

### 成功点
1. ✅ Foundry 项目初始化成功（`forge init`）
2. ✅ 合约编译通过（Solc 0.8.30）
3. ✅ 部署到 Sepolia 成功（合约地址确认）
4. ✅ `cast call` 读取值正确（0 → 1）
5. ✅ `cast send` 写入成功（事件正常触发）

### 遇到的问题 & 解决
| 问题 | 原因 | 解决方式 |
|---|---|---|
| `forge create` 找不到文件 | 没有 `foundry.toml` | 先 `forge init` |
| 测试文件编译报错 | 旧模板函数名不匹配 | 重写 `Counter.t.sol` |
| keystore 路径错误 | 目录名是 `keystores`（复数） | 用 `--account test-wallet` 自动查找 |

### 下一步
- [ ] 验证 Etherscan 上合约源码验证（verify）
- [ ] 实验 3：AI 生成合约调用脚本
- [ ] 用 `cast send` 调用 `dec()` 和 `reset()`

---

> 实验完成时间：2026-05-19  
> 执行者：NikoHeiHeiHei  
> 工具：Foundry (forge + cast) + Sepolia 测试网

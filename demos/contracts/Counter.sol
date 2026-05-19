// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Counter
/// @notice 最简单的计数器合约，用于演示部署和读写操作
contract Counter {
    uint256 private count;

    event Incremented(address indexed by, uint256 newValue);

    /// @notice 读取当前计数值
    function get() external view returns (uint256) {
        return count;
    }

    /// @notice 计数值 +1
    function inc() external {
        count++;
        emit Incremented(msg.sender, count);
    }

    /// @notice 计数值 -1
    function dec() external {
        require(count > 0, "underflow");
        count--;
    }

    /// @notice 重置为 0
    function reset() external {
        count = 0;
    }
}

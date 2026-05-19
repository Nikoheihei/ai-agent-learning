// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test, console2} from "forge-std/Test.sol";
import {Counter} from "../src/Counter.sol";

contract CounterTest is Test {
    Counter public counter;

    function setUp() public {
        counter = new Counter();
    }

    function test_GetInitial() public {
        assertEq(counter.get(), 0);
    }

    function test_Inc() public {
        counter.inc();
        assertEq(counter.get(), 1);
    }

    function test_DecRevertWhenZero() public {
        vm.expectRevert("underflow");
        counter.dec();
    }
}

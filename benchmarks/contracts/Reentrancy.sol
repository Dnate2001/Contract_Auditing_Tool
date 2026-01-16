// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Reentrancy
 * @notice Classic reentrancy vulnerability
 * Expected vulnerabilities: 1 (reentrancy in withdraw)
 */
contract Reentrancy {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE: External call before state update
    function withdraw(uint256 _amount) public {
        require(balances[msg.sender] >= _amount, "Insufficient balance");

        // External call BEFORE state update
        (bool success, ) = msg.sender.call{value: _amount}("");
        require(success, "Transfer failed");

        // State update AFTER external call
        balances[msg.sender] -= _amount;
    }

    function getBalance() public view returns (uint256) {
        return balances[msg.sender];
    }
}

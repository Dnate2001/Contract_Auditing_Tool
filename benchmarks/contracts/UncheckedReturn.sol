// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title UncheckedReturn
 * @notice Unchecked low-level call return value
 * Expected vulnerabilities: 1 (unchecked call)
 */
contract UncheckedReturn {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE: Call return value not checked
    function withdraw(uint256 _amount) public {
        require(balances[msg.sender] >= _amount, "Insufficient balance");
        balances[msg.sender] -= _amount;

        // Return value not checked
        payable(msg.sender).call{value: _amount}("");
    }
}

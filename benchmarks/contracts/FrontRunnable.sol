// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title FrontRunnable
 * @notice Front-running vulnerability via predictable randomness
 * Expected vulnerabilities: 1 (weak randomness)
 */
contract FrontRunnable {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE: Predictable randomness using block.timestamp
    function claimReward() public {
        uint256 reward = uint256(
            keccak256(abi.encodePacked(block.timestamp, msg.sender))
        ) % 1000;
        balances[msg.sender] += reward;
    }

    function withdraw(uint256 _amount) public {
        require(balances[msg.sender] >= _amount, "Insufficient balance");
        balances[msg.sender] -= _amount;
        payable(msg.sender).transfer(_amount);
    }
}

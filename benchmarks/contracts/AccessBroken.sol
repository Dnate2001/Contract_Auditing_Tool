// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title AccessBroken
 * @notice Missing access control on critical functions
 * Expected vulnerabilities: 2 (unprotected withdraw, unprotected setOwner)
 */
contract AccessBroken {
    address public owner;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // VULNERABLE: No access control
    function withdraw(uint256 _amount) public {
        require(address(this).balance >= _amount, "Insufficient funds");
        payable(msg.sender).transfer(_amount);
    }

    // VULNERABLE: No access control
    function setOwner(address _newOwner) public {
        owner = _newOwner;
    }
}

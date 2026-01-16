// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title SelfDestructVuln
 * @notice Unprotected selfdestruct
 * Expected vulnerabilities: 1 (unprotected selfdestruct)
 */
contract SelfDestructVuln {
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {}

    // VULNERABLE: Anyone can destroy the contract
    function destroy(address payable _recipient) public {
        selfdestruct(_recipient);
    }
}

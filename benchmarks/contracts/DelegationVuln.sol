// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title DelegationVuln
 * @notice Unrestricted delegatecall vulnerability
 * Expected vulnerabilities: 1 (arbitrary delegatecall)
 */
contract DelegationVuln {
    address public owner;
    uint256 public value;

    constructor() {
        owner = msg.sender;
    }

    // VULNERABLE: Anyone can delegatecall to any address
    function execute(
        address _target,
        bytes memory _data
    ) public returns (bytes memory) {
        (bool success, bytes memory result) = _target.delegatecall(_data);
        require(success, "Delegatecall failed");
        return result;
    }

    function setValue(uint256 _value) public {
        value = _value;
    }
}

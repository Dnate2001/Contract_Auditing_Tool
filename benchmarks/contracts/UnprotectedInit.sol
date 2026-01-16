// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title UnprotectedInit
 * @notice Unprotected initialization function
 * Expected vulnerabilities: 1 (anyone can initialize)
 */
contract UnprotectedInit {
    address public owner;
    bool public initialized;

    // VULNERABLE: No access control on initialization
    function initialize(address _owner) public {
        require(!initialized, "Already initialized");
        owner = _owner;
        initialized = true;
    }

    function withdraw() public {
        require(msg.sender == owner, "Not owner");
        payable(owner).transfer(address(this).balance);
    }

    receive() external payable {}
}

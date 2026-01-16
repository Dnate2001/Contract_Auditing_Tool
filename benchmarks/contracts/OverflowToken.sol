// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title OverflowToken
 * @notice Integer overflow in unchecked block
 * Expected vulnerabilities: 1 (overflow in mint)
 */
contract OverflowToken {
    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;

    // VULNERABLE: Unchecked arithmetic can overflow
    function mint(address _to, uint256 _amount) public {
        unchecked {
            balanceOf[_to] += _amount;
            totalSupply += _amount;
        }
    }

    function transfer(address _to, uint256 _amount) public {
        require(balanceOf[msg.sender] >= _amount, "Insufficient balance");
        balanceOf[msg.sender] -= _amount;
        balanceOf[_to] += _amount;
    }
}

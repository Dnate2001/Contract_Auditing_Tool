// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "../contracts/BrokenToken.sol";

/**
 * @title BrokenTokenTest - Medusa Fuzzing Test Suite
 * @notice Property-based tests to detect vulnerabilities
 */
contract BrokenTokenTest {
    BrokenToken public token;
    address public owner;
    address public user1;
    address public user2;

    uint256 constant INITIAL_SUPPLY = 1_000_000 * 10 ** 18;

    constructor() {
        owner = address(this);
        user1 = address(0x1111);
        user2 = address(0x2222);

        // Deploy the vulnerable token
        token = new BrokenToken(INITIAL_SUPPLY);
    }

    /**
     * @notice PROPERTY 1: Total supply should never decrease (except burns)
     * @dev This will fail due to the selfdestruct vulnerability
     */
    function property_totalSupplyNeverDecreases() public view returns (bool) {
        return token.totalSupply() >= INITIAL_SUPPLY;
    }

    /**
     * @notice PROPERTY 2: Sum of balances should equal total supply
     * @dev This will fail due to reentrancy and mint vulnerabilities
     */
    function property_balancesEqualSupply() public view returns (bool) {
        uint256 sumBalances = token.balanceOf(owner) +
            token.balanceOf(user1) +
            token.balanceOf(user2);
        return sumBalances <= token.totalSupply();
    }

    /**
     * @notice PROPERTY 3: Only authorized users should mint
     * @dev This will fail because anyone can call mint()
     */
    function property_onlyOwnerCanMint(
        address caller,
        uint256 amount
    ) public returns (bool) {
        uint256 supplyBefore = token.totalSupply();

        // Try to mint from arbitrary caller
        try token.mint(caller, amount) {
            // If mint succeeded, check if supply increased
            if (token.totalSupply() > supplyBefore) {
                // Mint worked! This should only happen for owner
                return caller == owner;
            }
        } catch {
            // Mint failed, which is expected for non-owners
        }
        return true;
    }

    /**
     * @notice PROPERTY 4: Transfer should not allow reentrancy
     * @dev This will fail due to the reentrancy vulnerability
     */
    function property_transferNoReentrancy(
        address to,
        uint256 amount
    ) public returns (bool) {
        // Ensure we have enough balance
        if (token.balanceOf(address(this)) < amount) {
            return true; // Skip if insufficient balance
        }

        uint256 balanceBefore = token.balanceOf(address(this));

        try token.transfer(to, amount) {
            uint256 balanceAfter = token.balanceOf(address(this));
            // Balance should decrease by exactly the amount transferred
            return (balanceBefore - balanceAfter) == amount;
        } catch {
            return true; // Revert is acceptable
        }
    }

    /**
     * @notice PROPERTY 5: Contract should not be destructible by anyone
     * @dev This will fail because destroy() has no access control
     */
    function property_contractNotDestructible(
        address caller
    ) public view returns (bool) {
        // Check if contract still exists
        return address(token).code.length > 0;
    }

    /**
     * @notice PROPERTY 6: Approve should not accept zero address
     * @dev This will fail because approve() doesn't validate spender
     */
    function property_approveValidatesSpender(
        address spender,
        uint256 amount
    ) public returns (bool) {
        if (spender == address(0)) {
            // Approval to zero address should fail
            try token.approve(spender, amount) returns (bool success) {
                return !success; // Should return false or revert
            } catch {
                return true; // Revert is good
            }
        }
        return true;
    }

    /**
     * @notice PROPERTY 7: Random rewards should be truly random
     * @dev This will fail because randomness is predictable
     */
    function property_randomnessNotPredictable() public returns (bool) {
        uint256 balanceBefore = token.balanceOf(address(this));
        token.claimRandomReward();
        uint256 reward1 = token.balanceOf(address(this)) - balanceBefore;

        // In a truly random system, calling again should give different result
        // But with block.timestamp, it will be the same in the same block
        balanceBefore = token.balanceOf(address(this));
        token.claimRandomReward();
        uint256 reward2 = token.balanceOf(address(this)) - balanceBefore;

        // If rewards are identical, randomness is weak
        return reward1 != reward2;
    }
}

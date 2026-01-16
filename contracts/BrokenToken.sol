// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title BrokenToken - Intentionally Vulnerable ERC20 Token
 * @notice This contract contains multiple vulnerabilities for fuzzing demonstration
 * @dev DO NOT USE IN PRODUCTION - For educational purposes only
 */
contract BrokenToken {
    string public name = "BrokenToken";
    string public symbol = "BROKE";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(
        address indexed owner,
        address indexed spender,
        uint256 value
    );

    constructor(uint256 _initialSupply) {
        totalSupply = _initialSupply;
        balanceOf[msg.sender] = _initialSupply;
    }

    /**
     * @notice VULNERABILITY 1: Reentrancy in transfer
     * @dev No reentrancy guard, allows external calls before state update
     */
    function transfer(
        address _to,
        uint256 _value
    ) public returns (bool success) {
        require(balanceOf[msg.sender] >= _value, "Insufficient balance");

        // VULNERABLE: External call before state update
        if (_to.code.length > 0) {
            (bool callSuccess, ) = _to.call(
                abi.encodeWithSignature(
                    "onTokenReceived(address,uint256)",
                    msg.sender,
                    _value
                )
            );
            require(callSuccess, "Callback failed");
        }

        // State update AFTER external call (reentrancy vulnerability)
        balanceOf[msg.sender] -= _value;
        balanceOf[_to] += _value;

        emit Transfer(msg.sender, _to, _value);
        return true;
    }

    /**
     * @notice VULNERABILITY 2: Integer overflow in mint (if using older Solidity)
     * @dev No overflow check on totalSupply
     */
    function mint(address _to, uint256 _amount) public {
        // VULNERABLE: No access control - anyone can mint!
        balanceOf[_to] += _amount;
        totalSupply += _amount;
        emit Transfer(address(0), _to, _amount);
    }

    /**
     * @notice VULNERABILITY 3: Unchecked return value
     * @dev approve doesn't validate inputs properly
     */
    function approve(
        address _spender,
        uint256 _value
    ) public returns (bool success) {
        // VULNERABLE: No check for zero address
        allowance[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    /**
     * @notice VULNERABILITY 4: Front-running in transferFrom
     * @dev Classic ERC20 approve/transferFrom race condition
     */
    function transferFrom(
        address _from,
        address _to,
        uint256 _value
    ) public returns (bool success) {
        require(_value <= balanceOf[_from], "Insufficient balance");
        require(
            _value <= allowance[_from][msg.sender],
            "Insufficient allowance"
        );

        balanceOf[_from] -= _value;
        balanceOf[_to] += _value;
        allowance[_from][msg.sender] -= _value;

        emit Transfer(_from, _to, _value);
        return true;
    }

    /**
     * @notice VULNERABILITY 5: Dangerous delegatecall
     * @dev Allows arbitrary code execution
     */
    function executeArbitrary(
        address _target,
        bytes memory _data
    ) public returns (bool success) {
        // EXTREMELY VULNERABLE: Unrestricted delegatecall
        (success, ) = _target.delegatecall(_data);
    }

    /**
     * @notice VULNERABILITY 6: Weak randomness
     * @dev Uses block.timestamp for "random" rewards
     */
    function claimRandomReward() public {
        // VULNERABLE: Predictable randomness
        uint256 reward = uint256(
            keccak256(abi.encodePacked(block.timestamp, msg.sender))
        ) % 1000;
        balanceOf[msg.sender] += reward;
        totalSupply += reward;
    }

    /**
     * @notice VULNERABILITY 7: Unprotected self-destruct
     * @dev Anyone can destroy the contract
     */
    function destroy(address payable _recipient) public {
        // VULNERABLE: No access control on selfdestruct
        selfdestruct(_recipient);
    }
}

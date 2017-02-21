pragma solidity ^0.4.6;

contract token {
	function transferFrom(address sender, address receiver, uint amount) returns(bool success){}
	function burn() {}
}

/**
*	Crowdsale for Edgeless Tokens.
*	Author: Julia Altenried
**/
contract Crowdsale {
    /* if successful, the funds will be retrievable by this address */
	address public beneficiary = 0;
	/* if the funding goal is not reached, investors may withdraw their funds */
	uint public fundingGoal = 50000000;
	/* the maximum amount of tokens to be sold */
	uint public maxGoal = 440000000;
	/* how much has been raised by crowdale (in ETH) */
	uint public amountRaised;
	/* the start date of the crowdsale */
	uint public start = 1488294000;
	/* the number of tokens already sold */
	uint public tokensSold;
	/* there are different prices in different time intervals */
	uint[4] public deadlines = [1488297600, 1488902400, 1489507200,1490112000];

	/* Prices before a deadline is reached */
	uint[4] public prices = [833333333333333, 909090909090909,952380952380952, 1000000000000000];
	/* the address of the token contract */
	token public tokenReward;
	/* the balances (in ETH) of all investors */
	mapping(address => uint256) public balanceOf;
	bool fundingGoalReached = false;
	bool crowdsaleClosed = false;
	/* notifying transfers and the success of the crowdsale*/
	event GoalReached(address beneficiary, uint amountRaised);
	event FundTransfer(address backer, uint amount, bool isContribution);

    /* Time override */
	uint _current;

    /*  initialization, set the token address */
    function Crowdsale(address _beneficiary) {
        beneficiary = _beneficiary;
    }

    /* Build circular references between contracts. */
    function setToken(address _token) public {
        if(msg.sender != beneficiary) throw;
        if(address(tokenReward) != 0) throw; // No double set
        tokenReward = token(_token);
    }

    /** Override current() for testing */
    function current() public returns (uint) {
        return _current;
    }

    function setCurrent(uint __current) {
        _current = __current;
    }

    /* whenever anyone sends funds to a contract, the corresponding amount of tokens is transfered to the sender
    	if the crowdsale started and hasn't been closed already and the maxGoal wasn't reached yet.*/
    function () payable{
        invest(msg.sender);
    }

    /* if the crowdsale started and hasn't been closed already and the maxGoal wasn't reached yet tokens are transfered to the receiver.
    to be called in case the msg.sender is not the one to receive the tokens.*/
    function invest(address receiver) payable{
    	uint amount = msg.value;
        uint numTokens = amount / getPrice();

        if (crowdsaleClosed||current()<start||tokensSold+numTokens>maxGoal) throw;
        balanceOf[receiver] += amount;
        amountRaised += amount;
        tokensSold+=numTokens;
        if(!tokenReward.transferFrom(beneficiary, receiver, numTokens)) throw;
        FundTransfer(receiver, amount, true);
    }

    /* looks up the current token price */
    function getPrice() constant returns (uint256 price){
        for(var i = 0; i < deadlines.length; i++)
            if(current()<deadlines[i])
                return prices[i];
        return prices[prices.length-1];//should never be returned, but to be sure to not divide by 0
    }

    modifier afterDeadline() { if (current() >= deadlines[deadlines.length-1]) _; }

    /* checks if the goal or time limit has been reached and ends the campaign */
    function checkGoalReached() afterDeadline {
        if (tokensSold >= fundingGoal){
            fundingGoalReached = true;
            GoalReached(beneficiary, amountRaised);
        }
        crowdsaleClosed = true;
    }

    /* allows the beneficiary and/or the funders to withdraw their funds */
    function safeWithdrawal() afterDeadline {
        // if the goal hasn't been reached, investors may withdraw their funds
        if (!fundingGoalReached) {
            uint amount = balanceOf[msg.sender];
            balanceOf[msg.sender] = 0;
            if (amount > 0) {
                if (msg.sender.send(amount)) {
                    FundTransfer(msg.sender, amount, false);
                } else {
                    balanceOf[msg.sender] = amount;
                }
            }
        }
        //if the goal has benn reached and the beneficiary himself is the sender, he may withdraw everything
        if (fundingGoalReached && beneficiary == msg.sender) {
            tokenReward.burn(); //burn remaining tokens but 60 000 000
            if (beneficiary.send(amountRaised)) {
                FundTransfer(beneficiary, amountRaised, false);
            } else {
                //If we fail to send the funds to beneficiary, unlock funders balance
                fundingGoalReached = false;
            }
        }
    }
}

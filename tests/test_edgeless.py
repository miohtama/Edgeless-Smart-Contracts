"""Edgeless ICO test suite."""
import datetime

import pytest
from ethereum.tester import TransactionFailed
from web3 import Web3
from web3.contract import Contract
from web3.utils.currency import to_wei


@pytest.fixture
def crowdsale(chain, beneficiary, multisig) -> Contract:
    """Create crowdsale contract."""
    args = [beneficiary, multisig]
    contract = chain.get_contract('Crowdsale', deploy_args=args)
    return contract


@pytest.fixture
def token(chain, crowdsale, beneficiary) -> Contract:
    """Create ICO contract."""
    #owner = crowdsale.address
    args = [beneficiary]  # Owner set
    contract = chain.get_contract('EdgelessToken', deploy_args=args)
    assert crowdsale.call().tokenReward() == '0x0000000000000000000000000000000000000000'
    crowdsale.transact({"from": beneficiary}).setToken(contract.address)
    assert crowdsale.call().tokenReward() != '0x0000000000000000000000000000000000000000'

    # Allow crowdsale contract to issue out tokens
    contract.transact({"from": beneficiary}).approve(crowdsale.address, 500000000)

    return contract


@pytest.fixture
def customer(accounts) -> str:
    """Get a customer address."""
    return accounts[1]


@pytest.fixture
def customer_2(accounts) -> str:
    """Get another customer address."""
    return accounts[2]

@pytest.fixture
def beneficiary(accounts) -> str:
    """The team control address."""
    return accounts[3]


@pytest.fixture
def multisig(accounts) -> str:
    """The team multisig address."""
    return accounts[4]


@pytest.fixture
def start():
    """Match in TestableCrowdsale."""
    return 1488294000


@pytest.fixture
def end():
    """Match in TestableCrowdsale."""
    return 1490112000


@pytest.fixture
def open_crowdsale(crowdsale, token, start):
    """We live in time when crowdsale is open"""
    crowdsale.transact().setCurrent(start + 1)
    token.transact().setCurrent(start + 1)
    return crowdsale


@pytest.fixture
def early_crowdsale(crowdsale, token, start):
    """We live in time when crowdsale is not yet open"""
    crowdsale.transact().setCurrent(start-1)
    token.transact().setCurrent(start-1)
    return crowdsale


@pytest.fixture
def finished_crowdsale(crowdsale, token, end):
    """We live in time when crowdsale is done."""
    crowdsale.transact().setCurrent(end+1)
    token.transact().setCurrent(end+1)
    return crowdsale


def test_initialized(crowdsale: Contract, token: Contract, beneficiary: str):
    assert token.call().balanceOf(beneficiary) == 500000000
    assert token.call().totalSupply() == 500000000
    assert token.call().owner() == beneficiary
    assert token.call().allowance(beneficiary, crowdsale.address) == 500000000
    assert token.call().owner() == crowdsale.call().beneficiary()


def test_get_price_tiers(crowdsale: Contract, token: Contract, customer: str, web3: Web3):
    """Test out different price tiers"""

    deadlines = [1488297600, 1488902400, 1489507200, 1490112000]
    prices = [833333333333333, 909090909090909, 952380952380952, 1000000000000000]

    for idx, deadline in enumerate(deadlines):
        crowdsale.transact().setCurrent(deadline-1)
        assert crowdsale.call().getPrice() == prices[idx]

    # Post last deadline prcie
    crowdsale.transact().setCurrent(deadlines[-1] + 1)
    assert crowdsale.call().getPrice() == 1000000000000000


def test_dates(crowdsale: Contract, token: Contract, customer: str, web3: Web3):
    """See dates match - read output by eye."""

    deadlines = [1488297600, 1488902400, 1489507200, 1490112000]

    for idx, deadline in enumerate(deadlines):
        print("Deadline {} is {}".format(idx, datetime.datetime.fromtimestamp(deadline)))

    print("Token is transferable {}".format(datetime.datetime.fromtimestamp(token.call().startTime())))

    assert token.call().startTime() == deadlines[-1]


def test_buy_tokens(open_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3):
    """Sending in ETH succesful buys tokens."""

    web3.eth.sendTransaction({
        "from": customer,
        "to": open_crowdsale.address,
        "value": to_wei(20, "ether"),
        "gas": 250000,
    })

    events = token.pastEvents("Transfer").get()
    assert len(events) == 1
    e = events[0]
    assert e["args"]["to"] == customer
    assert e["args"]["from"] == beneficiary
    assert e["args"]["value"] == 24000


def test_buy_rounded_to_zero(open_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3):
    """We buy very small amount that is rounded to zero."""

    web3.eth.sendTransaction({
        "from": customer,
        "to": open_crowdsale.address,
        "value": 1,  # 1 wei
        "gas": 250000,
    })

    events = token.pastEvents("Transfer").get()
    assert len(events) == 1
    e = events[0]
    assert e["args"]["to"] == customer
    assert e["args"]["from"] == beneficiary
    assert e["args"]["value"] == 0


def test_buy_too_many_tokens(open_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3):
    """Try to outbuy the system."""

    buy_everything_amount = open_crowdsale.call().getPrice() * open_crowdsale.call().maxGoal()

    web3.eth.sendTransaction({
        "from": customer,
        "to": open_crowdsale.address,
        "value": buy_everything_amount,
        "gas": 200000,
    })

    events = token.pastEvents("Transfer").get()
    assert len(events) == 1
    e = events[0]
    assert e["args"]["to"] == customer
    assert e["args"]["from"] == beneficiary
    assert e["args"]["value"] == open_crowdsale.call().maxGoal()

    # Cannot buy a single token more
    with pytest.raises(TransactionFailed):
        web3.eth.sendTransaction({
            "from": customer,
            "to": open_crowdsale.address,
            "value": open_crowdsale.call().getPrice(),  # Minimum value to buy one token
            "gas": 200000,
        })


def test_buy_tokens_too_early(early_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3):
    """Somebody tries to shortcut in the queue."""
    with pytest.raises(TransactionFailed):
        web3.eth.sendTransaction({
            "from": customer,
            "to": early_crowdsale.address,
            "value": to_wei(20, "ether"),
            "gas": 250000,
        })


def test_call_check_goal_reached_too_early(open_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3):
    """Make sure afterDeadline works."""
    open_crowdsale.transact().checkGoalReached()
    assert open_crowdsale.call().crowdsaleClosed() == False


def test_call_check_goal_reached_after_close(finished_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3):
    """Make sure afterDeadline works."""
    finished_crowdsale.transact().checkGoalReached()
    assert finished_crowdsale.call().crowdsaleClosed() == True

def test_check_goal_not_reached(open_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3, end: int):
    """We don't reach our goal."""

    # Buy some tokens
    web3.eth.sendTransaction({
        "from": customer,
        "to": open_crowdsale.address,
        "value": to_wei(20, "ether"),
        "gas": 250000,
    })

    open_crowdsale.transact().setCurrent(end + 1)
    finished_crowdsale = open_crowdsale

    finished_crowdsale.transact().checkGoalReached()
    assert finished_crowdsale.call().fundingGoalReached() == False


def test_check_burn(open_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3, end: int):
    """Make sure we burn properly."""

    minimum_goal_value = open_crowdsale.call().fundingGoal() * open_crowdsale.call().getPrice()

    # Buy some tokens
    web3.eth.sendTransaction({
        "from": customer,
        "to": open_crowdsale.address,
        "value": minimum_goal_value,
        "gas": 250000,
    })

    # Close
    token.transact().setCurrent(end + 1)
    finished_token = token

    open_crowdsale.transact().setCurrent(end + 1)
    finished_crowdsale = open_crowdsale

    # Supply before burn
    supply_before_burn = token.call().totalSupply()
    owner_before_burn = token.call().balanceOf(beneficiary)
    assert not finished_token.call().burned()

    # Trigger goal check
    finished_crowdsale.transact().checkGoalReached()
    assert finished_crowdsale.call().fundingGoalReached()

    # We burned succesfully
    assert finished_token.call().burned()
    assert token.call().totalSupply() < supply_before_burn
    assert token.call().balanceOf(beneficiary) < owner_before_burn

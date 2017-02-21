"""Edgeless ICO test suite."""

import pytest
from ethereum.tester import TransactionFailed
from web3 import Web3
from web3.contract import Contract
from web3.utils.currency import to_wei



@pytest.fixture
def crowdsale(chain, beneficiary) -> Contract:
    """Create crowdsale contract."""
    args = [beneficiary]
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
    """The team multisig address."""
    return accounts[3]


@pytest.fixture
def start():
    """Match in TestableCrowdsale."""
    return 1488294000


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


def test_buy_tokens_too_early(early_crowdsale: Contract, token: Contract, customer: str, beneficiary: str, web3: Web3):

    with pytest.raises(TransactionFailed):
        web3.eth.sendTransaction({
            "from": customer,
            "to": early_crowdsale.address,
            "value": to_wei(20, "ether"),
            "gas": 250000,
        })

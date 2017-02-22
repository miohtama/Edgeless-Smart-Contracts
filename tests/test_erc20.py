import pytest
from ethereum.tester import TransactionFailed
from web3.contract import Contract


def test_erc20_interface(erc20_token: Contract, token_owner: str, empty_address: str):
    """See we satisfy ERC-20 interface.

    Test against a deployed contract where one account holder has tokens.

    https://github.com/OpenZeppelin/zeppelin-solidity/blob/master/contracts/token/ERC20.sol
    """

    token = erc20_token
    assert token.call().totalSupply() > 0
    assert token.call().balanceOf(token_owner) > 0
    assert token.call().balanceOf(empty_address) == 0
    assert token.call().allowance(token_owner, empty_address) == 0

    # Event
    # We follow OpenZeppelin - in the ERO20 issue names are _from, _to, _value
    transfer = token._find_matching_event_abi("Transfer", ["from", "to", "value"])
    assert transfer

    approval = token._find_matching_event_abi("Approval", ["owner", "spender", "value"])
    assert approval


def test_erc20_transfer(erc20_token: Contract, token_owner: str, empty_address: str):
    """We can do ERC-20 transfer."""

    token = erc20_token
    amount = 5000
    initial_balance = token.call().balanceOf(token_owner)

    token.transact({"from": token_owner}).transfer(empty_address, amount)

    assert token.call().balanceOf(token_owner) == initial_balance - amount
    assert token.call().balanceOf(empty_address) == amount

    events = token.pastEvents("Transfer").get()
    assert len(events) == 1
    e = events[0]
    assert e["args"]["to"] == empty_address
    assert e["args"]["from"] == token_owner
    assert e["args"]["value"] == amount


def test_erc20_not_enough_balance(erc20_token: Contract, token_owner: str, empty_address: str):
    """We cannot transfer more than we have."""

    token = erc20_token
    initial_balance = token.call().balanceOf(token_owner)
    amount = initial_balance + 1

    with pytest.raises(TransactionFailed):
        token.transact({"from": token_owner}).transfer(empty_address, amount)


def test_erc20_transfer_with_allowance(erc20_token: Contract, token_owner: str, empty_address: str, allowed_party):
    """Transfer tokens with allowance approval."""

    token = erc20_token
    amount = 5000
    initial_balance = token.call().balanceOf(token_owner)
    token.transact({"from": token_owner}).approve(allowed_party, amount)
    assert token.call().allowance(token_owner, allowed_party) == amount

    events = token.pastEvents("Approval").get()
    assert len(events) > 0  # Edgeless gets 2 events, because one is needed to construct token
    e = events[-1]
    assert e["args"]["owner"] == token_owner
    assert e["args"]["spender"] == allowed_party
    assert e["args"]["value"] == amount

    token.transact({"from": allowed_party}).transferFrom(token_owner, empty_address, amount)

    events = token.pastEvents("Transfer").get()
    assert len(events) == 1
    e = events[0]
    assert e["args"]["to"] == empty_address
    assert e["args"]["from"] == token_owner
    assert e["args"]["value"] == amount

    assert token.call().balanceOf(token_owner) == initial_balance - amount
    assert token.call().balanceOf(empty_address) == amount
    assert token.call().allowance(token_owner, allowed_party) == 0


def test_erc20_transfer_with_allowance_too_much(erc20_token: Contract, token_owner: str, empty_address: str, allowed_party):
    """We are cannot transfer more than our allowance."""

    token = erc20_token
    amount = 5000
    token.transact({"from": token_owner}).approve(allowed_party, amount)

    with pytest.raises(TransactionFailed):
        token.transact({"from": allowed_party}).transferFrom(token_owner, empty_address, amount+1)

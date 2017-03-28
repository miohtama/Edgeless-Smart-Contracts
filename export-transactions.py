"""Export transactions from crowdsale."""

import csv
import datetime
from collections import OrderedDict

from eth_utils import from_wei

from populus import Project


def main():

    address_data = OrderedDict()

    project = Project()
    with project.get_chain("mainnet") as chain:
        Crowdsale = chain.get_contract_factory('OriginalCrowdsale')
        crowdsale = Crowdsale(address="0x362bb67f7fdbdd0dbba4bce16da6a284cf484ed6")

        # We have configured non-default timeout as pastEvents() takes long
        web3 = chain.web3

        # Sanity check
        print("Block number is", web3.eth.blockNumber)
        print("Amount raised is", crowdsale.call().amountRaised())

        print("Getting events")
        events = crowdsale.pastEvents("FundTransfer").get(only_changes=False)

        # Merge several transactions from the same address to one
        print("Analysing results")
        for e in events:
            address = e["args"]["backer"]
            data = address_data.get(address, {})

            # TODO: Not sure if we get events in block order
            timestamp = web3.eth.getBlock(e["blockNumber"])["timestamp"]
            current_first = data.get("first_payment", 99999999999999999)
            if timestamp < current_first:
                data["first_payment"] = timestamp

            data["raised"] = data.get("raised", 0) + from_wei(e["args"]["amount"], "ether")
            address_data[address] = data

        print("Writing results")
        with open('transactions.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for address, data in address_data.items():
                timestamp = data["first_payment"]
                dt = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
                writer.writerow([address, dt.isoformat(), str(data["raised"])])

        print("OK")


if __name__ == "__main__":
    main()

.. highlight:: shell

.. contents:: :local:

Introduction
============

This repository contains smart contracts for Edgeless project.

* Crowdsale contract

* Token contract

* Populus based test suite

About Populus
^^^^^^^^^^^^^

`Populus <http://populus.readthedocs.io/>`_ is a tool for the Ethereum blockchain and smart contract management. The project uses Populus internally. Populus is a Python based suite for

* Running arbitrary Ethereum chains (mainnet, testnet, private testnet)

* Running test suites against Solidity smart contracts

Installation
============

Preface
^^^^^^^

Instructions are written in OSX and Linux in mind.

Experience needed

* Basic command line usage

* Basic Github usage

Setting up - OSX
^^^^^^^^^^^^^^^^

Packages needed

* `Populus native dependencies <http://populus.readthedocs.io/en/latest/quickstart.html>`_

Get Solidity compiler. For OSX:

.. code-block:: console

    # Install solcjs using npm (JavaScript port of solc)
    sudo npm install -g solc@0.4.8

    # Symlink solcjs as solc, so that Populus finds it as default solc command
    sudo ln -f -s `which solcjs` /usr/local/bin/solc

Clone this repository from Github.

Python 3.x required. `See installing Python <https://www.python.org/downloads/>`_.

.. code-block:: console

     python3.5 --version
     Python 3.5.2

Create virtualenv for Python package management in the project root folder (same as where ``setup.py`` is):

.. code-block:: console

    python3.5 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Setting up - Ubuntu Linux 14.04
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install dependencies:

.. code-block:: console

    sudo add-apt-repository ppa:fkrull/deadsnakes
    sudo apt-get update
    sudo apt-get install -y python3.5 python3.5-dev
    sudo apt install -y git build-essential python3-setuptools libssl-dev

`Install Go Ethereum <https://github.com/ethereum/go-ethereum/wiki/Installation-Instructions-for-Ubuntu>`_:

.. code-block:: console

    sudo apt-get install software-properties-common
    sudo add-apt-repository -y ppa:ethereum/ethereum
    sudo apt-get update
    sudo apt-get install -y ethereum solc

Then:

.. code-block:: console

    git clone # ...
    cd Smart-Contracts
    python3.5 -m venv --without-pip venv
    source venv/bin/activate
    curl https://bootstrap.pypa.io/get-pip.py | python
    pip install -r requirements.txt
    pip install -e .

Usage
=====

Running tests
^^^^^^^^^^^^^

Running tests::

    py.test tests

Run a specific test::

    py.test tests -k test_get_price_tiers

Deploying on testnet
^^^^^^^^^^^^^^^^^^^^

Compile contracts::

    populus compile

Deploy::

    python testnet_deploy.py


Deploying on a private testnet
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a local chain::

    populus chain run local

Compile contracts::

    populus compile

Deploy::

    python private_testnet_deploy.py

Run private testnet::


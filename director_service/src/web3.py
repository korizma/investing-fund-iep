from web3 import Web3
import os
import json

# ganache
GANACHE_URL = os.environ['GANACHE_PROVIDER_URL']
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

server_acc = w3.eth.accounts[0]


CONTRACT_ABI = 'solidity/VotingContract.abi'
CONTRACT_BIN = 'solidity/VotingContract.bin'

def get_bin_and_abi():
    abi = None
    bin = None
    with open(CONTRACT_ABI) as f:
        abi = json.load(f)
    with open(CONTRACT_BIN) as f:
        bin = f.read()
    
    bin = '0x' + bin

    return bin, abi
    

def get_contract_to_deploy():
    bytecode, abi = get_bin_and_abi()

    contract_vt = w3.eth.contract(
        abi=abi,
        bytecode=bytecode,
    )

    return contract_vt, abi


def deploy_and_get_response(voters):

    contract_vt, contract_abi = get_contract_to_deploy()

    tx_hash = contract_vt.constructor(voters).transact({"from": server_acc})

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    contract_address = tx_receipt.contractAddress

    response = {
        'approve_transaction': {
            'to': contract_address,
            'data': contract_vt.encodeABI(fn_name="vote", args=[True]),
        },
        'reject_transaction': {
            'to': contract_address,
            'data': contract_vt.encodeABI(fn_name="vote", args=[False]),
        }
    }

    return contract_address, contract_abi, response

def get_contract(contract_address, contact_abi):
    return w3.eth.contract(address=contract_address, abi=contact_abi)
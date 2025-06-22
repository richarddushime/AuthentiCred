# blockchain/clients/besu.py
# Similar structure to polygon.py but for Hyperledger Besu
import json
import os
from web3 import Web3
from django.conf import settings
from ..exceptions import BlockchainError

class BesuClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
        if not self.w3.is_connected():
            raise BlockchainError("Failed to connect to Besu node")
        
        self.chain_id = settings.BESU_CHAIN_ID
        self.private_key = settings.BLOCKCHAIN_OPERATOR_KEY
        self.sender_address = settings.BLOCKCHAIN_OPERATOR_ADDRESS
    
    def _load_contract(self, contract_name):
        abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abis', f'{contract_name}.json')
        with open(abi_path) as f:
            abi = json.load(f)
        
        address = getattr(settings, f"{contract_name.upper()}_ADDRESS")
        return self.w3.eth.contract(address=address, abi=abi)
    
    def execute_contract_function(self, contract_name, function_name, *args):
        contract = self._load_contract(contract_name)
        nonce = self.w3.eth.get_transaction_count(self.sender_address)
        
        tx = contract.functions[function_name](*args).build_transaction({
            'chainId': self.chain_id,
            'gas': 500000,
            'nonce': nonce,
            'from': self.sender_address,
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash.hex()
    
    def call_contract_function(self, contract_name, function_name, *args):
        contract = self._load_contract(contract_name)
        return contract.functions[function_name](*args).call()
    
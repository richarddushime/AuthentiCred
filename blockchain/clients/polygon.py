# Blockchain node connectors
# blockchain/clients/polygon.py
import json
import os
from web3 import Web3
from django.conf import settings
from ..exceptions import BlockchainError

class PolygonClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
        if not self.w3.is_connected():
            raise BlockchainError("Failed to connect to Polygon node")
        
        self.chain_id = settings.POLYGON_CHAIN_ID
        self.private_key = settings.BLOCKCHAIN_OPERATOR_KEY
        self.sender_address = settings.BLOCKCHAIN_OPERATOR_ADDRESS
    
    def _load_contract(self, contract_name):
        """Load contract ABI and address from settings"""
        # Load ABI
        abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abis', f'{contract_name}.json')
        with open(abi_path) as f:
            abi = json.load(f)
        
        # Get contract address from settings
        address = getattr(settings, f"{contract_name.upper()}_ADDRESS")
        return self.w3.eth.contract(address=address, abi=abi)
    
    def execute_contract_function(self, contract_name, function_name, *args):
        """Execute a write function on a smart contract"""
        contract = self._load_contract(contract_name)
        nonce = self.w3.eth.get_transaction_count(self.sender_address)
        
        # Build transaction
        tx = contract.functions[function_name](*args).build_transaction({
            'chainId': self.chain_id,
            'gas': 500000,  # Adjust based on contract requirements
            'gasPrice': self.w3.to_wei('30', 'gwei'),
            'nonce': nonce,
            'from': self.sender_address,
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash.hex()
    
    def call_contract_function(self, contract_name, function_name, *args):
        """Call a read function on a smart contract"""
        contract = self._load_contract(contract_name)
        return contract.functions[function_name](*args).call()
    
    def get_transaction_receipt(self, tx_hash):
        """Get transaction receipt from blockchain"""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return receipt
        except Exception as e:
            raise BlockchainError(f"Failed to get transaction receipt: {str(e)}")
    
# blockchain/clients/ganache.py
import json
import os
from web3 import Web3
from django.conf import settings
from ..exceptions import BlockchainError

class GanacheClient:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
        if not self.w3.is_connected():
            raise BlockchainError("Failed to connect to Ganache node")
        
        # Get the actual chain ID from the blockchain instead of using settings
        self.chain_id = self.w3.eth.chain_id
        
        # Handle private key format - ensure it's in the correct format for Web3.py
        private_key = settings.BLOCKCHAIN_OPERATOR_KEY
        if private_key.startswith('0x'):
            private_key = private_key[2:]
        # Ensure private key is exactly 64 characters (32 bytes)
        if len(private_key) != 64:
            raise BlockchainError(f"Invalid private key length: {len(private_key)} (expected 64)")
        # Add 0x prefix back for Web3.py
        self.private_key = f"0x{private_key}"
        
        self.sender_address = settings.BLOCKCHAIN_OPERATOR_ADDRESS
    
    def _load_contract(self, contract_name):
        """Load contract ABI and address from settings"""
        # Load ABI
        abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abis', f'{contract_name}.json')
        with open(abi_path) as f:
            contract_data = json.load(f)
        
        # Extract ABI from the contract data
        if isinstance(contract_data, dict) and 'abi' in contract_data:
            abi = contract_data['abi']
        else:
            abi = contract_data
        
        # Get contract address
        address = getattr(settings, f"{contract_name.upper()}_ADDRESS")
        if not address:
            raise BlockchainError(f"Contract address not set for {contract_name}")
        
        # Validate address format
        if not self.w3.is_address(address):
            raise BlockchainError(f"Invalid contract address for {contract_name}: {address}")
            
        return self.w3.eth.contract(address=address, abi=abi)
    
    def execute_contract_function(self, contract_name, function_name, *args):
        """Execute a write function on a smart contract"""
        try:
            contract = self._load_contract(contract_name)
            nonce = self.w3.eth.get_transaction_count(self.sender_address)
            
            # Convert string arguments to proper format for bytes32
            formatted_args = []
            for arg in args:
                if isinstance(arg, str) and len(arg) == 64 and all(c in '0123456789abcdefABCDEF' for c in arg):
                    # Convert hex string to bytes32
                    formatted_args.append(bytes.fromhex(arg))
                else:
                    formatted_args.append(arg)
            
            # Build transaction
            tx = contract.functions[function_name](*formatted_args).build_transaction({
                'chainId': self.chain_id,
                'gas': 500000,
                'gasPrice': self.w3.to_wei('20', 'gwei'),
                'nonce': nonce,
                'from': self.sender_address,
            })
            
            # For Ganache, if we're using a different account than the configured one,
            # we can use send_transaction directly since accounts are unlocked
            if self.sender_address != settings.BLOCKCHAIN_OPERATOR_ADDRESS:
                # Use the unlocked account directly
                tx_hash = self.w3.eth.send_transaction(tx)
            else:
                # Use the configured private key
                signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
                
                # Get the raw transaction bytes
                try:
                    # Try the standard attribute first
                    raw_tx = signed_tx.rawTransaction
                except AttributeError:
                    try:
                        # Try alternative attribute name
                        raw_tx = signed_tx.raw_transaction
                    except AttributeError:
                        # For newer Web3.py versions, try to serialize the transaction
                        if hasattr(signed_tx, 'rawTransaction'):
                            raw_tx = signed_tx.rawTransaction
                        elif hasattr(signed_tx, 'raw_transaction'):
                            raw_tx = signed_tx.raw_transaction
                        else:
                            raise BlockchainError(f"Could not access raw transaction from signed transaction. Available attributes: {dir(signed_tx)}")
                
                tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            
            return tx_hash.hex()
            
        except Exception as e:
            raise BlockchainError(f"Contract execution failed for {contract_name}.{function_name}: {str(e)}") from e
    
    def call_contract_function(self, contract_name, function_name, *args):
        """Call a read function on a smart contract"""
        try:
            contract = self._load_contract(contract_name)
            
            # Convert string arguments to proper format for bytes32
            formatted_args = []
            for arg in args:
                if isinstance(arg, str) and len(arg) == 64 and all(c in '0123456789abcdefABCDEF' for c in arg):
                    # Convert hex string to bytes32
                    formatted_args.append(bytes.fromhex(arg))
                else:
                    formatted_args.append(arg)
            
            return contract.functions[function_name](*formatted_args).call()
        except Exception as e:
            raise BlockchainError(f"Contract call failed for {contract_name}.{function_name}: {str(e)}")
    
    def get_transaction_receipt(self, tx_hash):
        """Get transaction receipt from blockchain"""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return receipt
        except Exception as e:
            raise BlockchainError(f"Failed to get transaction receipt: {str(e)}")
    
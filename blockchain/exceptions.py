# blockchain/exceptions.py
class BlockchainError(Exception):
    """Base exception for blockchain operations"""
    pass

class TransactionFailedError(BlockchainError):
    """Raised when a blockchain transaction fails"""
    pass

class ContractCallError(BlockchainError):
    """Raised when a smart contract call fails"""
    pass

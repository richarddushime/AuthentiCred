# blockchain/utils/merkle_tree.py
from hashlib import sha256
from typing import List

def compute_sha256(data: str) -> str:
    return sha256(data.encode('utf-8')).hexdigest()

class MerkleTree:
    def __init__(self, leaves: List[str]):
        self.leaves = [compute_sha256(leaf) for leaf in leaves]
        self.tree = self.build_tree(self.leaves)
    
    def build_tree(self, leaves: List[str]) -> List[List[str]]:
        tree = [leaves]
        current_level = leaves
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = left + right
                next_level.append(compute_sha256(combined))
            tree.append(next_level)
            current_level = next_level
        
        return tree
    
    def get_root(self) -> str:
        return self.tree[-1][0] if self.tree else None
    
    def get_proof(self, index: int) -> List[str]:
        proof = []
        idx = index
        
        for level in self.tree[:-1]:
            if idx % 2 == 1:  # Left node
                proof.append(level[idx - 1])
            elif idx + 1 < len(level):  # Right node exists
                proof.append(level[idx + 1])
            idx //= 2
        
        return proof
    
    @staticmethod
    def verify_proof(root: str, leaf: str, proof: List[str]) -> bool:
        current = compute_sha256(leaf)
        
        for node in proof:
            if current < node:
                current = compute_sha256(current + node)
            else:
                current = compute_sha256(node + current)
        
        return current == root
    
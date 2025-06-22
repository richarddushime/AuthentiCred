// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract CredentialAnchor {
    mapping(bytes32 => bool) public anchoredProofs;
    event ProofAnchored(bytes32 proofHash);

    function storeProof(bytes32 proofHash) public {
        anchoredProofs[proofHash] = true;
        emit ProofAnchored(proofHash);
    }

    function verifyProof(bytes32 proofHash) public view returns (bool) {
        return anchoredProofs[proofHash];
    }
}
// This contract allows for the anchoring of cryptographic proofs, such as hashes of credentials or other data.
// It provides a way to store and verify these proofs on the blockchain, ensuring their integrity and authenticity.
// The `storeProof` function allows anyone to anchor a proof by providing its hash, while the `verifyProof` function checks if a given proof hash has been anchored.
// The `ProofAnchored` event is emitted whenever a proof is successfully anchored, allowing for tracking and monitoring of anchored proofs on the blockchain.
// This contract can be used in conjunction with other contracts, such as a DID registry or trust registry, to enhance the security and trustworthiness of digital credentials and identities on the blockchain.
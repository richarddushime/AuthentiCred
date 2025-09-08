// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract DIDRegistry {
    mapping(string => string) public didToPublicKey;
    event DIDRegistered(string indexed did, string publicKey);

    function registerDID(string memory did, string memory publicKey) public {
        require(bytes(did).length > 0, "DID cannot be empty");
        require(bytes(publicKey).length > 0, "Public key cannot be empty");
        require(bytes(didToPublicKey[did]).length == 0, "DID already registered");
        
        didToPublicKey[did] = publicKey;
        emit DIDRegistered(did, publicKey);
    }

    function resolveDID(string memory did) public view returns (string memory) {
        return didToPublicKey[did];
    }
}

// Decentralisez Identifiers 
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

// This contract serves as a decentralized identifier (DID) registry, allowing users to register and resolve DIDs.
// The `registerDID` function allows anyone to register a DID along with its associated public key,
// ensuring that the DID is unique and not already registered.
// The `resolveDID` function allows anyone to retrieve the public key associated with a given DID.
// The `DIDRegistered` event is emitted whenever a DID is successfully registered,
// providing a way to track and monitor registrations on the blockchain. 

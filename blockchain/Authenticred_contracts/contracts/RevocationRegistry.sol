// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract RevocationRegistry {
    mapping(string => bool) public revokedCredentials;
    event CredentialRevoked(string indexed credentialId);

    function revokeCredential(string memory credentialId) public {
        revokedCredentials[credentialId] = true;
        emit CredentialRevoked(credentialId);
    }

    function isRevoked(string memory credentialId) public view returns (bool) {
        return revokedCredentials[credentialId];
    }
}
// This contract allows for the revocation of credentials by their unique identifiers.
// It provides a way to mark credentials as revoked, ensuring that they can no longer be considered valid.
// The `revokeCredential` function allows anyone to revoke a credential by providing its ID, while the `isRevoked` function checks if a given credential ID has been revoked.           
// The `CredentialRevoked` event is emitted whenever a credential is successfully revoked, allowing for tracking and monitoring of revoked credentials on the blockchain.
// This contract can be used in conjunction with other contracts, such as a DID registry or trust

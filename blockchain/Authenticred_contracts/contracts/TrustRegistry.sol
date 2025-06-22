// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

contract TrustRegistry {
    mapping(string => bool) public trustedIssuers;
    event TrustStatusUpdated(string indexed did, bool trusted);

    function setIssuerTrustStatus(string memory did, bool trusted) public {
        trustedIssuers[did] = trusted;
        emit TrustStatusUpdated(did, trusted);
    }

    function isIssuerTrusted(string memory did) public view returns (bool) {
        return trustedIssuers[did];
    }
}

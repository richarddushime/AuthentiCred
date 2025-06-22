const DIDRegistry = artifacts.require("DIDRegistry");
const TrustRegistry = artifacts.require("TrustRegistry");
const CredentialAnchor = artifacts.require("CredentialAnchor");
const RevocationRegistry = artifacts.require("RevocationRegistry");

module.exports = function(deployer) {
  deployer.deploy(DIDRegistry);
  deployer.deploy(TrustRegistry);
  deployer.deploy(CredentialAnchor);
  deployer.deploy(RevocationRegistry);
};
// This migration script deploys the four smart contracts: DIDRegistry, TrustRegistry, CredentialAnchor, and RevocationRegistry.

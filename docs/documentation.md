## **OVERVIEW**

AuthentiCred is a **Django-based web application** that implements a **decentralized credential verification system** using blockchain technology and W3C Verifiable Credentials (VCs). The system consists of four main Django apps:

### **Core Apps:**
1. **`users`** - User management and authentication
2. **`blockchain`** - Smart contract interactions and blockchain operations
3. **`credentials`** - Credential issuance, management, and verification
4. **`wallets`** - Digital wallet functionality for credential storage

## **PURPOSE & PROBLEM STATEMENT**

**Problem:** Traditional credential verification is slow, insecure, and fragmented:
- Days to verify credentials vs. seconds
- Paper records easily forged vs. blockchain-anchored tamper-proof records
- Country-specific processes vs. global interoperability
- Institutions control user data vs. user-controlled data
- Multiple transcripts needed vs. one lifelong wallet

**Solution:** AuthentiCred provides:
- **Instant verification** through blockchain anchoring
- **Tamper-proof credentials** using cryptographic signatures
- **Global interoperability** through W3C standards
- **User sovereignty** over personal data
- **Unified credential storage** in digital wallets

## **👥 USER TYPES & ROLES**

The system supports three distinct user types:

1. **STUDENT (Credential Holder)**
   - Receives and stores credentials in digital wallet
   - Shares credentials via QR codes or secure links
   - Controls what data to share with verifiers

2. **INSTITUTION (Credential Issuer)**
   - Creates credential schemas and templates
   - Issues digitally signed verifiable credentials
   - Registers DIDs on blockchain for trust verification
   - Can revoke credentials when necessary

3. **EMPLOYER (Credential Verifier)**
   - Verifies credential authenticity instantly
   - Scans QR codes or uses verification portal
   - No need to contact institutions directly

## **BLOCKCHAIN INTEGRATION**

### **Smart Contracts (Solidity):**

1. **`DIDRegistry.sol`**
   - Maps DIDs to public keys
   - Enables decentralized identity resolution
   - Stores institution identities

2. **`TrustRegistry.sol`**
   - Manages trusted issuer status
   - Controls which institutions can issue valid credentials
   - Enables trust verification

3. **`CredentialAnchor.sol`**
   - Anchors credential hashes to blockchain
   - Provides immutable proof of credential existence
   - Enables instant verification

4. **`RevocationRegistry.sol`**
   - Tracks revoked credentials
   - Prevents use of invalid credentials
   - Maintains credential lifecycle

### **Blockchain Network:**
- **Development:** Ganache (localhost:7545)
- **Production:** Supports Polygon, Besu(ongoing)
- **Chain ID:** 1337 (Ganache default)

## **CRYPTOGRAPHIC SECURITY**

### **Key Management:**
- **SECP256k1** elliptic curve cryptography
- **Ed25519** for DID operations
- **Encrypted storage** of private keys using Django encrypted fields
- **Key derivation** from private keys for public key generation

### **Credential Signing:**
- **ECDSA signatures** with SHA-256 hashing
- **JSON-LD canonicalization** for consistent signing
- **JWS (JSON Web Signatures)** format for proofs
- **Verifiable Credential** standard compliance

## **DATA MODELS**

### **User Management:**
```python
User (AbstractUser)
├── user_type (STUDENT/INSTITUTION/EMPLOYER)
├── did (Decentralized Identifier)
├── public_key (Cryptographic public key)
└── InstitutionProfile (for institutions)
    ├── name, description, website
    ├── accreditation_proof
    └── is_trusted (blockchain verified)
```

### **Credential System:**
```python
CredentialSchema
├── name, version, type
├── fields (JSON structure)
└── created_by (User)

Credential
├── vc_json (W3C Verifiable Credential)
├── issuer, holder (Users)
├── schema (CredentialSchema)
├── status (DRAFT/ISSUED/REVOKED/EXPIRED)
└── vc_hash (SHA-256 of credential)
```

### **Wallet System:**
```python
Wallet
├── user (OneToOne)
├── private_key (Encrypted)
└── wallet_credentials (ManyToMany)

WalletCredential
├── wallet, credential
└── is_archived (Boolean)
```

### **Blockchain Tracking:**
```python
OnChainTransaction
├── tx_hash, status, transaction_type
├── metadata (JSON)
└── block_number

DIDRegistration
├── did, public_key
├── institution (InstitutionProfile)
└── transaction (OnChainTransaction)
```

## **TECHNICAL STACK**

### **Backend:**
- **Django** - Web framework
- **Postgresql** - Database (production: PostgreSQL)
- **Celery** - Background task processing
- **Redis** - Message broker and result backend
- **Web3.py** - Blockchain interaction

### **Frontend:**
- **Bootstrap 5.3.0** - UI framework
- **Bootstrap Icons** - Icon library
- **QR Code generation** - For credential sharing
- **Responsive design** - Mobile-friendly interface

### **Blockchain:**
- **Solidity 0.8.19** - Smart contract language
- **Truffle** - Development framework
- **Ganache** - Local blockchain
- **Web3.js** - Contract interaction

### **Security:**
- **Django encrypted fields** - Sensitive data encryption
- **CSRF protection** - Cross-site request forgery prevention
- **Session management** - Secure user sessions
- **Field-level encryption** - Private key protection

## **WORKFLOWS**

### **1. Institution Registration:**
1. Institution registers with platform
2. DID and key pair generated automatically
3. DID registered on blockchain via smart contract
4. Trust status updated after confirmation
5. Institution can now issue credentials

### **2. Credential Issuance:**
1. Institution creates credential schema
2. Fills credential data for student
3. System generates W3C Verifiable Credential
4. Credential signed with institution's private key
5. Credential hash anchored to blockchain
6. Credential added to student's wallet

### **3. Credential Verification:**
1. Verifier scans QR code or enters credential hash
2. System checks multiple verification factors:
   - Cryptographic signature validity
   - Blockchain anchoring confirmation
   - Issuer trust status
   - Revocation status
   - Expiration date
3. Instant verification result provided

### **4. Credential Sharing:**
1. Student selects credential from wallet
2. System generates shareable link and QR code
3. Verifier accesses credential via link
4. Real-time verification performed
5. No sensitive data stored on verifier's system

## **DEPLOYMENT & OPERATIONS**

### **Background Tasks (Celery):**
- **Transaction monitoring** - Every 10 seconds
- **DID confirmation processing** - Every 5 minutes
- **Retry mechanisms** - For failed blockchain operations
- **Status updates** - Transaction confirmation tracking

### **Management Commands:**
- **`deploy_contracts`** - Deploy smart contracts to blockchain
- **`create_missing_wallets`** - Generate wallets for existing users

### **Configuration:**
- **Environment-based settings** - Development vs. production
- **Contract addresses** - Stored in Django settings
- **Network configuration** - RPC URLs and chain IDs
- **Encryption keys** - Fernet key for field encryption

## **VERIFICATION PROCESS**

The system performs comprehensive credential verification:

1. **Cryptographic Verification:**
   - Validates ECDSA signature using issuer's public key
   - Verifies JSON-LD canonicalization
   - Checks proof structure and format

2. **Blockchain Verification:**
   - Confirms credential hash is anchored on blockchain
   - Verifies issuer DID is registered and trusted
   - Checks credential is not revoked

3. **Temporal Verification:**
   - Validates credential hasn't expired
   - Checks issuance date is reasonable

4. **Trust Verification:**
   - Confirms issuer is in trusted registry
   - Validates institution accreditation

## **KEY INNOVATIONS**

1. **Self-Sovereign Identity** - Users control their credentials
2. **Instant Verification** - No manual institution contact needed
3. **Global Interoperability** - W3C standards compliance
4. **Tamper-Proof Records** - Blockchain anchoring
5. **Privacy-Preserving** - Selective disclosure of credential data
6. **Lifelong Credential Storage** - Single wallet for all credentials

## **USE CASES**

- **Academic Institutions** - Issue degrees, certificates, transcripts
- **Professional Training** - Certify skills and competencies
- **Employment Verification** - Instant background checks
- **Immigration Services** - Verify educational qualifications
- **Scholarship Programs** - Validate applicant credentials
- **Licensing Boards** - Verify professional qualifications

This is a **production-ready, enterprise-grade solution** for digital credential management that addresses real-world problems in academic and professional credential verification while maintaining security, privacy, and user sovereignty.

# AuthentiCred Blockchain Interaction Sequence Diagram

## Credential Verification Flow

```mermaid
sequenceDiagram
    participant User as User (Frontend)
    participant Django as Django Backend
    participant SmartContract as Smart Contracts
    participant Ethereum as Ethereum Network
    participant Wallet as Digital Wallet

    Note over User, Ethereum: Credential Issuance Flow
    
    User->>Django: Register as Issuer/Student
    Django->>SmartContract: Register DID (Decentralized Identity)
    SmartContract->>Ethereum: Transaction mined
    Ethereum-->>SmartContract: Block confirmation
    SmartContract-->>Django: DID registered event
    Django-->>User: Registration successful

    Note over User, Ethereum: Credential Creation & Issuance
    
    User->>Django: Create credential template
    Django->>Django: Generate credential hash (SHA256)
    Django->>Django: Create cryptographic proof
    Django->>SmartContract: Anchor credential hash
    SmartContract->>Ethereum: Transaction mined
    Ethereum-->>SmartContract: Block confirmation
    SmartContract-->>Django: Credential anchored event
    Django->>Wallet: Store encrypted credential
    Django-->>User: Credential issued successfully

    Note over User, Ethereum: Credential Verification Flow
    
    User->>Django: Share credential (QR/Link)
    Django->>Django: Extract credential data
    Django->>Django: Verify cryptographic signature
    Django->>SmartContract: Check credential anchor
    SmartContract->>Ethereum: Query blockchain state
    Ethereum-->>SmartContract: Credential status
    SmartContract-->>Django: Verification result
    Django->>SmartContract: Check issuer trust
    SmartContract->>Ethereum: Query trust registry
    Ethereum-->>SmartContract: Trust status
    SmartContract-->>Django: Trust verification result
    Django-->>User: Verification complete (2 seconds)

    Note over User, Ethereum: Credential Revocation Flow
    
    User->>Django: Request credential revocation
    Django->>SmartContract: Revoke credential
    SmartContract->>Ethereum: Transaction mined
    Ethereum-->>SmartContract: Block confirmation
    SmartContract-->>Django: Revocation confirmed event
    Django-->>User: Credential revoked successfully
```

## Smart Contract Interaction Flow

```mermaid
sequenceDiagram
    participant Django as Django Backend
    participant DIDRegistry as DID Registry Contract
    participant TrustRegistry as Trust Registry Contract
    participant CredentialAnchor as Credential Anchor Contract
    participant RevocationRegistry as Revocation Registry Contract
    participant Ethereum as Ethereum Network

    Note over Django, Ethereum: Smart Contract Deployment & Setup
    
    Django->>DIDRegistry: Deploy DID Registry
    DIDRegistry->>Ethereum: Contract deployment transaction
    Ethereum-->>DIDRegistry: Contract address confirmed
    
    Django->>TrustRegistry: Deploy Trust Registry
    TrustRegistry->>Ethereum: Contract deployment transaction
    Ethereum-->>TrustRegistry: Contract address confirmed
    
    Django->>CredentialAnchor: Deploy Credential Anchor
    CredentialAnchor->>Ethereum: Contract deployment transaction
    Ethereum-->>CredentialAnchor: Contract address confirmed
    
    Django->>RevocationRegistry: Deploy Revocation Registry
    RevocationRegistry->>Ethereum: Contract deployment transaction
    Ethereum-->>RevocationRegistry: Contract address confirmed

    Note over Django, Ethereum: DID Management
    
    Django->>DIDRegistry: registerDID(did_hash)
    DIDRegistry->>Ethereum: DID registration transaction
    Ethereum-->>DIDRegistry: DID registered event
    
    Django->>DIDRegistry: resolveDID(did_hash)
    DIDRegistry-->>Django: DID owner address

    Note over Django, Ethereum: Trust Management
    
    Django->>TrustRegistry: trustIssuer(issuer_address, trust_score)
    TrustRegistry->>Ethereum: Trust update transaction
    Ethereum-->>TrustRegistry: Issuer trusted event
    
    Django->>TrustRegistry: isIssuerTrusted(issuer_address)
    TrustRegistry-->>Django: Trust status (true/false)

    Note over Django, Ethereum: Credential Management
    
    Django->>CredentialAnchor: anchorCredential(credential_hash)
    CredentialAnchor->>Ethereum: Credential anchoring transaction
    Ethereum-->>CredentialAnchor: Credential anchored event
    
    Django->>CredentialAnchor: verifyCredential(credential_hash)
    CredentialAnchor-->>Django: Anchored status (true/false)

    Note over Django, Ethereum: Revocation Management
    
    Django->>RevocationRegistry: revokeCredential(credential_hash)
    RevocationRegistry->>Ethereum: Revocation transaction
    Ethereum-->>RevocationRegistry: Credential revoked event
    
    Django->>RevocationRegistry: isRevoked(credential_hash)
    RevocationRegistry-->>Django: Revocation status (true/false)
```

## System Architecture Flow

```mermaid
sequenceDiagram
    participant User as End User
    participant Frontend as Frontend (Tailwind CSS)
    participant Django as Django Backend
    participant Database as PostgreSQL Database
    participant Redis as Redis Cache
    participant Celery as Celery Workers
    participant Blockchain as Ethereum Blockchain
    participant SmartContracts as Smart Contracts

    Note over User, SmartContracts: Complete System Architecture
    
    User->>Frontend: Access platform
    Frontend->>Django: API request
    Django->>Database: Query user data
    Database-->>Django: User information
    Django->>Redis: Cache frequently accessed data
    Redis-->>Django: Cached response
    Django-->>Frontend: User dashboard data
    Frontend-->>User: Display user interface

    Note over User, SmartContracts: Credential Workflow
    
    User->>Frontend: Issue credential
    Frontend->>Django: Credential creation request
    Django->>Django: Validate credential data
    Django->>Database: Store credential record
    Django->>Celery: Queue blockchain operation
    Celery->>Blockchain: Deploy smart contract transaction
    Blockchain-->>SmartContracts: Transaction confirmation
    SmartContracts-->>Celery: Contract event
    Celery->>Database: Update credential status
    Django-->>Frontend: Credential issued confirmation
    Frontend-->>User: Success notification

    Note over User, SmartContracts: Verification Workflow
    
    User->>Frontend: Verify credential
    Frontend->>Django: Verification request
    Django->>Database: Retrieve credential data
    Django->>Blockchain: Query smart contract state
    Blockchain-->>SmartContracts: Contract state query
    SmartContracts-->>Django: Verification result
    Django->>Redis: Cache verification result
    Django-->>Frontend: Verification response
    Frontend-->>User: Verification result display
```

## Key Components Description

### **Frontend Layer**
- **Technology**: HTML5, Tailwind CSS, JavaScript
- **Features**: Responsive design, mobile-first approach
- **Components**: User dashboards, credential forms, verification interface

### **Django Backend**
- **Framework**: Django 5.2.5
- **Features**: REST API, authentication, business logic
- **Integration**: Web3.py for blockchain interaction

### **Smart Contracts**
- **DID Registry**: Manages decentralized identities
- **Trust Registry**: Verifies issuer authenticity
- **Credential Anchor**: Stores credential hashes on blockchain
- **Revocation Registry**: Handles credential revocation

### **Blockchain Layer**
- **Network**: Ethereum (Ganache for development)
- **Technology**: Web3.py integration
- **Features**: Real-time transactions, gas optimization

### **Data Flow**
1. **User Interaction**: Frontend receives user input
2. **Backend Processing**: Django validates and processes data
3. **Blockchain Integration**: Smart contracts execute on Ethereum
4. **Confirmation**: Events confirm successful operations
5. **Response**: Results returned to user interface

## Performance Metrics

- **Credential Issuance**: < 5 seconds
- **Verification**: < 2 seconds
- **Blockchain Transaction**: < 30 seconds
- **Database Queries**: < 100ms
- **API Response**: < 200ms

## Security Features

- **Cryptographic**: ECDSA signatures, SHA256 hashing
- **Blockchain**: Immutable credential storage
- **Authentication**: JWT tokens, role-based access
- **Data Protection**: Encryption at rest and in transit

---

*This sequence diagram illustrates the complete flow of the AuthentiCred platform, showing how user interactions flow through the system architecture to provide secure, tamper-proof credential verification.*

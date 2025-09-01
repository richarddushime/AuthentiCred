# AuthentiCred

**Where Technology Meets Trust**

*Blockchain-based credential verification platform for the digital age*

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/richarddushime/AuthentiCred)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Ethereum](https://img.shields.io/badge/Ethereum-3C3C3D?style=for-the-badge&logo=Ethereum&logoColor=white)](https://ethereum.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

## Technology Stack

### Frontend
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Django Templates](https://img.shields.io/badge/Django_Templates-092E20?style=for-the-badge&logo=django&logoColor=white)](https://docs.djangoproject.com/en/stable/topics/templates/)

### Backend
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://celeryproject.org)

### Blockchain
[![Web3.py](https://img.shields.io/badge/Web3.py-F16822?style=for-the-badge&logo=web3&logoColor=white)](https://web3py.readthedocs.io/)
[![Solidity](https://img.shields.io/badge/Solidity-363636?style=for-the-badge&logo=solidity&logoColor=white)](https://soliditylang.org)
[![Ganache](https://img.shields.io/badge/Ganache-5E464D?style=for-the-badge&logo=ganache&logoColor=white)](https://trufflesuite.com/ganache/)
[![Ethereum](https://img.shields.io/badge/Ethereum-3C3C3D?style=for-the-badge&logo=Ethereum&logoColor=white)](https://ethereum.org)

### Security
[![ECDSA](https://img.shields.io/badge/ECDSA-000000?style=for-the-badge&logo=bitcoin&logoColor=white)](https://en.wikipedia.org/wiki/Elliptic_Curve_Digital_Signature_Algorithm)
[![SHA256](https://img.shields.io/badge/SHA256-000000?style=for-the-badge&logo=bitcoin&logoColor=white)](https://en.wikipedia.org/wiki/SHA-2)
[![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)](https://jwt.io)
[![PKI](https://img.shields.io/badge/PKI-000000?style=for-the-badge&logo=key&logoColor=white)](https://en.wikipedia.org/wiki/Public_key_infrastructure)

---

## What is AuthentiCred?

**AuthentiCred** is a revolutionary blockchain-based platform that transforms how educational credentials are issued, verified, and shared. Built on cutting-edge blockchain technology and W3C standards, it provides instant, tamper-proof verification of academic achievements.

![AuthentiCred Platform](images/Home.png)
*The main platform interface showcasing professional design and key features*

### Key Features

- **Cryptographically Secure** - ECDSA signatures and SHA256 hashing
- **Blockchain Anchored** - Immutable credential verification
- **W3C Compliant** - Follows international standards
- **Instant Verification** - Real-time credential validation
- **Beautiful UI** - Modern, responsive design with Tailwind CSS
- **Automated Workflows** - Smart contract-based operations

---

## Technology Stack

### Frontend
- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first styling
- **JavaScript** - Interactive features
- **Django Templates** - Server-side rendering

### Backend
- **Django 5.2.5** - Web framework
- **Python 3.13** - Programming language
- **SQLite/PostgreSQL** - Database systems
- **Celery** - Task queue management

### Blockchain
- **Web3.py** - Ethereum integration
- **Solidity** - Smart contracts
- **Ganache** - Development blockchain
- **Ethereum** - Blockchain platform

### Security
- **ECDSA** - Digital signatures
- **SHA256** - Cryptographic hashing
- **JWT** - Authentication tokens
- **PKI** - Key management

---

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- Ganache (for local blockchain)
- Git

### Platform Overview

![User Authentication](images/loginpage.png)
*Secure login interface with modern authentication*

![Dashboard Interface](images/issuer-dashboard.png)
*Professional dashboard for managing credentials and users*

![Credential Management](images/credentialinformations.png)
*Comprehensive credential management and verification system*

### Installation

```bash
# Clone the repository
git clone https://github.com/richarddushime/AuthentiCred.git
cd AuthentiCred

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd theme
npm install

# Start services
./start.sh
```

### What Happens Next?

1. **Ganache** starts with pre-funded accounts
2. **Smart contracts** deploy automatically
3. **Django server** starts on localhost:8000
4. **Celery workers** begin processing tasks
5. **Blockchain state** restores automatically

### Blockchain Development Environment

![Ganache Interface](images/ganache-tx-creation.png)
*Local blockchain development environment with Ganache*

![Smart Contract Management](images/contracts-ganache.png)
*Smart contract deployment and interaction interface*

---

## Documentation Sections

### [Project Overview](project_report.md)
Complete project documentation with screenshots and visual guides. Perfect for presentations and stakeholder briefings.

### [Technical Architecture](techstacks.md)
Deep dive into blockchain technology, smart contracts, and how everything works together.

### [Technical Documentation](documentation.md)
Comprehensive technical specifications, data models, and system architecture details.

### [Management Commands](management_commands.md)
Essential Django management commands for debugging, fixing, and maintaining the system.

### [Automation Guide](AUTOMATION_README.md)
Complete setup and automation instructions for development and deployment.

---

## Development Workflow

```mermaid
graph TD
    A[Start Development] --> B[Activate Virtual Environment]
    B --> C[Start Ganache]
    C --> D[Deploy Smart Contracts]
    D --> E[Start Django Server]
    E --> F[Start Celery Workers]
    F --> G[Test Credential Flow]
    G --> H[Verify Blockchain State]
    H --> I[Commit & Push Changes]
```

---

## Why Choose AuthentiCred?

### For Institutions
- **Instant Verification** - No more manual credential checks
- **Global Recognition** - W3C standards ensure interoperability
- **Cost Reduction** - Automated processes reduce administrative overhead
- **Enhanced Security** - Blockchain prevents credential forgery

### For Students
- **Portable Credentials** - Access credentials from anywhere
- **Instant Sharing** - Share with employers and institutions instantly
- **Privacy Control** - Selective disclosure of credential information
- **Lifetime Access** - Credentials stored securely forever

### For Verifiers
- **Real-time Verification** - Instant credential validation
- **Trust Assurance** - Cryptographic proof of authenticity
- **Global Access** - Verify credentials from anywhere
- **Cost Efficiency** - No need for manual verification processes

---

## Contributing

We welcome contributions from the community! Whether you're a developer, designer, or blockchain enthusiast, there are many ways to get involved.

- **Report Bugs** - Help us improve by reporting issues
- **Suggest Features** - Share your ideas for new functionality
- **Submit Code** - Contribute code improvements and new features
- **Improve Docs** - Help make our documentation even better
- **Spread the Word** - Share AuthentiCred with your network

See our [Contributing Guide](contributing.md) for more details.

---

## Support & Community

- **GitHub Issues**: [Report bugs and request features](https://github.com/richarddushime/AuthentiCred/issues)
- **Discussions**: [Join community conversations](https://github.com/richarddushime/AuthentiCred/discussions)
- **Wiki**: [Additional resources and guides](https://github.com/richarddushime/AuthentiCred/wiki)
- **Email**: [contact@authenticred.com](mailto:contact@authenticred.com)

---

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/richarddushime/AuthentiCred/blob/main/LICENSE) file for details.

---

**Made with dedication by the AuthentiCred Team**

*Building the future of credential verification, one block at a time*

[Get Started →](project_report.md)

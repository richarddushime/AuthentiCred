# AuthentiCred

*A Simple, Secure, and Global Way to Verify Academic Credentials & Recommendations*

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/richarddushime/AuthentiCred)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Ethereum](https://img.shields.io/badge/Ethereum-3C3C3D?style=for-the-badge&logo=Ethereum&logoColor=white)](https://ethereum.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

## Technology Stacks

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

##  What Is AuthentiCred?

AuthentiCred is an open source platform that makes it **easy**, **fast**, and **secure** to issue, store, and verify academic documents degrees, certificates, training records, and letters of recommendation. Built on **blockchain** technology and W3C **Verifiable Credentials (VCs)**, 

![AuthentiCred Homepage](docs/images/Home.png)
*The main homepage showcasing the platform's professional interface*

## Statement Problem

Today, proving your hard-earned school or job qualifications is a frustrating and inefficient ordeal. Employers face a slow, costly verification process, often resorting to individual calls or emails to each institution to confirm degrees(when needed). This outdated system makes it easy for forged paper and diplomas to slip through the cracks, undermining trust and leading to unqualified hires.
Adding to the chaos, every college and training center operates on different, incompatible systems. This forces students to juggle multiple transcripts and spend valuable time and money repeatedly just to apply for jobs or further education. Even worse, your most sensitive personal qualification data is frequently stored by third parties, leaving it vulnerable and completely out of your control.AuthentiCred revolutionizes this broken system. We empower educational institutions to issue tamper-proof digital certificates on a secure, decentralized network. Students gain a single, intuitive digital wallet to securely store all their academic and professional records. With AuthentiCred, anyone can verify credentials in seconds, without the need to share sensitive personal details.


## Who Can Use It?

- **Issuers**: Schools, universities, training providers  
- **Holders**: Students, alumni, professionals  
- **Verifiers**: Employers, scholarship & grant programs, licensing boards, immigration services  


##  Quick Start (Developers)

### **Automated Setup (Recommended)**
```bash
# Clone the repository
git clone <repository-url>
cd AuthentiCred

# Install dependencies
npm install -g ganache
pip install -r requirements.txt

# Start everything with one command
./start.sh
```

### **Manual Setup**
```bash
# 1. Start Ganache blockchain
ganache --port 7545

# 2. Deploy contracts
python manage.py deploy_contracts

# 3. Start Redis
docker run -d -p 6379:6379 redis

# 4. Run migrations
python manage.py migrate

# 5. Start Celery worker
celery -A AuthentiCred worker --loglevel=info

# 6. Start Django server
python manage.py runserver
```

## Documentation

For comprehensive documentation, visit our [Documentation Hub](docs/index.md) which includes:

- **[Academic Report](docs/authenticred_academic_report.md)** - Complete project report with technical details
- **[Technical Documentation](docs/authenticred_technical_documentation.md)** - Implementation guide
- **[Technology Stack](docs/authenticred_technology_stack.md)** - Architecture overview
- **[Management Commands](docs/authenticred_management_commands.md)** - Django commands
- **[Contributing Guide](docs/authenticred_contributing_guide.md)** - How to contribute
- **[Automation Setup](docs/authenticred_automation_setup.md)** - CI/CD configuration
- **[API Reference](docs/authenticred_api_reference.md)** - API documentation

For detailed setup instructions, see [Automation Setup](docs/authenticred_automation_setup.md)

##  Getting Started

1. **For Institutions**  
   - Register as an issuer  
   - Define and issue credential templates  
   - Integrate with student management systems  

2. **For Learners**  
   - Download the AuthentiCred Wallet App  
   - Add your issued credentials  
   - Share with anyone via QR code or secure link  

3. **For Verifiers**  
   - Use the AuthentiCred Verification Portal  
   - Scan or paste the VC link  
   - Instantly confirm authenticity  

##  Development

### **Available Scripts**
- `./start.sh` - Start all services (automated)
- `./stop.sh` - Stop all services
- `python start_authenticred.py` - Advanced automation with options

### **Network Configuration**
- **Ganache**: `http://127.0.0.1:8545`
- **Django**: `http://127.0.0.1:8000`
- **Metamask**: Connect to `Localhost 8545`

### Blockchain Development Environment
![Ganache Interface](docs/images/ganache-tx-creation.png)
*Ganache blockchain interface for local development and testing*

![Blockchain Transactions](docs/images/transactions-ganache.png)
*Real-time blockchain transaction monitoring and management*

**Ready to secure and simplify your credential journey?**  
> Visit [AuthentiCred](https://authenticred-8a4c46d20c03.herokuapp.com/) or contact us 

For more read the Documentation [here](https://richarddushime.github.io/AuthentiCred/authenticred_technical_documentation/)

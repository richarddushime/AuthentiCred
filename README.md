# AuthentiCred

> **A Simple, Secure, and Global Way to Verify Academic Credentials & Recommendations**

---

##  What Is AuthentiCred?

AuthentiCred is an open source platform that makes it **easy**, **fast**, and **secure** to issue, store, and verify academic documents degrees, certificates, training records, and letters of recommendation. Built on **blockchain** technology and W3C **Verifiable Credentials (VCs)**, 

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
ganache --port 8545

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

For detailed setup instructions, see [AUTOMATION_README.md](https://richarddushime.github.io/AuthentiCred/AUTOMATION_README/)

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

> **Ready to secure and simplify your credential journey?**  
> Visit [AuthentiCred](https://authenticred-8a4c46d20c03.herokuapp.com/) or contact us 

For more read the Documentation [here](https://richarddushime.github.io/AuthentiCred/documentation/)

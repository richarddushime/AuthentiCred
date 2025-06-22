# blockchain/tasks.py
from celery import shared_task
from celery.schedules import crontab
from celery.exceptions import MaxRetriesExceededError
from .services import BlockchainService
from .models import OnChainTransaction
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def register_did_task(self, did, public_key):
    try:
        service = BlockchainService()
        tx_hash = service.register_did(did, public_key)
        return tx_hash
    except Exception as e:
        logger.warning(f"Retrying DID registration for {did} (attempt {self.request.retries})")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(f"DID registration failed after retries: {did}")
            # Update transaction status to failed
            OnChainTransaction.objects.filter(
                tx_hash=self.request.id, 
                transaction_type='DID_REGISTRATION'
            ).update(status='FAILED')
            raise

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def anchor_credential_task(self, vc_hash):
    try:
        service = BlockchainService()
        tx_hash = service.anchor_credential(vc_hash)
        return tx_hash
    except Exception as e:
        logger.warning(f"Retrying credential anchoring for {vc_hash} (attempt {self.request.retries})")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(f"Credential anchoring failed after retries: {vc_hash}")
            OnChainTransaction.objects.filter(
                tx_hash=self.request.id, 
                transaction_type='CREDENTIAL_ANCHORING'
            ).update(status='FAILED')
            raise

@shared_task
def monitor_transactions():
    """Periodic task to check transaction statuses"""
    from web3 import Web3
    from django.conf import settings
    
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
    pending_txs = OnChainTransaction.objects.filter(status='PENDING')
    
    for tx in pending_txs:
        try:
            receipt = w3.eth.get_transaction_receipt(tx.tx_hash)
            if receipt is None:
                continue  # Still pending
                
            if receipt.status == 1:
                tx.status = 'CONFIRMED'
                tx.block_number = receipt.blockNumber
            else:
                tx.status = 'FAILED'
            
            tx.save()
            
        except Exception as e:
            logger.error(f"Error checking tx {tx.tx_hash}: {str(e)}")
            continue

def start_celery_beat():
    """Start Celery beat if not already running"""
    from celery import current_app
    if not current_app.conf.beat_schedule:
        current_app.conf.beat_schedule = settings.CELERY_BEAT_SCHEDULE
        
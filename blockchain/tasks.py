# blockchain/tasks.py
from celery import shared_task
from celery.schedules import crontab
from celery.exceptions import MaxRetriesExceededError

from blockchain import apps

from .exceptions import BlockchainError
from .services import BlockchainService
from django.conf import settings
import logging
from .models import OnChainTransaction, DIDRegistration
from django.utils import timezone


logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def register_did_task(self, did, public_key):
    try:
        service = BlockchainService()
        tx_hash = service.register_did(did, public_key)
        
        # Update the DID registration record with the transaction
        try:
            registration = DIDRegistration.objects.get(did=did, transaction__isnull=True)
            tx = OnChainTransaction.objects.get(tx_hash=tx_hash)
            registration.transaction = tx
            registration.save()
            logger.info(f"DID registration transaction linked: {did} -> {tx_hash}")
        except (DIDRegistration.DoesNotExist, OnChainTransaction.DoesNotExist) as e:
            logger.warning(f"Could not link DID registration to transaction: {e}")
        
        return tx_hash
    except Exception as e:
        logger.warning(f"Retrying DID registration for {did} (attempt {self.request.retries})")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(f"DID registration failed after retries: {did}")
            # Mark DID registration as failed
            try:
                registration = DIDRegistration.objects.get(did=did, transaction__isnull=True)
                registration.trust_updated = False  # Mark as failed
                registration.save()
            except DIDRegistration.DoesNotExist:
                pass
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

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def revoke_credential_task(self, credential_id):
    try:
        service = BlockchainService()
        tx_hash = service.revoke_credential(credential_id)
        return tx_hash
    except Exception as e:
        logger.warning(f"Retrying credential revocation for {credential_id} (attempt {self.request.retries})")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            logger.error(f"Credential revocation failed after retries: {credential_id}")
            raise

@shared_task
def monitor_transactions():
    """Monitor and update transaction statuses every 10 seconds"""
    service = BlockchainService()
    pending_txs = OnChainTransaction.objects.filter(status='PENDING')
    
    for tx in pending_txs:
        try:
            if service.is_transaction_confirmed(tx.tx_hash):
                tx.status = 'CONFIRMED'
                tx.updated_at = timezone.now()
                tx.save()
                logger.info(f"Transaction confirmed: {tx.tx_hash}")
        except Exception as e:
            logger.error(f"Error checking transaction {tx.tx_hash}: {str(e)}")
            # Mark as failed after multiple attempts?
            # tx.status = 'FAILED'
            # tx.save()

@shared_task
def process_did_registration_confirmation():
    """Process confirmed DID registrations every 5 minutes"""
    service = BlockchainService()
    pending_registrations = DIDRegistration.objects.filter(
        transaction__status='CONFIRMED',
        trust_updated=False
    ).select_related('transaction', 'institution')
    
    for registration in pending_registrations:
        try:
            # Update trust status on blockchain
            trust_tx = service.update_issuer_trust_status(registration.did)
            
            # Update local state
            registration.trust_updated = True
            registration.save()
            
            # Update institution profile
            institution = registration.institution
            institution.is_trusted = True
            institution.save()
            
            logger.info(f"Trust status updated for {registration.did}: {trust_tx.tx_hash}")
        except Exception as e:
            logger.error(f"Failed to update trust status for {registration.did}: {str(e)}")


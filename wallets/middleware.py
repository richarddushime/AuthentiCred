# wallets/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class WalletCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Import models inside the method to avoid startup issues
            from wallets.models import Wallet
            from wallets.utils import generate_key_pair
            
            if not hasattr(request.user, 'wallet'):
                # Create wallet if missing
                private_key, public_key = generate_key_pair()
                Wallet.objects.create(user=request.user, private_key=private_key)
                request.user.public_key = public_key
                request.user.save()
                
        response = self.get_response(request)
        return response
    
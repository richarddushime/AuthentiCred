# wallets/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from wallets.models import Wallet

class WalletCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not hasattr(request.user, 'wallet'):
                # Create wallet if missing
                from wallets.utils import generate_key_pair
                private_key, public_key = generate_key_pair()
                Wallet.objects.create(user=request.user, private_key=private_key)
                request.user.public_key = public_key
                request.user.save()
                
        response = self.get_response(request)
        return response
    
import os
import requests
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def initiate_payment(request):
    if request.method == 'POST':
        data = request.POST
        booking_reference = data.get('booking_reference')
        amount = float(data.get('amount'))

        # Create Payment record with Pending status
        payment = Payment.objects.create(
            booking_reference=booking_reference,
            amount=amount,
            status='Pending'
        )

        # Prepare Chapa API request
        headers = {
            'Authorization': f"Bearer {os.getenv('CHAPA_SECRET_KEY')}",
            'Content-Type': 'application/json',
        }

        payload = {
            "amount": amount,
            "email": data.get('email'),  # collect user email
            "callback_url": "http://localhost:8000/api/verify_payment/",  # your verification endpoint
            "reference": booking_reference,
            "currency": "NGN",
            # Add other optional fields if needed
        }

        response = requests.post('https://api.chapa.co/v1/initialize', json=payload, headers=headers)
        res_data = response.json()

        if response.status_code == 200 and res_data.get('status') == 'success':
            # Store transaction ID
            payment.transaction_id = res_data['data']['transaction']['id']
            payment.save()
            # Send payment link to user
            payment_url = res_data['data']['payment_url']
            return JsonResponse({'payment_url': payment_url, 'status': 'Pending'})
        else:
            payment.status = 'Failed'
            payment.save()
            return JsonResponse({'error': 'Failed to initiate payment', 'details': res_data}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def verify_payment(request):
    if request.method == 'POST':
        reference = request.POST.get('reference')
        # Fetch the payment record
        try:
            payment = Payment.objects.get(booking_reference=reference)
        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Payment not found'}, status=404)

        headers = {
            'Authorization': f"Bearer {os.getenv('CHAPA_SECRET_KEY')}",
        }

        response = requests.get(f'https://api.chapa.co/v1/transaction/verify/{payment.transaction_id}', headers=headers)
        res_data = response.json()

        if response.status_code == 200:
            status = res_data['data']['status']
            if status == 'success':
                payment.status = 'Completed'
                payment.save()
                # Trigger email notification here (see next)
                return JsonResponse({'status': 'Payment successful'})
            else:
                payment.status = 'Failed'
                payment.save()
                return JsonResponse({'status': 'Payment failed'})
        else:
            return JsonResponse({'error': 'Verification failed', 'details': res_data}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

class ListingView(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Listing instances.
    """
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally restricts the returned listings to those created by the authenticated user.
        """
        user = self.request.user
        if user.is_authenticated:
            return Listing.objects.filter(host=user).order_by('-created_at')
        return Listing.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BookingView(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Booking instances.
    Only returns bookings made by the currently authenticated user.
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

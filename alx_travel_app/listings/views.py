from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Listing, Booking
from .serializers import ListingSerializer, BookingSerializer

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

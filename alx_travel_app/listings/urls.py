from django.urls import path, include
from rest_framework import routers
from .views import ListingView, BookingView, verify_payment, initiate_payment

router = routers.DefaultRouter()
router.register(r"listings", ListingView, basename="listing")
router.register(r"bookings", BookingView, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
    path('verify_payment/', verify_payment, name='verify_payment'),
    path('initiate_payment/', initiate_payment, name='initiate_payment'),
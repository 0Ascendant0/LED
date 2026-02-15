from django.contrib import admin
from .models import (
    AccommodationBooking,
    ActivityTemplate,
    AirportTransfer,
    BookedActivity,
    Client,
    ClientPayments,
    CustomUser,
    FlightBooking,
    
    TravelContract,
    TravelRequirements,
    Traveler,
)

admin.site.register(CustomUser)
admin.site.register(Client)
admin.site.register(TravelContract)
admin.site.register(Traveler)
admin.site.register(ClientPayments)
admin.site.register(TravelRequirements)
admin.site.register(ActivityTemplate)
admin.site.register(BookedActivity)
admin.site.register(AccommodationBooking)
admin.site.register(FlightBooking)
admin.site.register(AirportTransfer)

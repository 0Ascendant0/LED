from django.contrib import admin
from .models import (
    ActivityTemplate,
    BookedActivity,
    Client,
    ClientPayments,
    CustomUser,
    SupplierPayments,
    Suppliers,
    TravelContract,
    TravelRequirements,
    Traveler,
)

admin.site.register(CustomUser)
admin.site.register(Client)
admin.site.register(TravelContract)
admin.site.register(Traveler)
admin.site.register(ClientPayments)
admin.site.register(Suppliers)
admin.site.register(TravelRequirements)
admin.site.register(ActivityTemplate)
admin.site.register(BookedActivity)
admin.site.register(SupplierPayments)

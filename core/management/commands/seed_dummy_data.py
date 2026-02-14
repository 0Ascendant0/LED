from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    ActivityTemplate,
    BookedActivity,
    Client,
    ClientPayments,
    SupplierPayments,
    Suppliers,
    TravelContract,
    Traveler,
    TravelRequirements,
)


class Command(BaseCommand):
    help = "Seed dummy records for all non-user models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing non-user records before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            SupplierPayments.objects.all().delete()
            BookedActivity.objects.all().delete()
            TravelRequirements.objects.all().delete()
            Traveler.objects.all().delete()
            ClientPayments.objects.all().delete()
            ActivityTemplate.objects.all().delete()
            TravelContract.objects.all().delete()
            Suppliers.objects.all().delete()
            Client.objects.all().delete()
            self.stdout.write(self.style.WARNING("Existing non-user records deleted."))

        clients = [
            Client.objects.create(
                first_name="John",
                last_name="Doe",
                phone="+263771000001",
                email="john.doe@example.com",
            ),
            Client.objects.create(
                first_name="Jane",
                last_name="Moyo",
                phone="+263771000002",
                email="jane.moyo@example.com",
            ),
            Client.objects.create(
                first_name="Tariro",
                last_name="Ncube",
                phone="+263771000003",
                email="tariro.ncube@example.com",
            ),
        ]

        suppliers = [
            Suppliers.objects.create(
                name="SkyWings",
                supplier_type="flight",
                phone="+263242700001",
                email="ops@skywings.test",
            ),
            Suppliers.objects.create(
                name="Grand Safari Lodge",
                supplier_type="accommodation",
                phone="+263242700002",
                email="bookings@grand-safari.test",
            ),
            Suppliers.objects.create(
                name="WildTracks Adventures",
                supplier_type="activity",
                phone="+263242700003",
                email="hello@wildtracks.test",
            ),
        ]

        activities = [
            ActivityTemplate.objects.create(
                name="Victoria Falls Tour",
                supplier=suppliers[2],
                description="Guided day tour with transfers.",
                price_adult=Decimal("120.00"),
                price_child=Decimal("80.00"),
                price_infant=Decimal("0.00"),
            ),
            ActivityTemplate.objects.create(
                name="Chobe Day Trip",
                supplier=suppliers[2],
                description="Cross-border safari experience.",
                price_adult=Decimal("210.00"),
                price_child=Decimal("150.00"),
                price_infant=Decimal("0.00"),
            ),
        ]

        today = date.today()
        contracts = []
        for index, client in enumerate(clients):
            departure = today + timedelta(days=20 + index * 7)
            contract = TravelContract.objects.create(
                client=client,
                destination=["Cape Town", "Dubai", "Paris"][index],
                departure_date=departure,
                return_date=departure + timedelta(days=7),
                total_package_price=Decimal(["2500.00", "3200.00", "4100.00"][index]),
                final_payment_due_date=departure - timedelta(days=5),
                contract_signed_date=today - timedelta(days=10 - index),
                status=["incomplete_payment", "paid_not_settled", "fully_settled"][index],
            )
            contracts.append(contract)

        for index, contract in enumerate(contracts):
            Traveler.objects.create(
                contract=contract,
                first_name=contract.client.first_name,
                last_name=contract.client.last_name,
                traveller_type="adult",
                price=Decimal("900.00"),
            )
            Traveler.objects.create(
                contract=contract,
                first_name=f"{contract.client.first_name} Jr",
                last_name=contract.client.last_name,
                traveller_type="child",
                price=Decimal("600.00"),
            )

            ClientPayments.objects.create(
                contract=contract,
                payment_number=1,
                receipt_number=f"RCPT-{today:%Y%m%d}-{index + 1}",
                amount_paid=Decimal("500.00"),
                payment_date=today - timedelta(days=2),
            )

            TravelRequirements.objects.create(
                contract=contract,
                requirement_type="passport",
                is_required=True,
                is_submitted=index > 0,
            )
            TravelRequirements.objects.create(
                contract=contract,
                requirement_type="visa",
                is_required=True,
                is_submitted=index == 2,
            )

            booked_activity = BookedActivity.objects.create(
                contract=contract,
                activity=activities[index % len(activities)],
                quantity_adult=1,
                quantity_child=1,
                quantity_infant=0,
                total_price=Decimal("0.00"),
            )

            SupplierPayments.objects.create(
                supplier=booked_activity.activity.supplier,
                booked_activity=booked_activity,
                amount_paid=Decimal("300.00"),
                payment_date=today - timedelta(days=1),
                reference_number=f"SUP-{today:%Y%m%d}-{index + 1}",
            )

        self.stdout.write(self.style.SUCCESS("Dummy data created for all non-user models."))

from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AccommodationBooking, Client, CustomUser, TravelContract, TravelRequirements


def make_client(first_name="Test", last_name="Client"):
    return Client.objects.create(
        first_name=first_name,
        last_name=last_name,
        national_id_or_passport_number=f"{first_name}-{last_name}-ID",
        phone="263771234567",
        email=f"{first_name.lower()}.{last_name.lower()}@example.com",
    )


def make_contract(client, **overrides):
    payload = {
        "client": client,
        "destination": "Cape Town",
        "departure_date": date(2026, 4, 10),
        "return_date": date(2026, 4, 18),
        "final_payment_due_date": date(2026, 4, 5),
        "contract_signed_date": date(2026, 3, 20),
        "has_flight_included": False,
        "has_airport_transfer": False,
        "has_travel_insurance": False,
        "airport_transfer_price": "0.00",
    }
    payload.update(overrides)
    return TravelContract.objects.create(**payload)


class RequirementStatusApiTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            password="pass12345",
            role="admin",
            is_active=True,
        )
        self.viewer = CustomUser.objects.create_user(
            email="viewer@example.com",
            password="pass12345",
            role="viewer",
            is_active=True,
        )
        self.client_record = make_client("Req", "Client")
        self.contract = make_contract(self.client_record)
        self.url = reverse("contract_requirement_status", kwargs={"contract_id": self.contract.id})

    def test_get_returns_all_requirement_types_with_defaults(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(TravelRequirements.REQUIREMENT_TYPES))
        for row in response.data:
            self.assertIn("requirement_type", row)
            self.assertIn("requirement_label", row)
            self.assertFalse(row["is_required"])
            self.assertEqual(row["status"], "pending")

    def test_patch_updates_status_and_submission(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            self.url,
            {
                "requirement_type": "passport",
                "is_required": True,
                "status": "submitted",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        requirement = TravelRequirements.objects.get(contract=self.contract, requirement_type="passport")
        self.assertTrue(requirement.is_required)
        self.assertEqual(requirement.status, "submitted")
        self.assertTrue(requirement.is_submitted)

    def test_patch_for_not_required_forces_pending(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            self.url,
            {
                "requirement_type": "visa",
                "is_required": False,
                "status": "submitted",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        requirement = TravelRequirements.objects.get(contract=self.contract, requirement_type="visa")
        self.assertFalse(requirement.is_required)
        self.assertEqual(requirement.status, "pending")
        self.assertFalse(requirement.is_submitted)

    def test_patch_rejects_non_admin(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.patch(
            self.url,
            {
                "requirement_type": "passport_photo",
                "is_required": True,
                "status": "pending",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TravelContractValidationApiTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="validator@example.com",
            password="pass12345",
            role="admin",
            is_active=True,
        )
        self.client.force_authenticate(self.admin)
        self.client_record = make_client("Validation", "User")
        self.url = reverse("travel_contract_list")

    def test_rejects_airport_transfer_when_flight_not_included(self):
        response = self.client.post(
            self.url,
            {
                "client": self.client_record.id,
                "destination": "Nairobi",
                "departure_date": "2026-05-10",
                "return_date": "2026-05-18",
                "final_payment_due_date": "2026-05-01",
                "contract_signed_date": "2026-04-20",
                "has_flight_included": False,
                "has_airport_transfer": True,
                "airport_transfer_price": "30.00",
                "has_travel_insurance": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("has_airport_transfer", response.data)


class AccommodationStatusModelTests(TestCase):
    def test_confirmation_number_drives_status(self):
        contract = make_contract(make_client("Accommodation", "Flow"))

        booking = AccommodationBooking.objects.create(
            contract=contract,
            supplier_name="Harare Hotel",
            check_in_date=date(2026, 6, 2),
            check_out_date=date(2026, 6, 8),
            meal_plan="breakfast",
            room_type="single",
            confirmation_number="",
        )
        self.assertEqual(booking.status, "not_confirmed")

        booking.confirmation_number = "CONF-123"
        booking.save()
        booking.refresh_from_db()
        self.assertEqual(booking.status, "confirmed")

        booking.confirmation_number = ""
        booking.save()
        booking.refresh_from_db()
        self.assertEqual(booking.status, "not_confirmed")


class SupplierChecklistInsuranceApiTests(APITestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            email="insurance-admin@example.com",
            password="pass12345",
            role="admin",
            is_active=True,
        )
        self.client.force_authenticate(self.admin)
        self.client_record = make_client("Insurance", "Client")
        self.contract = make_contract(self.client_record, has_travel_insurance=True)
        self.url = reverse("client_supplier_checklist", kwargs={"pk": self.client_record.id})

    def test_checklist_contains_and_updates_insurance_item(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        insurance_items = [item for item in get_response.data["items"] if item["entity_type"] == "insurance"]
        self.assertEqual(len(insurance_items), 1)
        insurance_item = insurance_items[0]

        patch_response = self.client.patch(
            self.url,
            {
                "items": [
                    {
                        "entity_type": "insurance",
                        "entity_id": str(self.contract.id),
                        "is_paid": True,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        self.contract.refresh_from_db()
        self.assertTrue(self.contract.is_travel_insurance_paid)

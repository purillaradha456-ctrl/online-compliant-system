import unittest
import os
from app import app
from database import init_db, get_db

class ComplaintSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()
        init_db()

    def test_homepage(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Online Grievance", response.data)
        self.assertIn(b"Quick Complaint Tracking", response.data)

    def test_public_tracking(self):
        # Sample seeded complaint: CMP-2026-8812
        response = self.client.get("/track?tracking_id=CMP-2026-8812")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CMP-2026-8812", response.data)
        self.assertIn(b"IT &amp; Network", response.data)

    def test_user_login_and_lodge_complaint(self):
        # 1. Login with demo user
        login_res = self.client.post("/login", data={
            "email": "student@example.com",
            "password": "user123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"User Grievance Dashboard", login_res.data)

        # 2. Lodge a new complaint
        complaint_res = self.client.post("/complaint/new", data={
            "category": "Infrastructure",
            "priority": "High",
            "title": "Broken bench in Lecture Hall 1",
            "location": "Academic Block A, Room 101",
            "description": "The wooden desk bench is fractured and unsafe for students."
        }, follow_redirects=True)
        self.assertEqual(complaint_res.status_code, 200)
        self.assertIn(b"Complaint registered successfully", complaint_res.data)
        self.assertIn(b"Broken bench in Lecture Hall 1", complaint_res.data)

    def test_admin_flow_and_export(self):
        # 1. Login with admin
        login_res = self.client.post("/login", data={
            "email": "admin@system.com",
            "password": "admin123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Administrator Management Dashboard", login_res.data)

        # 2. Access Admin Manage page for CMP-2026-8812
        manage_res = self.client.get("/admin/complaint/CMP-2026-8812")
        self.assertEqual(manage_res.status_code, 200)
        self.assertIn(b"Administrative Action Panel", manage_res.data)

        # 3. Update status to Resolved with admin remark
        update_res = self.client.post("/admin/complaint/CMP-2026-8812", data={
            "status": "Resolved",
            "priority": "High",
            "admin_remark": "Router firmware updated and access point tested successfully."
        }, follow_redirects=True)
        self.assertEqual(update_res.status_code, 200)
        self.assertIn(b"successfully updated", update_res.data)

        # 4. Test CSV Export
        export_res = self.client.get("/admin/export/csv")
        self.assertEqual(export_res.status_code, 200)
        self.assertEqual(export_res.content_type, "text/csv; charset=utf-8")
        self.assertIn(b"Tracking ID", export_res.data)
        self.assertIn(b"CMP-2026-8812", export_res.data)

if __name__ == "__main__":
    unittest.main()

import unittest
from datetime import datetime, timedelta
from app import create_app
from config import TestConfig
from models import db, User, Role, Building, Flat, Resident, Staff, Complaint, ComplaintHistory
from services.complaint_service import ComplaintService
from services.staff_service import StaffService

class ComplaintWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        db.create_all()
        self._seed_test_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _seed_test_data(self):
        # 1. Roles
        admin_role = Role(name='Admin', description='Administrator')
        resident_role = Role(name='Resident', description='Resident')
        db.session.add_all([admin_role, resident_role])
        db.session.commit()

        # 2. Users
        self.admin = User(username='test_admin', email='admin@test.com', role_id=admin_role.id)
        self.admin.set_password('AdminPass123!')

        self.resident1 = User(username='resident_one', email='res1@test.com', role_id=resident_role.id)
        self.resident1.set_password('ResPass123!')

        self.resident2 = User(username='resident_two', email='res2@test.com', role_id=resident_role.id)
        self.resident2.set_password('ResPass123!')

        db.session.add_all([self.admin, self.resident1, self.resident2])
        db.session.commit()

        # 3. Building & Flats
        building = Building(name='Tower A', floors_count=10)
        db.session.add(building)
        db.session.commit()

        self.flat1 = Flat(building_id=building.id, flat_number='A-101', floor_number=1)
        self.flat2 = Flat(building_id=building.id, flat_number='A-102', floor_number=1)
        db.session.add_all([self.flat1, self.flat2])
        db.session.commit()

        # 4. Residents
        res_link1 = Resident(user_id=self.resident1.id, flat_id=self.flat1.id, resident_type='Owner', emergency_contact='9876543210')
        res_link2 = Resident(user_id=self.resident2.id, flat_id=self.flat2.id, resident_type='Tenant', emergency_contact='9876543211')
        db.session.add_all([res_link1, res_link2])
        db.session.commit()

        # 5. Staff Members
        self.electrician = Staff(
            full_name='Ramesh Sharma',
            phone='9876500001',
            department='Electrical',
            designation='Senior Electrician',
            is_active=True
        )
        self.plumber = Staff(
            full_name='Suresh Verma',
            phone='9876500002',
            department='Plumbing',
            designation='Plumber',
            is_active=True
        )
        self.inactive_electrician = Staff(
            full_name='Mahesh Kumar',
            phone='9876500003',
            department='Electrical',
            designation='Junior Electrician',
            is_active=False
        )
        db.session.add_all([self.electrician, self.plumber, self.inactive_electrician])
        db.session.commit()

    def _login(self, username, password):
        return self.client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)

    def _logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    # -------------------------------------------------------------
    # 1. LIFECYCLE TESTS
    # -------------------------------------------------------------
    def test_complaint_initial_state(self):
        """A new complaint starts as Pending and unassigned."""
        complaint, err = ComplaintService.file_complaint(
            title='Leaking Kitchen Tap',
            description='Water is dripping continuously from the tap.',
            category='Plumbing',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        self.assertIsNone(err)
        self.assertEqual(complaint.status, 'Pending')
        self.assertIsNone(complaint.assigned_to_staff_id)
        self.assertIsNone(complaint.resolved_at)

        # Audit history verifies creation
        history = ComplaintHistory.query.filter_by(complaint_id=complaint.id).all()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].action, 'Created')
        self.assertEqual(history[0].new_status, 'Pending')

    def test_assignment_updates_status_to_assigned(self):
        """Admin assigning staff sets status to Assigned."""
        complaint, _ = ComplaintService.file_complaint(
            title='Main MCB Tripping',
            description='Power cuts off repeatedly.',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        success, msg = ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        self.assertTrue(success)
        self.assertEqual(complaint.status, 'Assigned')
        self.assertEqual(complaint.assigned_to_staff_id, self.electrician.id)
        self.assertIsNotNone(complaint.assigned_at)
        self.assertEqual(complaint.assigned_by_user_id, self.admin.id)

    def test_resolution_without_notes_succeeds(self):
        """Resolution notes are optional by default and resolution succeeds when notes are empty."""
        complaint, _ = ComplaintService.file_complaint(
            title='Corridor Light Blinking',
            description='Bulb is flickering.',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)

        # Resolve without notes (empty / whitespace)
        success, msg = ComplaintService.resolve_complaint(complaint.id, resolution_notes='', resolved_by_user_id=self.admin.id)
        self.assertTrue(success)
        self.assertEqual(complaint.status, 'Resolved')
        self.assertIsNotNone(complaint.resolved_at)
        self.assertEqual(complaint.resolved_by_user_id, self.admin.id)

        # Audit history records resolution
        h_resolved = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Resolved').first()
        self.assertIsNotNone(h_resolved)
        self.assertEqual(h_resolved.new_status, 'Resolved')

    def test_resolution_with_notes_stores_notes_and_timestamp(self):
        """Resolution with notes stores them and preserves in history."""
        complaint, _ = ComplaintService.file_complaint(
            title='Broken Drain Pipe',
            description='Water leaking under sink.',
            category='Plumbing',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.plumber.id, admin_user_id=self.admin.id)

        notes = 'Replaced 1.5-inch PVC elbow joint and sealed with Teflon tape.'
        success, _ = ComplaintService.resolve_complaint(complaint.id, resolution_notes=notes, resolved_by_user_id=self.admin.id)
        self.assertTrue(success)
        self.assertEqual(complaint.status, 'Resolved')
        self.assertEqual(complaint.resolution_notes, notes)

        h_resolved = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Resolved').first()
        self.assertIn(notes, h_resolved.notes)

    def test_direct_resolution_from_assigned_state(self):
        """Admin can resolve directly from Assigned without forcing In Progress state."""
        complaint, _ = ComplaintService.file_complaint(
            title='Switch Board Loose',
            description='Socket is coming off wall.',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        self.assertEqual(complaint.status, 'Assigned')

        # Direct resolve without In Progress
        success, _ = ComplaintService.resolve_complaint(complaint.id, resolution_notes='Tightened screws', resolved_by_user_id=self.admin.id)
        self.assertTrue(success)
        self.assertEqual(complaint.status, 'Resolved')

    def test_reopening_sets_status_to_reopened_and_preserves_history(self):
        """Reopening sets status to Reopened (not In Progress) and preserves original resolution."""
        complaint, _ = ComplaintService.file_complaint(
            title='Tap dripping again',
            description='Bathroom tap leaks.',
            category='Plumbing',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.plumber.id, admin_user_id=self.admin.id)
        original_notes = 'Washer replaced initially.'
        ComplaintService.resolve_complaint(complaint.id, resolution_notes=original_notes, resolved_by_user_id=self.admin.id)

        # Reopen complaint
        reopen_reason = 'Dripping restarted this morning.'
        success, msg = ComplaintService.reopen_complaint(complaint.id, reason=reopen_reason, user_id=self.resident1.id)
        self.assertTrue(success)
        self.assertEqual(complaint.status, 'Reopened')
        # Preserves staff assignment
        self.assertEqual(complaint.assigned_to_staff_id, self.plumber.id)

        # Preserves earlier resolution event in history
        h_resolved = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Resolved').first()
        self.assertIsNotNone(h_resolved)
        self.assertEqual(h_resolved.notes, original_notes)

        # Preserves new Reopened event
        h_reopened = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Reopened').first()
        self.assertIsNotNone(h_reopened)
        self.assertEqual(h_reopened.new_status, 'Reopened')
        self.assertIn(reopen_reason, h_reopened.notes)

    def test_reopened_complaint_can_be_resolved_again(self):
        """A reopened complaint can be resolved again and full history is preserved."""
        complaint, _ = ComplaintService.file_complaint(
            title='Door latch jammed',
            description='Lock gets stuck.',
            category='Plumbing',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.plumber.id, admin_user_id=self.admin.id)
        ComplaintService.resolve_complaint(complaint.id, resolution_notes='Lubricated latch', resolved_by_user_id=self.admin.id)
        ComplaintService.reopen_complaint(complaint.id, reason='Still sticking', user_id=self.resident1.id)

        # Resolve again directly from Reopened
        followup_notes = 'Replaced whole locking mechanism.'
        success, _ = ComplaintService.resolve_complaint(complaint.id, resolution_notes=followup_notes, resolved_by_user_id=self.admin.id)
        self.assertTrue(success)
        self.assertEqual(complaint.status, 'Resolved')

        # Verify all actions exist chronologically
        history_actions = [h.action for h in ComplaintHistory.query.filter_by(complaint_id=complaint.id).order_by(ComplaintHistory.created_at.asc()).all()]
        self.assertEqual(history_actions, ['Created', 'Assigned', 'Resolved', 'Reopened', 'Resolved'])

    # -------------------------------------------------------------
    # 2. STAFF ASSIGNMENT VALIDATION TESTS
    # -------------------------------------------------------------
    def test_wrong_department_assignment_rejected(self):
        """Plumbing complaints cannot be assigned to Electrical staff and vice-versa."""
        complaint, _ = ComplaintService.file_complaint(
            title='Pipe burst in bathroom',
            description='Flooding risk.',
            category='Plumbing',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        # Attempt to assign electrician to plumbing complaint
        success, msg = ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        self.assertFalse(success)
        self.assertIn('not eligible', msg)
        self.assertEqual(complaint.status, 'Pending')
        self.assertIsNone(complaint.assigned_to_staff_id)

    def test_inactive_staff_assignment_rejected(self):
        """Inactive staff cannot receive new assignments."""
        complaint, _ = ComplaintService.file_complaint(
            title='Light fixture broken',
            description='Wiring damaged.',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        success, msg = ComplaintService.assign_complaint(complaint.id, self.inactive_electrician.id, admin_user_id=self.admin.id)
        self.assertFalse(success)
        self.assertIn('Inactive', msg)
        self.assertIsNone(complaint.assigned_to_staff_id)

    def test_nonexistent_staff_id_rejected(self):
        """Invalid staff IDs fail safely."""
        complaint, _ = ComplaintService.file_complaint(
            title='Short circuit',
            description='Sparks seen.',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        success, msg = ComplaintService.assign_complaint(complaint.id, 99999, admin_user_id=self.admin.id)
        self.assertFalse(success)
        self.assertIn('does not exist', msg)

    def test_reassignment_updates_metadata_and_records_history(self):
        """Reassigning staff updates assigned staff and records Reassigned history."""
        # Create second active electrician
        electrician2 = Staff(
            full_name='Kavita Sharma',
            phone='9876500004',
            department='Electrical',
            designation='Lead Electrician',
            is_active=True
        )
        db.session.add(electrician2)
        db.session.commit()

        complaint, _ = ComplaintService.file_complaint(
            title='Power outage',
            description='Circuit tripped.',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        self.assertEqual(complaint.assigned_to_staff_id, self.electrician.id)

        # Reassign to second electrician
        success, _ = ComplaintService.assign_complaint(complaint.id, electrician2.id, admin_user_id=self.admin.id)
        self.assertTrue(success)
        self.assertEqual(complaint.assigned_to_staff_id, electrician2.id)

        h_reassigned = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Reassigned').first()
        self.assertIsNotNone(h_reassigned)
        self.assertEqual(h_reassigned.previous_staff_id, self.electrician.id)
        self.assertEqual(h_reassigned.assigned_staff_id, electrician2.id)

    def test_reopen_unassigns_if_assigned_staff_became_inactive(self):
        """If staff member becomes inactive while ticket was resolved, reopening unassigns them."""
        complaint, _ = ComplaintService.file_complaint(
            title='Fuse blown',
            description='Main board fuse blown.',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        ComplaintService.resolve_complaint(complaint.id, resolution_notes='Replaced wire', resolved_by_user_id=self.admin.id)

        # Staff member becomes inactive
        self.electrician.is_active = False
        db.session.commit()

        # Resident reopens
        success, _ = ComplaintService.reopen_complaint(complaint.id, reason='Fuse blown again', user_id=self.resident1.id)
        self.assertTrue(success)
        self.assertEqual(complaint.status, 'Reopened')
        self.assertIsNone(complaint.assigned_to_staff_id, "Inactive staff must be unassigned on reopen")

        h_reopen = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Reopened').first()
        self.assertIn('inactive', h_reopen.notes.lower())

    # -------------------------------------------------------------
    # 3. SECURITY & AUTHORIZATION TESTS
    # -------------------------------------------------------------
    def test_unauthenticated_requests_blocked(self):
        """Logged-out users cannot access complaints or perform actions."""
        res_list = self.client.get('/complaint/')
        self.assertIn(res_list.status_code, [302, 401])

        res_assign = self.client.post('/complaint/assign/1', data={'staff_id': self.electrician.id})
        self.assertIn(res_assign.status_code, [302, 401])

    def test_resident_cannot_assign_staff(self):
        """Residents cannot invoke administrator-only staff assignment."""
        complaint, _ = ComplaintService.file_complaint(
            title='Test ticket',
            description='Test description',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )

        self._login('resident_one', 'ResPass123!')

        # Attempt to assign staff
        res_assign = self.client.post(f'/complaint/assign/{complaint.id}', data={'staff_id': self.electrician.id})
        self.assertIn(res_assign.status_code, [302, 403])
        self.assertIsNone(complaint.assigned_to_staff_id)

    def test_authorized_owner_can_resolve_own_complaint(self):
        """An authorized owner can resolve their own assigned complaint without mandatory notes."""
        complaint, _ = ComplaintService.file_complaint(
            title='Living room switch sparked',
            description='Issue in owner flat A-101',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        self.assertEqual(complaint.status, 'Assigned')

        # Owner logs in and resolves
        self._login('resident_one', 'ResPass123!')
        res_resolve = self.client.post(f'/complaint/resolve/{complaint.id}', data={}, follow_redirects=True)
        self.assertEqual(res_resolve.status_code, 200)

        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'Resolved')
        self.assertEqual(complaint.resolved_by_user_id, self.resident1.id)
        self.assertIsNotNone(complaint.resolved_at)

        # Audit history identifies resident actor
        h_res = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Resolved').first()
        self.assertIsNotNone(h_res)
        self.assertEqual(h_res.changed_by_user_id, self.resident1.id)
        self.assertIn('resident_one', h_res.notes)

    def test_authorized_tenant_can_resolve_own_complaint(self):
        """An authorized tenant can resolve their own assigned complaint."""
        # Flat A-102 has tenant resident2
        complaint, _ = ComplaintService.file_complaint(
            title='Geyser water cold',
            description='Issue in tenant flat A-102',
            category='Electrical',
            flat_id=self.flat2.id,
            created_by_user_id=self.resident2.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)

        # Tenant logs in and resolves
        self._login('resident_two', 'ResPass123!')
        res_resolve = self.client.post(f'/complaint/resolve/{complaint.id}', data={}, follow_redirects=True)
        self.assertEqual(res_resolve.status_code, 200)

        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'Resolved')
        self.assertEqual(complaint.resolved_by_user_id, self.resident2.id)

    def test_unrelated_resident_cannot_resolve_other_complaint(self):
        """A resident cannot resolve another resident's complaint (strictly rejected with 403)."""
        complaint, _ = ComplaintService.file_complaint(
            title='Flat A-101 Issue',
            description='Belongs to Flat A-101',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)

        # Resident 2 (Flat A-102) logs in and attempts to resolve Flat A-101 complaint
        self._login('resident_two', 'ResPass123!')
        res_resolve = self.client.post(f'/complaint/resolve/{complaint.id}', data={})
        self.assertIn(res_resolve.status_code, [302, 403])

        db.session.refresh(complaint)
        self.assertNotEqual(complaint.status, 'Resolved')
        self.assertEqual(complaint.status, 'Assigned')

    def test_admin_can_resolve_as_fallback(self):
        """Administrator can resolve complaints as a fallback when resident does not click button."""
        complaint, _ = ComplaintService.file_complaint(
            title='Balcony Light Repaired',
            description='Reported by resident',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)

        self._login('test_admin', 'AdminPass123!')
        res_admin = self.client.post(f'/complaint/resolve/{complaint.id}', data={'resolution_notes': 'Admin confirmed complete with worker'}, follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)

        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'Resolved')
        self.assertEqual(complaint.resolved_by_user_id, self.admin.id)

    def test_unassigned_pending_complaint_cannot_be_resolved(self):
        """Unassigned pending complaints cannot be resolved before staff assignment."""
        complaint, _ = ComplaintService.file_complaint(
            title='Unassigned issue',
            description='Not yet assigned to any staff',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )

        self._login('resident_one', 'ResPass123!')
        res = self.client.post(f'/complaint/resolve/{complaint.id}', data={}, follow_redirects=True)
        db.session.refresh(complaint)
        self.assertEqual(complaint.status, 'Pending', "Unassigned complaint must not transition to Resolved")

    def test_duplicate_resolution_handled_safely(self):
        """Calling resolve on an already resolved complaint returns an error and does not corrupt state."""
        complaint, _ = ComplaintService.file_complaint(
            title='Already fixed',
            description='Testing duplicate resolve',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        ComplaintService.resolve_complaint(complaint.id, resolution_notes='First resolve', resolved_by_user_id=self.admin.id)
        orig_resolved_at = complaint.resolved_at

        # Attempt to resolve again
        success, msg = ComplaintService.resolve_complaint(complaint.id, resolution_notes='Duplicate resolve', resolved_by_user_id=self.admin.id)
        self.assertFalse(success)
        self.assertIn('already marked as resolved', msg.lower())
        self.assertEqual(complaint.resolved_at, orig_resolved_at)

    def test_unrelated_resident_cannot_view_or_reopen_other_complaint(self):
        """One resident cannot view or reopen another resident's complaint."""
        complaint, _ = ComplaintService.file_complaint(
            title='Private Issue',
            description='Private description in Flat A-101',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        ComplaintService.resolve_complaint(complaint.id, resolution_notes='Done', resolved_by_user_id=self.admin.id)

        # Login as resident 2 (Flat A-102)
        self._login('resident_two', 'ResPass123!')

        # Attempt to view Flat A-101's complaint
        res_view = self.client.get(f'/complaint/{complaint.id}')
        self.assertIn(res_view.status_code, [302, 403])

        # Attempt to reopen Flat A-101's complaint
        res_reopen = self.client.post(f'/complaint/reopen/{complaint.id}', data={'reason': 'Malicious'})
        self.assertIn(res_reopen.status_code, [302, 403])
        self.assertEqual(complaint.status, 'Resolved')

    # -------------------------------------------------------------
    # 4. OVERDUE TRACKING TESTS
    # -------------------------------------------------------------
    def test_complaint_below_threshold_is_not_overdue(self):
        """A fresh complaint below 24 hours is not overdue."""
        complaint, _ = ComplaintService.file_complaint(
            title='Fresh complaint',
            description='Just filed',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        self.assertFalse(complaint.is_overdue)

    def test_complaint_past_threshold_is_flagged_overdue(self):
        """A complaint created more than 24 hours ago is flagged as overdue."""
        complaint, _ = ComplaintService.file_complaint(
            title='Old pending complaint',
            description='Waiting long time',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        # Backdate created_at by 25 hours
        complaint.created_at = datetime.utcnow() - timedelta(hours=25)
        db.session.commit()

        self.assertTrue(complaint.is_overdue)
        self.assertIn('1d 1h', complaint.elapsed_time_formatted)
        # Overdue does NOT silently resolve
        self.assertEqual(complaint.status, 'Pending')

    def test_resolved_complaints_excluded_from_active_overdue(self):
        """Resolved complaints are never flagged as active overdue."""
        complaint, _ = ComplaintService.file_complaint(
            title='Resolved old complaint',
            description='Resolved long ago',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        ComplaintService.resolve_complaint(complaint.id, resolution_notes='Finished', resolved_by_user_id=self.admin.id)

        # Backdate created_at and resolved_at
        complaint.created_at = datetime.utcnow() - timedelta(hours=48)
        complaint.resolved_at = datetime.utcnow() - timedelta(hours=24)
        db.session.commit()

        self.assertFalse(complaint.is_overdue)
        # Verify get_all_complaints with Overdue filter excludes resolved
        overdue_list = ComplaintService.get_all_complaints(status='Overdue')
        self.assertNotIn(complaint, overdue_list)

    def test_reopened_complaints_tracked_for_overdue(self):
        """Reopened complaints calculate overdue based on reopened timestamp."""
        complaint, _ = ComplaintService.file_complaint(
            title='Reopened overdue complaint',
            description='Recurred issue',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        ComplaintService.assign_complaint(complaint.id, self.electrician.id, admin_user_id=self.admin.id)
        ComplaintService.resolve_complaint(complaint.id, resolution_notes='Resolved once', resolved_by_user_id=self.admin.id)
        ComplaintService.reopen_complaint(complaint.id, reason='Broken again', user_id=self.resident1.id)

        # Reopened history entry backdated 26 hours
        h_reopen = ComplaintHistory.query.filter_by(complaint_id=complaint.id, action='Reopened').first()
        h_reopen.created_at = datetime.utcnow() - timedelta(hours=26)
        db.session.commit()

        self.assertTrue(complaint.is_overdue)
        overdue_list = ComplaintService.get_all_complaints(status='Overdue')
        self.assertIn(complaint, overdue_list)

    # -------------------------------------------------------------
    # 5. PERSISTENCE & HISTORY TESTS
    # -------------------------------------------------------------
    def test_state_and_history_survive_fresh_db_session(self):
        """Data persists correctly and reload from fresh database session yields identical state."""
        complaint, _ = ComplaintService.file_complaint(
            title='Persistent ticket',
            description='Testing db persistence',
            category='Electrical',
            flat_id=self.flat1.id,
            created_by_user_id=self.resident1.id
        )
        cid = complaint.id
        ComplaintService.assign_complaint(cid, self.electrician.id, admin_user_id=self.admin.id)
        ComplaintService.resolve_complaint(cid, resolution_notes='Phase 1 resolved', resolved_by_user_id=self.admin.id)
        ComplaintService.reopen_complaint(cid, reason='Phase 2 reopen', user_id=self.resident1.id)

        # Clear and recreate session
        db.session.expire_all()

        reloaded = Complaint.query.get(cid)
        self.assertEqual(reloaded.status, 'Reopened')
        self.assertEqual(reloaded.assigned_to_staff_id, self.electrician.id)
        self.assertEqual(len(reloaded.history), 4)  # Created, Assigned, Resolved, Reopened

if __name__ == '__main__':
    unittest.main()

from src.resume_service import Appointment, patient_notification


def test_needs_review_gets_patient_safe_instruction():
    appointment = Appointment("Mina Chen", "2026-09-08 09:30", "needs_review")
    assert patient_notification(appointment) == "Please contact the clinic about your appointment at 2026-09-08 09:30."


def test_cancelled_appointment_has_no_outbound_notice():
    appointment = Appointment("Mina Chen", "2026-09-08 09:30", "cancelled")
    assert patient_notification(appointment) is None

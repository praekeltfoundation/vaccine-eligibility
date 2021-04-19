from vaccine.healthcheck_ussd import Application as HealthCheckApp
from vaccine.vaccine_reg_ussd import Application as VacRegApp


def test_no_state_name_clashes():
    hc_states = set(s for s in dir(HealthCheckApp) if s.startswith("state_"))
    vr_states = set(s for s in dir(VacRegApp) if s.startswith("state_"))
    intersection = (hc_states & vr_states) - {"state_name"}
    assert len(intersection) == 0, f"Common states to both apps: {intersection}"

from app.services.dashboard_service import DashboardService
from frontend.db_actions import get_actor, run_db_action


def fetch_provider_stats(provider_id: int) -> dict:
    def action(session):
        get_actor(session, provider_id)
        return DashboardService(session).provider_stats(provider_id)
    return run_db_action(action)

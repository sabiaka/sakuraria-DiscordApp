from .event_management import setup as setup_event_management
from .role_management import setup as setup_role_management

async def setup(bot):
    await setup_event_management(bot)
    await setup_role_management(bot) 
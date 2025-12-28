from pyee.asyncio import AsyncIOEventEmitter

# Singleton instance of the Event Bus
event_bus = AsyncIOEventEmitter()

# Event Constants
class Events:
    METER_VALUES = "meter_values"
    STATUS_NOTIFICATION = "status_notification"

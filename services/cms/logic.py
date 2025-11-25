import logging

logger = logging.getLogger(__name__)

def validate_charger(vendor: str, model: str) -> bool:
    # Mock validation logic
    logger.info(f"Validating charger: Vendor={vendor}, Model={model}")
    return True

def save_meter_values(charger_id: str, payload: dict):
    # Mock DB save
    logger.info(f"Saving meter values for {charger_id}: {payload}")

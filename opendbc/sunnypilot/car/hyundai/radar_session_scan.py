from opendbc.car import uds
from opendbc.car.carlog import carlog
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery
import cereal.messaging as messaging
import time

# Radar address
RADAR_ADDR = 0x7d0
RADAR_RESP = RADAR_ADDR + 8
BUS = 0
TIMEOUT = 0.2

# Data Identifier for radar config
CONFIG_DATA_ID = bytes([0x01, 0x42])
READ_DATA_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER]) + CONFIG_DATA_ID
READ_DATA_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40])

# Session codes to test
SESSION_CODES = [0x01, 0x02, 0x03, 0x04, 0x06, 0x07, 0x85]

def try_session(sendcan, logcan, session_code):
    carlog.error(f"\n--- Trying Diagnostic Session: 0x{session_code:02X} ---")
    session_req = bytes([uds.SERVICE_TYPE.DIAGNOSTIC_SESSION_CONTROL, session_code])
    session_resp = bytes([uds.SERVICE_TYPE.DIAGNOSTIC_SESSION_CONTROL + 0x40, session_code])

    # Switch session
    query = IsoTpParallelQuery(sendcan, logcan, BUS, [RADAR_ADDR], [session_req], [session_resp])
    resp = query.get_data(TIMEOUT)
    if not resp:
        carlog.error(f"Session 0x{session_code:02X} - No response")
        return

    carlog.error(f"Session 0x{session_code:02X} - OK, trying to read 0x0142...")

    # Try reading config
    query = IsoTpParallelQuery(sendcan, logcan, BUS, [RADAR_ADDR], [READ_DATA_REQUEST], [READ_DATA_RESPONSE])
    resp = query.get_data(TIMEOUT)
    if resp:
        for _, data in resp.items():
            carlog.error(f"Session 0x{session_code:02X} - Read 0x0142: {data.hex()}")
    else:
        carlog.error(f"Session 0x{session_code:02X} - Read 0x0142 failed")


if __name__ == "__main__":
    sendcan = messaging.pub_sock('sendcan')
    logcan = messaging.sub_sock('can')
    time.sleep(1)

    for code in SESSION_CODES:
        try_session(sendcan, logcan, code)

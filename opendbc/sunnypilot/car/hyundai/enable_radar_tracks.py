"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

from opendbc.car import uds
from opendbc.car.carlog import carlog
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery

DEVELOPER_DIAGNOSTIC = 0x07
CUSTOM_DIAGNOSTIC_REQUEST = bytes([uds.SERVICE_TYPE.DIAGNOSTIC_SESSION_CONTROL, DEVELOPER_DIAGNOSTIC])
CUSTOM_DIAGNOSTIC_RESPONSE = bytes([uds.SERVICE_TYPE.DIAGNOSTIC_SESSION_CONTROL + 0x40, DEVELOPER_DIAGNOSTIC])

READ_DATA_REQUEST = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER])
READ_DATA_RESPONSE = bytes([uds.SERVICE_TYPE.READ_DATA_BY_IDENTIFIER + 0x40])

WRITE_DATA_REQUEST = bytes([uds.SERVICE_TYPE.WRITE_DATA_BY_IDENTIFIER])
WRITE_DATA_RESPONSE = bytes([uds.SERVICE_TYPE.WRITE_DATA_BY_IDENTIFIER + 0x40])

CONFIG_DATA_ID = bytes([0x01, 0x42])
DEFAULT_CONFIG = bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x00])
TRACKS_ENABLED_CONFIG = bytes([0x00, 0x00, 0x00, 0x01, 0x00, 0x01])
TRACKS_ENABLED_CONFIG_BYTES = b"\x00\x00\x01\x00\x01"

RESET_REQUEST = b'\x11\x01'
RESET_RESPONSE = b''

def print_uds_response(label, data):
  if not data:
    carlog.error(f"{label} → No response")
    return
  hex_data = data.hex()
  if data[0] == 0x7F:
    carlog.error(f"{label} → NEGATIVE RESPONSE: Service 0x{data[1]:02X}, Code 0x{data[2]:02X}")
  else:
    carlog.error(f"{label} → POSITIVE RESPONSE: {hex_data}")

def enable_radar_tracks(logcan, sendcan, bus=4, addr=0x7d0, timeout=0.1, retry=10):
  carlog.error("radar_tracks: enabling ...")

  try:
    # Send reset first because the disable request below is not getting to the radar soon enough
    carlog.error("sending reset (0x11 0x01)")
    reset_query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [RESET_REQUEST], [RESET_RESPONSE])
    reset_query.get_data(timeout=0.1)
  except Exception:
    carlog.error("reset failed or unsupported")

  for i in range(retry):
    try:
      # Step 1: Enter Developer Diagnostic Session
      query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [CUSTOM_DIAGNOSTIC_REQUEST], [CUSTOM_DIAGNOSTIC_RESPONSE])
      for _, dev_resp in query.get_data(timeout).items():
        print_uds_response("Enter Dev Session", dev_resp)

        # Step 2: Read Current Config
        request = READ_DATA_REQUEST + CONFIG_DATA_ID
        query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [request], [READ_DATA_RESPONSE])
        for _, read_resp in query.get_data(timeout).items():
          print_uds_response("Read Config", read_resp)
          current_config = read_resp[3:]

          carlog.error(f"radar_tracks: current config bytes: {current_config.hex()}")

          if current_config == TRACKS_ENABLED_CONFIG_BYTES:
            carlog.error("radar_tracks: already enabled, skipping ...")
          else:
            carlog.error("radar_tracks: reconfiguring radar to output radar points ...")
            request = WRITE_DATA_REQUEST + CONFIG_DATA_ID + TRACKS_ENABLED_CONFIG
            query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [request], [WRITE_DATA_RESPONSE])
            for _, write_resp in query.get_data(timeout).items():
              print_uds_response("Write Config", write_resp)
            carlog.error("radar_tracks: successfully enabled")

          return True

    except Exception as e:
      carlog.exception(f"radar_tracks exception: {e}")

    carlog.error(f"radar_tracks retry ({i + 1}) ...")
  carlog.error("radar_tracks: failed")
  return False

if __name__ == "__main__":
  import time
  import cereal.messaging as messaging
  sendcan = messaging.pub_sock('sendcan')
  logcan = messaging.sub_sock('can')
  time.sleep(7)

  enabled = enable_radar_tracks(logcan, sendcan, bus=4, addr=0x7d0, timeout=0.1)
  print(f"enabled: {enabled}")

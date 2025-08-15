"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

from opendbc.car import uds
from opendbc.car.carlog import carlog
from opendbc.car.isotp_parallel_query import IsoTpParallelQuery
import time

DEVELOPER_DIAGNOSTIC = 0x03
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

def uds_request(sendcan, logcan, bus, addr, req, resp, timeout=0.1):
    query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [req], [resp])
    return query.get_data(timeout)

def try_session(sendcan, logcan, bus, addr, session_id):
    carlog.error(f"=== Trying Diagnostic Session 0x{session_id:02X} ===")
    req = bytes([0x10, session_id])
    resp = bytes([0x50, session_id])
    data = uds_request(sendcan, logcan, bus, addr, req, resp)
    if data:
        carlog.error(f"Entered session 0x{session_id:02X}")
    else:
        carlog.error(f"Session 0x{session_id:02X} rejected")

def security_access(sendcan, logcan, bus, addr, level):
    carlog.error(f"=== Security Access Level {level} (Seed Request) ===")
    req = bytes([0x27, level])
    resp = bytes([0x67, level])
    data = uds_request(sendcan, logcan, bus, addr, req, resp)
    if data:
        carlog.error(f"Seed: {data}")
    else:
        carlog.error("Security access rejected or not supported")

def read_did(sendcan, logcan, bus, addr, did):
    carlog.error(f"=== Reading DID 0x{did:04X} ===")
    req = bytes([0x22, did >> 8, did & 0xFF])
    resp = bytes([0x62, did >> 8, did & 0xFF])
    data = uds_request(sendcan, logcan, bus, addr, req, resp)
    if data:
        carlog.error(f"DID 0x{did:04X} data: {data}")
    else:
        carlog.error(f"DID 0x{did:04X} not supported")


def enable_radar_tracks(logcan, sendcan, bus=4, addr=0x7d0, timeout=0.1, retry=5):
  carlog.error("radar_tracks: enabling ...")
  #time.sleep(10)

  try:
    # Send reset first because the request below is not getting to the radar soon enough
    carlog.error("sending reset (0x11 0x01)")
    reset_query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [RESET_REQUEST], [RESET_RESPONSE])
    reset_query.get_data(timeout=0.1)
  except Exception:
    carlog.error("reset failed or unsupported")

  for i in range(retry):
    try:
      query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [CUSTOM_DIAGNOSTIC_REQUEST], [CUSTOM_DIAGNOSTIC_RESPONSE])
      carlog.error(f"radar_tracks: sent diagnostic request on bus {bus}, address {addr}")

      for _, _ in query.get_data(timeout).items():
        carlog.error("radar_tracks: check current config ...")

        request = READ_DATA_REQUEST + CONFIG_DATA_ID
        query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [request], [READ_DATA_RESPONSE])

        for _, data in query.get_data(timeout).items():
          current_config = data[3:]

          carlog.error(f"radar_tracks: current config: {current_config.hex()}")

          if current_config == TRACKS_ENABLED_CONFIG_BYTES:
            carlog.error("radar_tracks: already enabled, skipping ...")
          else:
            carlog.error("radar_tracks: reconfigure radar to output radar points ...")
            request = WRITE_DATA_REQUEST + CONFIG_DATA_ID + TRACKS_ENABLED_CONFIG
            query = IsoTpParallelQuery(sendcan, logcan, bus, [addr], [request], [WRITE_DATA_RESPONSE])
            query.get_data(0)

            carlog.error("radar_tracks: successfully enabled")

          return True

    except Exception as e:
      carlog.exception(f"radar_tracks exception: {e}")
      time.sleep(.2)

    carlog.error(f"radar_tracks retry ({i + 1}) ...")
  carlog.error("radar_tracks: failed")
  return False


if __name__ == "__main__":
  import time
  import cereal.messaging as messaging
  sendcan = messaging.pub_sock('sendcan')
  logcan = messaging.sub_sock('can')
  time.sleep(1)

  enabled = enable_radar_tracks(logcan, sendcan, bus=4, addr=0x7d0, timeout=0.1)
  print(f"enabled: {enabled}")
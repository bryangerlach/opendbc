"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
from opendbc.car import structs
from opendbc.car.can_definitions import CanRecvCallable, CanSendCallable
from opendbc.car.hyundai.values import HyundaiFlags
from opendbc.sunnypilot.car.hyundai.enable_radar_tracks import enable_radar_tracks as hyundai_enable_radar_tracks
from opendbc.sunnypilot.car.hyundai.enable_radar_tracks import try_session, security_access, read_did
from opendbc.sunnypilot.car.hyundai.values import HyundaiFlagsSP


def setup_interfaces(CP: structs.CarParams, CP_SP: structs.CarParamsSP, can_recv: CanRecvCallable = None, can_send: CanSendCallable = None) -> None:
  _initialize_radar_tracks(CP, CP_SP, can_recv, can_send)


def _initialize_radar_tracks(CP: structs.CarParams, CP_SP: structs.CarParamsSP, can_recv: CanRecvCallable = None, can_send: CanSendCallable = None) -> None:
  if CP.brand == 'hyundai':
    if CP.flags & HyundaiFlags.MANDO_RADAR and (CP.radarUnavailable or CP_SP.flags & HyundaiFlagsSP.ENHANCED_SCC):
      # Try both sessions
      try_session(can_recv, can_send, 4, 0x7d0, 0x03)  # Extended
      try_session(can_recv, can_send, 4, 0x7d0, 0x07)  # Developer

      # Try security access
      security_access(can_recv, can_send, 4, 0x7d0, 0x01)

      # Try reading some DIDs
      for did in [0xF100, 0xF101, 0x0142]:
          read_did(can_recv, can_send, 4, 0x7d0, did)


      tracks_enabled = hyundai_enable_radar_tracks(can_recv, can_send, bus=4, addr=0x7d0)
      CP.radarUnavailable = not tracks_enabled

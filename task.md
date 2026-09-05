# Phase 3 & 4 — Task Tracker

## Phase 3 — Liveness Detection
- [ ] `liveness/__init__.py`
- [ ] `liveness/base.py` — LivenessChecker ABC
- [ ] `liveness/mock_liveness.py` — always returns is_live=True
- [ ] `liveness/mini_fasnet.py` — ONNX inference + auto-download
- [ ] Modify `pipeline.py` — integrate liveness checker
- [ ] Modify `api/faces.py` — add liveness_score to response

## Phase 4 — Raspberry Pi Client
- [ ] `rpi-client/config.py`
- [ ] `rpi-client/.env`
- [ ] `rpi-client/camera/capture.py`
- [ ] `rpi-client/api/client.py`
- [ ] `rpi-client/offline/queue.py`
- [ ] `rpi-client/hardware/esp32_bridge.py`
- [ ] `rpi-client/ui/display.py`
- [ ] `rpi-client/main.py`
- [ ] `rpi-client/requirements.txt`
- [ ] `rpi-client/README.md`
- [ ] Package __init__.py files

## Verification
- [ ] Run existing backend tests
- [ ] Verify mock liveness path works

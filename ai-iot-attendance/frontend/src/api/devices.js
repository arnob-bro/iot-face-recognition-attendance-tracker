/**
 * Devices API service
 *
 * Endpoints:
 *   GET  /api/v1/devices
 *   POST /api/v1/devices
 *   PUT  /api/v1/devices/{device_id}/enabled?enabled=true
 */

import { apiRequest } from "./client";


export async function listDevices() {
  return apiRequest("/api/v1/devices");
}


export async function createDevice(data) {
  return apiRequest("/api/v1/devices", {
    method: "POST",
    body: data,
  });
}


export async function updateDeviceStatus(deviceId, enabled) {
  return apiRequest(
    `/api/v1/devices/${deviceId}/enabled?enabled=${enabled}`,
    {
      method: "PUT",
    }
  );
}
import "./Devices.css";
import { useEffect, useState } from "react";
import {
  listDevices,
  createDevice,
  updateDeviceStatus,
} from "../api/devices";
import Loader from "../components/Loader";

function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");


  const [showForm, setShowForm] = useState(false);

  const [formData, setFormData] = useState({
    device_id: "",
    name: "",
    location: "",
  });

  const [deviceSecret, setDeviceSecret] = useState("");

  const loadDevices = async () => {
    setLoading(true);
    setMessage("");

    try {
      const data = await listDevices();
      setDevices(Array.isArray(data) ? data : []);
    } catch (err) {
      setMessage(err.message || "Failed to load devices.");
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    loadDevices();
  }, []);


  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };


  const handleCreateDevice = async (e) => {
    e.preventDefault();

    try {
      setMessage("");

      const response = await createDevice(formData);

      setDeviceSecret(response.device_secret || "");

      setFormData({
        device_id: "",
        name: "",
        location: "",
      });

      setShowForm(false);
      await loadDevices();

    } catch (err) {
      setMessage(err.message || "Failed to create device.");
    }
  };


  const handleToggleDevice = async (device) => {
    try {
      setMessage("");

      await updateDeviceStatus(
        device.device_id,
        !device.enabled
      );

      await loadDevices();

    } catch (err) {
      setMessage(err.message || "Failed to update device.");
    }
  };


  return (
    <div className="devices-page">

      <div className="devices-header">
        <div>
          <p className="devices-subtitle">
            Raspberry Pi Management
          </p>

          <h1>Devices</h1>

          <p className="devices-description">
            Register and manage Raspberry Pi attendance devices.
          </p>
        </div>


        <button
          className="devices-primary-button"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? "Close" : "+ Add Device"}
        </button>
      </div>


      {message && (
        <p className="devices-error">
          {message}
        </p>
      )}


      {deviceSecret && (
        <div className="devices-secret-card">
          <h3>Device Registered</h3>

          <p>
            Save this secret. It will not be shown again.
          </p>

          <code>{deviceSecret}</code>

          <button
            className="devices-reset-button"
            onClick={() => setDeviceSecret("")}
          >
            Close
          </button>
        </div>
      )}



      {showForm && (
        <div className="devices-card">

          <div className="devices-card-header">
            <h2>Add New Device</h2>
          </div>


          <form
            className="devices-form"
            onSubmit={handleCreateDevice}
          >

            <div className="devices-field">
              <label>Device ID</label>
              <input
                name="device_id"
                value={formData.device_id}
                onChange={handleInputChange}
                required
              />
            </div>


            <div className="devices-field">
              <label>Name</label>
              <input
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                required
              />
            </div>


            <div className="devices-field">
              <label>Location</label>
              <input
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                required
              />
            </div>


            <button
              className="devices-primary-button"
              type="submit"
            >
              Register Device
            </button>

          </form>

        </div>
      )}




      <div className="devices-card">

        <div className="devices-card-header">

          <div>
            <h2>Registered Devices</h2>

            <div>
              {loading ? (
                <Loader />
              ) : (
                <p>
                  {devices.length} device{devices.length === 1 ? "" : "s"} found
                </p>
              )}
            </div>
          </div>


          <button
            className="devices-reset-button"
            onClick={loadDevices}
          >
            ↻ Refresh
          </button>

        </div>



        <div className="devices-table-wrapper">

          <table className="devices-table">

            <thead>
              <tr className="devices-table-head">
                <th>Device ID</th>
                <th>Name</th>
                <th>Location</th>
                <th>Status</th>
                <th>Last Seen</th>
                <th>Action</th>
              </tr>
            </thead>


            <tbody>

              {devices.map((device) => (

                <tr key={device.device_id}>

                  <td>{device.device_id}</td>

                  <td>{device.name}</td>

                  <td>{device.location || "-"}</td>


                  <td>
                    <span
                      className={
                        device.enabled
                          ? "devices-status enabled"
                          : "devices-status disabled"
                      }
                    >
                      {device.enabled
                        ? "Enabled"
                        : "Disabled"}
                    </span>
                  </td>


                  <td>
                    {device.last_seen_at || "-"}
                  </td>


                  <td>
                    <button
                      className="devices-action-button"
                      onClick={() =>
                        handleToggleDevice(device)
                      }
                    >
                      {device.enabled
                        ? "Disable"
                        : "Enable"}
                    </button>
                  </td>

                </tr>

              ))}



              {!loading && devices.length === 0 && (
                <tr>
                  <td
                    colSpan="6"
                    className="devices-empty"
                  >
                    No devices registered.
                  </td>
                </tr>
              )}

            </tbody>

          </table>

        </div>

      </div>

    </div>
  );
}

export default Devices;
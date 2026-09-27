import { BrowserRouter, Routes, Route } from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Students from "./pages/Students";
import Attendance from "./pages/Attendance";
import Reports from "./pages/Reports";
import Homepage from "./pages/Homepage";
import ProtectedRoute from "./components/ProtectedRoute";
import AppNav from "./components/AppNav";
import Devices from "./pages/Devices";
import Teachers from "./pages/Teachers";
import AdminRoute from "./components/AdminRoute";
import Courses from "./pages/Courses";
import StudentDashboard from "./pages/StudentDashboard";
import StudentProfile from "./pages/StudentProfile";
import StudentAttendance from "./pages/StudentAttendance";
import Routines from "./pages/Routines";



function ProtectedLayout({ children }) {
  return (
    <>
      <AppNav />
      {children}
    </>
  );
}


function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/" element={<Homepage />} />


        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Dashboard />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/dashboard"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <StudentDashboard />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/student/profile"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <StudentProfile />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />


        <Route
          path="/student/attendance"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <StudentAttendance />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />


        <Route
          path="/students"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Students />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />


        <Route
          path="/attendance"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Attendance />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/courses"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Courses />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Reports />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />


        <Route
          path="/devices"
          element={
            <AdminRoute>
              <ProtectedLayout>
                <Devices />
              </ProtectedLayout>
            </AdminRoute>
          }
        />


        <Route
          path="/teachers"
          element={
            <AdminRoute>
              <ProtectedLayout>
                <Teachers />
              </ProtectedLayout>
            </AdminRoute>
          }
        />

        <Route
          path="/routines"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Routines />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />


      </Routes>
    </BrowserRouter>
  );
}

export default App;
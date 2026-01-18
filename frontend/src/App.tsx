import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/providers/auth-provider";
import LoginPage from "@/pages/LoginPage";
import Dashboard from "@/pages/Dashboard";
import ChargerDetail from "@/pages/ChargerDetail";
import UsersPage from "@/pages/UsersPage";
import RentersPage from "@/pages/RentersPage";
import ParkingSpotsPage from "@/pages/ParkingSpotsPage";
import { Loader2 } from "lucide-react";
import { type ReactNode } from "react";

function PrivateRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

// Dashboard imported from pages

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/chargers/:id"
            element={
              <PrivateRoute>
                <ChargerDetail />
              </PrivateRoute>
            }
          />
          <Route
            path="/users"
            element={
              <PrivateRoute>
                <UsersPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/renters"
            element={
              <PrivateRoute>
                <RentersPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/parking-spots"
            element={
              <PrivateRoute>
                <ParkingSpotsPage />
              </PrivateRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { configureAuth } from "@/services/api";
import { useAuthStore } from "@/stores/auth";
import { useMe } from "@/hooks/useAuth";
import Layout from "@/components/Layout";
import ProtectedRoute from "@/components/ProtectedRoute";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Events from "@/pages/Events";
import EventDetail from "@/pages/EventDetail";
import EventForm from "@/pages/EventForm";
import Checkout from "@/pages/Checkout";
import OrderConfirmation from "@/pages/OrderConfirmation";
import MyTickets from "@/pages/MyTickets";
import CheckinEvents from "@/pages/CheckinEvents";
import CheckinEvent from "@/pages/CheckinEvent";
import Admin from "@/pages/Admin";

const queryClient = new QueryClient();

configureAuth(
  () => useAuthStore.getState().token,
  () => useAuthStore.getState().logout(),
);

function AuthInit() {
  useMe();
  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthInit />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/events" element={<Events />} />
              <Route path="/events/new" element={<EventForm />} />
              <Route path="/events/:slug/edit" element={<EventForm />} />
              <Route path="/events/:slug" element={<EventDetail />} />
              <Route path="/checkout/:slug" element={<Checkout />} />
              <Route path="/orders/:id" element={<OrderConfirmation />} />
              <Route path="/tickets" element={<MyTickets />} />
              <Route path="/checkin" element={<CheckinEvents />} />
              <Route path="/checkin/:eventId" element={<CheckinEvent />} />
              <Route path="/admin" element={<Admin />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

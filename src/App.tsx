import { Routes, Route, Navigate } from "react-router-dom";
import DashboardLayout from "@/layouts/DashboardLayout";
import AuthLayout from "@/layouts/AuthLayout";

import LandingPage from "@/pages/LandingPage";
import LoginPage from "@/pages/auth/LoginPage";
import SignupPage from "@/pages/auth/SignupPage";
import ForgotPasswordPage from "@/pages/auth/ForgotPasswordPage";
import OtpVerificationPage from "@/pages/auth/OtpVerificationPage";

import StudentDashboard from "@/pages/StudentDashboard";
import TeacherDashboard from "@/pages/TeacherDashboard";
import AttendancePage from "@/pages/AttendancePage";
import NotesSummaryPage from "@/pages/NotesSummaryPage";
import ChatbotPage from "@/pages/ChatbotPage";
import AssignmentCheckerPage from "@/pages/AssignmentCheckerPage";
import QuizGeneratorPage from "@/pages/QuizGeneratorPage";
import ProfilePage from "@/pages/ProfilePage";
import NotificationsPage from "@/pages/NotificationsPage";
import SettingsPage from "@/pages/SettingsPage";
import NotFoundPage from "@/pages/NotFoundPage";

import { useAuth } from "@/contexts/AuthContext";

function DashboardRouter() {
  const { user } = useAuth();
  return user?.role === "teacher" ? <TeacherDashboard /> : <StudentDashboard />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />

      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/otp-verification" element={<OtpVerificationPage />} />
      </Route>

      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<DashboardRouter />} />
        <Route path="/attendance" element={<AttendancePage />} />
        <Route path="/notes-summary" element={<NotesSummaryPage />} />
        <Route path="/chatbot" element={<ChatbotPage />} />
        <Route path="/assignment-checker" element={<AssignmentCheckerPage />} />
        <Route path="/quiz-generator" element={<QuizGeneratorPage />} />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}

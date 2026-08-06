export type UserRole = "student" | "teacher";

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatarUrl?: string;
  grade?: string;
  rollNumber?: string;
}

export interface ClassSession {
  id: string;
  subject: string;
  teacher: string;
  time: string;
  room: string;
  status: "upcoming" | "live" | "completed";
  color: string;
}

export interface Assignment {
  id: string;
  title: string;
  subject: string;
  dueDate: string;
  status: "pending" | "submitted" | "graded" | "overdue";
  grade?: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  description: string;
  time: string;
  type: "assignment" | "attendance" | "quiz" | "system" | "message";
  read: boolean;
}

export interface StudentRecord {
  id: string;
  name: string;
  rollNumber: string;
  attendance: number;
  avgScore: number;
  status: "present" | "absent" | "late" | "not-marked";
  trend: "up" | "down" | "stable";
}

export interface QuizResult {
  id: string;
  quizTitle: string;
  date: string;
  score: number;
  totalMarks: number;
  rank?: number;
}

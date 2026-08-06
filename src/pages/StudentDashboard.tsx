import { Link } from "react-router-dom";
import {
  Sparkles,
  Clock,
  MapPin,
  ArrowRight,
  FileText,
  MessageSquareText,
  Brain,
  ClipboardCheck,
  BookOpen,
  Trophy,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { useState } from "react";
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip as RTooltip, CartesianGrid } from "recharts";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { PageHeader } from "@/components/shared/PageHeader";
import { useAuth } from "@/contexts/AuthContext";
import { useApi } from "@/hooks/useApi";
import { cn } from "@/utils/cn";

const quickActions = [
  { label: "Summarize notes", icon: FileText, to: "/notes-summary" },
  { label: "Ask AI a doubt", icon: MessageSquareText, to: "/chatbot" },
  { label: "Generate a quiz", icon: Brain, to: "/quiz-generator" },
  { label: "Check assignment", icon: ClipboardCheck, to: "/assignment-checker" },
];

function MiniCalendar() {
  const [monthOffset, setMonthOffset] = useState(0);
  const base = new Date();
  base.setMonth(base.getMonth() + monthOffset);
  const monthLabel = base.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  const daysInMonth = new Date(base.getFullYear(), base.getMonth() + 1, 0).getDate();
  const startDay = new Date(base.getFullYear(), base.getMonth(), 1).getDay();
  const today = new Date();
  const isCurrentMonth = base.getMonth() === today.getMonth() && base.getFullYear() === today.getFullYear();

  const cells = [
    ...Array.from({ length: startDay }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-sm">{monthLabel}</CardTitle>
        <div className="flex gap-1">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setMonthOffset((m) => m - 1)} aria-label="Previous month">
            <ChevronLeft className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setMonthOffset((m) => m + 1)} aria-label="Next month">
            <ChevronRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-7 gap-1 text-center text-[11px] font-medium text-muted-foreground">
          {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
            <span key={i}>{d}</span>
          ))}
        </div>
        <div className="mt-2 grid grid-cols-7 gap-1">
          {cells.map((day, i) => {
            const isToday = isCurrentMonth && day === today.getDate();
            return (
              <div
                key={i}
                className={cn(
                  "relative flex h-8 items-center justify-center rounded-lg text-xs",
                  isToday ? "bg-brand-gradient font-semibold text-white" : "hover:bg-muted",
                  day === null && "invisible"
                )}
              >
                {day}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export default function StudentDashboard() {
  const { user } = useAuth();
  const { data: dashboard, loading, error } = useApi<any>("/dashboard/student");

  const todayStr = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const attendancePct = dashboard?.attendance_percentage ?? 0;
  const attendanceTrend = dashboard?.attendance_trend ?? [];
  const upcomingAssignments = dashboard?.upcoming_assignments ?? [];
  const quizHistory = dashboard?.quiz_history ?? [];
  const recentSummaries = dashboard?.recent_ai_summaries ?? [];
  const todaysSchedule = dashboard?.todays_schedule ?? [];
  const unreadNotifs = dashboard?.unread_notifications_count ?? 0;

  return (
    <div>
      <PageHeader
        title={`Good morning, ${user?.name?.split(" ")[0] ?? "Student"} 👋`}
        description="Here's what's happening in your classroom today."
      />

      {/* Welcome card */}
      <Card className="mb-6 overflow-hidden border-none bg-brand-gradient text-white shadow-glow">
        <CardContent className="relative flex flex-col items-start justify-between gap-4 p-6 sm:flex-row sm:items-center sm:p-8">
          <div className="pointer-events-none absolute inset-0 aura-bg opacity-40" />
          <div className="relative z-10">
            {user?.grade && <Badge className="border-white/30 bg-white/15 text-white">{user.grade}</Badge>}
            <h2 className="mt-3 text-xl font-bold sm:text-2xl">Welcome to your Learning Hub</h2>
            <p className="mt-1.5 max-w-md text-sm text-white/85">
              Access your classes, AI study assistants, quizzes, and assignments all in one place.
            </p>
          </div>
          <Button variant="glass" className="relative z-10 shrink-0 text-foreground" asChild>
            <Link to="/quiz-generator">
              Take today's quiz <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left + middle column */}
        <div className="space-y-6 lg:col-span-2">
          {/* Today's classes */}
          <Card>
            <CardHeader>
              <CardTitle>Today's classes</CardTitle>
              <CardDescription>{todayStr}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {todaysSchedule.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No classes scheduled for today.</p>
              ) : (
                todaysSchedule.map((cls: any, i: number) => (
                  <div
                    key={i}
                    className="flex items-center gap-4 rounded-xl border border-border p-3.5 transition-colors hover:bg-muted/40"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{cls.subject || cls.course}</p>
                      <p className="truncate text-xs text-muted-foreground">{cls.teacher || "Faculty"}</p>
                    </div>
                    {cls.time && (
                      <div className="text-right text-xs text-muted-foreground">
                        <p className="flex items-center gap-1"><Clock className="h-3 w-3" /> {cls.time}</p>
                      </div>
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Attendance + Quiz performance charts */}
          <div className="grid gap-6 sm:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Attendance</CardTitle>
                <CardDescription>Overall Record</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold">{attendancePct}%</span>
                </div>
                {attendanceTrend.length > 0 && (
                  <div className="mt-3 h-32">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={attendanceTrend}>
                        <defs>
                          <linearGradient id="attGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#4F46E5" stopOpacity={0.35} />
                            <stop offset="100%" stopColor="#4F46E5" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} />
                        <YAxis hide domain={[0, 100]} />
                        <CartesianGrid vertical={false} strokeDasharray="3 3" opacity={0.15} />
                        <RTooltip contentStyle={{ borderRadius: 12, fontSize: 12, border: "1px solid #e5e7eb" }} />
                        <Area type="monotone" dataKey="value" stroke="#4F46E5" strokeWidth={2} fill="url(#attGradient)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quiz Performance</CardTitle>
                <CardDescription>Average Score</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold">{dashboard?.average_quiz_score ?? 0}%</span>
                </div>
                {quizHistory.length > 0 ? (
                  <div className="mt-3 space-y-2">
                    {quizHistory.slice(0, 3).map((q: any, i: number) => (
                      <div key={i} className="flex justify-between text-xs">
                        <span className="truncate font-medium">{q.title}</span>
                        <span className="font-semibold">{q.score}%</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-4 text-xs text-muted-foreground">No quiz attempts yet.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Upcoming assignments */}
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Upcoming assignments</CardTitle>
                <CardDescription>{upcomingAssignments.length} pending</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/assignment-checker">View all</Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {upcomingAssignments.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No upcoming assignments.</p>
              ) : (
                upcomingAssignments.map((a: any) => (
                  <div key={a.id} className="flex items-center justify-between gap-4 rounded-xl border border-border p-3.5">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{a.title}</p>
                      <p className="text-xs text-muted-foreground">{a.due_date ? `Due ${new Date(a.due_date).toLocaleDateString()}` : "No due date"}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Recent notes */}
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>Recent notes</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/notes-summary">Open all</Link>
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              {recentSummaries.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No recent study notes found.</p>
              ) : (
                recentSummaries.map((note: any) => (
                  <div key={note.id} className="flex items-center gap-3 rounded-xl border border-border p-3.5 hover:bg-muted/40">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-gradient-soft">
                      <BookOpen className="h-4 w-4 text-primary" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{note.title}</p>
                      <p className="text-xs text-muted-foreground">{note.created_at ? new Date(note.created_at).toLocaleDateString() : ""}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* AI Assistant Callout */}
          <Card className="border-none bg-brand-gradient text-white">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                <CardTitle className="text-white">AI Study Assistant</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-white/90">
                Ask questions about your course materials, get instant doubt resolution, and generate custom study packages.
              </p>
            </CardContent>
            <CardFooter>
              <Button variant="glass" size="sm" className="text-foreground" asChild>
                <Link to="/chatbot">Ask AI a Question</Link>
              </Button>
            </CardFooter>
          </Card>

          {/* Quick actions */}
          <Card>
            <CardHeader>
              <CardTitle>Quick actions</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-3">
              {quickActions.map(({ label, icon: Icon, to }) => (
                <Link
                  key={label}
                  to={to}
                  className="flex flex-col items-center gap-2 rounded-xl border border-border p-4 text-center text-xs font-medium transition-colors hover:bg-muted"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-gradient-soft">
                    <Icon className="h-4 w-4 text-primary" />
                  </span>
                  {label}
                </Link>
              ))}
            </CardContent>
          </Card>

          {/* Calendar */}
          <MiniCalendar />

          {/* Notifications summary */}
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>Notifications</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/notifications">See all ({unreadNotifs})</Link>
              </Button>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {unreadNotifs > 0 ? `You have ${unreadNotifs} unread notifications.` : "You have no unread notifications."}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

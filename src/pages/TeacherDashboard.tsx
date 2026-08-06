import { Link } from "react-router-dom";
import { Sparkles, Users, TrendingUp, AlertTriangle, ArrowRight, CheckCircle2, Clock, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/shared/PageHeader";
import { useAuth } from "@/contexts/AuthContext";
import { useApi } from "@/hooks/useApi";

export default function TeacherDashboard() {
  const { user } = useAuth();
  const { data: dashboard, loading, error } = useApi<any>("/dashboard/teacher");

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const attendancePct = dashboard?.student_attendance_percentage ?? 0;
  const assignmentStats = dashboard?.assignment_statistics ?? { total_published: 0, submitted: 0, graded: 0 };
  const quizStats = dashboard?.quiz_statistics ?? { total_quizzes: 0, avg_class_score: 0 };
  const pendingReviews = dashboard?.pending_assignment_reviews_count ?? 0;
  const todaysClasses = dashboard?.todays_classes ?? [];
  const announcements = dashboard?.announcements ?? [];

  const summaryStats = [
    { label: "Assigned Courses", value: String(todaysClasses.length), icon: Users, change: "Active" },
    { label: "Avg. Attendance", value: `${attendancePct}%`, icon: CheckCircle2, change: "Overall" },
    { label: "Avg. Quiz Score", value: `${quizStats.avg_class_score}%`, icon: TrendingUp, change: `${quizStats.total_quizzes} quizzes` },
    { label: "Pending Reviews", value: String(pendingReviews), icon: AlertTriangle, change: "Assignments" },
  ];

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${user?.name?.split(" ")[0] ?? "Teacher"}`}
        description="Here's how your classes are performing."
        actions={
          <Button asChild>
            <Link to="/attendance">
              Take attendance <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
        }
      />

      {/* Summary stats */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {summaryStats.map(({ label, value, icon: Icon, change }) => (
          <Card key={label}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft">
                  <Icon className="h-5 w-5 text-primary" />
                </span>
              </div>
              <p className="mt-3 text-2xl font-extrabold">{value}</p>
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="mt-1 text-[11px] font-medium text-success">{change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Today's Classes */}
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Assigned Courses</CardTitle>
                <CardDescription>Active Course Modules</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {todaysClasses.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No courses assigned currently.</p>
              ) : (
                todaysClasses.map((cls: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-xl border border-border p-3.5">
                    <div>
                      <p className="text-sm font-medium">{cls.course}</p>
                      <p className="text-xs text-muted-foreground">Code: {cls.code}</p>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Assignment Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Assignment Statistics</CardTitle>
              <CardDescription>Submission and Grading Metrics</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="rounded-xl border p-3">
                  <p className="text-xl font-bold">{assignmentStats.total_published}</p>
                  <p className="text-xs text-muted-foreground">Published</p>
                </div>
                <div className="rounded-xl border p-3">
                  <p className="text-xl font-bold">{assignmentStats.submitted}</p>
                  <p className="text-xs text-muted-foreground">Submitted</p>
                </div>
                <div className="rounded-xl border p-3">
                  <p className="text-xl font-bold">{assignmentStats.graded}</p>
                  <p className="text-xs text-muted-foreground">Graded</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {/* Announcements */}
          <Card>
            <CardHeader>
              <CardTitle>Announcements</CardTitle>
              <CardDescription>Classroom Updates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {announcements.length === 0 ? (
                <p className="py-2 text-xs text-muted-foreground">No recent announcements posted.</p>
              ) : (
                announcements.map((a: any) => (
                  <div key={a.id} className="rounded-xl border border-border p-3">
                    <p className="text-sm font-medium">{a.title}</p>
                    <p className="text-xs text-muted-foreground">{a.content}</p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

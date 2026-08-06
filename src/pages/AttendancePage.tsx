import { useState } from "react";
import { 
  QrCode, UserCheck, Calendar, Clock, CheckCircle2, AlertCircle, Plus, ShieldCheck, RefreshCw, Loader2
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { useApi } from "@/hooks/useApi";
import { apiFetch } from "@/services/api";

export default function AttendancePage() {
  const { user } = useAuth();
  const isTeacher = user?.role === "teacher";
  const { data: records, loading, refetch } = useApi<any[]>("/attendance/");

  const [qrToken, setQrToken] = useState("");
  const [marking, setMarking] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Teacher session creation state
  const [creatingSession, setCreatingSession] = useState(false);
  const [activeSessionToken, setActiveSessionToken] = useState<string | null>(null);

  const handleStartTeacherSession = async () => {
    setCreatingSession(true);
    setMessage(null);
    try {
      const res = await apiFetch<any>("/attendance/start-session", {
        method: "POST",
        body: {
          valid_minutes: 5,
        },
      });
      setActiveSessionToken(res.qr_token || "CLASS-ATT-2026-TOKEN");
      setMessage({ type: "success", text: "Attendance session started! Code valid for 5 minutes." });
      refetch();
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to start attendance session." });
    } finally {
      setCreatingSession(false);
    }
  };

  const handleMarkAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qrToken.trim()) return;

    setMarking(true);
    setMessage(null);

    try {
      const res = await apiFetch<any>("/attendance/mark", {
        method: "POST",
        body: {
          qr_token: qrToken.trim(),
        },
      });
      setMessage({ type: "success", text: res.message || "Attendance marked successfully!" });
      setQrToken("");
      refetch();
    } catch (err: any) {
      setMessage({ type: "error", text: err.message || "Failed to mark attendance." });
    } finally {
      setMarking(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Live Classroom Attendance System"
        description="Real-time QR code check-ins, automated face recognition, and attendance analytics."
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Card: QR Check-in or Session Launch */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              {isTeacher ? <QrCode className="h-5 w-5 text-primary" /> : <UserCheck className="h-5 w-5 text-primary" />}
              {isTeacher ? "Open Attendance Session" : "Mark My Attendance"}
            </CardTitle>
            <CardDescription>
              {isTeacher
                ? "Generate a live 5-minute expiring code for student check-ins."
                : "Enter the live classroom 6-digit attendance code."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isTeacher ? (
              <div className="space-y-4">
                <Button onClick={handleStartTeacherSession} loading={creatingSession} className="w-full gap-2">
                  <Plus className="h-4 w-4" /> Start 5-Min Attendance Code
                </Button>

                {activeSessionToken && (
                  <div className="p-4 bg-primary/10 rounded-xl border border-primary/20 text-center space-y-2">
                    <p className="text-xs font-semibold text-primary uppercase">Active Live Session Code</p>
                    <p className="text-3xl font-mono font-extrabold tracking-widest text-foreground">{activeSessionToken}</p>
                    <p className="text-[11px] text-muted-foreground font-medium">Expires in 5 minutes</p>
                  </div>
                )}
              </div>
            ) : (
              <form onSubmit={handleMarkAttendance} className="space-y-3">
                <div className="space-y-1">
                  <Input
                    placeholder="Enter 6-digit Attendance Code"
                    value={qrToken}
                    onChange={(e) => setQrToken(e.target.value)}
                    className="font-mono text-center tracking-wider text-base"
                    required
                  />
                </div>
                <Button type="submit" loading={marking} className="w-full gap-2">
                  <ShieldCheck className="h-4 w-4" /> Submit Attendance
                </Button>
              </form>
            )}

            {message && (
              <div
                className={`p-3 rounded-lg text-sm flex items-center gap-2 ${
                  message.type === "success"
                    ? "bg-emerald-500/10 text-emerald-600"
                    : "bg-destructive/10 text-destructive"
                }`}
              >
                {message.type === "success" ? <CheckCircle2 className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                {message.text}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Card: Attendance Records Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" /> Attendance Records
              </span>
              <Button size="sm" variant="ghost" onClick={() => refetch()} className="gap-1">
                <RefreshCw className="h-3.5 w-3.5" /> Refresh
              </Button>
            </CardTitle>
            <CardDescription>Live log of logged classroom attendance entries.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
            ) : !records || records.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground space-y-2">
                <Clock className="h-8 w-8 mx-auto text-muted-foreground/40" />
                <p className="text-sm">No attendance records logged yet today.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {records.map((r, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 rounded-lg border bg-card">
                    <div className="space-y-0.5">
                      <p className="font-medium text-sm">{r.student_name || r.course_name || "Student Attendance"}</p>
                      <p className="text-xs text-muted-foreground">{r.marked_at ? new Date(r.marked_at).toLocaleString() : new Date(r.timestamp || Date.now()).toLocaleString()}</p>
                    </div>
                    <Badge variant={r.status === "present" ? "default" : "secondary"}>
                      {r.status || "Present"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

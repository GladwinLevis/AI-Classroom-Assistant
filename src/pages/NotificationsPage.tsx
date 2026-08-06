import { useState } from "react";
import { 
  Bell, Check, Megaphone, Calendar, Sparkles, CheckCheck, RefreshCw, Loader2
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/hooks/useApi";
import { apiFetch } from "@/services/api";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const { data: notifications, loading, refetch } = useApi<NotificationItem[]>("/notifications/");
  const [markingId, setMarkingId] = useState<string | null>(null);

  const handleMarkAsRead = async (id: string) => {
    setMarkingId(id);
    try {
      await apiFetch(`/notifications/${id}/read`, { method: "POST" });
      refetch();
    } catch (err: any) {
      console.error(err);
    } finally {
      setMarkingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications & Announcements"
        description="Stay updated with course announcements, quiz schedules, assignment deadlines, and system alerts."
      />

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-4 border-b">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Bell className="h-5 w-5 text-primary" /> System & Classroom Feed
            </CardTitle>
            <CardDescription>Real-time updates from teachers and course administrators.</CardDescription>
          </div>
          <Button size="sm" variant="outline" onClick={() => refetch()} className="gap-2">
            <RefreshCw className="h-4 w-4" /> Refresh
          </Button>
        </CardHeader>
        <CardContent className="pt-4">
          {loading ? (
            <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
          ) : !notifications || notifications.length === 0 ? (
            <div className="text-center py-16 text-muted-foreground space-y-2">
              <Bell className="h-10 w-10 mx-auto text-muted-foreground/30" />
              <h3 className="font-medium text-base">No Notifications</h3>
              <p className="text-xs">You are all caught up! No unread notifications found.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((n) => (
                <div
                  key={n.id}
                  className={`p-4 rounded-xl border transition-all flex items-start justify-between gap-4 ${
                    n.is_read ? "bg-card opacity-70 border-border" : "bg-primary/5 border-primary/30"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary mt-0.5">
                      {n.type === "announcement" ? <Megaphone className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-sm">{n.title}</p>
                        {!n.is_read && <Badge variant="default" className="text-[10px]">New</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">{n.message}</p>
                      <p className="text-[10px] text-muted-foreground">{new Date(n.created_at).toLocaleString()}</p>
                    </div>
                  </div>

                  {!n.is_read && (
                    <Button
                      size="sm"
                      variant="ghost"
                      loading={markingId === n.id}
                      onClick={() => handleMarkAsRead(n.id)}
                      className="shrink-0 gap-1 text-xs"
                    >
                      <Check className="h-3.5 w-3.5" /> Mark Read
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

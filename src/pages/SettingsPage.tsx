import { useState } from "react";
import { 
  Settings, Bell, Lock, Shield, Moon, Sun, Save, CheckCircle2, KeyRound
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

export default function SettingsPage() {
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [aiAlerts, setAiAlerts] = useState(true);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [savingMessage, setSavingMessage] = useState<string | null>(null);

  const handleSaveSettings = (e: React.FormEvent) => {
    e.preventDefault();
    setSavingMessage("Preferences saved successfully!");
    setTimeout(() => setSavingMessage(null), 3000);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application & System Settings"
        description="Configure workspace preferences, notifications, and security options."
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Security & Password Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Lock className="h-4 w-4 text-primary" /> Security & Password
            </CardTitle>
            <CardDescription>Update your login credentials.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSaveSettings} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="currPw">Current Password</Label>
                <Input
                  id="currPw"
                  type="password"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="newPw">New Password</Label>
                <Input
                  id="newPw"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>

              {savingMessage && (
                <div className="p-3 bg-emerald-500/10 text-emerald-600 text-sm rounded-lg flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> {savingMessage}
                </div>
              )}

              <Button type="submit" className="gap-2">
                <Save className="h-4 w-4" /> Update Password
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Notifications & AI Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Bell className="h-4 w-4 text-primary" /> Notification Preferences
            </CardTitle>
            <CardDescription>Manage how you receive updates and AI insights.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg border">
              <div>
                <p className="font-medium text-sm">Email Notifications</p>
                <p className="text-xs text-muted-foreground">Receive course announcements and quiz updates via email.</p>
              </div>
              <input
                type="checkbox"
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
                className="h-4 w-4 rounded accent-primary cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg border">
              <div>
                <p className="font-medium text-sm">AI Study Alerts</p>
                <p className="text-xs text-muted-foreground">Receive AI recommendations when weak topics are detected.</p>
              </div>
              <input
                type="checkbox"
                checked={aiAlerts}
                onChange={(e) => setAiAlerts(e.target.checked)}
                className="h-4 w-4 rounded accent-primary cursor-pointer"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

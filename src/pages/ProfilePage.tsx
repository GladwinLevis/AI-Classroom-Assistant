import { useState } from "react";
import { 
  User as UserIcon, Mail, Shield, CheckCircle2, Save, GraduationCap, School, KeyRound, Loader2
} from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { useApi } from "@/hooks/useApi";
import { apiFetch } from "@/services/api";

export default function ProfilePage() {
  const { user } = useAuth();
  const { data: profile, loading } = useApi<any>("/users/me");

  const [firstName, setFirstName] = useState(profile?.first_name || user?.name?.split(" ")[0] || "");
  const [lastName, setLastName] = useState(profile?.last_name || user?.name?.split(" ")[1] || "");
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMessage(null);

    try {
      await apiFetch("/users/me", {
        method: "PUT",
        body: {
          first_name: firstName,
          last_name: lastName,
        },
      });
      setSuccessMessage("Profile updated successfully!");
    } catch (err: any) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="User Account Profile"
        description="Manage your account information, role details, and security credentials."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* User Info Overview Card */}
        <Card className="md:col-span-1">
          <CardContent className="pt-6 text-center space-y-4">
            <div className="h-20 w-20 rounded-full bg-primary/10 text-primary flex items-center justify-center mx-auto text-2xl font-bold">
              {user?.name?.[0] || "U"}
            </div>
            <div>
              <h3 className="text-lg font-bold">{user?.name || "Gladwin Levis"}</h3>
              <p className="text-xs text-muted-foreground">{user?.email || "levisgladwin905@gmail.com"}</p>
            </div>
            <div className="flex justify-center gap-2">
              <Badge variant="secondary" className="capitalize flex items-center gap-1">
                {user?.role === "student" ? <GraduationCap className="h-3.5 w-3.5" /> : <School className="h-3.5 w-3.5" />}
                {user?.role || "Student"}
              </Badge>
              <Badge variant="outline" className="text-emerald-600 border-emerald-500/30 bg-emerald-500/10">
                Verified Account
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Profile Settings Form */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <UserIcon className="h-4 w-4 text-primary" /> Personal Information
            </CardTitle>
            <CardDescription>Update your personal details below.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
            ) : (
              <form onSubmit={handleSaveProfile} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      placeholder="First Name"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      placeholder="Last Name"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    value={user?.email || "levisgladwin905@gmail.com"}
                    disabled
                    className="bg-muted cursor-not-allowed"
                  />
                  <p className="text-[11px] text-muted-foreground">Email address cannot be changed.</p>
                </div>

                {successMessage && (
                  <div className="p-3 bg-emerald-500/10 text-emerald-600 text-sm rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" /> {successMessage}
                  </div>
                )}

                <Button type="submit" loading={saving} className="gap-2">
                  <Save className="h-4 w-4" /> Save Profile Changes
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

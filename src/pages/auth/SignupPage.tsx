import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Mail, Lock, User, GraduationCap, School } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/utils/cn";
import { apiFetch } from "@/services/api";
import type { UserRole } from "@/types";

const signupSchema = z
  .object({
    name: z.string().min(2, "Enter your full name"),
    email: z.string().email("Enter a valid email address"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type SignupFormValues = z.infer<typeof signupSchema>;

export default function SignupPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<UserRole>("student");
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<SignupFormValues>({ resolver: zodResolver(signupSchema) });

  const emailValue = watch("email", "");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [signupError, setSignupError] = useState<string | null>(null);

  const getEmailSuggestions = (val: string) => {
    if (!val || val.length < 2) return [];
    if (!val.includes("@")) {
      return [`${val}@gmail.com`, `${val}@outlook.com`, `${val}@yahoo.com`];
    }
    return [];
  };
  const suggestions = getEmailSuggestions(emailValue);

  const onSubmit = async (data: SignupFormValues) => {
    setSignupError(null);
    try {
      const nameParts = data.name.trim().split(" ");
      await apiFetch("/auth/register", {
        method: "POST",
        body: {
          first_name: nameParts[0] || "",
          last_name: nameParts.slice(1).join(" ") || "",
          email: data.email,
          password: data.password,
          role,
        },
      });
      navigate("/otp-verification", { state: { email: data.email } });
    } catch (err: any) {
      if (err.status === 409 || err.message?.includes("409") || err.message?.toLowerCase().includes("already exists")) {
        setSignupError("An account with this email address already exists.");
      } else {
        setSignupError(err.message || "Signup failed. Please try again.");
      }
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <h1 className="text-2xl font-bold">Create your account</h1>
      <p className="mt-1 text-sm text-muted-foreground">Join thousands of students and teachers using AI Classroom Assistant.</p>

      <div className="mt-6 grid grid-cols-2 gap-2 rounded-xl bg-muted p-1">
        {(["student", "teacher"] as UserRole[]).map((r) => (
          <button
            key={r}
            type="button"
            onClick={() => setRole(r)}
            className={cn(
              "flex items-center justify-center gap-2 rounded-lg py-2 text-sm font-medium capitalize transition-all",
              role === r ? "bg-card shadow-sm text-foreground" : "text-muted-foreground"
            )}
            aria-pressed={role === r}
          >
            {r === "student" ? <GraduationCap className="h-4 w-4" /> : <School className="h-4 w-4" />}
            {r}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
        <div className="space-y-1.5">
          <Label htmlFor="name">Full name</Label>
          <div className="relative">
            <User className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground z-10" />
            <Input id="name" placeholder="Your full name" className="pl-9" error={!!errors.name} {...register("name")} />
          </div>
          {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
        </div>

        <div className="space-y-1.5 relative">
          <Label htmlFor="email">Email address</Label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground z-10" />
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@school.edu"
              className="pl-9"
              error={!!errors.email}
              {...register("email")}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            />
          </div>

          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-50 left-0 right-0 top-full mt-1 bg-popover border border-border shadow-xl rounded-xl overflow-hidden p-1 space-y-0.5">
              <p className="text-[10px] font-semibold text-muted-foreground px-2.5 py-1 uppercase tracking-wider">Quick Suggestions</p>
              {suggestions.map((s, idx) => (
                <div
                  key={idx}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    setValue("email", s, { shouldValidate: true });
                    setShowSuggestions(false);
                  }}
                  className="px-2.5 py-1.5 text-xs rounded-lg cursor-pointer hover:bg-primary/10 hover:text-primary transition-all flex items-center justify-between font-medium"
                >
                  <span>{s}</span>
                  <span className="text-[10px] text-muted-foreground">Select</span>
                </div>
              ))}
            </div>
          )}

          {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              className="pl-9 pr-10"
              error={!!errors.password}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <div className="relative">
            <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="confirmPassword"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              className="pl-9"
              error={!!errors.confirmPassword}
              {...register("confirmPassword")}
            />
          </div>
          {errors.confirmPassword && <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>}
        </div>

        {signupError && (
          <div className="rounded-lg bg-destructive/10 p-3 text-sm font-medium text-destructive space-y-1">
            <p>{signupError}</p>
            {signupError.includes("already exists") && (
              <p className="text-xs font-semibold text-primary">
                Already registered? <Link to="/login" className="underline font-bold">Click here to Log In</Link>
              </p>
            )}
          </div>
        )}

        <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-primary hover:underline">
          Log in
        </Link>
      </p>
    </motion.div>
  );
}

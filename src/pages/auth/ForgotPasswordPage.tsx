import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { Mail, ArrowLeft, MailCheck } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { apiFetch } from "@/services/api";

const schema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
});

type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormValues) => {
    setErrorMsg(null);
    try {
      await apiFetch("/auth/forgot-password", {
        method: "POST",
        body: { email: data.email },
      });
      setSent(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to send reset email. Please try again.");
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
      <Link to="/login" className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" /> Back to login
      </Link>

      {!sent ? (
        <>
          <h1 className="text-2xl font-bold">Forgot your password?</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter the email linked to your account and we'll send a reset link.
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="email">Email address</Label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input id="email" type="email" placeholder="you@school.edu" className="pl-9" error={!!errors.email} {...register("email")} />
              </div>
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>

            <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>
              Send reset link
            </Button>
          </form>
        </>
      ) : (
        <div className="flex flex-col items-center py-6 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-success/10">
            <MailCheck className="h-7 w-7 text-success" />
          </span>
          <h1 className="mt-4 text-xl font-bold">Check your inbox</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            We've sent a password reset link to <span className="font-medium text-foreground">{getValues("email")}</span>.
          </p>
          <Button variant="outline" className="mt-6" onClick={() => setSent(false)}>
            Use a different email
          </Button>
        </div>
      )}
    </motion.div>
  );
}

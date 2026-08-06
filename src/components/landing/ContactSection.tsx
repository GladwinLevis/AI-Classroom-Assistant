import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Mail, Phone, MapPin, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const schema = z.object({
  name: z.string().min(2, "Enter your name"),
  email: z.string().email("Enter a valid email"),
  message: z.string().min(10, "Message should be at least 10 characters"),
});
type FormValues = z.infer<typeof schema>;

export function ContactSection() {
  const [sent, setSent] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (data: FormValues) => {
    // Contact form submission
    setSent(true);
    reset();
    setTimeout(() => setSent(false), 4000);
  };

  return (
    <section id="contact" className="py-20 sm:py-28">
      <div className="container">
        <div className="grid gap-10 rounded-3xl border border-border bg-card p-8 shadow-soft lg:grid-cols-2 lg:p-12">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-primary">Get in touch</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight">Questions? We'd love to help.</h2>
            <p className="mt-4 text-muted-foreground">
              Whether you're a student exploring the free plan or a school planning a full rollout, our team responds within one business day.
            </p>

            <div className="mt-8 space-y-4">
              <div className="flex items-center gap-3 text-sm">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft">
                  <Mail className="h-4 w-4 text-primary" />
                </span>
                hello@aiclassroomassistant.app
              </div>
              <div className="flex items-center gap-3 text-sm">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft">
                  <Phone className="h-4 w-4 text-primary" />
                </span>
                +91 44 4567 8900
              </div>
              <div className="flex items-center gap-3 text-sm">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft">
                  <MapPin className="h-4 w-4 text-primary" />
                </span>
                Chennai, Tamil Nadu, India
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="contact-name">Name</Label>
              <Input id="contact-name" placeholder="Your name" error={!!errors.name} {...register("name")} />
              {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contact-email">Email</Label>
              <Input id="contact-email" type="email" placeholder="you@school.edu" error={!!errors.email} {...register("email")} />
              {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contact-message">Message</Label>
              <Textarea id="contact-message" placeholder="Tell us what you're looking for..." error={!!errors.message} {...register("message")} />
              {errors.message && <p className="text-xs text-destructive">{errors.message.message}</p>}
            </div>
            <Button type="submit" className="w-full" size="lg" loading={isSubmitting}>
              {sent ? (
                <>
                  <CheckCircle2 className="h-4 w-4" /> Message sent
                </>
              ) : (
                "Send message"
              )}
            </Button>
          </form>
        </div>
      </div>
    </section>
  );
}

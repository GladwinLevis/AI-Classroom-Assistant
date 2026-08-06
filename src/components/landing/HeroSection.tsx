import { Link } from "react-router-dom";
import { ArrowRight, PlayCircle, Sparkles, TrendingUp, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";

export function HeroSection() {
  return (
    <section id="top" className="relative overflow-hidden pb-20 pt-14 sm:pb-28 sm:pt-20">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[640px] aura-bg opacity-60" />

      <div className="container relative grid items-center gap-14 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3.5 py-1.5 text-xs font-medium text-primary-700 dark:text-primary-300">
            <Sparkles className="h-3.5 w-3.5" /> Now with real-time AI doubt solving
          </span>

          <h1 className="mt-5 text-4xl font-extrabold leading-[1.1] tracking-tight sm:text-5xl lg:text-[54px]">
            Your classroom, <span className="text-gradient">understood by AI.</span>
          </h1>

          <p className="mt-5 max-w-lg text-base text-muted-foreground sm:text-lg">
            Attendance, notes, doubts, quizzes and grading — AI Classroom Assistant turns everyday
            classroom work into one calm, intelligent workspace for students and teachers.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button size="lg" asChild>
              <Link to="/signup">
                Start free trial <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline">
              <PlayCircle className="h-4 w-4" /> Watch 2-min demo
            </Button>
          </div>

          <div className="mt-8 flex items-center gap-4 text-sm text-muted-foreground">
            Trusted by students and teachers nationwide
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.15 }}
          className="relative mx-auto w-full max-w-md lg:max-w-none"
        >
          <div className="relative rounded-[2rem] border border-border bg-card p-3 shadow-glass">
            <div className="rounded-[1.5rem] bg-brand-gradient p-5 text-white">
              <div className="flex items-center justify-between">
                <p className="text-xs font-medium text-white/80">AI Lecture Summary</p>
                <Sparkles className="h-4 w-4" />
              </div>
              <p className="mt-3 text-sm font-semibold leading-relaxed">
                "Key concepts and step-by-step summary generated from uploaded document."
              </p>
            </div>

            <div className="mt-4 space-y-3 p-2">
              {[
                { label: "Attendance today", value: "Live", icon: CheckCircle2 },
                { label: "Quiz avg. score", value: "Active", icon: TrendingUp },
              ].map(({ label, value, icon: Icon }) => (
                <div key={label} className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3">
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient-soft">
                      <Icon className="h-4 w-4 text-primary" />
                    </span>
                    <span className="text-sm font-medium">{label}</span>
                  </div>
                  <span className="text-sm font-bold">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <motion.div
            animate={{ y: [0, -12, 0] }}
            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -left-6 -top-6 hidden rounded-2xl border border-border bg-card px-4 py-3 shadow-glass sm:block"
          >
            <p className="text-xs text-muted-foreground">Quiz engine</p>
            <p className="text-sm font-bold">Auto-generated</p>
          </motion.div>

          <motion.div
            animate={{ y: [0, 10, 0] }}
            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -bottom-6 -right-4 hidden rounded-2xl border border-border bg-card px-4 py-3 shadow-glass sm:block"
          >
            <p className="text-xs text-muted-foreground">Assignment grader</p>
            <p className="text-sm font-bold">AI Evaluated</p>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}

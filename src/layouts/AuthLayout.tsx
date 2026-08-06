import { Outlet, Link } from "react-router-dom";
import { Sparkles, ShieldCheck, Zap, BarChart3 } from "lucide-react";
import { motion } from "framer-motion";

const highlights = [
  { icon: Zap, text: "Instant AI-generated lecture summaries" },
  { icon: BarChart3, text: "Live attendance and performance analytics" },
  { icon: ShieldCheck, text: "Private, secure, classroom-grade data handling" },
];

export default function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative flex flex-col justify-between overflow-hidden bg-foreground px-8 py-10 text-background lg:px-14 lg:py-14">
        <div className="pointer-events-none absolute inset-0 aura-bg opacity-70" />
        <div className="relative z-10 flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient">
            <Sparkles className="h-5 w-5 text-white" />
          </span>
          <span className="font-bold">AI Classroom Assistant</span>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative z-10 max-w-md"
        >
          <h2 className="text-3xl font-bold leading-tight lg:text-4xl">
            One assistant for every classroom moment.
          </h2>
          <p className="mt-3 text-background/70">
            From attendance to AI-graded assignments, everything your school needs, in one calm workspace.
          </p>
          <ul className="mt-8 space-y-4">
            {highlights.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-background/85">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <Icon className="h-4 w-4" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </motion.div>

        <p className="relative z-10 text-xs text-background/50">
          © {new Date().getFullYear()} AI Classroom Assistant. All rights reserved.
        </p>
      </div>

      <div className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">
          <Outlet />
          <p className="mt-8 text-center text-xs text-muted-foreground">
            Need help?{" "}
            <Link to="/#contact" className="text-primary hover:underline">
              Contact support
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

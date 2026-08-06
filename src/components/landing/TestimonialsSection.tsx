import { motion } from "framer-motion";
import { Sparkles, Shield, Heart } from "lucide-react";

export function TestimonialsSection() {
  return (
    <section id="testimonials" className="py-16">
      <div className="container">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-3xl rounded-3xl border border-border bg-brand-gradient-soft p-8 text-center sm:p-12"
        >
          <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-gradient text-white">
            <Sparkles className="h-6 w-6" />
          </span>
          <h2 className="mt-4 text-2xl font-bold tracking-tight sm:text-3xl">Built for Next-Gen Education</h2>
          <p className="mt-3 text-sm text-muted-foreground sm:text-base">
            Empowering students and educators with AI-driven learning tools, automated assessment, and real-time classroom analytics.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-6 text-xs font-medium text-muted-foreground">
            <span className="flex items-center gap-1.5"><Shield className="h-4 w-4 text-primary" /> Data Privacy First</span>
            <span className="flex items-center gap-1.5"><Heart className="h-4 w-4 text-primary" /> Student-Centered Design</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

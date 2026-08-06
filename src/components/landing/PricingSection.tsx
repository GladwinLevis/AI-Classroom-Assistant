import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowRight, Mail } from "lucide-react";

export function PricingSection() {
  return (
    <section id="pricing" className="py-16 sm:py-24">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary">Access & Deployment</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Platform Availability</h2>
          <p className="mt-4 text-muted-foreground">
            AI Classroom Assistant is available for institution-wide deployment and single classroom access.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mx-auto mt-12 max-w-2xl rounded-3xl border border-border bg-card p-8 shadow-soft text-center sm:p-10"
        >
          <h3 className="text-xl font-bold">Ready to get started?</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Create an account to explore all features instantly or contact our team for custom institutional setup.
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button asChild size="lg">
              <Link to="/signup">Get Started Free <ArrowRight className="h-4 w-4 ml-1" /></Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <a href="#contact"><Mail className="h-4 w-4 mr-1" /> Contact Sales</a>
            </Button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/utils/cn";

const faqs = [
  {
    q: "Does AI Classroom Assistant work for both students and teachers?",
    a: "Yes. Students get a dashboard for attendance, notes, doubts and quizzes, while teachers get analytics, grading tools and class-wide insights — all in the same product.",
  },
  {
    q: "Is my classroom data kept private?",
    a: "Every school gets isolated, encrypted storage. We never share student data with third parties, and admins control exactly who can access what.",
  },
  {
    q: "Can I upload my own notes for the AI to summarize?",
    a: "Yes — PDF, DOCX and PPT uploads are all supported. The AI extracts key points, definitions and generates a downloadable summary in seconds.",
  },
  {
    q: "What happens after the free trial?",
    a: "You can continue on the free Starter plan indefinitely with reduced limits, or upgrade to Pro or School at any time — no credit card required to start.",
  },
  {
    q: "Can schools roll this out to multiple classrooms?",
    a: "The School plan includes bulk onboarding, admin analytics and role-based access so IT teams can deploy across an entire campus.",
  },
];

export function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="py-20 sm:py-28">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary">FAQ</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Frequently asked questions</h2>
        </div>

        <div className="mx-auto mt-12 max-w-2xl space-y-3">
          {faqs.map((faq, i) => {
            const isOpen = openIndex === i;
            return (
              <div key={faq.q} className="rounded-2xl border border-border bg-card">
                <button
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                  onClick={() => setOpenIndex(isOpen ? null : i)}
                  aria-expanded={isOpen}
                >
                  <span className="text-sm font-medium sm:text-base">{faq.q}</span>
                  <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted-foreground transition-transform", isOpen && "rotate-180")} />
                </button>
                <div
                  className={cn(
                    "grid transition-all duration-300 ease-out",
                    isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                  )}
                >
                  <div className="overflow-hidden">
                    <p className="px-5 pb-4 text-sm text-muted-foreground">{faq.a}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

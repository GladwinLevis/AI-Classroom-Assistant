import {
  CalendarCheck,
  FileText,
  MessageSquareText,
  ClipboardCheck,
  Brain,
  BarChart3,
} from "lucide-react";
import { motion } from "framer-motion";

const features = [
  {
    icon: CalendarCheck,
    title: "Smart attendance",
    description: "Mark, track and export attendance with automatic monthly trend graphs for every student.",
  },
  {
    icon: FileText,
    title: "AI notes summarizer",
    description: "Upload PDFs, DOCX or slides and get key points, definitions and takeaways in seconds.",
  },
  {
    icon: MessageSquareText,
    title: "AI doubt chatbot",
    description: "A ChatGPT-style tutor that explains concepts, solves problems and cites the source material.",
  },
  {
    icon: ClipboardCheck,
    title: "Assignment checker",
    description: "Automatic grammar scoring, plagiarism checks and rubric-based feedback on every submission.",
  },
  {
    icon: Brain,
    title: "Quiz generator",
    description: "Turn any set of notes into a timed multiple-choice quiz with adjustable difficulty.",
  },
  {
    icon: BarChart3,
    title: "Insight dashboards",
    description: "Teachers get live class analytics; students get a clear view of their own progress.",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-20 sm:py-28">
      <div className="container">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-primary">Everything included</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">
            Built for the way classrooms actually run
          </h2>
          <p className="mt-4 text-muted-foreground">
            No separate tools for attendance, grading and doubts. AI Classroom Assistant brings them
            together with AI that understands your syllabus.
          </p>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, description }, i) => (
            <motion.div
              key={title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.05 }}
              className="group rounded-2xl border border-border bg-card p-6 shadow-soft transition-all hover:-translate-y-1 hover:shadow-glass"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-gradient-soft transition-colors group-hover:bg-brand-gradient">
                <Icon className="h-5 w-5 text-primary transition-colors group-hover:text-white" />
              </span>
              <h3 className="mt-4 font-semibold">{title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

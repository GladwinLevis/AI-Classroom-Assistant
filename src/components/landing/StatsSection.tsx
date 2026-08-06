import { motion } from "framer-motion";

const highlights = [
  { value: "AI-Powered", label: "Intelligent classroom assistant" },
  { value: "Real-Time", label: "Instant attendance & insights" },
  { value: "Enterprise", label: "Grade security & privacy" },
  { value: "24/7", label: "Available study companion" },
];

export function StatsSection() {
  return (
    <section className="border-y border-border bg-brand-gradient-soft py-16">
      <div className="container">
        <div className="grid grid-cols-2 gap-8 lg:grid-cols-4">
          {highlights.map((item, i) => (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
              className="text-center"
            >
              <p className="text-2xl font-extrabold text-gradient sm:text-3xl">{item.value}</p>
              <p className="mt-1.5 text-sm text-muted-foreground">{item.label}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

import { motion } from "framer-motion";
import { Card } from "../../components/ui";

export default function StudentDashboard() {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--fg)]">Welcome back</h2>
        <p className="text-sm text-[var(--fg-muted)]">Your academic hub at a glance</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <h3 className="mb-2 text-sm font-semibold text-[var(--fg)]">Recent Activity</h3>
          <p className="text-sm text-[var(--fg-subtle)]">No recent activity yet.</p>
        </Card>
        <Card>
          <h3 className="mb-2 text-sm font-semibold text-[var(--fg)]">Quick Links</h3>
          <p className="text-sm text-[var(--fg-subtle)]">Your important resources will appear here.</p>
        </Card>
      </div>
    </motion.div>
  );
}

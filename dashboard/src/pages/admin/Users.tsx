import { motion } from "framer-motion";
import { Card } from "../../components/ui";

export default function AdminUsers() {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-[var(--fg)]">Student Directory</h2>
        <p className="text-sm text-[var(--fg-muted)]">Manage student records and Telegram links</p>
      </div>
      <Card>
        <div className="flex h-64 items-center justify-center text-sm text-[var(--fg-subtle)]">
          Interactive data table with search, filter, and sort will be built here.
        </div>
      </Card>
    </motion.div>
  );
}

import React, { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Building2, CreditCard, Lock, Mail, ChevronRight, ChevronLeft, Check, Sparkles, Moon, Sun, Search } from "lucide-react";
import { Button, Input, cn } from "../../components/ui";
import { useTheme } from "../../lib/theme";

type Step = 1 | 2 | 3;

export default function Register() {
  const { theme, toggleTheme } = useTheme();

  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Step 1: Institution
  const [institutionSearch, setInstitutionSearch] = useState("");
  const [selectedInstitution, setSelectedInstitution] = useState<string | null>(null);

  // Step 2: Student ID
  const [studentId, setStudentId] = useState("");
  const [_studentName, setStudentName] = useState("");
  const [_idVerified, setIdVerified] = useState(false);

  // Step 3: Password
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [email, setEmail] = useState("");

  // Mock institutions (will be wired to API)
  const institutions = [
    { slug: "sit", name: "Semonegna Institute of Technology" },
  ];

  const filteredInstitutions = institutions.filter((i) =>
    i.name.toLowerCase().includes(institutionSearch.toLowerCase()),
  );

  const handleVerifyId = async () => {
    if (!studentId.trim()) {
      setError("Please enter your Student ID.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      // TODO: Wire to backend - verify student ID exists for this institution
      // const res = await api.verifyStudentId(selectedInstitution, studentId);
      // setStudentName(res.full_name);
      setStudentName("Student");
      setIdVerified(true);
      setStep(3);
    } catch (err: any) {
      setError(err?.detail || "Student ID not found for this institution.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      // TODO: Wire to backend - create student password
      // await api.registerStudent({ institution: selectedInstitution, studentId, password, email });
      setError("Registration backend coming soon.");
    } catch (err: any) {
      setError(err?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  const stepLabels = ["Institution", "Student ID", "Create Password"];

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg)] px-4">
      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 z-50 rounded-full border border-[var(--border)] bg-[var(--bg-elevated)] p-2.5 text-[var(--fg-muted)] hover:text-[var(--fg)] transition-colors"
      >
        {theme === "night" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full max-w-sm"
      >
        {/* Logo */}
        <div className="mb-6 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent)] text-[var(--accent-fg)]">
            <Sparkles className="h-6 w-6" />
          </div>
          <h1 className="text-xl font-bold text-[var(--fg)]">Create Account</h1>
          <p className="mt-1 text-sm text-[var(--fg-muted)]">Join your academic hub</p>
        </div>

        {/* Progress Steps */}
        <div className="mb-6 flex items-center justify-center gap-2">
          {stepLabels.map((label, i) => {
            const stepNum = (i + 1) as Step;
            const isActive = step === stepNum;
            const isComplete = step > stepNum;
            return (
              <React.Fragment key={label}>
                {i > 0 && <div className={cn("h-px w-8", isComplete ? "bg-[var(--accent)]" : "bg-[var(--border)]")} />}
                <div className="flex items-center gap-1.5">
                  <div
                    className={cn(
                      "flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold transition-colors",
                      isActive ? "bg-[var(--accent)] text-[var(--accent-fg)]" : isComplete ? "bg-[var(--accent)] text-[var(--accent-fg)]" : "bg-[var(--surface)] text-[var(--fg-subtle)]",
                    )}
                  >
                    {isComplete ? <Check className="h-3 w-3" /> : stepNum}
                  </div>
                  <span className={cn("hidden text-[11px] font-medium sm:inline", isActive ? "text-[var(--fg)]" : "text-[var(--fg-subtle)]")}>
                    {label}
                  </span>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-3">
              <Input
                label="Search your institution"
                placeholder="Type to search..."
                value={institutionSearch}
                onChange={(e) => setInstitutionSearch(e.target.value)}
                icon={<Search className="h-4 w-4" />}
              />
              <div className="max-h-48 overflow-y-auto rounded-[var(--radius-sm)] border border-[var(--border)]">
                {filteredInstitutions.map((inst) => (
                  <button
                    key={inst.slug}
                    onClick={() => { setSelectedInstitution(inst.slug); setStep(2); setError(""); }}
                    className={cn(
                      "flex w-full items-center gap-3 px-4 py-3 text-left text-sm transition-colors",
                      selectedInstitution === inst.slug ? "bg-[var(--surface)] text-[var(--fg)]" : "text-[var(--fg-muted)] hover:bg-[var(--surface)]",
                    )}
                  >
                    <Building2 className="h-4 w-4 shrink-0 text-[var(--fg-subtle)]" />
                    <span className="flex-1">{inst.name}</span>
                    <ChevronRight className="h-4 w-4 text-[var(--fg-subtle)]" />
                  </button>
                ))}
                {filteredInstitutions.length === 0 && (
                  <p className="px-4 py-3 text-sm text-[var(--fg-subtle)]">No institutions found.</p>
                )}
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
              <Input
                label="Student ID Number"
                placeholder="SIT-ST-2029-00034"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                icon={<CreditCard className="h-4 w-4" />}
              />
              {error && (
                <p className="rounded-[var(--radius-sm)] border border-[var(--danger)]/20 bg-[var(--danger)]/5 px-3 py-2 text-xs text-[var(--danger)]">{error}</p>
              )}
              <div className="flex gap-3">
                <Button variant="secondary" onClick={() => { setStep(1); setError(""); }}>
                  <ChevronLeft className="h-4 w-4" /> Back
                </Button>
                <Button loading={loading} onClick={handleVerifyId} className="flex-1">
                  Verify ID
                </Button>
              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
              <form onSubmit={handleRegister} className="space-y-4">
                <Input
                  label="Create Password"
                  type="password"
                  placeholder="Min 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  icon={<Lock className="h-4 w-4" />}
                />
                <Input
                  label="Confirm Password"
                  type="password"
                  placeholder="Repeat password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  icon={<Lock className="h-4 w-4" />}
                />
                <Input
                  label="Email (Optional)"
                  type="email"
                  placeholder="your@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  icon={<Mail className="h-4 w-4" />}
                />
                <p className="text-[11px] text-[var(--fg-subtle)]">
                  Adding email enables Google Sign-In for faster future access.
                </p>
                {error && (
                  <p className="rounded-[var(--radius-sm)] border border-[var(--danger)]/20 bg-[var(--danger)]/5 px-3 py-2 text-xs text-[var(--danger)]">{error}</p>
                )}
                <div className="flex gap-3">
                  <Button variant="secondary" type="button" onClick={() => { setStep(2); setError(""); }}>
                    <ChevronLeft className="h-4 w-4" /> Back
                  </Button>
                  <Button type="submit" loading={loading} className="flex-1">
                    Create Account
                  </Button>
                </div>
              </form>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Links */}
        <p className="mt-6 text-center text-xs text-[var(--fg-subtle)]">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-[var(--fg-muted)] hover:text-[var(--fg)] underline underline-offset-2 transition-colors">
            Sign in
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

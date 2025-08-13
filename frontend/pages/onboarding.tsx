// pages/onboarding.tsx
import { useRouter } from "next/router";
import OnboardingModal from "@/components/OnboardingModal";
import { useState } from "react";

export default function OnboardingPage() {
  const router = useRouter();
  const [open] = useState(true); // always open; no cancel

  return (
    <>
      <OnboardingModal
        isOpen={open}
        onClose={() => { /* no-op: cannot close */ }}
        hideCancel={true}
        onSaved={() => {
          // after successful PUT, go home
          router.replace("/");
        }}
      />
      {/* Fallback skeleton (never shown if modal is open) */}
      <div className="min-h-screen flex items-center justify-center" />
    </>
  );
}

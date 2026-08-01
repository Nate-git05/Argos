"use client";

import { X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

export function RegistrationModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [submitted, setSubmitted] = useState(false);
  const firstInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;

    setSubmitted(false);
    firstInputRef.current?.focus();

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // No registration API exists yet -- this is UI-only for now, so the
    // "success" state below is purely local, not a confirmed submission.
    setSubmitted(true);
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-heading/40 backdrop-blur-sm"
      />

      <div className="relative w-full max-w-sm rounded-xl border border-border bg-surface p-6 shadow-xl shadow-heading/10 sm:p-7">
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute top-4 right-4 rounded-md p-1 text-muted transition-colors hover:bg-surface-alt hover:text-heading cursor-pointer"
        >
          <X className="h-4 w-4" strokeWidth={2} />
        </button>

        {submitted ? (
          <div className="py-4 text-center">
            <p className="text-base font-medium text-heading">You&apos;re on the list.</p>
            <p className="mt-1.5 text-sm text-body">We&apos;ll be in touch with updates.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <h2 className="text-lg font-semibold text-heading">Register</h2>

            <div className="mt-5 flex flex-col gap-3.5">
              <div className="flex gap-3">
                <div className="flex-1">
                  <label htmlFor="firstName" className="mb-1 block text-xs font-medium text-muted">
                    First name
                  </label>
                  <input
                    ref={firstInputRef}
                    id="firstName"
                    name="firstName"
                    type="text"
                    required
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-heading outline-none transition-colors focus:border-teal-500"
                  />
                </div>
                <div className="flex-1">
                  <label htmlFor="lastName" className="mb-1 block text-xs font-medium text-muted">
                    Last name
                  </label>
                  <input
                    id="lastName"
                    name="lastName"
                    type="text"
                    required
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-heading outline-none transition-colors focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="mb-1 block text-xs font-medium text-muted">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-heading outline-none transition-colors focus:border-teal-500"
                />
              </div>
            </div>

            <p className="mt-4 text-xs text-muted">
              Register to get updates on new features and changes to Argos.
            </p>

            <button
              type="submit"
              className="mt-5 w-full rounded-lg bg-teal-500 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-teal-700 cursor-pointer"
            >
              Submit
            </button>
          </form>
        )}
      </div>
    </div>,
    document.body,
  );
}

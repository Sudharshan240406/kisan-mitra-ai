"use client";

import React, { useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SmartphoneCallScreen } from "./SmartphoneCallScreen";

interface DemoModeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

/* ════════════════════════════════════════════════════════════
   DemoModeModal — Crash-safe modal wrapper.

   Crash-fix notes:
   - Locks body scroll when modal is open to prevent competing
     scroll listeners from interfering with internal scroll.
   - Uses pointer-events and overflow isolation on the backdrop.
   - AnimatePresence key is stable (does not depend on random state).
   ════════════════════════════════════════════════════════════ */

export function DemoModeModal({ isOpen, onClose }: DemoModeModalProps) {
  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = prev;
      };
    }
  }, [isOpen]);

  // Close on Escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      return () => document.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, handleKeyDown]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          key="demo-modal-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          // Backdrop — click outside to close
          className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/80 backdrop-blur-md p-4 pt-8"
          onClick={(e) => {
            // Only close if clicking the backdrop itself
            if (e.target === e.currentTarget) onClose();
          }}
          // Prevent scroll events on backdrop from bubbling to page
          style={{ overscrollBehavior: "contain" }}
        >
          <motion.div
            key="demo-modal-content"
            initial={{ opacity: 0, scale: 0.94, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 12 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            // Prevent backdrop close when clicking the card
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-xl"
          >
            <SmartphoneCallScreen onClose={onClose} />
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

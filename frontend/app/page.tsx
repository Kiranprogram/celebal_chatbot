"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (getAccessToken()) router.replace("/chat");
    else router.replace("/login");
  }, [router]);

  return (
    <main className="grid min-h-screen place-items-center">
      <p className="text-sm text-[var(--muted)]">Loading…</p>
    </main>
  );
}

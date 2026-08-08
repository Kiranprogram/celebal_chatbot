"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register(email, password, name);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-16">
      <p className="font-display text-3xl tracking-tight">Create account</p>
      <p className="mt-2 text-sm text-[var(--muted)]">JWT-secured access to chat, memory, and knowledge tools.</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4 rounded-2xl border border-[var(--line)] bg-[var(--panel)] p-6">
        <label className="block text-sm">
          Name
          <input
            className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 outline-none focus:border-[var(--accent)]"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Email
          <input
            className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 outline-none focus:border-[var(--accent)]"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="block text-sm">
          Password
          <input
            className="mt-1 w-full rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 outline-none focus:border-[var(--accent)]"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
        </label>
        {error && <p className="text-sm text-red-300">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-[var(--accent)] px-4 py-2.5 font-medium text-[#04140f] disabled:opacity-60"
        >
          {loading ? "Creating…" : "Register"}
        </button>
      </form>
      <p className="mt-4 text-sm text-[var(--muted)]">
        Already registered?{" "}
        <Link className="text-[var(--warm)] underline" href="/login">
          Sign in
        </Link>
      </p>
    </main>
  );
}

"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { authVerifyEmail } from "@/lib/api";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("No verification token found.");
      return;
    }

    authVerifyEmail(token)
      .then(() => {
        setStatus("success");
        setMessage("Your email has been verified!");
      })
      .catch((err: { detail?: string }) => {
        setStatus("error");
        setMessage(err.detail || "Verification failed. The link may have expired.");
      });
  }, [token]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm space-y-4 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
          Email Verification
        </h1>

        {status === "loading" && (
          <p className="text-sm text-gray-500">Verifying your email...</p>
        )}

        {status === "success" && (
          <>
            <div className="rounded-md bg-green-50 p-3 text-sm text-green-700">
              {message}
            </div>
            <Link
              href="/auth/login"
              className="inline-block rounded-md bg-gray-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-gray-800"
            >
              Sign in
            </Link>
          </>
        )}

        {status === "error" && (
          <>
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
              {message}
            </div>
            <Link
              href="/auth/login"
              className="text-sm text-gray-500 hover:text-gray-900"
            >
              Back to login
            </Link>
          </>
        )}
      </div>
    </main>
  );
}

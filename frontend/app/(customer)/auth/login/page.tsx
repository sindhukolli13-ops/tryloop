"use client";

import { useSearchParams } from "next/navigation";
import Link from "next/link";
import LoginForm from "@/components/auth/LoginForm";
import GoogleButton from "@/components/auth/GoogleButton";

export default function LoginPage() {
  const searchParams = useSearchParams();
  const registered = searchParams.get("registered");

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">
            Welcome back
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Sign in to your Tryloop account
          </p>
        </div>

        {/* Success message after registration */}
        {registered && (
          <div className="rounded-md bg-green-50 p-3 text-sm text-green-700">
            Account created! Check your email to verify, then sign in.
          </div>
        )}

        {/* Login form */}
        <LoginForm />

        {/* Forgot password link */}
        <div className="text-center">
          <Link
            href="/auth/reset-password"
            className="text-sm text-gray-500 hover:text-gray-900"
          >
            Forgot your password?
          </Link>
        </div>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-200" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="bg-gray-50 px-2 text-gray-400">or</span>
          </div>
        </div>

        {/* Google OAuth */}
        <GoogleButton />

        {/* Link to signup */}
        <p className="text-center text-sm text-gray-500">
          Don&apos;t have an account?{" "}
          <Link href="/auth/signup" className="font-medium text-gray-900 hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </main>
  );
}

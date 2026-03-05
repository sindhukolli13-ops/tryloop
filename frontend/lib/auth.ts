/**
 * NextAuth configuration — CredentialsProvider (email/password via backend)
 * and GoogleProvider. Stores backend JWT tokens in the NextAuth session.
 */

import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import { authLogin, authGoogle } from "@/lib/api";

// Extend NextAuth types to include our custom fields
declare module "next-auth" {
  interface User {
    accessToken: string;
    refreshToken: string;
    role: string;
  }
  interface Session {
    accessToken: string;
    refreshToken: string;
    user: {
      id: string;
      name: string;
      email: string;
      role: string;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken: string;
    refreshToken: string;
    role: string;
    id: string;
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    // Email/password — calls our backend /auth/login endpoint
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        try {
          const tokens = await authLogin({
            email: credentials.email,
            password: credentials.password,
          });

          // Decode the access token to get user info (sub = user_id, role)
          const payload = JSON.parse(
            Buffer.from(tokens.access_token.split(".")[1], "base64").toString()
          );

          return {
            id: payload.sub,
            name: credentials.email, // will be overwritten by /auth/me later
            email: credentials.email,
            accessToken: tokens.access_token,
            refreshToken: tokens.refresh_token,
            role: payload.role,
          };
        } catch {
          return null; // login failed — NextAuth shows error
        }
      },
    }),

    // Google OAuth — exchanges Google token for backend JWT tokens
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    }),
  ],

  callbacks: {
    // Store backend tokens in the NextAuth JWT
    async jwt({ token, user, account }) {
      // Initial sign-in with credentials
      if (user) {
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.role = user.role;
        token.id = user.id;
      }

      // Google OAuth sign-in — exchange Google token for backend tokens
      if (account?.provider === "google" && account.id_token) {
        try {
          const tokens = await authGoogle(account.id_token);
          const payload = JSON.parse(
            Buffer.from(tokens.access_token.split(".")[1], "base64").toString()
          );
          token.accessToken = tokens.access_token;
          token.refreshToken = tokens.refresh_token;
          token.role = payload.role;
          token.id = payload.sub;
        } catch {
          // Google auth failed — token will be incomplete
        }
      }

      return token;
    },

    // Expose backend tokens and role in the client-side session
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      session.refreshToken = token.refreshToken;
      session.user = {
        ...session.user,
        id: token.id,
        role: token.role,
      };
      return session;
    },
  },

  pages: {
    signIn: "/auth/login",
    error: "/auth/login",
  },

  session: {
    strategy: "jwt",
  },

  secret: process.env.NEXTAUTH_SECRET,
};

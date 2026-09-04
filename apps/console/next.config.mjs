/**
 * next.config.mjs --- Next.js configuration for the admin console
 *
 * Next 14 loads config from .js/.mjs only; a .ts config aborts the build with
 * "Configuring Next.js via 'next.config.ts' is not supported".
 *
 * Contains:
 *   API_URL: API origin the /api rewrite proxies to
 *   nextConfig: framework configuration exported to Next.js
 */

// The image is built without an env file, so an unguarded template literal
// resolves to the string "undefined" and Next rejects the rewrite outright.
// Compose supplies the real value at run time, which is when rewrites apply.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** @type {import("next").NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;

/**
 * next.config.mjs --- Next.js configuration for the admin console
 *
 * Next 14 loads config from .js/.mjs only; a .ts config aborts the build with
 * "Configuring Next.js via 'next.config.ts' is not supported".
 *
 * Contains:
 *   nextConfig: framework configuration exported to Next.js
 */

/** @type {import("next").NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;

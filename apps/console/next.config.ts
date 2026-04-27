#!/usr/bin/env ts-node
/**
 * next.config.ts --- Next.js configuration for the admin console
 *
 * Contains:
 *   nextConfig: framework configuration exported to Next.js
 */

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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

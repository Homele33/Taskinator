import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactStrictMode: true,
  output: 'standalone', // This is important for Docker

  // Disable image optimization for Docker
  images: {
    disableStaticImages: true,
  },
};

export default nextConfig;

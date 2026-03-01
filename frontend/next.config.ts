import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "cdn.rebrickable.com" },
      { protocol: "https", hostname: "img.bricklink.com" },
    ],
  },
};

export default nextConfig;

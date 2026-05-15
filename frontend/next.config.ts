import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // This is the magic line that shrinks the build
};

export default nextConfig;

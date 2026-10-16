/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: process.env.LUOJIA_NEXT_DIST_DIR || ".next",
  agentRules: false,
  allowedDevOrigins: ["127.0.0.1"],
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;


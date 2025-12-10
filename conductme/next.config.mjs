/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Don't fail build on ESLint errors
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Don't fail build on TypeScript errors (only warn)
  typescript: {
    ignoreBuildErrors: false, // Keep this false to catch real type errors
  },
};

export default nextConfig;

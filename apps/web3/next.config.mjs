/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Single-port architecture: this is statically exported to apps/web3/out and
  // served directly by the FastAPI process (see apps/api/main.py) so the whole
  // platform runs on one port with no separate Next.js dev/prod server.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;

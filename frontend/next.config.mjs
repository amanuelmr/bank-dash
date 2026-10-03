/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // `domains` is deprecated in favour of `remotePatterns`.
    remotePatterns: [{ protocol: "https", hostname: "cdn.freelogovectors.net" }],
  },
};

export default nextConfig;
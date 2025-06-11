/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: '.next',
  reactStrictMode: true,
  swcMinify: false, // it was detected as invalid option
  trailingSlash: true,
}

module.exports = nextConfig
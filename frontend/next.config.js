/** @type {import('next').NextConfig} */

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'export',
  distDir: 'dist', // Specify dist directory
  trailingSlash: true, // Add trailing slashes to all URLs

  // Image Optimization Configuration
  // https://nextjs.org/docs/pages/api-reference/components/image#remotepatterns
  // Add remote patterns for any external image sources you use (e.g., Supabase Storage)
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'hqzoibcaibusectmwrif.supabase.co', // Your actual Supabase project ID
        port: '',
        pathname: '/storage/v1/object/public/**',
      },
      {
        protocol: 'https',
        hostname: 'chatchonk.com', // Your production domain
        port: '',
        pathname: '/**',
      },
      // Add other domains if needed, e.g., for user avatars from other services
    ],
    // You can also specify deviceSizes, imageSizes if you have specific needs
    // but the defaults are generally good.
    unoptimized: true, // Handle unoptimized images for static export
  },

  // Environment Variables
  // Next.js automatically handles environment variables.
  // - Variables prefixed with NEXT_PUBLIC_ are exposed to the browser.
  // - Other variables are only available on the server-side.
  // Explicitly define environment variables for better clarity and validation
  env: {
    // API Configuration
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,

    // Supabase Configuration (for direct client access)
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,

    // Frontend URLs
    NEXT_PUBLIC_FRONTEND_URL: process.env.NEXT_PUBLIC_FRONTEND_URL,
  },

  // Experimental features (use with caution)
  // experimental: {
  //   // appDir: true, // Enabled by default in Next.js 13.4+
  // },

  // Internationalization (i18n) - Placeholder for future setup
  // i18n: {
  //   locales: ['en-US', 'es'],
  //   defaultLocale: 'en-US',
  // },

  // Production Source Maps (disable if you don't want them in production for security/size reasons)
  productionBrowserSourceMaps: false, // Set to true to generate source maps for easier debugging in production (increases bundle size)

  // Webpack configuration (if you need to customize it)
  // webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
  //   // Important: return the modified config
  //   return config;
  // },
};

module.exports = nextConfig;

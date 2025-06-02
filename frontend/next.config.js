/** @type {import('next').NextConfig} */

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  // Output static export for Render static site deployment
  output: 'export',
  trailingSlash: true,
  // Image Optimization Configuration
  // https://nextjs.org/docs/pages/api-reference/components/image#remotepatterns
  // Add remote patterns for any external image sources you use (e.g., Supabase Storage)
  images: {
    unoptimized: true, // Required for static export
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

  // Security Headers
  // https://nextjs.org/docs/advanced-features/security-headers
  async headers() {
    const securityHeaders = [
      {
        key: 'X-Content-Type-Options',
        value: 'nosniff',
      },
      {
        key: 'X-Frame-Options',
        value: 'SAMEORIGIN', // Or DENY if you don't need to iframe your site
      },
      {
        key: 'X-XSS-Protection',
        value: '1; mode=block',
      },
      {
        key: 'Strict-Transport-Security',
        value: 'max-age=63072000; includeSubDomains; preload',
      },
      // Content Security Policy (CSP) - Start with a basic policy and customize it.
      // This is a critical security feature. Be sure to test thoroughly.
      // You might need to add more sources for scripts, styles, images, fonts, connect-src, etc.
      // depending on your integrations (e.g., analytics, payment providers, external APIs).
      // Consider using a tool to generate a more specific CSP for your needs.
      {
        key: 'Content-Security-Policy',
        value: [
          "default-src 'self'",
          "script-src 'self' 'unsafe-eval' 'unsafe-inline'", // 'unsafe-eval' and 'unsafe-inline' might be needed for some libraries or dev mode, try to remove them for production.
          "style-src 'self' 'unsafe-inline'", // 'unsafe-inline' for Tailwind, consider alternatives for stricter CSP.
          "img-src 'self' data: https://hqzoibcaibusectmwrif.supabase.co https://chatchonk.com", // Your actual Supabase hostname and domain
          "font-src 'self'",
          "connect-src 'self' http://localhost:8080 https://hqzoibcaibusectmwrif.supabase.co https://chatchonk.com", // Your actual API and Supabase URLs
          "frame-ancestors 'self'", // Prevents clickjacking
          "form-action 'self'",
          "object-src 'none'",
          "base-uri 'self'",
        ].join('; '),
      },
      {
        key: 'Referrer-Policy',
        value: 'origin-when-cross-origin',
      },
      {
        key: 'Permissions-Policy',
        value: 'camera=(), microphone=(), geolocation=(), payment=()', // Adjust as needed
      },
    ];
    return [
      {
        source: '/:path*', // Apply these headers to all routes
        headers: securityHeaders,
      },
    ];
  },

  // Redirects
  // https://nextjs.org/docs/api-reference/next.config.js/redirects
  // Example:
  // async redirects() {
  //   return [
  //     {
  //       source: '/old-path',
  //       destination: '/new-path',
  //       permanent: true,
  //     },
  //   ];
  // },

  // Rewrites
  // https://nextjs.org/docs/api-reference/next.config.js/rewrites
  // Useful for proxying API requests in development or cleaner URLs.
  // Example (proxying to backend in development, using your actual port 8080):
  async rewrites() {
    return process.env.NODE_ENV === 'development'
      ? [
          {
            source: '/api/:path*',
            destination: 'http://localhost:8080/api/:path*', // Your actual FastAPI backend URL
          },
        ]
      : [];
  },

  // CORS Configuration for Next.js API Routes (if you use them)
  // CORS headers for API routes (e.g., in `/pages/api` or App Router route handlers)
  // should be set directly within those route handlers.
  // This `next.config.js` does not globally configure CORS for API routes.
  // Example for an API route:
  // export default function handler(req, res) {
  //   res.setHeader('Access-Control-Allow-Origin', 'https://your-frontend-domain.com');
  //   res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  //   res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  //   // ... your API logic
  // }

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

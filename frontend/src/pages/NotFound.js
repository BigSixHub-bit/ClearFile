import { Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0A0A0A] flex flex-col items-center justify-center px-4 text-center" data-testid="not-found-page">
      <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#00C896] to-[#3B82F6] flex items-center justify-center mb-6">
        <span className="text-black font-bold text-xl">C</span>
      </div>
      <h1 className="text-5xl sm:text-6xl font-bold text-white mb-3">404</h1>
      <p className="text-lg text-[#A1A1AA] mb-2">Page not found</p>
      <p className="text-sm text-[#555] mb-8 max-w-sm">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <div className="flex flex-col sm:flex-row gap-3">
        <Link
          to="/"
          data-testid="not-found-home-link"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-[#00C896] text-black font-semibold text-sm hover:bg-[#00b386] transition-colors"
        >
          <Home className="w-4 h-4" /> Go to Homepage
        </Link>
        <button
          onClick={() => window.history.back()}
          data-testid="not-found-back-btn"
          className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl border border-[#1E1E1E] text-[#A1A1AA] font-semibold text-sm hover:border-[#00C896] hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Go Back
        </button>
      </div>
    </div>
  );
}

import { useNavigate } from "react-router-dom";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="text-center space-y-6">
        {/* 404 Icon */}
        <div className="flex justify-center">
          <div className="w-24 h-24 bg-zinc-900 rounded-full flex items-center justify-center border-4 border-zinc-800">
            <span className="text-5xl">🤔</span>
          </div>
        </div>

        {/* Error Message */}
        <div className="space-y-2">
          <h1 className="text-6xl font-bold text-white">404</h1>
          <h2 className="text-2xl font-semibold text-gray-300">Page Not Found</h2>
          <p className="text-gray-400 max-w-md mx-auto">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        {/* Actions */}
        <div className="flex gap-4 justify-center pt-4">
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-3 bg-zinc-800 text-white rounded-xl hover:bg-zinc-700 transition-colors"
          >
            ← Go Back
          </button>
          <button
            onClick={() => navigate("/chat")}
            className="px-6 py-3 bg-white text-black font-semibold rounded-xl hover:bg-gray-100 transition-colors"
          >
            Go to Chat
          </button>
        </div>
      </div>
    </div>
  );
}

import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";

export default function Landing() {
  const navigate = useNavigate();
  const [titleIndex, setTitleIndex] = useState(0);
  
  const titles = ["smart", "AI-powered", "automated", "efficient"];

  // Rotate titles
  useEffect(() => {
    const interval = setInterval(() => {
      setTitleIndex((prev) => (prev + 1) % titles.length);
    }, 2000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-gray-900 to-black text-white overflow-hidden">
      {/* Glow Effects */}
      <div className="absolute top-20 left-1/4 w-96 h-96 bg-blue-500/20 blur-[120px] rounded-full" />
      <div className="absolute bottom-20 right-1/4 w-96 h-96 bg-purple-500/20 blur-[120px] rounded-full" />

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
            <div className="w-5 h-5 bg-black rounded-full"></div>
          </div>
          <span className="text-2xl font-bold">NovaHR</span>
        </div>
        <button
          onClick={() => navigate("/login")}
          className="px-6 py-2 bg-white text-black font-semibold rounded-lg hover:bg-gray-100 transition-colors"
        >
          Sign In
        </button>
      </nav>

      {/* Hero Section */}
      <div className="relative z-10 max-w-6xl mx-auto px-8 py-20 text-center">
        {/* Animated Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="space-y-6"
        >
          <h1 className="text-6xl md:text-7xl font-bold leading-tight">
            Manage your HR with{" "}
            <motion.span
              key={titleIndex}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400"
            >
              {titles[titleIndex]}
            </motion.span>
            <br />
            AI assistant
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            AI-powered HR assistant to manage employees, leaves, and workflows effortlessly.
            Automate your HR tasks and focus on what matters.
          </p>

          {/* CTA Buttons */}
          <div className="flex gap-4 justify-center pt-8">
            <button
              onClick={() => navigate("/login")}
              className="px-8 py-4 bg-white text-black font-bold text-lg rounded-xl hover:bg-gray-100 transition-all hover:scale-105 shadow-2xl"
            >
              Get Started →
            </button>
            <button
              onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
              className="px-8 py-4 bg-zinc-800 text-white font-semibold text-lg rounded-xl hover:bg-zinc-700 transition-all border border-zinc-700"
            >
              Learn More
            </button>
          </div>
        </motion.div>

        {/* Animated Dashboard Preview */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.3 }}
          className="mt-20"
        >
          <div className="relative">
            {/* Glow behind preview */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/30 to-purple-500/30 blur-3xl" />
            
            {/* Preview Card */}
            <div className="relative bg-zinc-900 rounded-2xl border border-zinc-800 p-8 shadow-2xl">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              
              {/* Mock Chat Interface */}
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm">
                    🤖
                  </div>
                  <div className="bg-zinc-800 rounded-2xl rounded-tl-none px-4 py-3 text-left">
                    <p className="text-gray-300">Hello! How can I help you today?</p>
                  </div>
                </div>
                
                <div className="flex gap-3 justify-end">
                  <div className="bg-blue-600 rounded-2xl rounded-tr-none px-4 py-3 text-left">
                    <p className="text-white">I want to apply for leave</p>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-sm">
                    U
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Features Section */}
      <div id="features" className="relative z-10 max-w-6xl mx-auto px-8 py-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl font-bold text-center mb-16">
            Everything you need for HR management
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 hover:border-blue-500/50 transition-all"
            >
              <div className="text-5xl mb-4">🤖</div>
              <h3 className="text-2xl font-bold mb-3">AI Assistant</h3>
              <p className="text-gray-400">
                Chat with your AI HR assistant to handle leave requests, policy queries, and more.
              </p>
            </motion.div>

            {/* Feature 2 */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 hover:border-purple-500/50 transition-all"
            >
              <div className="text-5xl mb-4">📊</div>
              <h3 className="text-2xl font-bold mb-3">HR Dashboard</h3>
              <p className="text-gray-400">
                Visualize leave statistics, manage approvals, and track employee data in one place.
              </p>
            </motion.div>

            {/* Feature 3 */}
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 hover:border-green-500/50 transition-all"
            >
              <div className="text-5xl mb-4">📅</div>
              <h3 className="text-2xl font-bold mb-3">Leave Management</h3>
              <p className="text-gray-400">
                Apply for leaves, check balances, and get instant approvals through AI automation.
              </p>
            </motion.div>
          </div>
        </motion.div>
      </div>

      {/* CTA Section */}
      <div className="relative z-10 max-w-4xl mx-auto px-8 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12"
        >
          <h2 className="text-4xl font-bold mb-4">Ready to get started?</h2>
          <p className="text-xl text-gray-100 mb-8">
            Join NovaHR today and transform your HR management
          </p>
          <button
            onClick={() => navigate("/login")}
            className="px-10 py-4 bg-white text-black font-bold text-lg rounded-xl hover:bg-gray-100 transition-all hover:scale-105 shadow-2xl"
          >
            Get Started Now →
          </button>
        </motion.div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-zinc-800 py-8">
        <div className="max-w-6xl mx-auto px-8 text-center text-gray-400">
          <p>© 2026 NovaHR. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

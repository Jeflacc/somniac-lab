import { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import { useAuth } from '../contexts/AuthContext';

const PricingPage = () => {
  const { token, isAuthenticated } = useAuth();
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const paypalOptions = {
    clientId: "AVv8Lm-Z9AAkUc7Qj_chYZYbNgL9BMzz2Si5pfW4PkM8wszNc1eNJhYEhiboyjTyNm1sQORzcKX65knq",
    currency: "USD",
    intent: "capture",
  };

  const handleCapture = async (orderId: string) => {
    try {
      const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/payments/paypal/capture/${orderId}`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      
      if (res.ok) {
        setSuccess(true);
      } else {
        const data = await res.json();
        setError(data.detail || "Payment failed to verify");
      }
    } catch (err) {
      setError("An error occurred during payment verification.");
    }
  };

  const tiers = [
    {
      name: "Free",
      price: "$0",
      description: "Explore the basics of Artificial Consciousness.",
      features: ["Single AI Instance", "Standard Response Time", "Web Interface Only", "Community Support"],
      buttonText: "Get Started",
      isPro: false
    },
    {
      name: "Somniac Pro",
      price: "$19",
      description: "Full access to the advanced Somniac AC Engine.",
      features: [
        "3 Concurrent AI Instances", 
        "Priority AC Processing", 
        "WhatsApp Multi-Tenant Integration", 
        "Custom Memory Retention", 
        "Priority Support"
      ],
      buttonText: "Upgrade Now",
      highlight: true,
      isPro: true
    },
    {
      name: "Lab",
      price: "$99",
      description: "For researchers and enterprise-grade AC training.",
      features: [
        "Unlimited AI Instances", 
        "Custom AC Model Training", 
        "API Access for Developers", 
        "Dedicated Server Resources", 
        "24/7 Technical Support"
      ],
      buttonText: "Contact Us",
      isPro: false
    }
  ];

  return (
    <div className="min-h-screen bg-black text-white selection:bg-white/20 overflow-x-hidden">
      {/* Background Decor */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[#3B6255] opacity-10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-[#3B6255] opacity-10 blur-[120px]" />
      </div>

      {/* Header */}
      <nav className="relative z-50 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
        <Link to="/" className="flex items-center gap-3 no-underline group">
          <div className="w-8 h-8 rounded-full bg-white flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
            <div className="w-4 h-4 rounded-full bg-black" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">somniac</span>
        </Link>
        <div className="flex items-center gap-8">
          <Link to="/" className="text-sm font-medium text-white/50 hover:text-white transition-colors">Platform</Link>
          <Link to="/pricing" className="text-sm font-medium text-white">Pricing</Link>
          <Link to="/auth" className="rounded-full bg-white/5 border border-white/10 px-5 py-2 text-sm font-medium hover:bg-white/10 transition-all">
            {isAuthenticated ? "Go to Lab" : "Sign In"}
          </Link>
        </div>
      </nav>

      <main className="relative z-10 max-w-7xl mx-auto px-8 pt-20 pb-32">
        <div className="text-center space-y-4 mb-20">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-5xl md:text-7xl font-bold tracking-tighter"
          >
            Choose your <span className="text-white/40 italic">evolution</span>.
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-white/50 max-w-2xl mx-auto font-light"
          >
            Upgrade your connection to the Somniac AC Engine and unlock the full potential of your autonomous companions.
          </motion.p>
        </div>

        {success ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-xl mx-auto bg-white/5 border border-white/10 rounded-3xl p-12 text-center"
          >
            <div className="w-20 h-20 rounded-full bg-white mx-auto flex items-center justify-center mb-6">
              <svg className="w-10 h-10 text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold mb-4">You are now Pro.</h2>
            <p className="text-white/50 mb-8">Welcome to the inner circle. Your account has been upgraded to Somniac Pro.</p>
            <Link to="/lab" className="block w-full rounded-full bg-white text-black py-4 font-bold hover:bg-white/90 transition-all">
              Go to the Lab
            </Link>
          </motion.div>
        ) : (
          <div className="grid md:grid-cols-3 gap-8">
            {tiers.map((tier, idx) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * idx }}
                className={`relative group p-8 rounded-3xl border transition-all duration-500 ${
                  tier.highlight 
                  ? "bg-white/10 border-white/20 shadow-[0_0_40px_rgba(255,255,255,0.05)]" 
                  : "bg-white/5 border-white/10 hover:border-white/20"
                }`}
              >
                {tier.highlight && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-white text-black text-[10px] font-bold uppercase tracking-widest px-4 py-1.5 rounded-full">
                    Most Advanced
                  </div>
                )}
                
                <div className="mb-8">
                  <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold">{tier.price}</span>
                    {tier.price !== "$0" && <span className="text-white/40 text-sm">/month</span>}
                  </div>
                  <p className="text-white/50 mt-4 text-sm font-light leading-relaxed">
                    {tier.description}
                  </p>
                </div>

                <ul className="space-y-4 mb-10">
                  {tier.features.map((feature, fIdx) => (
                    <li key={fIdx} className="flex items-center gap-3 text-sm text-white/70">
                      <svg className="w-4 h-4 text-white/30 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>

                {tier.isPro ? (
                  isAuthenticated ? (
                    <div className="relative z-0">
                      <PayPalScriptProvider options={paypalOptions}>
                        <PayPalButtons 
                          style={{ layout: "vertical", shape: "pill", color: "white", label: "pay" }}
                          createOrder={(_data, actions) => {
                            return actions.order.create({
                              intent: "CAPTURE",
                              purchase_units: [
                                {
                                  amount: {
                                    currency_code: "USD",
                                    value: "19.00",
                                  },
                                  description: "Somniac Pro Subscription (Monthly)"
                                },
                              ],
                            });
                          }}
                          onApprove={(data, actions) => {
                            if (actions.order) {
                              return actions.order.capture().then((_details) => {
                                handleCapture(data.orderID);
                              });
                            }
                            return Promise.reject();
                          }}
                        />
                      </PayPalScriptProvider>
                    </div>
                  ) : (
                    <Link 
                      to="/auth" 
                      className="block w-full py-4 text-center rounded-full bg-white text-black font-bold hover:bg-white/90 transition-all"
                    >
                      Sign in to Upgrade
                    </Link>
                  )
                ) : (
                  <button className="w-full py-4 rounded-full bg-white/5 border border-white/10 text-white font-medium hover:bg-white/10 transition-all">
                    {tier.buttonText}
                  </button>
                )}
              </motion.div>
            ))}
          </div>
        )}

        {error && (
          <div className="mt-8 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-center text-sm">
            {error}
          </div>
        )}
      </main>

      <footer className="relative z-10 border-t border-white/5 py-20 px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
              <div className="w-3 h-3 rounded-full bg-white/40" />
            </div>
            <span className="text-white/40 font-medium">somniac lab</span>
          </div>
          <div className="flex gap-10 text-sm text-white/30">
            <Link to="#" className="hover:text-white transition-colors">Privacy</Link>
            <Link to="#" className="hover:text-white transition-colors">Terms</Link>
            <Link to="#" className="hover:text-white transition-colors">Security</Link>
            <Link to="#" className="hover:text-white transition-colors">Cookies</Link>
          </div>
          <div className="text-sm text-white/20">
            &copy; 2026 Somniac Lab. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PricingPage;

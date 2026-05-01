import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Book, Search, Calendar, ShieldCheck, ArrowRight, Zap } from 'lucide-react'
import './LibrxLanding.css'

const LibrxLanding = () => {
  const navigate = useNavigate()

  return (
    <div className="librx-landing">
      {/* NAVBAR */}
      <nav className="librx-nav">
        <div className="nav-container">
          <div className="logo">
            <Book className="logo-icon" />
            <span>LIBRX</span>
          </div>
          <div className="nav-links">
            <a href="#features">Features</a>
            <a href="#catalog">Catalog</a>
            <button className="login-btn" onClick={() => navigate('/login')}>Sign In</button>
            <button className="signup-btn" onClick={() => navigate('/register')}>Get Started</button>
          </div>
        </div>
      </nav>

      {/* HERO SECTION */}
      <header className="hero">
        <div className="hero-content">
          <div className="badge"><Zap size={14} /> The Future of Reading</div>
          <h1>Your Entire Library, <br /> <span className="gradient-text">In One Dashboard.</span></h1>
          <p>Manage your loans, track due dates, and discover your next favorite book with the LIBRX intelligent management system.</p>
          <div className="hero-actions">
            <button className="primary-cta" onClick={() => navigate('/login')}>
              Open My Library <ArrowRight size={18} />
            </button>
            <button className="secondary-cta">Browse Catalog</button>
          </div>
        </div>
        
        {/* DASHBOARD PREVIEW MOCKUP */}
        <div className="hero-preview">
          <div className="mockup-container">
             <div className="mockup-top-bar">
                <div className="dots"><span></span><span></span><span></span></div>
             </div>
             <div className="mockup-screen">
               <div className="screen-header">
                 <span></span>
                 <span></span>
               </div>
               <div className="screen-body">
                 <div className="screen-card"></div>
                 <div className="screen-card small"></div>
                 <div className="screen-row">
                   <div className="screen-block"></div>
                   <div className="screen-block"></div>
                 </div>
               </div>
             </div>
          </div>
        </div>
      </header>

      {/* STATS SECTION */}
      <section className="stats-row">
        <div className="stat"><h3>50k+</h3><p>Books Available</p></div>
        <div className="stat"><h3>12k+</h3><p>Active Readers</p></div>
        <div className="stat"><h3>24/7</h3><p>Access</p></div>
      </section>

      {/* FEATURES SECTION */}
      <section id="features" className="features">
        <h2>Built for the Modern Reader</h2>
        <div className="feature-grid">
          <div className="f-card">
            <Search className="f-icon" />
            <h3>Smart Search</h3>
            <p>Find books by author, category, or ISBN with lightning speed.</p>
          </div>
          <div className="f-card">
            <Calendar className="f-icon" />
            <h3>Loan Tracking</h3>
            <p>Never miss a due date again with automated reminders and easy renewals.</p>
          </div>
          <div className="f-card">
            <ShieldCheck className="f-icon" />
            <h3>Digital Identity</h3>
            <p>Secure profile management for students, faculty, and staff.</p>
          </div>
        </div>
      </section>
    </div>
  )
}
 
export default LibrxLanding

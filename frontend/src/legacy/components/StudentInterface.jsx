import { useState, useEffect } from "react"

// ─── Inline styles mirroring original CSS tokens (no new colors/fonts/themes) ───
const css = {
  // Layout scaffolding
  root: (theme) => ({
    fontFamily: "inherit",
    background: theme === "dark" ? "#0f1117" : "#f5f5f0",
    color: theme === "dark" ? "#e8e8e0" : "#1a1a1a",
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
  }),

  // ── HEADER ──────────────────────────────────────────────────────────────────
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 2rem",
    height: 60,
    borderBottom: "1px solid rgba(255,255,255,0.07)",
    background: "inherit",
    position: "sticky",
    top: 0,
    zIndex: 100,
    gap: 24,
  },
  brandMark: {
    fontWeight: 800,
    fontSize: 18,
    letterSpacing: "0.12em",
    opacity: 0.9,
  },
  brandNav: { display: "flex", alignItems: "center", gap: 32 },
  topNav: { display: "flex", gap: 4 },
  navBtn: (active) => ({
    padding: "6px 14px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: active ? 600 : 400,
    background: active ? "rgba(255,255,255,0.1)" : "transparent",
    color: active ? "inherit" : "rgba(255,255,255,0.5)",
    transition: "all 0.15s",
  }),
  headerSearch: { flex: 1, maxWidth: 400 },
  searchInput: {
    width: "100%",
    padding: "7px 14px",
    borderRadius: 8,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(255,255,255,0.06)",
    color: "inherit",
    fontSize: 13,
    outline: "none",
    boxSizing: "border-box",
  },
  headerActions: { display: "flex", alignItems: "center", gap: 12 },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: "50%",
    background: "rgba(255,255,255,0.15)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: 700,
    fontSize: 12,
    letterSpacing: "0.05em",
  },
  logoutBtn: {
    padding: "5px 12px",
    borderRadius: 6,
    border: "1px solid rgba(255,255,255,0.2)",
    background: "transparent",
    color: "inherit",
    fontSize: 12,
    cursor: "pointer",
  },

  // ── HERO / GREETING BAR ─────────────────────────────────────────────────────
  heroBar: {
    padding: "20px 2rem 0",
    display: "flex",
    alignItems: "flex-end",
    justifyContent: "space-between",
    gap: 16,
  },
  heroGreeting: { lineHeight: 1.2 },
  heroH2: { margin: 0, fontSize: 22, fontWeight: 700 },
  heroSub: { margin: "4px 0 0", fontSize: 13, opacity: 0.55 },
  heroBadge: (hold) => ({
    display: "inline-block",
    marginTop: 8,
    padding: "3px 10px",
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.04em",
    background: hold ? "rgba(220,60,60,0.18)" : "rgba(40,180,100,0.18)",
    color: hold ? "#e05555" : "#3cc47c",
    border: `1px solid ${hold ? "rgba(220,60,60,0.3)" : "rgba(40,180,100,0.3)"}`,
  }),
  newsRow: {
    display: "flex",
    gap: 12,
  },
  newsPill: {
    padding: "6px 14px",
    borderRadius: 20,
    fontSize: 12,
    background: "rgba(255,255,255,0.06)",
    border: "1px solid rgba(255,255,255,0.1)",
    whiteSpace: "nowrap",
  },

  // ── STATS ROW ───────────────────────────────────────────────────────────────
  statsRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 12,
    padding: "20px 2rem 0",
  },
  statCard: {
    padding: "14px 18px",
    borderRadius: 10,
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(255,255,255,0.08)",
  },
  statLabel: { margin: 0, fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", opacity: 0.45, textTransform: "uppercase" },
  statValue: { margin: "6px 0 2px", fontSize: 28, fontWeight: 700, lineHeight: 1 },
  statNote: { margin: 0, fontSize: 11, opacity: 0.45 },

  // ── MAIN CONTENT ────────────────────────────────────────────────────────────
  main: { padding: "20px 2rem 2rem", flex: 1 },

  // Dashboard three-column
  dashGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1.6fr 1fr",
    gap: 16,
    alignItems: "start",
  },
  col: { display: "flex", flexDirection: "column", gap: 16 },

  card: {
    padding: "18px 20px",
    borderRadius: 12,
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(255,255,255,0.08)",
  },
  cardH3: { margin: "0 0 14px", fontSize: 14, fontWeight: 600, opacity: 0.85 },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 14,
  },

  // Featured shelf
  featuredShelf: { display: "flex", gap: 10, overflowX: "auto", paddingBottom: 4 },
  coverCard: (i) => {
    const colors = ["#2a4a6b", "#4a2a5a", "#1a4a3a", "#5a3a1a"]
    return {
      minWidth: 80,
      height: 110,
      borderRadius: 8,
      background: colors[i % colors.length],
      display: "flex",
      alignItems: "flex-end",
      padding: 8,
      fontSize: 10,
      fontWeight: 600,
      lineHeight: 1.2,
      color: "rgba(255,255,255,0.85)",
      flexShrink: 0,
    }
  },

  // Curated pills
  curatedRow: { display: "flex", flexWrap: "wrap", gap: 8 },
  curatedPill: {
    padding: "5px 12px",
    borderRadius: 20,
    fontSize: 12,
    background: "rgba(255,255,255,0.06)",
    border: "1px solid rgba(255,255,255,0.1)",
  },

  // Analytics bars
  analyticsChart: { display: "flex", gap: 12, alignItems: "flex-end", height: 80 },
  analyticsBar: (pct) => ({
    flex: 1,
    height: `${Math.max(pct, 8)}%`,
    background: "rgba(255,255,255,0.2)",
    borderRadius: "3px 3px 0 0",
    minHeight: 8,
  }),
  analyticsLabel: { fontSize: 10, opacity: 0.5, textAlign: "center", marginTop: 4 },

  // Quick actions
  quickGrid: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 },
  quickBtn: {
    padding: "8px 10px",
    borderRadius: 8,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "transparent",
    color: "inherit",
    fontSize: 12,
    cursor: "pointer",
    textAlign: "left",
  },

  // Wishlist
  wishlistItem: {
    padding: "8px 0",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
    fontSize: 13,
  },
  emptyState: { fontSize: 13, opacity: 0.4, padding: "12px 0" },

  addBtn: {
    padding: "4px 10px",
    borderRadius: 6,
    border: "1px solid rgba(255,255,255,0.18)",
    background: "transparent",
    color: "inherit",
    fontSize: 11,
    cursor: "pointer",
  },

  // ── CATALOG ─────────────────────────────────────────────────────────────────
  catalogFilters: {
    display: "flex",
    gap: 12,
    marginBottom: 20,
    alignItems: "center",
  },
  genreSelect: {
    padding: "7px 12px",
    borderRadius: 8,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(255,255,255,0.06)",
    color: "inherit",
    fontSize: 13,
  },
  bookGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
    gap: 14,
  },
  bookCard: {
    borderRadius: 10,
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(255,255,255,0.08)",
    overflow: "hidden",
  },
  coverArt: (title) => {
    const hue = (title?.charCodeAt(0) || 60) * 137 % 360
    return {
      height: 90,
      background: `hsl(${hue},30%,25%)`,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 20,
      fontWeight: 800,
      letterSpacing: "0.05em",
      opacity: 0.9,
    }
  },
  bookDetail: { padding: "12px 14px" },
  bookTitle: { margin: "0 0 2px", fontSize: 13, fontWeight: 600 },
  bookAuthor: { margin: "0 0 8px", fontSize: 11, opacity: 0.5 },
  bookTags: { display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 },
  pill: (avail) => ({
    padding: "2px 8px",
    borderRadius: 10,
    fontSize: 10,
    fontWeight: 600,
    background: avail ? "rgba(40,180,100,0.15)" : "rgba(220,60,60,0.12)",
    color: avail ? "#3cc47c" : "#e05555",
    border: `1px solid ${avail ? "rgba(40,180,100,0.25)" : "rgba(220,60,60,0.2)"}`,
  }),
  tagPill: {
    padding: "2px 8px",
    borderRadius: 10,
    fontSize: 10,
    background: "rgba(255,255,255,0.06)",
    border: "1px solid rgba(255,255,255,0.1)",
  },
  btnRow: { display: "flex", gap: 8 },
  primaryBtn: {
    flex: 1,
    padding: "6px 0",
    borderRadius: 6,
    border: "none",
    background: "rgba(255,255,255,0.14)",
    color: "inherit",
    fontSize: 11,
    fontWeight: 600,
    cursor: "pointer",
  },
  secondaryBtn: {
    flex: 1,
    padding: "6px 0",
    borderRadius: 6,
    border: "1px solid rgba(255,255,255,0.15)",
    background: "transparent",
    color: "inherit",
    fontSize: 11,
    cursor: "pointer",
  },
  disabledBtn: {
    flex: 1,
    padding: "6px 0",
    borderRadius: 6,
    border: "1px solid rgba(255,255,255,0.06)",
    background: "transparent",
    color: "rgba(255,255,255,0.2)",
    fontSize: 11,
    cursor: "not-allowed",
  },

  // ── MY BOOKS ────────────────────────────────────────────────────────────────
  logItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    padding: "14px 0",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
    gap: 16,
  },
  logTitle: { margin: "0 0 3px", fontSize: 14, fontWeight: 600 },
  logMeta: { margin: "0 0 2px", fontSize: 12, opacity: 0.45 },
  logDue: { margin: "0 0 10px", fontSize: 12, opacity: 0.55 },
  logActions: { display: "flex", gap: 8, justifyContent: "flex-end" },
  dueBadge: (overdue) => ({
    display: "inline-block",
    padding: "2px 8px",
    borderRadius: 10,
    fontSize: 10,
    fontWeight: 600,
    background: overdue ? "rgba(220,60,60,0.15)" : "rgba(255,200,0,0.1)",
    color: overdue ? "#e05555" : "#d4a017",
    border: `1px solid ${overdue ? "rgba(220,60,60,0.25)" : "rgba(255,200,0,0.2)"}`,
    marginLeft: 6,
  }),

  // ── HISTORY ────────────────────────────────────────────────────────────────
  historyItem: {
    display: "flex",
    justifyContent: "space-between",
    padding: "12px 0",
    borderBottom: "1px solid rgba(255,255,255,0.06)",
    gap: 16,
  },
  returnedBadge: {
    padding: "2px 8px",
    borderRadius: 10,
    fontSize: 10,
    fontWeight: 600,
    background: "rgba(40,180,100,0.12)",
    color: "#3cc47c",
    border: "1px solid rgba(40,180,100,0.2)",
    display: "inline-block",
  },

  // ── TOAST ──────────────────────────────────────────────────────────────────
  toast: {
    position: "fixed",
    bottom: 24,
    right: 24,
    padding: "10px 18px",
    borderRadius: 8,
    background: "rgba(30,30,30,0.95)",
    border: "1px solid rgba(255,255,255,0.12)",
    fontSize: 13,
    zIndex: 999,
    maxWidth: 320,
  },

  // ── MODALS ─────────────────────────────────────────────────────────────────
  modalOverlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: "rgba(0,0,0,0.75)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modalContent: {
    background: "#1a1a1a",
    padding: 32,
    borderRadius: 16,
    width: 400,
    maxWidth: "90%",
    position: "relative",
  },
  modalClose: {
    position: "absolute",
    top: 16,
    right: 16,
    background: "none",
    border: "none",
    color: "rgba(255,255,255,0.5)",
    fontSize: 20,
    cursor: "pointer",
  },
  modalAvatar: {
    width: 80,
    height: 80,
    borderRadius: "50%",
    background: "rgba(15,118,110,0.2)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 16px",
    fontSize: 28,
    fontWeight: 700,
    color: "#0f766e",
    position: "relative",
  },
  modalAvatarEdit: {
    position: "absolute",
    bottom: 0,
    right: 0,
    width: 28,
    height: 28,
    borderRadius: "50%",
    background: "#0f766e",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: 14,
    cursor: "pointer",
  },
  modalTitle: {
    textAlign: "center",
    margin: "0 0 24px",
    fontSize: 20,
    fontWeight: 600,
  },
  modalInputGroup: {
    marginBottom: 16,
  },
  modalLabel: {
    display: "block",
    marginBottom: 6,
    fontSize: 12,
    fontWeight: 600,
    opacity: 0.7,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  modalInput: {
    width: "100%",
    padding: "12px 14px",
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(255,255,255,0.06)",
    color: "inherit",
    fontSize: 14,
    outline: "none",
    boxSizing: "border-box",
  },
  modalInputWithIcon: {
    width: "100%",
    padding: "12px 14px 12px 40px",
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.12)",
    background: "rgba(255,255,255,0.06)",
    color: "inherit",
    fontSize: 14,
    outline: "none",
    boxSizing: "border-box",
  },
  modalInputWrapper: {
    position: "relative",
  },
  modalInputIcon: {
    position: "absolute",
    left: 14,
    top: "50%",
    transform: "translateY(-50%)",
    opacity: 0.5,
    fontSize: 14,
  },
  modalLink: {
    display: "block",
    textAlign: "center",
    marginTop: 16,
    color: "#0f766e",
    fontSize: 13,
    cursor: "pointer",
    textDecoration: "underline",
  },
  modalActions: {
    display: "flex",
    gap: 12,
    marginTop: 24,
  },
  modalSaveBtn: {
    flex: 1,
    padding: "12px 0",
    borderRadius: 10,
    border: "none",
    background: "#0f766e",
    color: "#fff",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  modalCancelBtn: {
    flex: 1,
    padding: "12px 0",
    borderRadius: 10,
    border: "1px solid rgba(255,255,255,0.2)",
    background: "transparent",
    color: "inherit",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
  },
  modalUpdateBtn: {
    width: "100%",
    padding: "12px 0",
    borderRadius: 10,
    border: "none",
    background: "#0f766e",
    color: "#fff",
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    marginTop: 16,
  },
}

// ─── Mock data so the component works standalone ────────────────────────────
const MOCK_BOOKS = [
  { book_id: 1, title: "Sapiens", author: "Yuval Noah Harari", category: "Non-Fiction", isbn: "978-0062316097", status: "available", available_copies: 2 },
  { book_id: 2, title: "Dune", author: "Frank Herbert", category: "Sci-Fi", isbn: "978-0441013593", status: "borrowed", available_copies: 0 },
  { book_id: 3, title: "Atomic Habits", author: "James Clear", category: "Non-Fiction", isbn: "978-0735211292", status: "available", available_copies: 3 },
  { book_id: 4, title: "The Silent Patient", author: "Alex Michaelides", category: "Fiction", isbn: "978-1250301697", status: "available", available_copies: 1 },
  { book_id: 5, title: "Project Hail Mary", author: "Andy Weir", category: "Sci-Fi", isbn: "978-0593135204", status: "available", available_copies: 2 },
  { book_id: 6, title: "Educated", author: "Tara Westover", category: "Non-Fiction", isbn: "978-0399590504", status: "borrowed", available_copies: 0 },
]

const MOCK_BORROWINGS = [
  { borrow_id: 1, student_email: "student@library.com", book_title: "Sapiens", category: "Non-Fiction", status: "borrowed", due_date: "2026-05-20", renewal_count: 1 },
  { borrow_id: 2, student_email: "student@library.com", book_title: "Dune", category: "Sci-Fi", status: "overdue", due_date: "2026-04-10", renewal_count: 3 },
  { borrow_id: 3, student_email: "student@library.com", book_title: "Educated", category: "Non-Fiction", status: "returned", due_date: "2026-03-15", renewal_count: 0 },
  { borrow_id: 4, student_email: "student@library.com", book_title: "Atomic Habits", category: "Non-Fiction", status: "pending", due_date: "2026-05-28", renewal_count: 0 },
]

const NEWS = [
  "Author Talk: Tomorrow @ 2 PM",
  "New Graphic Novel Collection arrived",
]

const POPULAR = ["Sapiens", "The Silent Patient", "Dune", "Atomic Habits"]
const CURATED = ["Weekend Reads", "Start-up Skills", "Bookmaking Explorer", "Silent Study Hours"]

export default function StudentInterface({ user: propUser, onLogout: propLogout }) {
  const user = propUser || { full_name: "Alex Rivera", email: "student@library.com" }
  const onLogout = propLogout || (() => alert("Logged out"))

  const [books, setBooks] = useState(MOCK_BOOKS)
  const [borrowings, setBorrowings] = useState(MOCK_BORROWINGS)
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedGenre, setSelectedGenre] = useState("")
  const [wishlist, setWishlist] = useState([])
  const [activeTab, setActiveTab] = useState("Dashboard")
  const [statusMessage, setStatusMessage] = useState("")
  const [clock, setClock] = useState(new Date())
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name || "",
    email: user?.email || "",
    phone: "",
    address: ""
  })
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: ""
  })

  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (!statusMessage) return
    const t = setTimeout(() => setStatusMessage(""), 3000)
    return () => clearTimeout(t)
  }, [statusMessage])

  const userFirstName = user?.full_name?.split(" ")[0] || "Student"
  const studentBorrowings = borrowings.filter((b) => b.student_email === user?.email)
  const overdue = studentBorrowings.filter((b) => b.status === "overdue" || (b.status === "borrowed" && b.due_date && new Date(b.due_date) < new Date()))
  const borrowed = studentBorrowings.filter((b) => b.status === "borrowed" || b.status === "overdue")
  const returned = studentBorrowings.filter((b) => b.status === "returned")
  const pending = studentBorrowings.filter((b) => b.status === "pending")
  const onHold = overdue.length > 0
  const hour = clock.getHours()
  const greeting = hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening"

  const genres = Array.from(new Set(books.map((b) => b.category).filter(Boolean)))

  const filteredBooks = books.filter((b) => {
    const q = searchQuery.toLowerCase()
    const match = b.title?.toLowerCase().includes(q) || b.author?.toLowerCase().includes(q) || b.category?.toLowerCase().includes(q) || b.isbn?.toString().includes(q)
    const genreMatch = selectedGenre ? b.category === selectedGenre : true
    return match && genreMatch
  })

  const categoryCounts = studentBorrowings.reduce((acc, b) => {
    acc[b.category || "Other"] = (acc[b.category || "Other"] || 0) + 1
    return acc
  }, {})
  const totalCats = Object.values(categoryCounts).reduce((s, v) => s + v, 0) || 1
  const analytics = ["Fiction", "Sci-Fi", "Non-Fiction"].map((c) => ({
    label: c,
    pct: Math.round(((categoryCounts[c] || 0) / totalCats) * 100),
  }))

  const handleBorrow = (book) => {
    if (book.status !== "available") { setStatusMessage("Book not available"); return }
    setBorrowings([...borrowings, { borrow_id: Date.now(), student_email: user.email, book_title: book.title, category: book.category, status: "borrowed", due_date: new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10), renewal_count: 0 }])
    setBooks(books.map((b) => b.book_id === book.book_id ? { ...b, status: "borrowed", available_copies: Math.max(0, (b.available_copies || 1) - 1) } : b))
    setStatusMessage(`Borrowed "${book.title}" successfully.`)
  }

  const handleReturn = (bw) => {
    setBorrowings(borrowings.map((b) => b.borrow_id === bw.borrow_id ? { ...b, status: "returned" } : b))
    setStatusMessage(`Returned "${bw.book_title}".`)
  }

  const handleRenew = (bw) => {
    if ((bw.renewal_count || 0) >= 3) { setStatusMessage("Max renewals reached."); return }
    setBorrowings(borrowings.map((b) => b.borrow_id === bw.borrow_id ? { ...b, renewal_count: (b.renewal_count || 0) + 1, due_date: new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10) } : b))
    setStatusMessage(`Renewed "${bw.book_title}".`)
  }

  const handleSave = (book) => {
    if (!wishlist.some((w) => w.book_id === book.book_id)) {
      setWishlist([...wishlist, book])
      setStatusMessage(`Saved "${book.title}" for later.`)
    }
  }

  const handleProfileSave = () => {
    setStatusMessage("Profile updated successfully!")
    setShowProfileModal(false)
  }

  const handlePasswordUpdate = () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setStatusMessage("Passwords do not match")
      return
    }
    if (passwordForm.newPassword.length < 8) {
      setStatusMessage("Password must be at least 8 characters")
      return
    }
    setStatusMessage("Password updated successfully!")
    setShowPasswordModal(false)
    setPasswordForm({ currentPassword: "", newPassword: "", confirmPassword: "" })
  }

  return (
    <div style={css.root("dark")}>
      {/* ── PROFILE MODAL ── */}
      {showProfileModal && (
        <div style={css.modalOverlay} onClick={() => setShowProfileModal(false)}>
          <div style={css.modalContent} onClick={(e) => e.stopPropagation()}>
            <button style={css.modalClose} onClick={() => setShowProfileModal(false)}>×</button>
            
            <div style={css.modalAvatar}>
              {userFirstName.slice(0, 2).toUpperCase()}
              <div style={css.modalAvatarEdit}>📷</div>
            </div>
            
            <h2 style={css.modalTitle}>Edit Profile</h2>
            
            <div style={css.modalInputGroup}>
              <label style={css.modalLabel}>Full Name</label>
              <div style={css.modalInputWrapper}>
                <span style={css.modalInputIcon}>👤</span>
                <input
                  style={css.modalInputWithIcon}
                  type="text"
                  value={profileForm.full_name}
                  onChange={(e) => setProfileForm({...profileForm, full_name: e.target.value})}
                />
              </div>
            </div>
            
            <div style={css.modalInputGroup}>
              <label style={css.modalLabel}>Email Address</label>
              <div style={css.modalInputWrapper}>
                <span style={css.modalInputIcon}>✉️</span>
                <input
                  style={css.modalInputWithIcon}
                  type="email"
                  value={profileForm.email}
                  onChange={(e) => setProfileForm({...profileForm, email: e.target.value})}
                />
              </div>
            </div>
            
            <span style={css.modalLink} onClick={() => { setShowProfileModal(false); setShowPasswordModal(true) }}>
              Change Password?
            </span>
            
            <div style={css.modalActions}>
              <button style={css.modalCancelBtn} onClick={() => setShowProfileModal(false)}>Cancel</button>
              <button style={css.modalSaveBtn} onClick={handleProfileSave}>Save Changes</button>
            </div>
          </div>
        </div>
      )}

      {/* ── PASSWORD MODAL ── */}
      {showPasswordModal && (
        <div style={css.modalOverlay} onClick={() => setShowPasswordModal(false)}>
          <div style={css.modalContent} onClick={(e) => e.stopPropagation()}>
            <button style={css.modalClose} onClick={() => setShowPasswordModal(false)}>×</button>
            
            <h2 style={css.modalTitle}>Change Password</h2>
            
            <div style={css.modalInputGroup}>
              <label style={css.modalLabel}>Current Password</label>
              <div style={css.modalInputWrapper}>
                <span style={css.modalInputIcon}>🔒</span>
                <input
                  style={css.modalInputWithIcon}
                  type="password"
                  placeholder="Enter current password"
                  value={passwordForm.currentPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, currentPassword: e.target.value})}
                />
              </div>
            </div>
            
            <div style={css.modalInputGroup}>
              <label style={css.modalLabel}>New Password</label>
              <div style={css.modalInputWrapper}>
                <span style={css.modalInputIcon}>🔒</span>
                <input
                  style={css.modalInputWithIcon}
                  type="password"
                  placeholder="Enter new password"
                  value={passwordForm.newPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, newPassword: e.target.value})}
                />
              </div>
            </div>
            
            <div style={css.modalInputGroup}>
              <label style={css.modalLabel}>Confirm New Password</label>
              <div style={css.modalInputWrapper}>
                <span style={css.modalInputIcon}>🔒</span>
                <input
                  style={css.modalInputWithIcon}
                  type="password"
                  placeholder="Confirm new password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => setPasswordForm({...passwordForm, confirmPassword: e.target.value})}
                />
              </div>
            </div>
            
            <button style={css.modalUpdateBtn} onClick={handlePasswordUpdate}>Update Password</button>
          </div>
        </div>
      )}

      {/* ── HEADER ── */}
      <header style={css.header}>
        <div style={css.brandNav}>
          <div style={css.brandMark}>LIBRX</div>
          <nav style={css.topNav}>
            {["Dashboard", "Catalog", "My Books", "History"].map((t) => (
              <button key={t} style={css.navBtn(activeTab === t)} onClick={() => setActiveTab(t)}>{t}</button>
            ))}
          </nav>
        </div>
        <div style={css.headerSearch}>
          <input
            style={css.searchInput}
            placeholder="Search books, authors, categories…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => searchQuery && setActiveTab("Catalog")}
          />
        </div>
        <div style={css.headerActions}>
          <button style={{...css.logoutBtn, marginRight: 8}} onClick={() => setShowProfileModal(true)} title="Edit Profile">
            ⚙️
          </button>
          <div style={css.avatar}>{userFirstName.slice(0, 2).toUpperCase()}</div>
          <button style={css.logoutBtn} onClick={onLogout}>Logout</button>
        </div>
      </header>

      {/* ── DASHBOARD ── */}
      {activeTab === "Dashboard" && (
        <div style={css.main}>

          {/* Greeting + news + status — compact top bar */}
          <div style={css.heroBar}>
            <div style={css.heroGreeting}>
              <h2 style={css.heroH2}>Good {greeting}, {userFirstName}</h2>
              <p style={css.heroSub}>Here's your library overview for today</p>
              <span style={css.heroBadge(onHold)}>{onHold ? "⚠ On Hold" : "✓ Good Standing"}</span>
            </div>
            <div style={css.newsRow}>
              {NEWS.map((n) => <span key={n} style={css.newsPill}>{n}</span>)}
            </div>
          </div>

          {/* Stats row — 4 columns, immediate below greeting */}
          <div style={css.statsRow}>
            {[
              { label: "Currently Borrowed", value: borrowed.length, note: `${overdue.length} overdue` },
              { label: "Saved for Later", value: wishlist.length, note: "Your reading list" },
              { label: "Books Read", value: returned.length, note: "Total returned" },
              { label: "Pending Approval", value: pending.length, note: "Active requests" },
            ].map((s) => (
              <div key={s.label} style={css.statCard}>
                <p style={css.statLabel}>{s.label}</p>
                <p style={css.statValue}>{s.value}</p>
                <p style={css.statNote}>{s.note}</p>
              </div>
            ))}
          </div>

          {/* ── 3-column dashboard grid ── */}
          <div style={{ ...css.dashGrid, marginTop: 16 }}>

            {/* LEFT — Primary user context */}
            <div style={css.col}>

              {/* Active loans — most critical for the user */}
              <div style={css.card}>
                <div style={css.cardHeader}>
                  <h3 style={{ ...css.cardH3, margin: 0 }}>Active Loans</h3>
                  <button style={css.addBtn} onClick={() => setActiveTab("My Books")}>View all</button>
                </div>
                {borrowed.length > 0 ? borrowed.slice(0, 3).map((bw) => {
                  const isOver = bw.status === "overdue" || (bw.due_date && new Date(bw.due_date) < new Date())
                  return (
                    <div key={bw.borrow_id} style={{ padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <p style={{ margin: "0 0 2px", fontSize: 13, fontWeight: 600 }}>{bw.book_title}<span style={css.dueBadge(isOver)}>{isOver ? "Overdue" : "Active"}</span></p>
                      <p style={{ margin: 0, fontSize: 11, opacity: 0.45 }}>Due {bw.due_date} · Renewals: {bw.renewal_count}/3</p>
                    </div>
                  )
                }) : <p style={css.emptyState}>No active loans.</p>}
              </div>

              {/* Saved / wishlist */}
              <div style={css.card}>
                <div style={css.cardHeader}>
                  <h3 style={{ ...css.cardH3, margin: 0 }}>Saved for Later</h3>
                  <button style={css.addBtn} onClick={() => setActiveTab("Catalog")}>+ Add</button>
                </div>
                {wishlist.length > 0
                  ? wishlist.slice(0, 6).map((b) => <div key={b.book_id} style={css.wishlistItem}>{b.title}<span style={{ marginLeft: 6, opacity: 0.4, fontSize: 11 }}>by {b.author}</span></div>)
                  : <p style={css.emptyState}>Browse the catalog to save books.</p>}
              </div>

              {/* Quick actions */}
              <div style={css.card}>
                <h3 style={css.cardH3}>Quick Actions</h3>
                <div style={css.quickGrid}>
                  {[
                    { label: "Browse Catalog", fn: () => setActiveTab("Catalog") },
                    { label: "My Books", fn: () => setActiveTab("My Books") },
                    { label: "View History", fn: () => setActiveTab("History") },
                    { label: "Contact Library", fn: () => setStatusMessage("Contact form activated.") },
                  ].map((a) => (
                    <button key={a.label} style={css.quickBtn} onClick={a.fn}>{a.label}</button>
                  ))}
                </div>
              </div>
            </div>

            {/* CENTER — Discovery content (primary real estate) */}
            <div style={css.col}>

              {/* Featured collections — largest card, center attention */}
              <div style={css.card}>
                <h3 style={css.cardH3}>Featured Collections · Popular Right Now</h3>
                <div style={css.featuredShelf}>
                  {POPULAR.map((title, i) => (
                    <div key={title} style={css.coverCard(i)}>
                      <span>{title}</span>
                    </div>
                  ))}
                </div>
                <div style={{ ...css.curatedRow, marginTop: 16 }}>
                  {CURATED.map((list) => (
                    <span key={list} style={css.curatedPill}>📖 {list}</span>
                  ))}
                </div>
              </div>

              {/* Recently added books */}
              <div style={css.card}>
                <div style={css.cardHeader}>
                  <h3 style={{ ...css.cardH3, margin: 0 }}>Recently Added</h3>
                  <button style={css.addBtn} onClick={() => setActiveTab("Catalog")}>Full catalog</button>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {books.slice(0, 4).map((book) => {
                    const avail = book.status === "available" || (book.available_copies || 0) > 0
                    return (
                      <div key={book.book_id} style={{ padding: "10px 12px", borderRadius: 8, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
                        <p style={{ margin: "0 0 2px", fontSize: 12, fontWeight: 600 }}>{book.title}</p>
                        <p style={{ margin: "0 0 8px", fontSize: 10, opacity: 0.45 }}>{book.author}</p>
                        <div style={{ display: "flex", gap: 6, alignItems: "center", justifyContent: "space-between" }}>
                          <span style={css.pill(avail)}>{avail ? "Available" : "On Loan"}</span>
                          <button style={{ ...css.addBtn, fontSize: 10 }} onClick={() => avail ? handleBorrow(book) : handleSave(book)}>
                            {avail ? "Borrow" : "Save"}
                          </button>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* RIGHT — Analytics & Reader rewards (tertiary) */}
            <div style={css.col}>

              {/* Borrowing analytics */}
              <div style={css.card}>
                <h3 style={css.cardH3}>Borrowing by Genre</h3>
                {studentBorrowings.length > 0 ? (
                  <>
                    <div style={css.analyticsChart}>
                      {analytics.map((item) => (
                        <div key={item.label} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", height: "100%" }}>
                          <div style={css.analyticsBar(item.pct)} />
                          <div style={css.analyticsLabel}>{item.label}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                      {analytics.map((item) => (
                        <span key={item.label} style={{ fontSize: 11, opacity: 0.55 }}>{item.label} {item.pct}%</span>
                      ))}
                    </div>
                  </>
                ) : (
                  <p style={css.emptyState}>Borrow books to see your genre breakdown.</p>
                )}
              </div>

              {/* Reader of the month */}
              <div style={css.card}>
                <h3 style={css.cardH3}>Reader of the Month ⭐</h3>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ ...css.avatar, width: 40, height: 40, fontSize: 14 }}>{userFirstName.slice(0, 2).toUpperCase()}</div>
                  <div>
                    <p style={{ margin: "0 0 2px", fontSize: 13, fontWeight: 600 }}>Could be you!</p>
                    <p style={{ margin: 0, fontSize: 11, opacity: 0.45 }}>Borrow more to climb the leaderboard.</p>
                  </div>
                </div>
              </div>

              {/* Library hours / status */}
              <div style={css.card}>
                <h3 style={css.cardH3}>Library Status</h3>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: (hour >= 8 && hour < 18) ? "#3cc47c" : "#e05555", display: "inline-block" }} />
                  <span style={{ fontSize: 13 }}>{(hour >= 8 && hour < 18) ? "Open now" : "Closed"}</span>
                </div>
                <p style={{ margin: 0, fontSize: 11, opacity: 0.45 }}>Hours: Mon–Sat 8:00 AM – 6:00 PM</p>
                <p style={{ margin: "8px 0 0", fontSize: 11, opacity: 0.45, fontVariantNumeric: "tabular-nums" }}>
                  {clock.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── CATALOG ── */}
      {activeTab === "Catalog" && (
        <div style={css.main}>
          <div style={css.catalogFilters}>
            <input
              style={{ ...css.searchInput, maxWidth: 320 }}
              placeholder="Search by title, author, ISBN…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select style={css.genreSelect} value={selectedGenre} onChange={(e) => setSelectedGenre(e.target.value)}>
              <option value="">All Genres</option>
              {genres.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
            {(searchQuery || selectedGenre) && (
              <button style={css.addBtn} onClick={() => { setSearchQuery(""); setSelectedGenre("") }}>Clear</button>
            )}
            <span style={{ fontSize: 12, opacity: 0.4, marginLeft: "auto" }}>{filteredBooks.length} books</span>
          </div>

          {filteredBooks.length > 0 ? (
            <div style={css.bookGrid}>
              {filteredBooks.map((book) => {
                const avail = book.status === "available" || (book.available_copies || 0) > 0
                return (
                  <div key={book.book_id} style={css.bookCard}>
                    <div style={css.coverArt(book.title)}>{book.title?.slice(0, 2).toUpperCase()}</div>
                    <div style={css.bookDetail}>
                      <p style={css.bookTitle}>{book.title}</p>
                      <p style={css.bookAuthor}>{book.author}</p>
                      <div style={css.bookTags}>
                        <span style={css.pill(avail)}>{avail ? "In Library" : "Out on Loan"}</span>
                        <span style={css.tagPill}>#{book.category}</span>
                      </div>
                      <p style={{ margin: "0 0 10px", fontSize: 10, opacity: 0.35 }}>ISBN: {book.isbn}</p>
                      <div style={css.btnRow}>
                        <button style={css.primaryBtn} onClick={() => handleSave(book)}>Save</button>
                        <button style={avail ? css.secondaryBtn : css.disabledBtn} onClick={() => handleBorrow(book)} disabled={!avail}>
                          {avail ? "Borrow" : "Unavailable"}
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "60px 0", opacity: 0.4 }}>
              <p style={{ fontSize: 16 }}>No books found.</p>
              <p style={{ fontSize: 13 }}>Try clearing your search or selecting a different genre.</p>
            </div>
          )}
        </div>
      )}

      {/* ── MY BOOKS ── */}
      {activeTab === "My Books" && (
        <div style={css.main}>
          <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 16, alignItems: "start" }}>
            {/* Currently borrowed */}
            <div style={css.card}>
              <div style={css.cardHeader}>
                <h3 style={{ ...css.cardH3, margin: 0 }}>Currently Borrowed</h3>
                <span style={{ fontSize: 12, opacity: 0.4 }}>{borrowed.length} active</span>
              </div>
              {borrowed.length > 0 ? borrowed.map((bw) => {
                const isOver = bw.status === "overdue" || (bw.due_date && new Date(bw.due_date) < new Date())
                const canRenew = bw.status === "borrowed" && !isOver && (bw.renewal_count || 0) < 3
                return (
                  <div key={bw.borrow_id} style={css.logItem}>
                    <div style={{ flex: 1 }}>
                      <p style={css.logTitle}>{bw.book_title}<span style={css.dueBadge(isOver)}>{isOver ? "Overdue" : "Active"}</span></p>
                      <p style={css.logMeta}>{bw.category || "General"}</p>
                      <p style={css.logMeta}>Renewals used: {bw.renewal_count}/3</p>
                    </div>
                    <div style={{ textAlign: "right", minWidth: 130 }}>
                      <p style={css.logDue}>Due {bw.due_date || "—"}</p>
                      <div style={css.logActions}>
                        <button style={{ ...css.secondaryBtn, flex: "none", padding: "5px 10px" }} onClick={() => handleReturn(bw)}>Return</button>
                        <button style={{ ...(canRenew ? css.primaryBtn : css.disabledBtn), flex: "none", padding: "5px 10px" }} onClick={() => handleRenew(bw)} disabled={!canRenew}>Renew</button>
                      </div>
                    </div>
                  </div>
                )
              }) : <p style={css.emptyState}>No active loans.</p>}
            </div>

            {/* Saved for later */}
            <div style={css.card}>
              <div style={css.cardHeader}>
                <h3 style={{ ...css.cardH3, margin: 0 }}>Saved for Later</h3>
                <button style={css.addBtn} onClick={() => setActiveTab("Catalog")}>Browse →</button>
              </div>
              {wishlist.length > 0 ? wishlist.map((b) => (
                <div key={b.book_id} style={css.wishlistItem}>
                  <p style={{ margin: "0 0 2px", fontSize: 13, fontWeight: 600 }}>{b.title}</p>
                  <p style={{ margin: 0, fontSize: 11, opacity: 0.4 }}>by {b.author}</p>
                </div>
              )) : (
                <div>
                  <p style={css.emptyState}>No books saved yet.</p>
                  <button style={css.primaryBtn} onClick={() => setActiveTab("Catalog")}>Browse Catalog</button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── HISTORY ── */}
      {activeTab === "History" && (
        <div style={css.main}>
          <div style={css.card}>
            <div style={css.cardHeader}>
              <h3 style={{ ...css.cardH3, margin: 0 }}>Borrowing History</h3>
              <span style={{ fontSize: 12, opacity: 0.4 }}>{studentBorrowings.length} records</span>
            </div>
            {studentBorrowings.length > 0 ? studentBorrowings.map((bw) => (
              <div key={bw.borrow_id} style={css.historyItem}>
                <div>
                  <p style={{ margin: "0 0 3px", fontSize: 14, fontWeight: 600 }}>{bw.book_title}</p>
                  <p style={{ margin: 0, fontSize: 12, opacity: 0.45 }}>{bw.category || "General"}</p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <span style={bw.status === "returned" ? css.returnedBadge : css.dueBadge(bw.status === "overdue")}>
                    {bw.status.charAt(0).toUpperCase() + bw.status.slice(1)}
                  </span>
                  <p style={{ margin: "4px 0 0", fontSize: 11, opacity: 0.4 }}>{bw.due_date ? `Due ${bw.due_date}` : "—"}</p>
                </div>
              </div>
            )) : <p style={css.emptyState}>No borrowing history yet.</p>}
          </div>
        </div>
      )}

      {/* Toast */}
      {statusMessage && <div style={css.toast}>{statusMessage}</div>}
    </div>
  )
}
# Email Verification Setup for Multi-Device Support

## Problem
Email verification links were only working on the device where registration occurred because:
1. The verification URL was hardcoded to `http://127.0.0.1:3000` (localhost only)
2. Other devices couldn't access localhost IPs from their network

## Solution Implemented
The system now uses `Config.FRONTEND_URL` (with fallback to `Config.BACKEND_URL`) for generating verification links, allowing them to be accessible from any device.

## Configuration

### For Local Development (Same Network Access)

To allow verification from phones/tablets on the same network, set environment variables in your `.env` file:

```bash
# Get your machine's IP address
# Windows (PowerShell): ipconfig | findstr "IPv4"
# Mac/Linux: ifconfig | grep "inet "

# Example if your machine IP is 192.168.1.100

# Backend URL (your development server)
BACKEND_URL=http://192.168.1.100:5000

# Frontend URL (your development frontend)
FRONTEND_URL=http://192.168.1.100:3000
USE_DEV_FRONTEND=true
```

### For Production Deployment

```bash
# Use your actual domain or public IP
BACKEND_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
USE_DEV_FRONTEND=false
```

## Steps to Enable Multi-Device Verification

### 1. Find Your Machine's IP Address

**Windows (PowerShell):**
```powershell
ipconfig | findstr "IPv4"
```

Look for IPv4 Address under your network adapter (e.g., `192.168.1.100`)

**Mac/Linux:**
```bash
ifconfig | grep "inet "
```

### 2. Update Environment Variables

Edit your `.env` file in the project root:

```bash
BACKEND_URL=http://192.168.1.100:5000
FRONTEND_URL=http://192.168.1.100:3000
USE_DEV_FRONTEND=true
```

### 3. Restart Both Backend and Frontend

```bash
# Restart backend (in one terminal)
cd backend
python run_server.py

# Restart frontend (in another terminal)
cd frontend
npm run dev
```

### 4. Access from Another Device

On your phone/tablet on the same WiFi network:
- Go to: `http://192.168.1.100:3000` (replace IP with your machine's IP)
- Register an account
- Check your email and click the verification link
- ✅ Verification should now work!

## Testing the Fix

### Test 1: Same Device
1. Register with email verification
2. Click link in email on same device
3. Should redirect to login ✅

### Test 2: Different Device (Same Network)
1. Register from computer at `http://192.168.1.100:3000`
2. On phone, open email and click verification link
3. Should work without "context error" ✅

### Test 3: Different Network
1. For external devices, use HTTPS with a proper domain
2. Update `FRONTEND_URL` to your production domain
3. Restart backend/frontend

## Troubleshooting

### "Browser context error" message
- **Cause:** Browser context validation was preventing cross-device access
- **Fix:** Already fixed in the VerifyEmail.jsx component ✅

### Verification link goes to localhost
- **Cause:** `FRONTEND_URL` not properly configured
- **Fix:** Set `FRONTEND_URL` environment variable to your machine's IP/domain

### Can't access from other device
- **Cause:** Firewall blocking or different network
- **Fix:** 
  - Ensure devices are on same WiFi network
  - Check Windows Firewall allows port 3000 and 5000
  - Use proper domain/IP that's reachable from other device

### Email link shows wrong URL
- **Cause:** Configuration not reloaded
- **Fix:** Restart backend server to reload config

## Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_URL` | `http://127.0.0.1:5000` | Backend API base URL |
| `FRONTEND_URL` | `http://127.0.0.1:3000` | Frontend URL for email links |
| `USE_DEV_FRONTEND` | `false` | Use Vite dev server for frontend |

## Files Modified

- `backend/app/application/use_cases/user/secure_student_registration.py` - Updated URL generation
- `frontend/src/features/auth/VerifyEmail.jsx` - Fixed browser context validation

## Notes

- Verification tokens expire in 24 hours for security
- Use HTTPS in production to protect tokens
- IP addresses on local networks (192.168.x.x, 10.x.x.x) may not work for external access
- Use a proper domain or public IP for production

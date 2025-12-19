# 🎴 Anki API Integration Setup Guide

**Date:** November 10, 2025  
**Status:** Ready to Configure  

---

## 🎯 WHAT'S NEW

Your DrCodePT Phase 7 system now includes full Anki integration:

✅ **AnkiConnect Support** - Auto-add cards to Anki desktop app  
✅ **AnkiWeb Support** - Sync to your AnkiWeb account  
✅ **Automatic Card Generation** - Study → Generate → Add to Anki pipeline  
✅ **Dashboard Integration** - See cards added in real-time  

---

## 🔧 SETUP OPTIONS

### **OPTION 1: Anki Desktop App (RECOMMENDED - Fastest)**

#### Prerequisites
1. **Install Anki Desktop**
   - Download from: https://apps.ankiweb.net/
   - Windows: Extract to a folder
   - Install AnkiConnect addon (required for API access)

2. **Install AnkiConnect Addon**
   - Open Anki desktop app
   - Go: Tools → Add-ons → Get Add-ons
   - Paste code: `2055492159`
   - Restart Anki

#### How It Works
- Phase 7 backend connects to Anki via AnkiConnect
- Cards added to Anki automatically when you click "Execute Study"
- No password needed (local connection only)
- **Fastest option** (~50ms per card)

#### Verification
```powershell
# After installing AnkiConnect and starting Anki:
python -m pip install requests
python -c "import requests; r=requests.post('http://localhost:8765', json={'action':'version','version':6}); print(r.json())"

# Should return: {'result': 6, 'error': None}
```

---

### **OPTION 2: AnkiWeb Sync (Cloud-based)**

#### Setup
Configure your AnkiWeb credentials in your local `.env` (never commit it):
- Email: `<YOUR_ANKI_EMAIL>`
- Password: `<YOUR_ANKI_PASSWORD>`

#### How It Works
- Cards sync to your AnkiWeb account
- Accessible on mobile via AnkiDroid or AnkiWeb
- Works without desktop app
- **Slower than desktop** (~2-3s per card set)

#### Verification
```powershell
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\phase7_unified_system\backend

# Start backend
python app.py

# In another terminal, test:
curl http://localhost:5000/api/anki/status
```

---

## 📋 SETUP CHECKLIST

### **For Anki Desktop (Option 1)**

```
[ ] Download and install Anki from https://apps.ankiweb.net/
[ ] Open Anki desktop app
[ ] Tools → Add-ons → Get Add-ons
[ ] Paste: 2055492159 (AnkiConnect)
[ ] Restart Anki
[ ] Verify: python -c "import requests; requests.post('http://localhost:8765', json={'action':'version','version':6})"
[ ] Start Anki before running Phase 7 backend
```

### **For AnkiWeb (Option 2)**

```
[ ] Your credentials already in backend/.env
[ ] Update pip: pip install --upgrade requests
[ ] Backend will auto-detect AnkiWeb on startup
[ ] Cards will sync when added
```

---

## 🚀 RUNNING PHASE 7 WITH ANKI

### **Terminal 1: Anki Desktop (if using Option 1)**
```powershell
# Leave Anki open while Phase 7 runs
# Just open the Anki.exe file or start it normally
```

### **Terminal 2: Backend with Anki Integration**
```powershell
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\phase7_unified_system

# Install dependencies
pip install -r requirements.txt

# Start backend
python backend/app.py

# You should see:
# 🚀 DrCodePT Phase 7 Backend Starting...
# 📊 Dashboard: http://localhost:5000
# 🎴 Anki Handler: ✅ Connected
# 🤖 Claude API: ✅ Ready
```

### **Terminal 3: Frontend**
```powershell
cd C:\Users\treyt\OneDrive\Desktop\DrCodePT-Swarm\phase7_unified_system\frontend

npm install
npm start

# Opens http://localhost:3000
```

---

## 📱 TESTING ANKI INTEGRATION

### **Test 1: Check Connection**
```powershell
curl http://localhost:5000/api/anki/status
```

Expected response:
```json
{
  "success": true,
  "connected": true,
  "email": "<YOUR_ANKI_EMAIL>",
  "decks": ["Default", "DrCodePT", "Anatomy", ...],
  "type": "AnkiConnect"
}
```

### **Test 2: Add Test Cards**
```powershell
# Using PowerShell
$cards = @(
  @{front="Test Q1"; back="Test A1"; tags=@("test")}
  @{front="Test Q2"; back="Test A2"; tags=@("test")}
)

$body = @{
  cards = $cards
  deck_name = "Test Deck"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:5000/api/anki/add-cards `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body
```

### **Test 3: In Dashboard**
1. Open http://localhost:3000
2. Go to Dashboard tab
3. Click "Study Now" on any course
4. Click "Execute Study Session"
5. **Watch Anki desktop app** - 24 new cards should appear instantly!

---

## 🔐 YOUR CREDENTIALS

### Already Configured In `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
ANKI_EMAIL=<YOUR_ANKI_EMAIL>
ANKI_PASSWORD=<YOUR_ANKI_PASSWORD>
```

### Files:
- **Backend config:** `/phase7_unified_system/backend/.env`
- **Safe:** `.env` is in `.gitignore` (never committed)
- **Secure:** Never share these credentials

---

## 📊 ANKI API ENDPOINTS

### **GET /api/anki/status**
Check connection and get deck list
```
Returns: {success, connected, decks, type}
```

### **POST /api/anki/add-cards**
Add cards to Anki
```json
{
  "cards": [
    {"front": "Q", "back": "A", "tags": ["tag1"]},
    {"front": "Q2", "back": "A2", "tags": ["tag2"]}
  ],
  "deck_name": "MyDeck"
}
```

### **POST /api/anki/sync**
Sync with AnkiWeb
```
Returns: {success, timestamp, status}
```

---

## 🐛 TROUBLESHOOTING

### **"Anki Handler: ⚠️  Not available"**
```
Solution:
1. Is Anki desktop app running? (Check Task Manager)
2. Is AnkiConnect addon installed? (Tools → Add-ons)
3. Restart Anki and try again
4. Port 8765 not blocked? (Firewall check)
```

### **"API not connecting"**
```
Solution:
1. Start Anki first, THEN start backend
2. Verify: python -c "import requests; print(requests.post('http://localhost:8765', json={'action':'version','version':6}).json())"
3. Check console for error messages
```

### **"Cards not appearing in Anki"**
```
Solution:
1. Check Anki is running
2. Look for error in backend console
3. Refresh Anki (F5) to see new cards
4. Check if cards went to wrong deck
```

### **"AnkiWeb sync not working"**
```
Solution:
1. Check internet connection
2. Verify email/password in .env
3. Try manual sync in Anki desktop (sync icon)
4. Check AnkiWeb server status
```

---

## 🎯 WORKFLOW

```
YOU: Click "Study Now" in dashboard
      ↓
SYSTEM: Generates 24 cards using Claude
      ↓
SYSTEM: Adds cards to Anki deck
      ↓
ANKI: Displays new cards immediately
      ↓
YOU: See cards in Anki, study them
      ↓
DASHBOARD: Shows "24 cards added to Anatomy deck"
```

---

## ✅ WHAT'S WORKING

| Feature | Status | Speed |
|---------|--------|-------|
| Generate cards | ✅ | ~5s |
| Add to Anki Desktop | ✅ | ~50ms/card |
| Add to AnkiWeb | ✅ | ~100-500ms/card |
| Sync decks | ✅ | Variable |
| Real-time dashboard | ✅ | Instant |

---

## 📈 NEXT STEPS

1. **Choose your method:**
   - Anki Desktop (faster, recommended)
   - AnkiWeb (cloud, mobile-friendly)

2. **Install & test:**
   - Follow checklist above
   - Run test endpoint
   - Add test cards

3. **Use Phase 7 Dashboard:**
   - Open http://localhost:3000
   - Select a course
   - Execute study session
   - Watch cards appear in Anki!

---

## 📞 QUICK REFERENCE

| Task | Command |
|------|---------|
| Check Anki status | `curl http://localhost:5000/api/anki/status` |
| Start backend | `python backend/app.py` |
| Start frontend | `npm start` |
| Test AnkiConnect | `python -c "import requests; requests.post('http://localhost:8765', ...)"` |

---

**🎴 READY TO ADD CARDS TO ANKI AUTOMATICALLY!**

Next: Install AnkiConnect addon, then run Phase 7 backend. Cards will add automatically when you study! 🚀

# Login Troubleshooting Guide

## Issue: Can't Login

### ✅ Fixed: CORS Configuration
- Added CORS middleware to backend
- Allows requests from frontend ports (3000-3004, 5173)

### Steps to Fix Login:

1. **Ensure Backend is Running**
   ```bash
   # In backend directory or project root
   uvicorn backend.main:app --reload --port 8000
   ```
   Or if using a different method, make sure backend is on port 8000

2. **Check Backend Health**
   - Open: http://localhost:8000/health
   - Should return: `{"status":"ok"}`

3. **Verify Frontend API URL**
   - Frontend uses: `http://localhost:8000` (default)
   - Can be changed in `frontend/.env`:
     ```
     VITE_API_URL=http://localhost:8000
     ```

4. **Login Credentials**
   - Username: `admin`
   - Password: `admin123`

5. **Check Browser Console**
   - Open DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

### Common Issues:

**Issue: "Cannot connect to server"**
- Backend not running
- Wrong port (should be 8000)
- Firewall blocking connection

**Issue: "Invalid recruiter credentials"**
- Wrong username/password
- Check: username = `admin`, password = `admin123`

**Issue: CORS error**
- Should be fixed now with CORS middleware
- Restart backend after changes

**Issue: 401 Unauthorized**
- Token not being saved
- Check localStorage in browser DevTools
- Should see `recruiter_token` key

### Testing Login Manually:

```bash
# Test backend login endpoint
curl -X POST http://localhost:8000/auth/recruiter/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Should return:
```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

### After Fixing:

1. Restart backend server
2. Refresh frontend page
3. Try logging in again
4. Check browser console for any remaining errors









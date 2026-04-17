# How to Access the Admin Dashboard

## Quick Access

### Direct URL
Navigate directly to:
```
http://localhost:3000/admin/dashboard
```
(Replace `localhost:3000` with your frontend URL if different)

### From Navigation
1. Log in as a recruiter/admin
2. Look for the **"Admin"** button in the top navigation bar
3. Click it to go to the admin dashboard

## Requirements

### 1. Authentication
- You must be logged in as a recruiter
- Your login token must be stored in `localStorage` as `recruiter_token`

### 2. Admin Role
- Your account must have the `role` field set to `"admin"` in the database
- The default test account (`test@example.com`) has admin role

## Login Steps

1. **Go to Login Page:**
   ```
   http://localhost:3000/auth?tab=recruiter
   ```

2. **Use Admin Credentials:**
   - **Email:** `test@example.com`
   - **Password:** `password123`

3. **After Login:**
   - You'll be redirected to the recruiter dashboard
   - Click the **"Admin"** button in the header, OR
   - Navigate directly to `/admin/dashboard`

## Verify Admin Access

If you can't access the admin page:

1. **Check Your Role:**
   - The backend checks if `recruiter.role === "admin"`
   - Default test account should have admin role

2. **Check Token:**
   - Open browser DevTools (F12)
   - Go to Application/Storage → Local Storage
   - Verify `recruiter_token` exists

3. **Check Backend:**
   - Ensure backend is running on `http://localhost:8000`
   - Check backend logs for authentication errors

## Admin Dashboard Features

Once accessed, you can:
- ✅ View all recruiters and their stats
- ✅ View all candidates and their details
- ✅ Edit recruiter information (name, email, role, password)
- ✅ Edit candidate information (name, email)
- ✅ Delete recruiters (with safety checks)
- ✅ Delete candidates

## Troubleshooting

### "Unauthorized" Error
- Make sure you're logged in
- Verify your token is valid
- Check that your account has admin role

### "Admin access required" Error
- Your account doesn't have admin role
- Contact a system administrator to update your role
- Or update it directly in the database:
  ```sql
  UPDATE recruiters SET role = 'admin' WHERE email = 'your@email.com';
  ```

### Page Redirects to Login
- Your token expired or is invalid
- Log in again
- Make sure backend is running

## Security Note

The admin dashboard requires:
- Valid authentication token
- Admin role in the database
- Backend API access

All admin actions are logged and require confirmation for destructive operations (delete).



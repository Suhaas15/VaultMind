# Skyflow Authentication Troubleshooting

## Current Issue

Getting `401 Unauthorized` errors with message: "Authentication failed. Invalid issuer. Check your JWT assertion's 'iss' value."

## Diagnosis Results

✅ **Token Structure**: Correct - JWT is properly formatted with correct claims  
✅ **Issuer Match**: Token issuer (`iss`) matches credentials keyID  
❌ **Vault API**: JWT not accepted directly - returns 401  
❌ **OAuth Exchange**: Fails with "Failed to load ServiceAccount ID"  

## Root Cause

The error "Failed to load ServiceAccount ID wb067fe2565e46058421030607397bd6" during OAuth exchange suggests:
- The service account may not exist in your Skyflow account
- The `keyID` in `credentials.json` might be incorrect
- Credentials might be from a different Skyflow environment/account
- Service account might be inactive or deleted

## Solutions

### 1. Verify Credentials in Skyflow Studio

1. Log into [Skyflow Studio](https://manage.skyflowapis-preview.com) (or production)
2. Go to **Service Accounts** section
3. Verify the service account with keyID `wb067fe2565e46058421030607397bd6` exists
4. Check if the service account is **Active**
5. Verify the service account has **permissions** for your vault

### 2. Regenerate Service Account Credentials

If the service account doesn't exist or seems incorrect:

1. In Skyflow Studio, go to **Service Accounts**
2. Create a new service account (or regenerate credentials for existing one)
3. Download the new `credentials.json` file
4. Replace your current `credentials.json` with the new one
5. Regenerate the token:
   ```bash
   python3 generate_skyflow_token.py
   ```
6. Update `.env` with the new token

### 3. Verify Environment Match

Ensure your credentials match the environment:

- **Preview**: `https://manage.skyflowapis-preview.com`
- **Production**: `https://manage.skyflowapis.com`

Check your `.env`:
```bash
SKYFLOW_VAULT_URL=https://a370a9658141.vault.skyflowapis-preview.com  # Preview
```

Your `tokenURI` should match:
- Preview: `https://manage.skyflowapis-preview.com/v1/auth/sa/oauth/token`
- Production: `https://manage.skyflowapis.com/v1/auth/sa/oauth/token`

### 4. Check Vault Permissions

Ensure the service account has access to your vault:

1. In Skyflow Studio, go to your vault
2. Check **Access** or **Permissions** settings
3. Verify the service account has permissions to:
   - Insert records
   - Query records
   - Tokenize/detokenize

### 5. Test Authentication

After updating credentials, test authentication:

```bash
# Verify credentials structure
python3 verify_skyflow_token.py

# Test authentication
python3 test_skyflow_auth.py

# Regenerate token
python3 generate_skyflow_token.py
```

## Quick Fix

1. **Download fresh credentials** from Skyflow Studio
2. **Replace** `credentials.json` 
3. **Regenerate token**:
   ```bash
   python3 generate_skyflow_token.py
   ```
4. **Update** `.env` file with new token
5. **Restart** the application

## Additional Resources

- [Skyflow API Authentication Docs](https://docs.skyflow.com/api-authentication/)
- [Skyflow Service Accounts](https://docs.skyflow.com/docs/fundamentals/service-accounts)
- [Skyflow Data API](https://docs.skyflow-preview.com/api/data)


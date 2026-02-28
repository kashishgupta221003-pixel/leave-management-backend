from firebase_admin import auth
import firebase_config  # Import to ensure the app is initialized

# The firebase_config import handles the initialization.

# 🔥 Replace this with actual user UID from Firebase Authentication
uid = "cWCFSNINHvPxFB4KOiMmFAbiRGQ2"
# Set role (employee or manager)
auth.set_custom_user_claims(uid, {"role": "employee"})

# uid = "vMqrSLRwIEfWb9zfUX7MW9ZIjJB3"
# auth.set_custom_user_claims(uid, {"role": "employee"})
uid = "vMqrSLRwIEWb9zfUX7MW9ZIjJJB3"

auth.set_custom_user_claims(uid, {"role": "employee"})

print("Custom claim set successfully")

uid = "sdA9FgiHnMf9HaOJffhA2bFqmT52"
auth.set_custom_user_claims(uid, {"role": "manager"})


print("Role assigned successfully!")

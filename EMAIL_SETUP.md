# Email Configuration for Smart Study Portal

# For REAL email sending, you need to:

# 1. Create a Gmail account: smartstudyportal2024@gmail.com
# 2. Enable 2-Factor Authentication
# 3. Generate an App Password (not your regular password)

# Steps to setup Gmail App Password:
# 1. Go to Google Account settings
# 2. Security → 2-Step Verification → App passwords
# 3. Generate password for "Mail"
# 4. Use that password in the code

# Alternative: Use a free email service like:
# - SendGrid (free tier: 100 emails/day)
# - Mailgun (free tier: 5,000 emails/month)
# - SMTP2GO (free tier: 1,000 emails/month)

# For WhatsApp, you can use:
# 1. CallMeBot API (free)
# 2. Twilio WhatsApp API (paid)
# 3. WhatsApp Business API (paid)

# Current setup uses:
# - Gmail SMTP for emails
# - CallMeBot API for WhatsApp
# - Fallback to WhatsApp Web links

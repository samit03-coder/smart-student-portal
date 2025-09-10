# 🚀 REAL Email & WhatsApp Setup Guide

## 📧 **Email Setup (Choose One):**

### Option 1: Gmail SMTP (Recommended)
1. **Create Gmail account:** `smartstudyportal2024@gmail.com`
2. **Enable 2-Factor Authentication**
3. **Generate App Password:**
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use that password in `main.py` line 41

### Option 2: Free Email Service (Easier)
1. **Sign up for EmailJS:** https://www.emailjs.com/ (Free: 200 emails/month)
2. **Get your service ID and template ID**
3. **Replace the email function with EmailJS API**

### Option 3: SendGrid (Professional)
1. **Sign up for SendGrid:** https://sendgrid.com/ (Free: 100 emails/day)
2. **Get API key**
3. **Use SendGrid Python SDK**

## 📱 **WhatsApp Setup:**

### Option 1: CallMeBot (Free)
1. **Go to:** https://www.callmebot.com/blog/free-api-whatsapp-messages/
2. **Get your API key**
3. **Replace API key in `main.py` line 107**

### Option 2: WhatsApp Web Links (Always Works)
- Already implemented as fallback
- Opens WhatsApp Web with pre-filled message

### Option 3: Twilio WhatsApp API (Professional)
1. **Sign up for Twilio:** https://www.twilio.com/
2. **Get WhatsApp API credentials**
3. **Use Twilio Python SDK**

## ⚡ **Quick Setup (5 minutes):**

### For Email:
```python
# In main.py, line 41, replace:
sender_password = "your_app_password_here"
# With your Gmail App Password
```

### For WhatsApp:
```python
# In main.py, line 107, replace:
api_key = "123456789"
# With your CallMeBot API key
```

## 🎯 **Current Status:**
- ✅ **Email:** Ready to work with Gmail App Password
- ✅ **WhatsApp:** Ready to work with CallMeBot API
- ✅ **Fallback:** WhatsApp Web links always work
- ✅ **Download:** Google Drive links work immediately

## 🔧 **Test Commands:**
```bash
# Test email sending
python -c "from main import send_email_notification; send_email_notification('test@example.com', 'Test Material', 'https://example.com')"

# Test WhatsApp
python -c "from main import send_whatsapp_message; send_whatsapp_message('1234567890', 'Test Material', 'https://example.com')"
```

## 📞 **Support:**
- Email: smartstudyportal2024@gmail.com
- WhatsApp: +91-1234567890
- Portal: http://localhost:5000

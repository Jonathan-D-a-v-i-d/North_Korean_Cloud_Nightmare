import pyqrcode
import sys

mfa_secret = sys.argv[1]  # Pass the secret as an argument
issuer = "AWS"
account_name = "DevopsUser"

# Generate OTP Auth URI
otp_auth_uri = f"otpauth://totp/{issuer}:{account_name}?secret={mfa_secret}&issuer={issuer}"

# Generate and display QR Code
qr = pyqrcode.create(otp_auth_uri)
print(qr.terminal(quiet_zone=1))


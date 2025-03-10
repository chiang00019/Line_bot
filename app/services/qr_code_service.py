import cv2
import pyzbar.pyzbar as pyzbar
import base64
import binascii
import urllib.parse
import re
from google.protobuf.message import DecodeError
from google_authenticator_pb2 import MigrationPayload  # 解析 Google Authenticator QR Code
from PIL import Image

# Email 正規表達式
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

def fix_base64_padding(encoded_str):
    """ 修正 Base64 Padding """
    encoded_str = encoded_str.strip()
    missing_padding = len(encoded_str) % 4
    if missing_padding:
        encoded_str += '=' * (4 - missing_padding)
    return encoded_str

def extract_qr_data(image_path):
    """ 從 QR Code 圖片中讀取並解析資料 """
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "無法載入圖片，請確認圖片是否損壞！"}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    decoded_objects = pyzbar.decode(gray)

    if not decoded_objects:
        return {"error": "沒有偵測到 QR Code，請確認圖片清晰度！"}

    qr_contents = [obj.data.decode("utf-8") for obj in decoded_objects]
    return {"qr_data": qr_contents}

def decode_google_authenticator(qr_data):
    """ 解析 Google Authenticator QR Code，提取金鑰 """
    if "otpauth-migration://" not in qr_data:
        return {"error": "QR Code 並非 Google Authenticator 格式！"}

    try:
        encoded_data = qr_data.split("data=")[1]
        encoded_data = urllib.parse.unquote(encoded_data)
        encoded_data = fix_base64_padding(encoded_data)
        decoded_data = base64.b64decode(encoded_data)

        payload = MigrationPayload()
        payload.ParseFromString(decoded_data)

        accounts_data = []
        for account in payload.otp_parameters:
            accounts_data.append({
                "email": account.name,  # 假設 Google Authenticator 儲存的名稱是 Email
                "secret_key": base64.b32encode(account.secret).decode("utf-8"),
                "issuer": account.issuer
            })

        return {"accounts": accounts_data}

    except DecodeError:
        return {"error": "無法解析 Google Authenticator QR Code！"}
    except binascii.Error as e:
        return {"error": f"Base64 解析錯誤: {e}"}

def extract_emails_from_qr(qr_data):
    """ 從 QR Code 內容中提取 Email """
    emails = re.findall(EMAIL_REGEX, qr_data)
    return {"emails": emails} if emails else {"error": "未偵測到 Email"}

def process_qr_code(image_path):
    """ 綜合處理 QR Code 圖片，解析 Email 與 Google Authenticator 金鑰 """
    result = extract_qr_data(image_path)

    if "error" in result:
        return result

    all_emails = []
    all_accounts = []

    for qr_text in result["qr_data"]:
        email_result = extract_emails_from_qr(qr_text)
        if "emails" in email_result:
            all_emails.extend(email_result["emails"])

        auth_result = decode_google_authenticator(qr_text)
        if "accounts" in auth_result:
            all_accounts.extend(auth_result["accounts"])

    return {
        "emails": list(set(all_emails)),  # 避免重複 Email
        "accounts": all_accounts
    }


if __name__ == "__main__":
    image_path = r"C:\Users\Michael\Desktop\Line_bot\app\Key.jpg"  # 你的 QR Code 圖片
    qr_result = process_qr_code(image_path)

    # 輸出 Email
    if qr_result.get("emails"):
        print("\n📧 解析到的 Email:")
        for email in qr_result["emails"]:
            print(f"- {email}")
    else:
        print("\n❌ 沒有找到 Email")

    # 輸出 Google Authenticator 帳戶
    if qr_result.get("accounts"):
        print("\n🔑 解析到的 Google Authenticator 帳戶:")
        for account in qr_result["accounts"]:
            print(f"- Email: {account['email']}")
            print(f"  Issuer: {account['issuer']}")
            print(f"  Secret Key: {account['secret_key']}\n")
    else:
        print("\n❌ 沒有找到 Google Authenticator 資料")


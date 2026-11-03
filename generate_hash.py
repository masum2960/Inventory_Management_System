from werkzeug.security import generate_password_hash

password = "AdminTest123!"

hashed_password = generate_password_hash(password)

print("User ID: U001")
print("Normal password: AdminTest123!")
print("Hashed password:")
print(hashed_password)
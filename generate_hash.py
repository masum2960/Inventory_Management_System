from werkzeug.security import generate_password_hash

password = "staff3"

hashed_password = generate_password_hash(password)

print("User ID: U003")
print("Normal password: staff3")
print("Hashed password:")
print(hashed_password)

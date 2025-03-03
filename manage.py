from models import User

username = input("Enter username: ")
password = input("Enter password: ")

user = User(username, User.hash_password(password), role="admin")
user.save()
print("Admin user created.")

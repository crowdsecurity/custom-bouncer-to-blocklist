import sys

print("Hello!")

# Print all arguments passed to the script
if len(sys.argv) > 1:
    print("Arguments received:")
    for arg in sys.argv[1:]:  # sys.argv[0] is the script name
        print(f"- {arg}")
else:
    print("No arguments received.")

while True:
    user_input = input()  # Waits for stdin
    if user_input.strip().lower() == "exit":
        print("Goodbye!")
        break
    print(f"You said: {user_input}")
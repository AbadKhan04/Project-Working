import random
import time
import os

# Colors for terminal output (may not work on all consoles)
colors = [
    '\033[91m',  # Red
    '\033[92m',  # Green
    '\033[93m',  # Yellow
    '\033[94m',  # Blue
    '\033[95m',  # Purple
    '\033[96m',  # Cyan
    '\033[0m'    # Reset
]

# Generate a list of random numbers
def generate_random_list(size=20, start=0, end=100):
    return [random.randint(start, end) for _ in range(size)]

# Print a colorful list
def print_colorful_list(lst):
    for i, val in enumerate(lst):
        color = colors[i % (len(colors) - 1)]
        print(f"{color}{val}\033[0m", end=' ')
    print()

# Insertion sort with animation
def insertion_sort_animated(arr):
    a = arr.copy()
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and key < a[j]:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Sorting Animation (Insertion Sort)")
        print_colorful_list(a)
        time.sleep(0.5)
    return a

# Random quotes while doing nothing useful
quotes = [
    "Why sort when you can scramble?",
    "If it works, it’s probably luck.",
    "Real coders don’t need comments. Or sleep.",
    "This does nothing. And that’s the point.",
    "Keep staring, something might happen.",
    "I promise this is important. Maybe.",
    "Zero bugs, infinite nonsense."
]

def random_useless_quote():
    return random.choice(quotes)

# Main execution
if __name__ == "__main__":
    print("Welcome to the Ultimate Useless Sort-o-Matic 3000\n")

    nums = generate_random_list()
    print("Original List:")
    print_colorful_list(nums)

    print("\nPicking a random useless quote before sorting...")
    time.sleep(1)
    print(f"🧠 {random_useless_quote()}")
    time.sleep(2)

    print("\nBeginning animated insertion sort...")
    sorted_list = insertion_sort_animated(nums)

    print("\nFinal Sorted List:")
    print_colorful_list(sorted_list)

    print(f"\n✨ {random_useless_quote()}")
    print("\nDone doing absolutely everything and nothing. 🍵")

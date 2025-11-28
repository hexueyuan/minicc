#!/usr/bin/env python3
"""
Random Number Generator Script
Generates random numbers in various formats
"""

import random

def generate_random_integers(count=10, min_val=1, max_val=100):
    """Generate random integers"""
    return [random.randint(min_val, max_val) for _ in range(count)]

def generate_random_floats(count=10):
    """Generate random floats between 0 and 1"""
    return [random.random() for _ in range(count)]

def main():
    print("=== Random Number Generator ===\n")
    
    # Generate integers
    integers = generate_random_integers(5)
    print(f"Random Integers (1-100): {integers}")
    
    # Generate floats
    floats = generate_random_floats(5)
    print(f"Random Floats (0-1): {[f'{x:.4f}' for x in floats]}")
    
    # Generate a random choice
    colors = ['red', 'blue', 'green', 'yellow', 'purple']
    print(f"Random Color: {random.choice(colors)}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Demo script showing how the agent would solve the prime squares problem
"""

from tools import execute_code

def demo_prime_squares_problem():
    """Demonstrate solving the prime squares problem with code execution"""
    
    print("🧪 Demo: Prime Squares Problem")
    print("=" * 60)
    print("Problem: Sum of squares of all primes from 1 to 69997, modulo 1000")
    print()
    
    # This is the code the agent would generate
    code = """
def is_prime(n):
    \"\"\"Check if a number is prime\"\"\"
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to sqrt(n)
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True

def sum_of_squares_of_primes(n):
    \"\"\"Compute sum of squares of all primes from 1 to n, modulo 1000\"\"\"
    total = 0
    count = 0
    
    # Find all primes up to n and sum their squares
    for num in range(2, n + 1):
        if is_prime(num):
            total = (total + num * num) % 1000
            count += 1
            
            # Progress indicator for large numbers
            if count % 1000 == 0:
                print(f"Found {count} primes so far...")
    
    return total, count

# Solve the problem
n = 69997
print(f"Computing sum of squares of primes from 1 to {n}...")
result, prime_count = sum_of_squares_of_primes(n)

print(f"\\nFound {prime_count} prime numbers")
print(f"Sum of their squares modulo 1000: {result}")
"""
    
    print("🔧 Executing code...")
    print("-" * 40)
    
    # Execute the code using our tool
    result = execute_code(code)
    print(result)
    
    print("-" * 40)
    print("✅ Code execution completed!")

if __name__ == "__main__":
    demo_prime_squares_problem()

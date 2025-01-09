import secrets
import hashlib


def generate_cif(length, mod_divisor=10) -> str:
    sequence = ""
    for _ in range(length - 1):
        sequence += str(secrets.randbelow(10))

    return sequence + str(int(get_valid_checksum_digit(sequence, mod_divisor)))


def get_valid_checksum_digit(sequence, mod_divisor=10):
    odd_sum = 0
    even_sum = 0
    second = True
    for i in range(len(sequence) - 1, -1, -1):
        if not second:
            odd_sum += int(sequence[i])
            second = not second
            continue
        second = not second
        addent = 2 * int(sequence[i])
        if addent > 9:
            addent = addent % 10 + 1
        even_sum += addent
    if (odd_sum + even_sum) % mod_divisor == 0:
        return 0

    return mod_divisor - ((odd_sum + even_sum) % mod_divisor)


def verify_checksum(sequence, mod_divisor=10):
    odd_sum = 0
    even_sum = 0
    second = False
    for i in range(len(sequence) - 1, -1, -1):
        if not second:
            odd_sum += int(sequence[i])
            second = not second
            continue
        second = not second
        addent = 2 * int(sequence[i])
        if addent > 9:
            addent = addent % 10 + 1
        even_sum += addent
    return ((odd_sum + even_sum) % mod_divisor) == 0


def generate_12_digit_number(branch_code, customer_id):
    # Convert inputs to strings and combine them
    branch_code = str(branch_code).zfill(4)  # Ensure branch code is 4 digits
    customer_id = str(customer_id).zfill(4)  # Ensure customer ID is 4 digits

    # Add a random component
    random_part = str(secrets.randbelow(10**4)).zfill(4)  # Random 4-digit number

    # Combine inputs
    input_string = f"{branch_code}{customer_id}{random_part}"

    # Generate a SHA-256 hash of the input string
    sha256_hash = hashlib.sha256(input_string.encode()).hexdigest()

    # Convert the hash to an integer and extract the first 12 digits
    hash_int = int(sha256_hash, 16)  # Convert hex to integer
    twelve_digit_number = str(hash_int)[:12]  # Get the first 12 digits

    return twelve_digit_number

"""
lefttruncatable.py is written to print out all left-truncatable primes.
According to "Truncatable prime" in
https://en.wikipedia.org/wiki/Truncatable_prime,
there are 4260 decimal left-truncatable primes.
"""

import time
import math
import sys

# Parameters
INIT_MILESTONE_INCREMENT = 100      # We report a milestone when we found
                                    # MILESTONE_INCREMENT more left
                                    # truncatable primes.
NUM_LAST_LEFTTRNCPRIMES_TO_PRINT = 10   # Number of the largest (found) left trunctable primes to print.
MAX_INT64 = float(sys.maxsize)      # Float representation of the largest int64

def is_prime(x):
    """
    is_prime() tests if the given argument x is a prime.  It does not
    perform checks like whether x is an integer, etc.
    """

    # Check if x is even
    if x % 2 == 0:
        return False

    # Check if x is a multiple of 3
    if x % 3 == 0:
        return False

    # x is odd and it is not a multiple of 3.  We check if x can be
    # divided by another integer by trying divisor_candidate of the
    # form (6k+5) and (6k+7) with k being an integer and see if x is
    # one of divisor_candidate's multiples.  If x is found to be a
    # multiple of such divisor_candidate's, the loop can end.
    x_isprime = True
    divisor_candidate = 5
    while divisor_candidate*divisor_candidate <= x:
        if (x % divisor_candidate == 0) or \
           (x % (divisor_candidate + 2) == 0):
            x_isprime = False
            break
        divisor_candidate += 6

    return x_isprime


def main():
    """
    main() to generate a list of left truncatable primes.
    """

    start_time = time.time()

    # The list left_truncatables starts with all the single-digit primes,
    # and they happen to be left-truncatable primes as well.
    left_truncatables = [2, 3, 5, 7]
    left_truncatable_seeds = left_truncatables[:]
    milestone_increment = INIT_MILESTONE_INCREMENT
    next_milestone = milestone_increment
    exceedingInt64Max = False

    while len(left_truncatable_seeds) > 0:
        left_truncatable_candidate = left_truncatable_seeds.pop(0)

        # left truncatable primes contain no 0, so we want to check if
        # we obtain another left truncatable prime by prepending a nonzero
        # digit to its left.
        next_power10 = 10**(math.ceil(math.log10(left_truncatable_candidate)))
        # Note that float next_power10 could be larger than MAX_INT64 already,
        # and we will catch it below.
        for i in range(1, 10):
            if float(left_truncatable_candidate) + next_power10 > MAX_INT64:
                exceedingInt64Max = True
                break
            left_truncatable_candidate += int(next_power10)
            if is_prime(left_truncatable_candidate):
                left_truncatable_seeds.append(left_truncatable_candidate)
                left_truncatables.append(left_truncatable_candidate)
                if len(left_truncatables) == next_milestone:
                    print('Milestone %d: %d' % (next_milestone, left_truncatable_candidate))
                    next_milestone += milestone_increment

        # Check if we are here because of exceedingInt64Max, or we checked all the i's.
        if exceedingInt64Max:
            break
            
    elapsed_time = time.time() - start_time
    # We are out of the while loop, which means left_truncatable_candidate
    # list is empty or exceedingInt64Max is True.  For the latter, we want to dump
    # left_truncatable_seeds and left_truncatable_candidate.
    if exceedingInt64Max:
        print('Current candidate: %d' % left_truncatable_candidate)
    left_truncatables.sort()

    # Printing some information.
    print('\nWe found %d left-truncatable primes so far in %0.4f seconds.' \
          % (len(left_truncatables), elapsed_time))
    print("The largest left-truncatable primes are:")
    for left_truncatable in left_truncatables[-NUM_LAST_LEFTTRNCPRIMES_TO_PRINT:]:
        print(left_truncatable)
    return(0)


if __name__ == '__main__':
    main()

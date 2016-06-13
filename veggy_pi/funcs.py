#!/usr/bin/env python


def is_number(num):
    """
    """
    try:
        n = float(num)
    except ValueError:
        return False
    return True


def all_numbers(*numbers):
    """
    """
    for num in numbers:
        if not is_number(num):
            return False
    return True
